from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from openai import OpenAI

from app.config import get_settings


class LlmClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = None
        if self.settings.openai_api_key:
            self.client = OpenAI(api_key=self.settings.openai_api_key)

    def generate_text(self, system_prompt: str, user_prompt: str, fallback: str) -> str:
        if not self.client:
            return fallback
        try:
            response = self.client.responses.create(
                model=self.settings.openai_model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
            )
            return response.output_text.strip() or fallback
        except Exception:
            return fallback

    def extract_fields(self, message: str) -> Dict[str, Any]:
        if not self.client:
            return {}
        system_prompt = (
            "You extract structured fields from a customer message for a loan chatbot. "
            "Return JSON only with keys: name, phone, amount, tenure_months, monthly_salary, "
            "confirm, insurance_opt_in. Use null if not explicit. "
            "If the message is only a likely person name (1-4 words, no digits), set name. "
            "Do not treat action phrases (e.g., 'I have uploaded details', 'ok proceed') as a name. "
            "Phone must be a 10-digit Indian mobile number if present. "
            "amount and monthly_salary are INR integers; ignore interest rates or percentages. "
            "tenure_months must be an integer (convert years to months). "
            "confirm is true/false only when the user clearly agrees or declines to proceed. "
            "insurance_opt_in is true/false only if the user explicitly opts in/out of insurance."
        )
        try:
            response = self.client.responses.create(
                model=self.settings.openai_model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            text = response.output_text.strip()
            return _normalize_fields(_safe_json_extract(text))
        except Exception:
            return {}

    def extract_loan_history(self, message: str) -> Dict[str, Any]:
        if not self.client:
            return {}
        system_prompt = (
            "Extract outstanding loan details from the customer's message. "
            "Return JSON only with keys: has_loans (true/false), loans (array). "
            "Each loan: type, lender, outstanding, emi. Use integers for outstanding and emi. "
            "If the user says no outstanding loans, has_loans=false and loans=[]."
        )
        try:
            response = self.client.responses.create(
                model=self.settings.openai_model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            text = response.output_text.strip()
            return _normalize_loan_history(_safe_json_extract(text))
        except Exception:
            return {}


def _safe_json_extract(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _normalize_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    allowed = {
        "name",
        "phone",
        "amount",
        "tenure_months",
        "monthly_salary",
        "confirm",
        "insurance_opt_in",
    }
    cleaned: Dict[str, Any] = {}
    for key, value in data.items():
        if key not in allowed or value is None:
            continue
        if key in {"amount", "tenure_months", "monthly_salary"}:
            try:
                parsed = int(value)
                if parsed > 0:
                    cleaned[key] = parsed
            except (TypeError, ValueError):
                continue
        elif key in {"confirm", "insurance_opt_in"}:
            if isinstance(value, bool):
                cleaned[key] = value
        elif key == "phone":
            phone = re.sub(r"\D", "", str(value)).strip()
            if re.fullmatch(r"[6-9]\d{9}", phone):
                cleaned[key] = phone
        else:
            name = str(value).strip()
            if _is_valid_name(name):
                cleaned[key] = name[:60]
    return cleaned


def _normalize_loan_history(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    has_loans = data.get("has_loans")
    loans = data.get("loans") if isinstance(data.get("loans"), list) else []
    cleaned_loans = []
    for item in loans:
        if not isinstance(item, dict):
            continue
        entry = {
            "type": str(item.get("type", "")).strip() or "unspecified",
            "lender": str(item.get("lender", "")).strip() or "",
            "outstanding": _safe_int(item.get("outstanding")),
            "emi": _safe_int(item.get("emi")),
        }
        cleaned_loans.append(entry)
    if isinstance(has_loans, bool):
        return {"has_loans": has_loans, "loans": cleaned_loans}
    if cleaned_loans:
        return {"has_loans": True, "loans": cleaned_loans}
    return {}


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _is_valid_name(name: str) -> bool:
    if not name:
        return False
    cleaned = name.strip().strip("\"' ")
    if not cleaned or re.search(r"\d", cleaned):
        return False
    lowered = cleaned.lower()
    if lowered.startswith(("i ", "we ", "my ", "our ")):
        return False
    banned = [
        "upload",
        "uploaded",
        "document",
        "documents",
        "details",
        "loan",
        "amount",
        "tenure",
        "salary",
        "income",
        "interest",
        "month",
        "months",
        "year",
        "years",
        "need",
        "want",
        "require",
        "proceed",
        "continue",
        "ok",
        "okay",
        "hi",
        "hello",
        "thanks",
        "please",
    ]
    if any(word in lowered for word in banned):
        return False
    words = [word for word in cleaned.split() if word]
    if not words or len(words) > 4:
        return False
    if not all(re.fullmatch(r"[A-Za-z][A-Za-z\\.'-]*", word) for word in words):
        return False
    return True
