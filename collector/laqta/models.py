"""The one product shape every store is converted into."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


STORES = {
    "amazon": "أمازون",
    "noon": "نون",
    "shein": "شي إن",
    "aliexpress": "علي إكسبريس",
    "namshi": "نمشي",
    "temu": "تيمو",
}

CATEGORIES = {
    "tech": "إلكترونيات",
    "fashion": "أزياء",
    "beauty": "عطور وجمال",
    "home": "المنزل",
    "kids": "أطفال",
    "other": "أخرى",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class Product:
    store: str                      # key from STORES
    external_id: str                # the store's own id (ASIN, AliExpress product id, SKU…)
    title: str
    price: float                    # current price in SAR
    url: str                        # affiliate link (this is how you get paid)
    currency: str = "SAR"
    title_en: Optional[str] = None   # English name when the store gives one
    old_price: Optional[float] = None
    image: Optional[str] = None
    category: str = "other"
    brand: Optional[str] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    sales: Optional[int] = None     # total orders/sales count when the store gives it
    sales_rank: Optional[int] = None  # lower = better (Amazon-style rank)
    is_hot: bool = False            # store flagged it as hot/best seller
    commission_rate: Optional[float] = None  # 0.08 = 8%
    shipping: Optional[str] = None
    collected_at: str = field(default_factory=now_iso)

    @property
    def uid(self) -> str:
        return f"{self.store}:{self.external_id}"

    @property
    def discount(self) -> float:
        if self.old_price and self.old_price > self.price > 0:
            return round(1 - self.price / self.old_price, 4)
        return 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["uid"] = self.uid
        d["discount"] = self.discount
        return d
