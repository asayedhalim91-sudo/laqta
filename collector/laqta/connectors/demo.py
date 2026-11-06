"""Sample data so the whole system runs before you have any affiliate accounts.

The same few products appear in several stores at different prices, and sales numbers move a
little on every run, so price comparison and trending both have something to show.
Turn it off with `laqta collect --no-demo` once real connectors are set up.
"""
from __future__ import annotations

import random
from typing import Iterable

from ..models import Product
from .base import Connector

# (key, Arabic title, category, base price SAR, stores that sell it)
CATALOG = [
    ("anc-headphones", "سماعات لاسلكية بعزل الضوضاء بلوتوث 5.3", "tech", 189, ["amazon", "noon", "aliexpress", "namshi"]),
    ("amoled-watch", "ساعة ذكية رياضية بشاشة AMOLED لتتبع اللياقة", "tech", 249, ["noon", "amazon", "aliexpress"]),
    ("oud-100", "عطر عود فاخر 100 مل أو دو بارفان", "beauty", 320, ["namshi", "noon", "amazon"]),
    ("crepe-abaya", "عباية كريب بقصة واسعة مفتوحة من الأمام", "fashion", 139, ["shein", "namshi"]),
    ("summer-dress", "فستان صيفي طويل واسع بأكمام طويلة", "fashion", 79, ["shein", "temu"]),
    ("led-lamp", "أباجورة مكتب LED قابلة للطي وإعادة الشحن", "home", 45, ["temu", "aliexpress", "amazon"]),
    ("sport-earbuds", "سماعات أذن رياضية لاسلكية مقاومة للماء", "tech", 69, ["aliexpress", "amazon", "noon"]),
    ("bakhoor-set", "طقم هدايا بخور ودهن عود", "beauty", 159, ["noon", "amazon"]),
    ("charger-65w", "شاحن سريع 65 واط GaN بثلاث منافذ USB-C", "tech", 59, ["aliexpress", "amazon", "temu"]),
    ("backpack", "حقيبة ظهر للابتوب مقاومة للماء 15.6 إنش", "fashion", 64, ["temu", "shein", "amazon"]),
    ("kids-blocks", "مكعبات بناء مغناطيسية للأطفال 100 قطعة", "kids", 99, ["amazon", "noon", "temu"]),
    ("air-fryer", "قلاية هوائية رقمية 5.5 لتر بدون زيت", "home", 229, ["amazon", "noon"]),
]

EN_TITLES = {'سماعات لاسلكية بعزل الضوضاء بلوتوث 5.3': 'Wireless Noise-Cancelling Headphones, Bluetooth 5.3',
    'ساعة ذكية رياضية بشاشة AMOLED لتتبع اللياقة': 'AMOLED Sports Smart Watch & Fitness Tracker',
    'عطر عود فاخر 100 مل أو دو بارفان': 'Luxury Oud Eau de Parfum 100 ml',
    'عباية كريب بقصة واسعة مفتوحة من الأمام': 'Open-Front Loose Crepe Abaya',
    'فستان صيفي طويل واسع بأكمام طويلة': 'Long-Sleeve Loose Summer Maxi Dress',
    'أباجورة مكتب LED قابلة للطي وإعادة الشحن': 'Foldable Rechargeable LED Desk Lamp',
    'سماعات أذن رياضية لاسلكية مقاومة للماء': 'Waterproof Wireless Sport Earbuds',
    'طقم هدايا بخور ودهن عود': 'Bakhoor & Oud Oil Gift Set',
    'شاحن سريع 65 واط GaN بثلاث منافذ USB-C': '65W GaN Fast Charger, 3 USB-C Ports',
    'حقيبة ظهر للابتوب مقاومة للماء 15.6 إنش': 'Waterproof 15.6-inch Laptop Backpack',
    'مكعبات بناء مغناطيسية للأطفال 100 قطعة': 'Kids Magnetic Building Blocks, 100 Pieces',
    'قلاية هوائية رقمية 5.5 لتر بدون زيت': 'Digital Oil-Free Air Fryer 5.5 L'}

PRICE_FACTOR = {"amazon": 1.00, "noon": 1.05, "aliexpress": 0.92, "namshi": 1.18, "shein": 1.0, "temu": 0.88}
COMMISSION = {"amazon": 0.06, "noon": 0.06, "aliexpress": 0.10, "namshi": 0.07, "shein": 0.10, "temu": 0.09}
SHIPPING = {"amazon": "1–3 أيام", "noon": "1–2 يوم", "aliexpress": "7–12 يوم", "namshi": "1–2 يوم",
            "shein": "4–7 أيام", "temu": "5–10 أيام"}


class DemoConnector(Connector):
    name = "demo"

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)

    def collect(self) -> Iterable[Product]:
        for i, (key, title, cat, base, stores) in enumerate(CATALOG):
            for store in stores:
                price = round(base * PRICE_FACTOR[store] * self.rng.uniform(0.95, 1.03), 0)
                sales = int((len(CATALOG) - i) * 400 * self.rng.uniform(0.8, 1.4))
                yield Product(
                    store=store,
                    external_id=f"demo-{key}",
                    title=title,
                    title_en=EN_TITLES.get(title),
                    price=price,
                    old_price=round(price * self.rng.uniform(1.25, 1.6), 0),
                    url=f"https://example.com/{store}/{key}?ref=laqta-demo",
                    category=cat,
                    rating=round(self.rng.uniform(4.0, 4.9), 1),
                    reviews=int(sales * 0.08),
                    sales=sales,
                    is_hot=i < 4,
                    commission_rate=COMMISSION[store],
                    shipping=SHIPPING[store],
                )
