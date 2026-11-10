"""Settings come from environment variables (or a .env file). Never put secrets in code."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # dotenv is optional
    pass


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _list(name: str, default: str) -> list[str]:
    return [x.strip() for x in _env(name, default).split(",") if x.strip()]


@dataclass
class Settings:
    db_path: str = field(default_factory=lambda: _env("LAQTA_DB", "laqta.db"))
    # Words to search for on stores that need a keyword (Amazon, AliExpress search)
    keywords: list[str] = field(default_factory=lambda: _list(
        "LAQTA_KEYWORDS", "headphones,smart watch,perfume,abaya,dress,phone charger,backpack"))
    usd_to_sar: float = field(default_factory=lambda: float(_env("LAQTA_USD_TO_SAR", "3.75")))
    # Share of your commission given back to the user as cashback (0.5 = half)
    cashback_share: float = field(default_factory=lambda: float(_env("LAQTA_CASHBACK_SHARE", "0.5")))
    # Websites allowed to call the API from a browser (your site's domain), comma-separated
    cors_origins: list[str] = field(default_factory=lambda: _list("LAQTA_CORS_ORIGINS", "*"))

    # AliExpress Affiliate (portals.aliexpress.com + open.aliexpress.com)
    ali_app_key: str = field(default_factory=lambda: _env("ALIEXPRESS_APP_KEY"))
    ali_app_secret: str = field(default_factory=lambda: _env("ALIEXPRESS_APP_SECRET"))
    ali_tracking_id: str = field(default_factory=lambda: _env("ALIEXPRESS_TRACKING_ID"))
    ali_endpoint: str = field(default_factory=lambda: _env("ALIEXPRESS_ENDPOINT", "https://api-sg.aliexpress.com/sync"))
    ali_ship_to: str = field(default_factory=lambda: _env("ALIEXPRESS_SHIP_TO", "SA"))

    # Amazon Associates (amazon.sa) Creators API
    amazon_client_id: str = field(default_factory=lambda: _env("AMAZON_CREDENTIAL_ID"))
    amazon_client_secret: str = field(default_factory=lambda: _env("AMAZON_CREDENTIAL_SECRET"))
    amazon_credential_version: str = field(default_factory=lambda: _env("AMAZON_CREDENTIAL_VERSION", "3.2"))
    amazon_token_url: str = field(default_factory=lambda: _env("AMAZON_TOKEN_URL"))
    amazon_partner_tag: str = field(default_factory=lambda: _env("AMAZON_PARTNER_TAG"))
    amazon_marketplace: str = field(default_factory=lambda: _env("AMAZON_MARKETPLACE", "www.amazon.sa"))

    # Product feeds from affiliate networks (Noon, Shein, Namshi, Temu…): folder of CSV/JSON files
    feeds_dir: str = field(default_factory=lambda: _env("LAQTA_FEEDS_DIR", "feeds"))
    # Hand-picked products shown until a store's API or feed is connected (curated/amazon.json)
    curated_dir: str = field(default_factory=lambda: _env("LAQTA_CURATED_DIR", "curated"))

    @property
    def aliexpress_ready(self) -> bool:
        return bool(self.ali_app_key and self.ali_app_secret and self.ali_tracking_id)

    @property
    def amazon_ready(self) -> bool:
        return bool(self.amazon_client_id and self.amazon_client_secret and self.amazon_partner_tag)

    @property
    def feeds_path(self) -> Path:
        return Path(self.feeds_dir)

    @property
    def curated_path(self) -> Path:
        return Path(self.curated_dir)
