from __future__ import annotations

import json
from pathlib import Path

from core.config import DEFAULT_PRODUCTS_PATH
from models.product import Product


def load_products(path: str | Path = DEFAULT_PRODUCTS_PATH) -> list[Product]:
    raw_products = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Product.from_dict(raw_product) for raw_product in raw_products]
