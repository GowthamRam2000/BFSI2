from __future__ import annotations

from typing import Any, Dict

from .data_loader import find_customer_by_phone


def fetch_kyc_by_phone(phone: str) -> Dict[str, Any] | None:
    customer = find_customer_by_phone(phone)
    if not customer:
        return None
    return {
        "customer_id": customer["customer_id"],
        "name": customer["name"],
        "phone": customer["phone"],
        "email": customer["email"],
        "address": customer["address"],
        "city": customer["city"],
        "dob": customer["dob"],
        "pan": customer["pan"],
        "monthly_salary": customer.get("monthly_salary"),
        "employer": customer.get("employer"),
        "existing_loans": customer.get("existing_loans", []),
    }
