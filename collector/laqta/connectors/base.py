"""Shared helpers for every store connector."""
from __future__ import annotations

import re
from typing import Iterable, Optional

from ..models import Product

# Keyword → category. Matches English and Arabic titles.
_CATEGORY_WORDS = {
    "tech": ["headphone", "earbud", "earphone", "watch", "phone", "charger", "laptop", "tablet", "speaker",
             "camera", "cable", "power bank", "keyboard", "mouse", "سماع", "ساعة ذكية", "جوال", "شاحن", "لابتوب"],
    "fashion": ["dress", "abaya", "shirt", "jeans", "shoe", "sneaker", "bag", "backpack", "hijab", "jacket",
                "skirt", "فستان", "عباية", "عبايه", "قميص", "حذاء", "شنطة", "حقيبة", "طرحة"],
    "beauty": ["perfume", "oud", "fragrance", "makeup", "lipstick", "serum", "cream", "skin", "bakhoor",
               "عطر", "عود", "بخور", "مكياج", "كريم", "سيروم"],
    "home": ["lamp", "kitchen", "pillow", "blanket", "organizer", "vacuum", "pan", "mug", "أباجورة",
             "مطبخ", "وسادة", "مكنسة"],
    "kids": ["kids", "baby", "toy", "children", "أطفال", "طفل", "لعبة", "ألعاب"],
}


def guess_category(*texts: Optional[str]) -> str:
    blob = " ".join(t for t in texts if t).lower()
    for cat, words in _CATEGORY_WORDS.items():
        if any(w in blob for w in words):
            return cat
    return "other"


_NUM = re.compile(r"[-+]?\d[\d,]*\.?\d*")


def to_float(value) -> Optional[float]:
    """'1,299.00 SAR' -> 1299.0 ; '97.5%' -> 97.5 ; None/'' -> None"""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = _NUM.search(str(value))
    return float(m.group().replace(",", "")) if m else None


def to_int(value) -> Optional[int]:
    f = to_float(value)
    return int(f) if f is not None else None


def to_rate(value) -> Optional[float]:
    """'7.0%' -> 0.07 ; 0.07 -> 0.07 ; 7 -> 0.07"""
    f = to_float(value)
    if f is None:
        return None
    return round(f / 100, 4) if f > 1 else f


# Rough conversion to SAR. Update rates in .env-driven settings if you need precision.
FX_TO_SAR = {"SAR": 1.0, "USD": 3.75, "AED": 1.021, "EUR": 4.05}


def to_sar(amount: Optional[float], currency: str, usd_to_sar: float = 3.75) -> Optional[float]:
    if amount is None:
        return None
    currency = (currency or "SAR").upper()
    rate = usd_to_sar if currency == "USD" else FX_TO_SAR.get(currency, 1.0)
    return round(amount * rate, 2)


class Connector:
    """Every connector has a name and a collect() that yields Products."""
    name: str = "base"

    def collect(self) -> Iterable[Product]:  # pragma: no cover - interface
        raise NotImplementedError
