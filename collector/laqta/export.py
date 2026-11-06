"""Write the catalog as one JSON file the live web app reads (no server needed).

Run after every collection:  python -m laqta export --out ../laqta-web/data/products.json
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

from .config import Settings
from .db import DB
from .models import CATEGORIES, STORES, now_iso

# Store search pages, used only for sample products that have no real affiliate link yet
SEARCH_URLS = {
    "amazon": "https://www.amazon.sa/s?k={q}",
    "noon": "https://www.noon.com/saudi-ar/search/?q={q}",
    "shein": "https://ar.shein.com/pdsearch/{q}/",
    "aliexpress": "https://ar.aliexpress.com/w/wholesale-{q}.html",
    "namshi": "https://www.namshi.com/saudi-ar/search?q={q}",
    "temu": "https://www.temu.com/search_result.html?search_key={q}",
}


def _offer(row: dict, share: float, history: list[dict], amazon_tag: str = "") -> dict:
    rate = row["commission_rate"] or 0
    cashback = round(row["price"] * rate * share, 2)
    url = row["url"]
    sample = "example.com" in url or "laqta-demo" in url
    if sample:
        url = SEARCH_URLS[row["store"]].format(q=quote(row["title"]))
        # An Amazon Associates tag on a normal Amazon link still earns commission,
        # even before you qualify for the API.
        if row["store"] == "amazon" and amazon_tag:
            url += f"&tag={quote(amazon_tag)}"
    return {
        "uid": row["uid"],
        "store": row["store"],
        "price": row["price"],
        "old_price": row["old_price"],
        "cashback": cashback,
        "net_price": round(row["price"] - cashback, 2),
        "shipping": row["shipping"],
        "url": url,
        "sample": sample,
        "rating": row["rating"],
        "history": history,
    }


def build(db: DB, settings: Settings) -> dict:
    rows = db.rows("SELECT * FROM products WHERE active=1 ORDER BY trend_score DESC")
    hist: dict[str, list] = defaultdict(list)
    for h in db.rows("SELECT uid, at, price FROM price_history ORDER BY at"):
        hist[h["uid"]].append({"at": h["at"][:10], "price": h["price"]})

    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[r["group_id"] or r["uid"]].append(r)

    items = []
    for gid, members in groups.items():
        top = members[0]  # rows are sorted by trend score, so the first is the strongest
        offers = sorted((_offer(m, settings.cashback_share, hist[m["uid"]][-30:], settings.amazon_partner_tag)
                         for m in members),
                        key=lambda o: o["net_price"])
        best = offers[0]
        olds = [o["old_price"] for o in offers if o["old_price"]]
        items.append({
            "id": gid,
            "title": top["title"],
            "category": top["category"],
            "image": next((m["image"] for m in members if m["image"]), None),
            "brand": top["brand"],
            "rating": max((m["rating"] or 0 for m in members), default=0) or None,
            "sales": sum(m["sales"] or 0 for m in members),
            "hot": any(m["is_hot"] for m in members),
            "score": max(m["trend_score"] for m in members),
            "price": best["price"],
            "old_price": max(olds) if olds else None,
            "best_store": best["store"],
            "best_net": best["net_price"],
            "max_cashback": max(o["cashback"] for o in offers),
            "offers": offers,
        })
    items.sort(key=lambda i: i["score"], reverse=True)
    for i, item in enumerate(items, 1):
        item["rank"] = i
    return {
        "generated_at": now_iso(),
        "sample": all(o["sample"] for i in items for o in i["offers"]),
        "cashback_share": settings.cashback_share,
        "stores": [{"id": k, "name": v} for k, v in STORES.items()],
        "categories": [{"id": k, "name": v} for k, v in CATEGORIES.items()],
        "products": items,
    }


def export(out: str, settings: Settings | None = None) -> int:
    settings = settings or Settings()
    data = build(DB(settings.db_path), settings)
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return len(data["products"])
