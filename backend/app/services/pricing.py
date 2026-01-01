from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class RateDecision:
    tier: str
    rate: float
    reasons: List[str]


TIERS = [
    ("Tier A", 9.0),
    ("Tier B", 11.0),
    ("Tier C", 13.0),
    ("Tier D", 14.7),
]


def determine_rate_tier(
    credit_score: int,
    monthly_salary: int,
    existing_emi: float,
    salary_slip_uploaded: bool,
) -> RateDecision:
    reasons: List[str] = []

    if credit_score >= 800:
        credit_band = 0
    elif credit_score >= 750:
        credit_band = 1
    elif credit_score >= 700:
        credit_band = 2
    elif credit_score >= 650:
        credit_band = 3
    else:
        return RateDecision("Rejected", 0.0, ["Credit score below 650"])
    reasons.append(f"Credit score band: {credit_score}")

    if monthly_salary >= 100000:
        income_band = 0
    elif monthly_salary >= 70000:
        income_band = 1
    elif monthly_salary >= 45000:
        income_band = 2
    else:
        income_band = 3
    reasons.append(f"Income band: INR {monthly_salary}")

    emi_ratio = existing_emi / monthly_salary if monthly_salary > 0 else 1.0
    if emi_ratio <= 0.2:
        emi_band = 0
    elif emi_ratio <= 0.3:
        emi_band = 1
    elif emi_ratio <= 0.4:
        emi_band = 2
    else:
        emi_band = 3
    reasons.append(f"Existing EMI ratio: {emi_ratio:.2f}")

    band = max(credit_band, income_band, emi_band)
    if not salary_slip_uploaded:
        band = max(band, 2)
        reasons.append("Salary slip not uploaded; capped rate tier")

    tier_name, rate = TIERS[min(band, len(TIERS) - 1)]
    return RateDecision(tier_name, rate, reasons)
