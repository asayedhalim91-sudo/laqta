"""SQLite storage. One file, no server. Move to PostgreSQL later by swapping this module."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterable, Iterator

from .models import Product, now_iso

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    uid TEXT PRIMARY KEY,
    store TEXT NOT NULL,
    external_id TEXT NOT NULL,
    title TEXT NOT NULL,
    price REAL NOT NULL,
    old_price REAL,
    currency TEXT NOT NULL DEFAULT 'SAR',
    url TEXT NOT NULL,
    image TEXT,
    category TEXT NOT NULL DEFAULT 'other',
    brand TEXT,
    rating REAL,
    reviews INTEGER,
    sales INTEGER,
    sales_rank INTEGER,
    is_hot INTEGER NOT NULL DEFAULT 0,
    commission_rate REAL,
    shipping TEXT,
    group_id TEXT,               -- same product across stores share a group_id
    trend_score REAL NOT NULL DEFAULT 0,
    sales_velocity REAL NOT NULL DEFAULT 0,  -- new sales per day since last seen
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_products_trend ON products(active, trend_score DESC);
CREATE INDEX IF NOT EXISTS idx_products_cat ON products(category, active, trend_score DESC);
CREATE INDEX IF NOT EXISTS idx_products_group ON products(group_id);

CREATE TABLE IF NOT EXISTS price_history (
    uid TEXT NOT NULL,
    at TEXT NOT NULL,
    price REAL NOT NULL,
    sales INTEGER,
    PRIMARY KEY (uid, at)
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    source TEXT NOT NULL,
    products INTEGER NOT NULL DEFAULT 0,
    error TEXT
);
"""


class DB:
    def __init__(self, path: str):
        self.path = path
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    # --- writes ------------------------------------------------------------------------------
    def upsert(self, products: Iterable[Product]) -> int:
        """Insert or update products, record price history, compute sales velocity."""
        n = 0
        at = now_iso()
        with self.tx() as c:
            for p in products:
                prev = c.execute("SELECT sales, last_seen FROM products WHERE uid=?", (p.uid,)).fetchone()
                velocity = 0.0
                if prev and prev["sales"] is not None and p.sales is not None:
                    days = max(_days_between(prev["last_seen"], at), 1 / 24)  # at least one hour
                    velocity = max(p.sales - prev["sales"], 0) / days
                c.execute("""
                    INSERT INTO products (uid, store, external_id, title, price, old_price, currency, url, image,
                        category, brand, rating, reviews, sales, sales_rank, is_hot, commission_rate, shipping,
                        sales_velocity, first_seen, last_seen, active)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)
                    ON CONFLICT(uid) DO UPDATE SET
                        title=excluded.title, price=excluded.price, old_price=excluded.old_price,
                        url=excluded.url, image=COALESCE(excluded.image, products.image),
                        category=excluded.category, brand=COALESCE(excluded.brand, products.brand),
                        rating=excluded.rating, reviews=excluded.reviews, sales=excluded.sales,
                        sales_rank=excluded.sales_rank, is_hot=excluded.is_hot,
                        commission_rate=excluded.commission_rate, shipping=excluded.shipping,
                        sales_velocity=excluded.sales_velocity, last_seen=excluded.last_seen, active=1
                """, (p.uid, p.store, p.external_id, p.title, p.price, p.old_price, p.currency, p.url, p.image,
                      p.category, p.brand, p.rating, p.reviews, p.sales, p.sales_rank, int(p.is_hot),
                      p.commission_rate, p.shipping, velocity, at, at))
                c.execute("INSERT OR REPLACE INTO price_history (uid, at, price, sales) VALUES (?,?,?,?)",
                          (p.uid, at, p.price, p.sales))
                n += 1
        return n

    def deactivate_stale(self, days: int = 3) -> int:
        """Hide products a store stopped sending (sold out / removed)."""
        with self.tx() as c:
            cur = c.execute("UPDATE products SET active=0 WHERE active=1 AND julianday('now') - julianday(last_seen) > ?",
                            (days,))
            return cur.rowcount

    def log_run(self, source: str, started: str, count: int, error: str | None = None) -> None:
        with self.tx() as c:
            c.execute("INSERT INTO runs (started_at, finished_at, source, products, error) VALUES (?,?,?,?,?)",
                      (started, now_iso(), source, count, error))

    # --- reads -------------------------------------------------------------------------------
    def rows(self, sql: str, params: tuple = ()) -> list[dict]:
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def lowest_price(self, uid: str, days: int = 30) -> float | None:
        r = self.conn.execute(
            "SELECT MIN(price) FROM price_history WHERE uid=? AND julianday('now') - julianday(at) <= ?",
            (uid, days)).fetchone()
        return r[0] if r else None


def _days_between(a: str, b: str) -> float:
    from datetime import datetime
    return (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds() / 86400
