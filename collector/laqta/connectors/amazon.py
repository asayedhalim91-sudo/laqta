"""Amazon.sa via the Amazon Associates Creators API (replaced PA-API 5 in 2026).

You need: an Amazon.sa Associates account, Creators API credentials from Associates Central
(Credential ID, Secret, Version) and your partner tag. Amazon only opens the API to accounts
with recent qualifying sales, so start with plain tagged links and switch this on once eligible.
"""
from __future__ import annotations

import logging
import time
from typing import Iterable

import httpx

from ..config import Settings
from ..models import Product
from .base import Connector, guess_category, to_float, to_int, to_sar

log = logging.getLogger(__name__)

BASE_URL = "https://creatorsapi.amazon/catalog/v1"
TOKEN_URLS = {
    "2.1": "https://creatorsapi.auth.us-east-1.amazoncognito.com/oauth2/token",
    "2.2": "https://creatorsapi.auth.eu-south-2.amazoncognito.com/oauth2/token",
    "2.3": "https://creatorsapi.auth.us-west-2.amazoncognito.com/oauth2/token",
    "3.1": "https://api.amazon.com/auth/o2/token",
    "3.2": "https://api.amazon.co.uk/auth/o2/token",
    "3.3": "https://api.amazon.co.jp/auth/o2/token",
}
RESOURCES = [
    "itemInfo.title",
    "itemInfo.byLineInfo",
    "itemInfo.classifications",
    "images.primary.large",
    "offersV2.listings.price",
    "offersV2.listings.isBuyBoxWinner",
    "browseNodeInfo.websiteSalesRank",
    "customerReviews.count",
    "customerReviews.starRating",
]


def _get(d, *path, default=None):
    """Walk nested dicts accepting camelCase or PascalCase keys."""
    cur = d
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key, cur.get(key[:1].upper() + key[1:], None))
        if cur is None:
            return default
    return cur


class AmazonConnector(Connector):
    name = "amazon"

    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self.s = settings
        self.client = client or httpx.Client(timeout=30)
        self._token: str | None = None
        self._token_exp = 0.0

    @property
    def version(self) -> str:
        return self.s.amazon_credential_version

    def token(self) -> str:
        if self._token and time.time() < self._token_exp - 60:
            return self._token
        url = self.s.amazon_token_url or TOKEN_URLS.get(self.version, TOKEN_URLS["3.2"])
        if self.version.startswith("3"):
            # Login with Amazon
            r = self.client.post(url, json={
                "grant_type": "client_credentials",
                "client_id": self.s.amazon_client_id,
                "client_secret": self.s.amazon_client_secret,
                "scope": "creatorsapi::default",
            })
        else:
            # Cognito (older v2.x credentials)
            r = self.client.post(url, data={"grant_type": "client_credentials", "scope": "creatorsapi/default"},
                                 auth=(self.s.amazon_client_id, self.s.amazon_client_secret))
        r.raise_for_status()
        body = r.json()
        self._token = body["access_token"]
        self._token_exp = time.time() + int(body.get("expires_in", 3600))
        return self._token

    def _headers(self) -> dict:
        auth = f"Bearer {self.token()}"
        if self.version.startswith("2"):
            auth += f", Version {self.version}"
        return {"Authorization": auth, "Content-Type": "application/json", "x-marketplace": self.s.amazon_marketplace}

    def search(self, keyword: str, page: int = 1) -> list[dict]:
        body = {
            "keywords": keyword,
            "searchIndex": "All",
            "itemPage": page,
            "itemCount": 10,
            "partnerTag": self.s.amazon_partner_tag,
            "marketplace": self.s.amazon_marketplace,
            "resources": RESOURCES,
        }
        r = self.client.post(f"{BASE_URL}/searchItems", headers=self._headers(), json=body)
        if r.status_code == 401:  # token expired early: refresh once and retry
            self._token = None
            r = self.client.post(f"{BASE_URL}/searchItems", headers=self._headers(), json=body)
        r.raise_for_status()
        return _get(r.json(), "searchResult", "items", default=[]) or []

    def to_product(self, item: dict) -> Product | None:
        listing = (_get(item, "offersV2", "listings", default=[]) or [{}])[0]
        money = _get(listing, "price", "money", default={}) or {}
        price = to_float(_get(money, "amount"))
        url = _get(item, "detailPageURL") or _get(item, "detailPageUrl")
        if not price or not url:
            return None
        cur = _get(money, "currency", default="SAR")
        basis = _get(listing, "price", "savingBasis", "money", "amount")
        title = _get(item, "itemInfo", "title", "displayValue", default="")
        rank = _get(item, "browseNodeInfo", "websiteSalesRank", "salesRank")
        return Product(
            store="amazon",
            external_id=_get(item, "asin"),
            title=title,
            price=to_sar(price, cur),
            old_price=to_sar(to_float(basis), cur),
            url=url,  # already carries your partner tag
            image=_get(item, "images", "primary", "large", "url"),
            category=guess_category(title, _get(item, "itemInfo", "classifications", "productGroup", "displayValue")),
            brand=_get(item, "itemInfo", "byLineInfo", "brand", "displayValue"),
            rating=to_float(_get(item, "customerReviews", "starRating", "value")),
            reviews=to_int(_get(item, "customerReviews", "count")),
            sales_rank=to_int(rank),
            is_hot=bool(rank and to_int(rank) and to_int(rank) <= 100),
            shipping="1–3 أيام",
        )

    def collect(self) -> Iterable[Product]:
        for kw in self.s.keywords:
            for item in self.search(kw):
                prod = self.to_product(item)
                if prod:
                    yield prod
            time.sleep(1.1)  # stay under the default 1 request/second limit
