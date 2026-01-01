from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "customers.json"


@lru_cache(maxsize=1)
def load_customers() -> List[Dict[str, Any]]:
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def find_customer_by_phone(phone: str) -> Dict[str, Any] | None:
    phone = phone.strip()
    for customer in load_customers():
        if customer.get("phone") == phone:
            return customer
    return None


def find_customer_by_id(customer_id: str) -> Dict[str, Any] | None:
    for customer in load_customers():
        if customer.get("customer_id") == customer_id:
            return customer
    return None
