"""Product feeds from affiliate networks (Arabclicks, Admitad, CJ, Awin, …).

Noon, Shein, Namshi and Temu don't give an open product API to affiliates. Instead the
affiliate network gives you a product feed file (CSV, JSON or XML/YML) with affiliate links
already inside. Drop the files into the feeds/ folder, named after the store:

    feeds/noon.csv   feeds/shein_women.csv   feeds/namshi.json   feeds/temu.xml

or set a download URL per store in feeds/sources.json and run `laqta collect --download`.
Column names differ between networks, so each field below accepts several names.
"""
from __future__ import annotations

import csv
import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable, Iterator

import httpx

from ..config import Settings
from ..models import STORES, Product
from .base import Connector, guess_category, to_float, to_int, to_rate, to_sar

log = logging.getLogger(__name__)

# field -> accepted column names (lower-case), first match wins
ALIASES = {
    "id": ["id", "product_id", "sku", "offer_id", "aw_product_id", "item_id", "productid"],
    "title": ["title_ar", "name_ar", "title", "name", "product_name", "product_title"],
    "title_en": ["title_en", "name_en", "title_english", "english_title"],
    "price": ["sale_price", "price", "search_price", "current_price", "final_price", "discounted_price"],
    "old_price": ["oldprice", "old_price", "original_price", "rrp_price", "regular_price", "list_price", "price_before"],
    "currency": ["currency", "currencyid", "currency_id"],
    "url": ["deeplink", "aw_deep_link", "affiliate_link", "tracking_url", "url", "link", "product_url", "buy_url"],
    "image": ["picture", "image", "image_link", "image_url", "merchant_image_url", "img"],
    "category": ["category", "category_name", "merchant_category", "product_type", "categoryid", "google_product_category"],
    "brand": ["brand", "vendor", "brand_name", "manufacturer"],
    "rating": ["rating", "stars", "average_rating"],
    "reviews": ["reviews", "review_count", "reviews_count"],
    "sales": ["sales", "orders", "sold", "sales_count"],
    "rank": ["rank", "sales_rank", "bestseller_rank", "position"],
    "hot": ["is_bestseller", "bestseller", "hot", "trending", "is_hot"],
    "commission": ["commission", "commission_rate", "cpa"],
}


def store_from_filename(path: Path) -> str | None:
    stem = path.stem.lower()
    for key in STORES:
        if stem == key or stem.startswith(key + "_") or stem.startswith(key + "-"):
            return key
    return None


def _pick(row: dict, field: str):
    for name in ALIASES[field]:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return None


def _truthy(v) -> bool:
    return str(v).strip().lower() in {"1", "true", "yes", "y", "نعم"}


def read_rows(path: Path) -> Iterator[dict]:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv", ".txt"}:
        with path.open(newline="", encoding="utf-8-sig") as f:
            sample = f.read(4096)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except csv.Error:
                dialect = csv.excel
            for row in csv.DictReader(f, dialect=dialect):
                yield {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
    elif suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("products") or data.get("items") or []
        for row in items:
            yield {str(k).lower(): v for k, v in row.items()}
    elif suffix in {".xml", ".yml"}:
        # Yandex YML (common on Admitad) or a flat <product> list
        root = ET.parse(path).getroot()
        for node in root.iter():
            if node.tag.lower() in {"offer", "product", "item"} and len(node):
                row = {k.lower(): v for k, v in node.attrib.items()}
                for child in node:
                    row[child.tag.lower().split("}")[-1]] = (child.text or "").strip()
                yield row
    else:
        log.warning("Skipping %s: unknown feed format", path.name)


def row_to_product(row: dict, store: str, usd_to_sar: float = 3.75) -> Product | None:
    price = to_float(_pick(row, "price"))
    url = _pick(row, "url")
    ext_id = _pick(row, "id")
    title = _pick(row, "title")
    if not (price and url and ext_id and title):
        return None
    cur = (_pick(row, "currency") or "SAR").upper()
    old = to_float(_pick(row, "old_price"))
    if old and old <= price:  # some feeds put the same number in both
        old = None
    cat_raw = _pick(row, "category")
    return Product(
        store=store,
        external_id=str(ext_id),
        title=str(title),
        title_en=_pick(row, "title_en"),
        price=to_sar(price, cur, usd_to_sar),
        old_price=to_sar(old, cur, usd_to_sar),
        url=str(url),
        image=_pick(row, "image"),
        category=guess_category(str(title), str(cat_raw or "")),
        brand=_pick(row, "brand"),
        rating=to_float(_pick(row, "rating")),
        reviews=to_int(_pick(row, "reviews")),
        sales=to_int(_pick(row, "sales")),
        sales_rank=to_int(_pick(row, "rank")),
        is_hot=_truthy(_pick(row, "hot") or ""),
        commission_rate=to_rate(_pick(row, "commission")),
    )


class FeedConnector(Connector):
    name = "feeds"

    def __init__(self, settings: Settings):
        self.s = settings

    def download(self) -> None:
        """Fetch feed files listed in feeds/sources.json: {"noon": "https://…", "shein_women": "https://…"}"""
        cfg = self.s.feeds_path / "sources.json"
        if not cfg.exists():
            return
        sources = json.loads(cfg.read_text(encoding="utf-8"))
        with httpx.Client(timeout=120, follow_redirects=True) as client:
            for name, url in sources.items():
                ext = ".xml" if any(x in url.lower() for x in (".xml", ".yml", "format=xml")) else \
                      ".json" if "json" in url.lower() else ".csv"
                dest = self.s.feeds_path / f"{name}{ext}"
                log.info("Downloading %s feed", name)
                r = client.get(url)
                r.raise_for_status()
                dest.write_bytes(r.content)

    def files(self) -> list[Path]:
        if not self.s.feeds_path.exists():
            return []
        return sorted(p for p in self.s.feeds_path.iterdir()
                      if p.is_file() and p.suffix.lower() in {".csv", ".tsv", ".txt", ".json", ".xml", ".yml"}
                      and not p.name.startswith("sources"))

    def collect(self) -> Iterable[Product]:
        for path in self.files():
            store = store_from_filename(path)
            if not store:
                log.warning("Skipping %s: name it after a store (%s)", path.name, ", ".join(STORES))
                continue
            count = 0
            for row in read_rows(path):
                prod = row_to_product(row, store, self.s.usd_to_sar)
                if prod:
                    count += 1
                    yield prod
            log.info("%s: %d products from %s", store, count, path.name)
