"""AliExpress Affiliate API (AliExpress Open Platform).

You need: an affiliate account (portals.aliexpress.com), an app on open.aliexpress.com with
Affiliate API access, its App Key + App Secret, and your Tracking ID. Hot products need the
"Advanced API" permission, which you request in App Management.
"""
from __future__ import annotations

import hashlib
import logging
import time
from typing import Iterable

import httpx

from ..config import Settings
from ..models import Product
from .base import Connector, guess_category, to_float, to_int, to_rate, to_sar

log = logging.getLogger(__name__)

FIELDS = ",".join([
    "product_id", "product_title", "target_sale_price", "target_sale_price_currency",
    "target_original_price", "product_main_image_url", "promotion_link", "lastest_volume",
    "evaluate_rate", "commission_rate", "first_level_category_name", "second_level_category_name",
])


def sign_md5(params: dict, secret: str) -> str:
    """AliExpress/TOP md5 signature: MD5(secret + k1v1k2v2… sorted by key + secret), upper-case hex."""
    body = "".join(f"{k}{params[k]}" for k in sorted(params) if params[k] is not None)
    return hashlib.md5(f"{secret}{body}{secret}".encode("utf-8")).hexdigest().upper()


class AliExpressConnector(Connector):
    name = "aliexpress"

    def __init__(self, settings: Settings, client: httpx.Client | None = None, page_size: int = 50):
        self.s = settings
        self.client = client or httpx.Client(timeout=30)
        self.page_size = page_size

    # --- low level -------------------------------------------------------------------------
    def call(self, method: str, **api_params) -> dict:
        params = {
            "app_key": self.s.ali_app_key,
            "method": method,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "sign_method": "md5",
            "format": "json",
            "v": "2.0",
            **{k: str(v) for k, v in api_params.items() if v is not None},
        }
        params["sign"] = sign_md5(params, self.s.ali_app_secret)
        r = self.client.post(self.s.ali_endpoint, data=params)
        r.raise_for_status()
        data = r.json()
        if "error_response" in data:
            raise RuntimeError(f"AliExpress error: {data['error_response']}")
        return data

    @staticmethod
    def _products_from(data: dict) -> list[dict]:
        # Response key is the method name with dots → underscores + "_response"
        for key, val in data.items():
            if key.endswith("_response"):
                result = (val.get("resp_result") or {}).get("result") or {}
                prods = (result.get("products") or {}).get("product") or []
                return prods if isinstance(prods, list) else [prods]
        return []

    # --- mapping -----------------------------------------------------------------------------
    def to_product(self, p: dict, hot: bool) -> Product | None:
        price_usd = to_float(p.get("target_sale_price"))
        if not price_usd or not p.get("promotion_link"):
            return None  # no affiliate link = no commission, skip it
        cur = p.get("target_sale_price_currency") or "USD"
        rating = to_float(p.get("evaluate_rate"))  # e.g. "97.5%" positive feedback
        title = p.get("product_title") or ""
        return Product(
            store="aliexpress",
            external_id=str(p.get("product_id")),
            title=title,
            price=to_sar(price_usd, cur, self.s.usd_to_sar),
            old_price=to_sar(to_float(p.get("target_original_price")), cur, self.s.usd_to_sar),
            url=p["promotion_link"],
            image=p.get("product_main_image_url"),
            category=guess_category(title, p.get("first_level_category_name"), p.get("second_level_category_name")),
            rating=round(rating / 20, 2) if rating else None,  # 0–100% → 0–5 stars
            sales=to_int(p.get("lastest_volume")),
            is_hot=hot,
            commission_rate=to_rate(p.get("commission_rate")),
            shipping="7–15 يوم",
        )

    # --- public ------------------------------------------------------------------------------
    def _query(self, method: str, keyword: str, hot: bool) -> Iterable[Product]:
        data = self.call(
            method,
            keywords=keyword,
            fields=FIELDS,
            page_no=1,
            page_size=self.page_size,
            sort="LAST_VOLUME_DESC",  # best sellers first
            target_currency="USD",
            target_language="EN",
            ship_to_country=self.s.ali_ship_to,
            tracking_id=self.s.ali_tracking_id,
        )
        for raw in self._products_from(data):
            prod = self.to_product(raw, hot=hot)
            if prod:
                yield prod

    def collect(self) -> Iterable[Product]:
        for kw in self.s.keywords:
            # Hot products pay higher commission but need "Advanced API" permission.
            try:
                yield from self._query("aliexpress.affiliate.hotproduct.query", kw, hot=True)
            except Exception as e:  # noqa: BLE001 - fall back to normal search
                log.warning("AliExpress hot products failed for %r (%s); using normal search", kw, e)
                yield from self._query("aliexpress.affiliate.product.query", kw, hot=False)
