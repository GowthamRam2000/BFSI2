from __future__ import annotations

from typing import Dict

from .data_loader import find_customer_by_id

DEFAULT_SCORE = 720


def fetch_credit_score(customer_id: str | None) -> Dict[str, int]:
    if not customer_id:
        return {"credit_score": DEFAULT_SCORE}
    customer = find_customer_by_id(customer_id)
    if not customer:
        return {"credit_score": DEFAULT_SCORE}
    return {"credit_score": int(customer.get("credit_score", DEFAULT_SCORE))}
