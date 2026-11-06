"""Trend score (what goes on top) and matching the same product across stores."""
from __future__ import annotations

import hashlib
import math
import re
from collections import defaultdict
from datetime import datetime, timezone

from .db import DB

# --- trend score ---------------------------------------------------------------------------------
# Weights add up to 100. Tune them as you learn what your users click and buy.
WEIGHTS = {
    "velocity": 35,   # selling fast right now (sales added since the last run)
    "sales": 20,      # sold a lot in total
    "hot": 15,        # the store itself flags it hot / best seller
    "rank": 10,       # Amazon-style sales rank (lower is better)
    "discount": 10,   # big discount
    "rating": 5,      # well rated
    "new": 5,         # just appeared
}


def _percentiles(values: dict[str, float]) -> dict[str, float]:
    """uid -> 0..1 position among its peers (ties share a value). Missing values -> 0."""
    present = {k: v for k, v in values.items() if v is not None and v > 0}
    if not present:
        return {k: 0.0 for k in values}
    ordered = sorted(set(present.values()))
    pos = {v: (i + 1) / len(ordered) for i, v in enumerate(ordered)}
    return {k: pos.get(v, 0.0) if v else 0.0 for k, v in values.items()}


def compute_trend_scores(db: DB) -> int:
    rows = db.rows("SELECT uid, store, sales, sales_velocity, sales_rank, is_hot, price, old_price, rating, first_seen "
                   "FROM products WHERE active=1")
    by_store: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_store[r["store"]].append(r)

    now = datetime.now(timezone.utc)
    updates = []
    for store_rows in by_store.values():
        # Compare each product with others from the SAME store, since stores report sales differently
        vel = _percentiles({r["uid"]: r["sales_velocity"] for r in store_rows})
        sales = _percentiles({r["uid"]: math.log1p(r["sales"]) if r["sales"] else None for r in store_rows})
        for r in store_rows:
            discount = 0.0
            if r["old_price"] and r["old_price"] > r["price"] > 0:
                discount = min((1 - r["price"] / r["old_price"]) / 0.6, 1.0)
            rank = 0.0
            if r["sales_rank"]:
                rank = max(0.0, 1 - math.log10(r["sales_rank"]) / 5)  # rank 1 → 1.0, rank 100k → 0
            rating = max(0.0, ((r["rating"] or 0) - 3.5) / 1.5) if r["rating"] else 0.0
            age_days = (now - datetime.fromisoformat(r["first_seen"])).total_seconds() / 86400
            new = 1.0 if age_days <= 3 else 0.0
            score = (WEIGHTS["velocity"] * vel[r["uid"]] + WEIGHTS["sales"] * sales[r["uid"]]
                     + WEIGHTS["hot"] * (1.0 if r["is_hot"] else 0.0) + WEIGHTS["rank"] * rank
                     + WEIGHTS["discount"] * discount + WEIGHTS["rating"] * min(rating, 1.0)
                     + WEIGHTS["new"] * new)
            updates.append((round(score, 2), r["uid"]))
    with db.tx() as c:
        c.executemany("UPDATE products SET trend_score=? WHERE uid=?", updates)
    return len(updates)


# --- cross-store matching ------------------------------------------------------------------------
_STOP = {"the", "and", "for", "with", "new", "of", "in", "a", "an", "to", "by", "set", "pcs", "piece", "pieces",
         "2024", "2025", "2026", "original", "men", "women", "unisex", "مع", "و", "من", "الى", "جديد"}
_TOKEN = re.compile(r"[a-z0-9؀-ۿ]+")


def tokens(title: str) -> frozenset[str]:
    words = _TOKEN.findall(title.lower())
    return frozenset(w for w in words if len(w) > 1 and w not in _STOP)


def similarity(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def match_groups(db: DB, threshold: float = 0.6) -> int:
    """Give the same product in different stores one group_id, so the app can compare prices.

    Simple and dependable for thousands of products per category. For very large catalogs,
    replace with a proper search index or embeddings, and match on brand/model codes or GTIN/EAN.
    """
    rows = db.rows("SELECT uid, store, title, category, price FROM products WHERE active=1")
    parent = {r["uid"]: r["uid"] for r in rows}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    by_cat: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        r["tok"] = tokens(r["title"])
        by_cat[r["category"]].append(r)

    for items in by_cat.values():
        for i, a in enumerate(items):
            for b in items[i + 1:]:
                if a["store"] == b["store"]:
                    continue
                lo, hi = sorted((a["price"], b["price"]))
                if lo <= 0 or hi / lo > 2.5:  # wildly different price → probably not the same item
                    continue
                if similarity(a["tok"], b["tok"]) >= threshold:
                    parent[find(a["uid"])] = find(b["uid"])

    groups: dict[str, list[str]] = defaultdict(list)
    for uid in parent:
        groups[find(uid)].append(uid)
    updates = []
    for members in groups.values():
        gid = "g_" + hashlib.sha1(min(members).encode()).hexdigest()[:12]
        updates.extend((gid, uid) for uid in members)
    with db.tx() as c:
        c.executemany("UPDATE products SET group_id=? WHERE uid=?", updates)
    return sum(1 for m in groups.values() if len(m) > 1)
