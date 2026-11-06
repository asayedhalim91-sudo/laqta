"""The API your app and website call. Run: uvicorn laqta.api:app --reload  → docs at /docs"""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .db import DB
from .models import CATEGORIES, STORES

settings = Settings()
db = DB(settings.db_path)

app = FastAPI(title="Laqta API", version="1.0",
              description="Products from every store, ranked by what is trending in Saudi Arabia.")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET"], allow_headers=["*"])

PUBLIC = ("uid, store, title, price, old_price, currency, url, image, category, brand, rating, reviews, "
          "sales, is_hot, commission_rate, shipping, group_id, trend_score, last_seen")


def _shape(row: dict) -> dict:
    """Add the fields the app shows: store name in Arabic, discount, cashback, net price."""
    price, old = row["price"], row.get("old_price")
    rate = row.get("commission_rate") or 0
    cashback = round(price * rate * settings.cashback_share, 2)
    out = {k: v for k, v in row.items() if k != "commission_rate"}  # keep your commission private
    out.update(
        store_name=STORES.get(row["store"], row["store"]),
        category_name=CATEGORIES.get(row["category"], row["category"]),
        discount=round(1 - price / old, 2) if old and old > price else 0,
        cashback=cashback,
        cashback_rate=round(rate * settings.cashback_share, 4),
        net_price=round(price - cashback, 2),
        is_hot=bool(row.get("is_hot")),
    )
    return out


def _one_per_group(rows: list[dict], limit: int) -> list[dict]:
    """Show each product once (its best-ranked store), with how many stores sell it."""
    gids = sorted({r["group_id"] for r in rows if r["group_id"]})
    counts: dict[str, int] = {}
    for i in range(0, len(gids), 500):  # SQLite parameter limit
        chunk = gids[i:i + 500]
        for c in db.rows(f"SELECT group_id, COUNT(*) AS n FROM products WHERE active=1 AND group_id IN "
                         f"({','.join('?' * len(chunk))}) GROUP BY group_id", tuple(chunk)):
            counts[c["group_id"]] = c["n"]
    seen, out = set(), []
    for r in rows:
        g = r["group_id"] or r["uid"]
        if g in seen:
            continue
        seen.add(g)
        item = _shape(r)
        item["store_count"] = counts.get(g, 1)
        out.append(item)
        if len(out) >= limit:
            break
    return out


def _filters(category: Optional[str], store: Optional[str]) -> tuple[str, list]:
    where, params = ["active=1"], []
    if category:
        if category not in CATEGORIES:
            raise HTTPException(400, f"category must be one of {list(CATEGORIES)}")
        where.append("category=?")
        params.append(category)
    if store:
        if store not in STORES:
            raise HTTPException(400, f"store must be one of {list(STORES)}")
        where.append("store=?")
        params.append(store)
    return " AND ".join(where), params


@app.get("/health")
def health():
    runs = db.rows("SELECT source, finished_at, products, error IS NOT NULL AS failed FROM runs ORDER BY id DESC LIMIT 10")
    total = db.rows("SELECT COUNT(*) AS n FROM products WHERE active=1")[0]["n"]
    return {"ok": True, "active_products": total, "last_runs": runs}


@app.get("/stores")
def stores():
    counts = {r["store"]: r["n"] for r in db.rows("SELECT store, COUNT(*) AS n FROM products WHERE active=1 GROUP BY store")}
    return [{"id": k, "name": v, "products": counts.get(k, 0)} for k, v in STORES.items()]


@app.get("/categories")
def categories():
    return [{"id": k, "name": v} for k, v in CATEGORIES.items()]


@app.get("/trending")
def trending(category: Optional[str] = None, store: Optional[str] = None,
             limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    """Best sellers / trending now. One card per product, with its best store."""
    where, params = _filters(category, store)
    rows = db.rows(f"SELECT {PUBLIC} FROM products WHERE {where} ORDER BY trend_score DESC, sales DESC LIMIT ? OFFSET ?",
                   (*params, (limit + offset) * 4, 0))
    items = _one_per_group(rows, limit + offset)[offset:]
    for i, item in enumerate(items, start=offset + 1):
        item["rank"] = i
    return {"items": items, "count": len(items)}


@app.get("/deals")
def deals(category: Optional[str] = None, min_discount: float = Query(0.3, ge=0, le=0.95),
          limit: int = Query(20, ge=1, le=100)):
    """Biggest discounts right now."""
    where, params = _filters(category, None)
    rows = db.rows(f"SELECT {PUBLIC} FROM products WHERE {where} AND old_price > price "
                   f"AND (1 - price/old_price) >= ? ORDER BY (1 - price/old_price) DESC LIMIT ?",
                   (*params, min_discount, limit * 4))
    return {"items": _one_per_group(rows, limit)}


@app.get("/search")
def search(q: str = Query(..., min_length=2), category: Optional[str] = None,
           sort: str = Query("trend", pattern="^(trend|price|discount)$"), limit: int = Query(30, ge=1, le=100)):
    where, params = _filters(category, None)
    words = [w for w in q.split() if w][:6]
    for w in words:
        where += " AND (title LIKE ? OR brand LIKE ?)"
        params += [f"%{w}%", f"%{w}%"]
    order = {"trend": "trend_score DESC", "price": "price ASC",
             "discount": "CASE WHEN old_price > price THEN 1 - price/old_price ELSE 0 END DESC"}[sort]
    rows = db.rows(f"SELECT {PUBLIC} FROM products WHERE {where} ORDER BY {order} LIMIT ?", (*params, limit * 4))
    return {"query": q, "items": _one_per_group(rows, limit)}


@app.get("/products/{uid:path}")
def product(uid: str):
    """One product with every store that sells it (cheapest after cashback first) and price history."""
    rows = db.rows(f"SELECT {PUBLIC} FROM products WHERE uid=?", (uid,))
    if not rows:
        raise HTTPException(404, "product not found")
    main = rows[0]
    offers = db.rows(f"SELECT {PUBLIC} FROM products WHERE active=1 AND group_id=?", (main["group_id"],)) \
        if main["group_id"] else rows
    offers = sorted((_shape(o) for o in offers), key=lambda o: o["net_price"])
    if offers:
        offers[0]["best"] = True
    history = db.rows("SELECT at, price FROM price_history WHERE uid=? ORDER BY at DESC LIMIT 60", (uid,))
    low = db.lowest_price(uid)
    return {
        "product": _shape(main),
        "offers": offers,
        "price_history": list(reversed(history)),
        "lowest_30d": low,
        "is_lowest_now": low is not None and main["price"] <= low,
    }
