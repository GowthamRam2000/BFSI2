from __future__ import annotations

import math
from typing import Dict, Tuple

from app.services.pricing import determine_rate_tier


def calculate_emi(principal: int, annual_rate: float, tenure_months: int) -> float:
    if tenure_months <= 0:
        return 0.0
    monthly_rate = annual_rate / 1200.0
    if monthly_rate == 0:
        return principal / tenure_months
    factor = math.pow(1 + monthly_rate, tenure_months)
    return principal * monthly_rate * factor / (factor - 1)


def evaluate_application(
    requested_amount: int,
    tenure_months: int,
    pre_approved_limit: int,
    credit_score: int,
    monthly_salary: int | None,
    existing_emi: float,
    salary_slip_uploaded: bool,
) -> Tuple[str, Dict[str, object]]:
    if credit_score < 650:
        return "rejected_low_score", {}
    if monthly_salary is None or monthly_salary < 25000:
        return "rejected_low_income", {}
    if requested_amount > 2 * pre_approved_limit:
        return "rejected_over_limit", {}
    if requested_amount > pre_approved_limit and not salary_slip_uploaded:
        return "needs_salary_slip", {}

    decision = determine_rate_tier(
        credit_score=credit_score,
        monthly_salary=monthly_salary,
        existing_emi=existing_emi,
        salary_slip_uploaded=salary_slip_uploaded,
    )
    if decision.tier == "Rejected":
        return "rejected_low_score", {}

    rate = decision.rate
    emi = calculate_emi(requested_amount, rate, tenure_months)
    total_emi = existing_emi + emi
    if total_emi > 0.5 * monthly_salary:
        return "rejected_emi", {"emi": emi, "rate": rate, "rate_tier": decision.tier}

    approval = "approved_instant" if requested_amount <= pre_approved_limit else "approved_with_slip"
    return (
        approval,
        {
            "emi": emi,
            "rate": rate,
            "rate_tier": decision.tier,
            "rate_reasons": decision.reasons,
        },
    )
