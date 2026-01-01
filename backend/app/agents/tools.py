from __future__ import annotations

import re
from typing import Any, Dict, Optional

from app.agents.llm import LlmClient


def parse_user_message(
    message: str,
    llm_client: LlmClient | None = None,
) -> Dict[str, Optional[int | str | bool]]:
    llm_data: Dict[str, Optional[int | str | bool]] = {}
    if llm_client:
        extracted = llm_client.extract_fields(message)
        if extracted.get("monthly_salary") is not None:
            llm_data["salary"] = extracted.get("monthly_salary")
        for key in ["name", "phone", "amount", "tenure_months", "confirm", "insurance_opt_in"]:
            if extracted.get(key) is not None:
                llm_data[key] = extracted.get(key)

    heuristic = _parse_user_message_heuristic(message)
    merged = {**heuristic, **llm_data}
    return {k: v for k, v in merged.items() if v is not None}


def _parse_user_message_heuristic(message: str) -> Dict[str, Optional[int | str | bool]]:
    lowered = message.lower()
    phone = _extract_phone(lowered)
    tenure = _extract_tenure(lowered)
    salary = _extract_salary(lowered)
    amount = _extract_amount(lowered)
    extracted: Dict[str, Optional[int | str | bool]] = {
        "phone": phone,
        "amount": amount,
        "tenure_months": tenure,
        "salary": salary,
        "name": _extract_name(message),
        "confirm": _extract_confirmation(lowered),
        "insurance_opt_in": _extract_insurance_preference(lowered),
    }
    if extracted["amount"] is not None and phone and str(extracted["amount"]) == phone:
        extracted["amount"] = None

    candidates = _extract_money_candidates(lowered)
    if phone:
        candidates = [value for value in candidates if str(value) != phone]
    if tenure:
        candidates = [value for value in candidates if value != tenure]

    salary_hint = _has_salary_hint(lowered)
    if extracted["salary"] is None and candidates and salary_hint:
        extracted["salary"] = _infer_salary(candidates)

    if extracted["amount"] is None and candidates:
        extracted["amount"] = _infer_amount(candidates, salary=extracted.get("salary"))

    return extracted


def classify_message(message: str, has_flow_data: bool) -> str:
    lowered = message.lower().strip()
    if not lowered:
        return "empty"
    if has_flow_data:
        return "flow"
    if _is_greeting(lowered):
        return "greeting"
    if _is_insurance_query(lowered):
        return "insurance_faq" if _is_question(lowered) else "insurance_note"
    if _is_loan_query(lowered):
        return "loan_faq" if _is_question(lowered) else "loan_note"
    return "off_topic"


def is_question(message: str) -> bool:
    return _is_question(message.lower().strip())


def document_status(documents: Dict[str, Dict[str, bool]] | None) -> Dict[str, Any]:
    docs = documents or {}
    uploaded = [key for key, info in docs.items() if info.get("uploaded")]
    missing = [key for key, info in docs.items() if not info.get("uploaded")]
    reviewed = [key for key, info in docs.items() if info.get("reviewed")]
    return {
        "uploaded": uploaded,
        "missing": missing,
        "reviewed": reviewed,
        "any_uploaded": bool(uploaded),
        "all_uploaded": bool(docs) and len(uploaded) == len(docs),
    }


def parse_loan_history(
    message: str, llm_client: LlmClient | None = None
) -> Dict[str, Optional[object]]:
    if is_no_loan_message(message):
        return {"has_loans": False, "loans": []}
    if not llm_client:
        return {}
    return llm_client.extract_loan_history(message)


def extract_interest_rate(message: str) -> Optional[float]:
    text = message.lower()
    match = re.search(r"(\\d+(?:\\.\\d+)?)\\s*(%|percent)", text)
    if not match:
        return None
    value = match.group(1)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def mentions_interest(message: str) -> bool:
    lowered = message.lower()
    return any(word in lowered for word in ["interest", "rate", "%", "percent"])


