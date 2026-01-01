from __future__ import annotations

from typing import Any, Dict

from .data_loader import find_customer_by_id

DEFAULT_OFFER = {
    "pre_approved_limit": 120000,
    "min_tenure": 12,
    "max_tenure": 60,
}


def fetch_offer(customer_id: str | None) -> Dict[str, Any]:
    if not customer_id:
        return DEFAULT_OFFER.copy()
    customer = find_customer_by_id(customer_id)
    if not customer:
        return DEFAULT_OFFER.copy()
    return {
        "pre_approved_limit": customer.get("pre_approved_limit", DEFAULT_OFFER["pre_approved_limit"]),
        "min_tenure": 12,
        "max_tenure": 60,
    }
