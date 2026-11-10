"""Hand-picked popular products, used until a store's product API or feed is connected.

Each entry in curated/<store>.json opens that store with your affiliate tag on the link, so a
purchase earns commission from day one. No price is shown in the app for these: Amazon only
allows prices that come from its API, and a hand-typed price goes out of date within hours.

    {"id": "airpods-pro", "title": "…", "title_en": "…", "query": "Apple AirPods Pro",
     "category": "tech", "brand": "Apple", "asin": "optional - links straight to the product page"}

The order of the file is the order in the app. Curated Amazon items stop automatically once
the Amazon API is connected (real products with real prices replace them).
"""
from __future__ import annotations

import json
import logging
from typing import Iterable
from urllib.parse import quote, quote_plus

from ..config import Settings
from ..models import Product
from .base import Connector

log = logging.getLogger(__name__)


def amazon_link(marketplace: str, tag: str, query: str = "", asin: str = "") -> str:
    base = f"https://{marketplace}"
    url = f"{base}/dp/{quote(asin)}" if asin else f"{base}/s?k={quote_plus(query)}"
    if tag:
        url += ("&" if "?" in url else "?") + f"tag={quote(tag)}"
    return url


class CuratedConnector(Connector):
    name = "curated"

    def __init__(self, settings: Settings):
        self.s = settings

    def collect(self) -> Iterable[Product]:
        path = self.s.curated_path / "amazon.json"
        if not path.exists() or self.s.amazon_ready:
            return
        if not self.s.amazon_partner_tag:
            log.warning("Curated Amazon links have no tag: set AMAZON_PARTNER_TAG, or they earn nothing")
        for i, row in enumerate(json.loads(path.read_text(encoding="utf-8")), 1):
            query = row.get("query") or row.get("title_en") or row["title"]
            yield Product(
                store="amazon",
                external_id=f"pick-{row['id']}",
                title=row["title"],
                title_en=row.get("title_en"),
                price=0,                       # 0 = "see the price in the store"
                url=amazon_link(self.s.amazon_marketplace, self.s.amazon_partner_tag, query, row.get("asin", "")),
                category=row.get("category", "other"),
                brand=row.get("brand"),
                sales_rank=i,                  # keeps the file's order in the ranking
                shipping="1–3 أيام",
            )