def is_no_loan_message(message: str) -> bool:
    text = message.lower().strip()
    if not text:
        return False
    if text in {"no", "nope", "nah", "none", "nil"}:
        return True
    patterns = [
        r"\bno\b.*\b(loan|loans|emi|emis|outstanding|debt|liabilit(?:y|ies))\b",
        r"\bno other\b.*\bloan(s)?\b",
        r"\bno existing\b.*\bloan(s)?\b",
        r"\bno current\b.*\bloan(s)?\b",
        r"\bwithout\b.*\bloan(s)?\b",
        r"\b(i|we)\s+(do not|don't|dont)\s+have\s+(any\s+)?(loan|loans|emi|emis|debt|liabilit(?:y|ies)|outstanding)\b",
        r"\b(i|we)\s+have\s+no\s+(loan|loans|emi|emis|debt|liabilit(?:y|ies)|outstanding)\b",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def _extract_phone(text: str) -> Optional[str]:
    match = re.search(r"\b([6-9]\d{9})\b", text)
    return match.group(1) if match else None


def _extract_amount(text: str) -> Optional[int]:
    keywords = ["loan", "amount", "need", "borrow", "required"]
    value = _extract_money_near_keywords(text, keywords, allow_before=True)
    if value is not None:
        return value
    if not any(word in text for word in keywords):
        return None
    return _extract_money(text)


def _extract_salary(text: str) -> Optional[int]:
    keywords = ["salary", "income", "take home", "takehome", "in hand", "inhand", "net"]
    value = _extract_money_near_keywords(text, keywords, allow_before=True)
    if value is not None:
        return value
    if not any(word in text for word in keywords):
        return None
    return _extract_money(text)


def _extract_tenure(text: str) -> Optional[int]:
    if "month" in text or "months" in text or "tenure" in text:
        match = re.search(r"(\d{1,2})\s*(month|months|mo)", text)
        if match:
            return int(match.group(1))
    if "year" in text or "years" in text or "yr" in text:
        match = re.search(r"(\d{1,2})\s*(year|years|yr)", text)
        if match:
            return int(match.group(1)) * 12
    return None


def _extract_name(message: str) -> Optional[str]:
    lowered = message.lower()
    patterns = ["i am", "i'm", "this is", "my name is"]
    for pattern in patterns:
        if pattern in lowered:
            idx = lowered.find(pattern) + len(pattern)
            name = message[idx:].strip()
            cleaned = _clean_name_candidate(name)
            if cleaned and _looks_like_name(cleaned):
                return cleaned[:60]
    if "," in message:
        first = message.split(",", 1)[0].strip()
        cleaned = _clean_name_candidate(first)
        if cleaned and _looks_like_name(cleaned):
            return cleaned[:60]
    phone_match = re.search(r"\b([6-9]\d{9})\b", message)
    if phone_match:
        prefix = message[: phone_match.start()].strip(" ,.-")
        prefix = re.sub(r"^(my name is|i am|i'm|this is)\s+", "", prefix, flags=re.I)
        tokens = [token for token in re.split(r"\s+", prefix) if token]
        if tokens and not any(re.search(r"\d", token) for token in tokens):
            if all(re.search(r"[A-Za-z]", token) for token in tokens):
                candidate = _clean_name_candidate(" ".join(tokens).strip())
                if candidate and _looks_like_name(candidate):
                    return candidate[:60]
    cleaned = _clean_name_candidate(message)
    if cleaned and _looks_like_name(cleaned):
        return cleaned[:60]
    return None


def _clean_name_candidate(candidate: str) -> Optional[str]:
    if not candidate:
        return None
    trimmed = candidate.strip().strip(".,").strip("\"'")
    if not trimmed:
        return None
    trimmed = re.split(r"\d", trimmed, maxsplit=1)[0]
    trimmed = re.split(
        r"\b(?:salary|loan|amount|tenure|mobile|phone|take home|takehome|income|emi|interest)\b",
        trimmed,
        maxsplit=1,
        flags=re.I,
    )[0]
    trimmed = trimmed.strip(" ,.-")
    if not trimmed or re.search(r"\d", trimmed):
        return None
    if not re.search(r"[A-Za-z]", trimmed):
        return None
    return " ".join(trimmed.split())


def _looks_like_name(text: str) -> bool:
    lowered = text.lower()
    if _is_greeting(lowered):
        return False
    if lowered.startswith(("i ", "we ", "my ", "our ")):
        return False
    stopwords = {
        "ok",
        "okay",
        "yes",
        "no",
        "need",
        "want",
        "require",
        "looking",
        "please",
        "hi",
        "hello",
        "thanks",
        "thank you",
        "uploaded",
        "upload",
        "document",
        "documents",
        "proof",
        "proofs",
        "continue",
        "next",
    }
    if lowered in stopwords:
        return False
    words = [word for word in re.split(r"\s+", text) if word]
    if not words or len(words) > 4:
        return False
    for word in words:
        if not re.fullmatch(r"[A-Za-z][A-Za-z\\.'-]*", word):
            return False
        if word.lower() in stopwords:
            return False
    return True


def _extract_money(text: str) -> Optional[int]:
    candidates = _extract_money_candidates(text)
    return candidates[0] if candidates else None


def _extract_confirmation(text: str) -> Optional[bool]:
    if any(word in text for word in ["yes", "ok", "sure", "go ahead", "confirm"]):
        return True
    if any(word in text for word in ["no", "not now", "later"]):
        return False
    return None


def _extract_insurance_preference(text: str) -> Optional[bool]:
    if "insurance" not in text:
        return None
    if any(word in text for word in ["yes", "add", "opt in", "include", "cover me"]):
        return True
    if any(word in text for word in ["no", "skip", "not now", "decline", "without"]):
        return False
    return None


def _has_salary_hint(text: str) -> bool:
    keywords = ["salary", "income", "take home", "takehome", "in hand", "inhand", "net"]
    return any(word in text for word in keywords)


def _extract_money_candidates(text: str) -> list[int]:
    results = []
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(lakh|l|lac|k)?", text):
        value = float(match.group(1))
        suffix = match.group(2)
        end = match.end()
        trailing = text[end : end + 10]
        if trailing.lstrip().startswith("%") or "percent" in trailing:
            continue
        if suffix in {"lakh", "l", "lac"}:
            amount = int(value * 100000)
        elif suffix == "k":
            amount = int(value * 1000)
        else:
            if value < 1000:
                continue
            amount = int(value)
        results.append(amount)
    return results


def _extract_money_near_keywords(
    text: str, keywords: list[str], allow_before: bool = False
) -> Optional[int]:
    keyword_group = "|".join(re.escape(word) for word in keywords)
    before_pattern = rf"(?:{keyword_group})[^0-9]{{0,10}}(\d+(?:\.\d+)?)\s*(lakh|l|lac|k)?"
    after_pattern = rf"(\d+(?:\.\d+)?)\s*(lakh|l|lac|k)?[^0-9]{{0,10}}(?:{keyword_group})"

    match = re.search(before_pattern, text)
    if match:
        return _normalize_money(match.group(1), match.group(2))
    if allow_before:
        match = re.search(after_pattern, text)
        if match:
            return _normalize_money(match.group(1), match.group(2))
    return None


def _normalize_money(value: str, suffix: Optional[str]) -> Optional[int]:
    number = float(value)
    if suffix in {"lakh", "l", "lac"}:
        return int(number * 100000)
    if suffix == "k":
        return int(number * 1000)
    if number < 1000:
        return None
    return int(number)


def _infer_amount(candidates: list[int], salary: Optional[int]) -> Optional[int]:
    if salary is not None:
        for value in candidates:
            if value != salary:
                return value
        return None
    return candidates[0] if candidates else None


def _infer_salary(candidates: list[int]) -> Optional[int]:
    return max(candidates) if candidates else None


def _is_question(text: str) -> bool:
    question_starters = (
        "what",
        "how",
        "when",
        "where",
        "why",
        "can",
        "do",
        "is",
        "are",
        "tell",
        "explain",
        "rate",
        "fees",
        "documents",
        "eligibility",
    )
    return "?" in text or text.startswith(question_starters)


def _is_greeting(text: str) -> bool:
    greetings = ["hi", "hello", "hey", "good morning", "good evening"]
    return any(re.search(rf"\b{re.escape(greet)}\b", text) for greet in greetings)


def _is_insurance_query(text: str) -> bool:
    keywords = ["insurance", "cover", "coverage", "policy", "premium", "protection"]
    return any(word in text for word in keywords)


def _is_loan_query(text: str) -> bool:
    keywords = [
        "loan",
        "emi",
        "interest",
        "rate",
        "tenure",
        "personal loan",
        "eligibility",
        "documents",
        "processing",
        "fees",
        "approval",
    ]
    return any(word in text for word in keywords)
