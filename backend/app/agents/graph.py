from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.llm import LlmClient
from app.agents.prompts import MASTER_SYSTEM, SALES_SYSTEM, SANCTION_SYSTEM
from app.agents.tools import (
    classify_message,
    document_status,
    extract_interest_rate,
    is_no_loan_message,
    is_question,
    mentions_interest,
    parse_loan_history,
    parse_user_message,
)
from app.services import credit_bureau, crm, offers, sanction, underwriting
from app.services.storage import StorageClient


class GraphState(TypedDict, total=False):
    session_id: str
    messages: List[Dict[str, str]]
    last_user_message: str
    reply: str
    events: List[Dict[str, str]]
    owner_id: str
    customer: Dict[str, Any]
    loan: Dict[str, Any]
    verified: bool
    underwritten: bool
    approved: bool
    rejected: bool
    needs_salary_slip: bool
    salary_slip_uploaded: bool
    info_collected: bool
    documents_requested: bool
    documents_reviewed: bool
    documents: Dict[str, Dict[str, bool]]
    loan_history_requested: bool
    loan_history_collected: bool
    offer_presented: bool
    offer_confirmed: bool
    loan_terms_ready: bool
    terms_presented: bool
    terms_confirmed: bool
    insurance_opted: bool | None
    insurance_prompted: bool
    credit_score: int
    pre_approved_limit: int
    rate_tier: str
    sanction_url: str
    sanction_signature: str
    sanction_ref: str
    sanctioned: bool
    halt: bool
    master_pass: bool


llm_client = LlmClient()


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _append_event(state: GraphState, agent: str, action: str, detail: str) -> None:
    state.setdefault("events", []).append(
        {"agent": agent, "action": action, "detail": detail, "ts": _now()}
    )


def _default_documents() -> Dict[str, Dict[str, bool]]:
    return {
        "salary_slip": {"uploaded": False, "reviewed": False},
        "bank_statement": {"uploaded": False, "reviewed": False},
        "address_proof": {"uploaded": False, "reviewed": False},
    }


def _has_required_info(state: GraphState) -> bool:
    customer = state.get("customer", {})
    loan = state.get("loan", {})
    return all(
        [
            customer.get("name"),
            customer.get("phone"),
            customer.get("monthly_salary"),
            loan.get("amount"),
            loan.get("tenure_months"),
        ]
    )


def _ensure_state_defaults(state: GraphState) -> None:
    state.setdefault("customer", {})
    state.setdefault("loan", {})
    state.setdefault("events", [])
    state.setdefault("messages", [])
    state.setdefault("owner_id", "")
    state.setdefault("verified", False)
    state.setdefault("underwritten", False)
    state.setdefault("approved", False)
    state.setdefault("rejected", False)
    state.setdefault("needs_salary_slip", False)
    state.setdefault("salary_slip_uploaded", False)
    state.setdefault("info_collected", False)
    state.setdefault("documents_requested", False)
    state.setdefault("documents_reviewed", False)
    documents = state.setdefault("documents", _default_documents())
    for key, value in _default_documents().items():
        documents.setdefault(key, value)
    state.setdefault("loan_history_requested", False)
    state.setdefault("loan_history_collected", False)
    state.setdefault("offer_presented", False)
    state.setdefault("offer_confirmed", False)
    state.setdefault("loan_terms_ready", False)
    state.setdefault("terms_presented", False)
    state.setdefault("terms_confirmed", False)
    state.setdefault("insurance_opted", None)
    state.setdefault("insurance_prompted", False)
    state.setdefault("sanctioned", False)
    state.setdefault("master_pass", False)


def master_node(state: GraphState) -> GraphState:
    _ensure_state_defaults(state)
    if not state.get("master_pass"):
        state["halt"] = False
        state["reply"] = ""
        state["master_pass"] = True

    if state.get("rejected"):
        state["reply"] = (
            "Thanks for your time. Based on the current details, we are unable to proceed with "
            "the personal loan. If you would like to explore alternative options, I can help."
        )
        state["halt"] = True
        return state

    if state.get("last_user_message"):
        parsed = parse_user_message(state["last_user_message"], llm_client=llm_client)
        loan_history_mode = state.get("loan_history_requested") and not state.get(
            "loan_history_collected"
        )
        has_flow_data = any(
            key in parsed for key in ["name", "phone", "amount", "tenure_months", "salary"]
        ) or parsed.get("confirm") is not None or "insurance_opt_in" in parsed
        if "name" in parsed and not state["customer"].get("name"):
            state["customer"]["name"] = parsed["name"]
        if "phone" in parsed:
            state["customer"]["phone"] = parsed["phone"]
        if not loan_history_mode and "amount" in parsed:
            # Context-aware fallback: If we already have loan amount but need salary, and new amount fits logic
            if state["loan"].get("amount") and not state["customer"].get("monthly_salary") and "salary" not in parsed:
                # Heuristic: If user just typed a number and we need salary, assume it's salary
                state["customer"]["monthly_salary"] = parsed["amount"]
            else:
                state["loan"]["amount"] = parsed["amount"]
        if not loan_history_mode and "tenure_months" in parsed:
            state["loan"]["tenure_months"] = parsed["tenure_months"]
        if not loan_history_mode and "salary" in parsed:
            state["customer"]["monthly_salary"] = parsed["salary"]

        if _has_required_info(state):
            state["info_collected"] = True
            state["loan_terms_ready"] = True

        if loan_history_mode:
            lowered = state["last_user_message"].strip().lower()
            if is_no_loan_message(state["last_user_message"]):
                state["customer"]["declared_loans"] = []
                state["loan_history_collected"] = True
                _append_event(state, "Verification", "loan_history", "No outstanding loans")
                state["last_user_message"] = ""
                return state
            history = parse_loan_history(state["last_user_message"], llm_client=llm_client)
            if history.get("has_loans") is False:
                state["customer"]["declared_loans"] = []
                state["loan_history_collected"] = True
                _append_event(state, "Verification", "loan_history", "No outstanding loans")
            elif history.get("loans"):
                state["customer"]["declared_loans"] = history.get("loans", [])
                state["loan_history_collected"] = True
                _append_event(state, "Verification", "loan_history", "Captured outstanding loans")
            if state.get("loan_history_collected"):
                state["last_user_message"] = ""
                return state

        offer_active = (
            state.get("offer_presented")
            and state.get("terms_presented")
            and state.get("underwritten")
            and state.get("approved")
        )

        if not loan_history_mode and offer_active and mentions_interest(state["last_user_message"]):
            desired_rate = extract_interest_rate(state["last_user_message"])
            current_rate = state["loan"].get("interest_rate")
            available_rates = [9.0, 11.0, 13.0, 14.7]
            if desired_rate:
                if current_rate and float(current_rate) == float(desired_rate):
                    prompt = (
                        f"You're already at {current_rate}% for this offer. "
                        "Would you like me to generate the signed loan slip?"
                    )
                elif desired_rate in available_rates:
                    prompt = (
                        f"Our rates are fixed tiers ({', '.join(str(rate) for rate in available_rates)}%). "
                        f"Based on your profile, the best available rate right now is {current_rate}%. "
                        "I can proceed with that, or we can adjust amount/tenure to see if another tier applies."
                    )
                else:
                    prompt = (
                        f"Our rates are fixed tiers ({', '.join(str(rate) for rate in available_rates)}%). "
                        f"Based on your profile, the best available rate right now is {current_rate}%. "
                        "Would you like to proceed with that or adjust the loan details?"
                    )
            else:
                prompt = (
                    f"Our rates are fixed tiers ({', '.join(str(rate) for rate in available_rates)}%). "
                    f"Based on your profile, the best available rate right now is {current_rate}%. "
                    "Would you like to proceed with that or adjust the loan details?"
                )
            state["reply"] = llm_client.generate_text(SALES_SYSTEM, prompt, fallback=prompt)
            _append_event(state, "Sales", "rate_discussion", "Customer requested rate change")
            state["halt"] = True
            return state

        if not loan_history_mode and offer_active and parsed.get("confirm") is True:
            state["offer_confirmed"] = True
            state["terms_confirmed"] = True
        if not loan_history_mode and offer_active and parsed.get("confirm") is False:
            state["reply"] = "No problem. Tell me what you'd like to change and I will adjust."
            _append_event(state, "Master", "offer_declined", "Customer declined offer")
            state["halt"] = True
            return state

        if (
            parsed.get("confirm") is not None
            and state.get("insurance_prompted")
            and not state.get("offer_presented")
        ):
            state["insurance_opted"] = bool(parsed["confirm"])
            choice = "opted_in" if state["insurance_opted"] else "declined"
            _append_event(state, "Master", "insurance_choice", f"Customer {choice}")
        if "insurance_opt_in" in parsed:
            state["insurance_opted"] = bool(parsed["insurance_opt_in"])
            choice = "opted_in" if state["insurance_opted"] else "declined"
            _append_event(state, "Master", "insurance_choice", f"Customer {choice}")

        if not loan_history_mode:
            documents = state.get("documents") or {}
            any_docs = any(info.get("uploaded") for info in documents.values())
            conversation_started = len(state.get("messages", [])) > 1
            flow_active = any(
                [
                    state.get("info_collected"),
                    state.get("documents_requested"),
                    state.get("verified"),
                    state.get("loan_history_requested"),
                    state.get("offer_presented"),
                    state.get("offer_confirmed"),
                    any_docs,
                    conversation_started,
                    state["customer"].get("name"),
                    state["customer"].get("phone"),
                    state["customer"].get("monthly_salary"),
                    state["loan"].get("amount"),
                    state["loan"].get("tenure_months"),
                ]
            )
            message_text = state["last_user_message"].lower()
            mentions_upload = any(
                word in message_text
                for word in ["upload", "uploaded", "document", "documents", "proof", "proofs"]
            )
            question_like = is_question(state["last_user_message"])
            effective_flow = has_flow_data or (flow_active and not question_like) or (mentions_upload and not question_like)
            intent = classify_message(state["last_user_message"], effective_flow)
            if intent in {"greeting", "off_topic", "insurance_faq", "insurance_note", "loan_faq", "loan_note"}:
                prompt = _faq_prompt(intent, state)
                state["reply"] = llm_client.generate_text(MASTER_SYSTEM, prompt, fallback=prompt)
                _append_event(state, "Master", "faq", f"Intent: {intent}")
                if intent in {"insurance_faq", "insurance_note"}:
                    state["insurance_prompted"] = True
                state["halt"] = True
                return state

    return state


def sales_agent(state: GraphState) -> GraphState:
    _ensure_state_defaults(state)
    if state["customer"].get("phone") and not state["customer"].get("monthly_salary"):
        crm_data = crm.fetch_kyc_by_phone(state["customer"]["phone"])
        if crm_data and crm_data.get("monthly_salary"):
            state["customer"]["monthly_salary"] = crm_data["monthly_salary"]
            if not state["customer"].get("name") and crm_data.get("name"):
                state["customer"]["name"] = crm_data["name"]

    docs = document_status(state.get("documents"))
    if docs["any_uploaded"] and not state.get("documents_requested"):
        state["documents_requested"] = True

    missing = []
    if not state["customer"].get("name"):
        missing.append("full name")
    if not state["customer"].get("phone"):
        missing.append("10-digit mobile number")
    if not state["loan"].get("amount"):
        missing.append("desired loan amount")
    if not state["loan"].get("tenure_months"):
        missing.append("preferred tenure in months")
    if not state["customer"].get("monthly_salary"):
        missing.append("monthly take-home salary")

    if missing:
        doc_note = ""
        if docs["all_uploaded"]:
            doc_note = " I can already see your documents in our system."
        elif docs["any_uploaded"]:
            uploaded_list = ", ".join(name.replace("_", " ") for name in docs["uploaded"])
            doc_note = f" I can see your {uploaded_list} uploaded; you can add the rest anytime."
        else:
            doc_note = (
                " If it's convenient, you can upload your salary slip, bank statement, and "
                "address proof now so we can review them early."
            )
        captured = []
        if state["customer"].get("name"):
            captured.append("full name")
        if state["customer"].get("phone"):
            captured.append("mobile number")
        if state["loan"].get("amount"):
            captured.append("loan amount")
        if state["loan"].get("tenure_months"):
            captured.append("tenure")
        if state["customer"].get("monthly_salary"):
            captured.append("salary")

        name = state["customer"].get("name")
        prefix = f"Thanks, {name}. " if name else "Thanks. "
        if captured:
            prefix += "I have your " + ", ".join(captured) + ". "

        missing_text = ", ".join(missing)
        if len(missing) == 1:
            ask = f"Just need your {missing_text} to continue."
        else:
            ask = f"I still need your {missing_text} to continue."
        fallback = (
            prefix
            + ask
            + doc_note
        )
        doc_summary = "none"
        if docs["all_uploaded"]:
            doc_summary = "all_uploaded"
        elif docs["any_uploaded"]:
            doc_summary = f"partial ({', '.join(docs['uploaded'])})"

        llm_prompt = (
            "Compose a warm, human one-turn reply for a loan intake chat. "
            f"Known details: {captured or 'none'}. Missing details: {missing}. "
            f"Documents: {doc_summary}. "
            "Use the customer's name if available. Ask only for missing details. "
            "If documents are already uploaded, acknowledge briefly. "
            "If none, invite uploads gently. Keep it to 1-2 short sentences."
        )
        state["reply"] = llm_client.generate_text(SALES_SYSTEM, llm_prompt, fallback=fallback)
        state["documents_requested"] = True
        _append_event(state, "Sales", "collect_info", "Requested missing details")
        state["halt"] = True
        return state

    if not state.get("info_collected"):
        state["info_collected"] = True
        state["loan_terms_ready"] = True

    if state.get("approved") and state.get("underwritten") and not state.get("offer_presented"):
        amount = state["loan"].get("amount")
        tenure = state["loan"].get("tenure_months")
        rate = state["loan"].get("interest_rate")
        tier = state.get("rate_tier", "")
        emi = state["loan"].get("emi")
        insurance = "included" if state.get("insurance_opted") else "optional"

        prompt = (
            f"Here are your personalized options: INR {amount} for {tenure} months at "
            f"{rate}% ({tier}). Estimated EMI is INR {emi}. "
            f"Loan protection insurance is {insurance}. "
            "Would you like me to generate the signed loan slip?"
        )
        state["reply"] = llm_client.generate_text(SALES_SYSTEM, prompt, fallback=prompt)
        state["offer_presented"] = True
        state["terms_presented"] = True
        _append_event(state, "Sales", "offer_presented", "Shared final offer options")
        state["halt"] = True
        return state

    if state.get("offer_presented") and not state.get("offer_confirmed"):
        prompt = (
            "Would you like me to generate the signed loan slip for the offer I just shared? "
            "You can say yes to proceed or tell me what you'd like to change."
        )
        state["reply"] = llm_client.generate_text(SALES_SYSTEM, prompt, fallback=prompt)
        _append_event(state, "Sales", "offer_followup", "Awaiting offer confirmation")
        state["halt"] = True
        return state

    if not state.get("documents_requested"):
        prompt = (
            "Please upload your salary slip, bank statement, and address proof. "
            "Devi will review them and then we will move to underwriting."
        )
        state["reply"] = llm_client.generate_text(SALES_SYSTEM, prompt, fallback=prompt)
        state["documents_requested"] = True
        _append_event(state, "Sales", "request_documents", "Requested document uploads")
        state["halt"] = True
        return state

    return state


def verification_agent(state: GraphState) -> GraphState:
    _ensure_state_defaults(state)
    phone = state["customer"].get("phone")
    if not phone:
        state["reply"] = "Please share your registered mobile number to continue verification."
        _append_event(state, "Verification", "request_phone", "Asked for phone")
        state["halt"] = True
        return state

    if not state.get("verified"):
        kyc = crm.fetch_kyc_by_phone(phone)
        if not kyc:
            state["customer"]["customer_id"] = "PROSPECT"
            state["verified"] = True
            state["reply"] = (
                "I could not find you in our records, so I will proceed as a new customer. "
                "If possible, share your city and address for KYC updates."
            )
            _append_event(state, "Verification", "verified_new", "Verified prospect details")
            state["halt"] = True
            return state

        state["customer"].update(kyc)
        state["verified"] = True
        _append_event(state, "Verification", "verified", "KYC verified from CRM")

    documents = state.get("documents") or _default_documents()
    state["documents"] = documents
    missing_docs = [key for key, info in documents.items() if not info.get("uploaded")]
    if missing_docs:
        doc_list = ", ".join(name.replace("_", " ") for name in missing_docs)
        state["reply"] = (
            "Please upload your "
            f"{doc_list}. I will review them before underwriting."
        )
        state["documents_requested"] = True
        _append_event(state, "Verification", "request_documents", "Requested document uploads")
        state["halt"] = True
        return state

    if not state.get("documents_reviewed"):
        reviewed = []
        for doc_key, info in documents.items():
            if info.get("uploaded") and not info.get("reviewed"):
                info["reviewed"] = True
                reviewed.append(doc_key.replace("_", " "))
                _append_event(state, "Verification", "document_review", f"Reviewed {doc_key}")
        state["documents_reviewed"] = True
        state["loan_history_requested"] = True
        reviewed_list = ", ".join(reviewed) if reviewed else "your documents"
        state["reply"] = (
            f"Thanks! I have reviewed {reviewed_list}. "
            "Do you have any outstanding loans? If yes, share lender, loan type, "
            "EMI, and outstanding balance. If none, just say 'no outstanding loans'."
        )
        state["halt"] = True
        return state

    if not state.get("loan_history_collected"):
        state["loan_history_requested"] = True
        state["reply"] = (
            "Quick check before underwriting - do you have any outstanding loans? "
            "Share lender, type, EMI, and outstanding balance, or say 'no outstanding loans'."
        )
        state["halt"] = True
        return state

    return state


def underwriting_agent(state: GraphState) -> GraphState:
    _ensure_state_defaults(state)
    if state.get("underwritten") or state.get("rejected"):
        return state

    loan_amount = state["loan"].get("amount")
    tenure = state["loan"].get("tenure_months")
    if not loan_amount or not tenure:
        return state

    customer_id = state["customer"].get("customer_id")
    offer = offers.fetch_offer(customer_id)
    credit = credit_bureau.fetch_credit_score(customer_id)
    state["credit_score"] = credit["credit_score"]
    state["pre_approved_limit"] = offer["pre_approved_limit"]

    existing_emi = sum(
        loan.get("emi", 0) for loan in state["customer"].get("existing_loans", [])
    )
    declared_loans = state["customer"].get("declared_loans", [])
    declared_emi = sum(loan.get("emi", 0) for loan in declared_loans if isinstance(loan, dict))
    total_existing_emi = existing_emi + declared_emi

    decision, details = underwriting.evaluate_application(
        requested_amount=loan_amount,
        tenure_months=tenure,
        pre_approved_limit=offer["pre_approved_limit"],
        credit_score=credit["credit_score"],
        monthly_salary=state["customer"].get("monthly_salary"),
        existing_emi=total_existing_emi,
        salary_slip_uploaded=state.get("salary_slip_uploaded", False),
    )

    if decision == "needs_salary_slip":
        state["needs_salary_slip"] = True
        state["reply"] = (
            "Your requested amount exceeds your pre-approved limit. "
            "Please upload your latest salary slip so I can complete underwriting."
        )
        _append_event(state, "Underwriting", "request_salary_slip", "Salary slip needed")
        state["halt"] = True
        return state

    if decision.startswith("rejected"):
        state["rejected"] = True
        state["underwritten"] = True
        reason = {
            "rejected_low_score": "credit score",
            "rejected_low_income": "income eligibility",
            "rejected_over_limit": "policy limits",
            "rejected_emi": "EMI affordability",
        }.get(decision, "policy limits")
        state["reply"] = (
            f"Thanks for the details. Based on current {reason}, we cannot approve the loan."
        )
        _append_event(state, "Underwriting", "rejected", f"Decision: {decision}")
        state["halt"] = True
        return state

    state["underwritten"] = True
    state["approved"] = True
    if details.get("emi"):
        state["loan"]["emi"] = round(details["emi"], 2)
    if details.get("rate"):
        state["loan"]["interest_rate"] = round(float(details["rate"]), 2)
    if details.get("rate_tier"):
        state["rate_tier"] = str(details["rate_tier"])
    tier = details.get("rate_tier", "")
    detail = f"Decision: {decision}" + (f"; Tier: {tier}" if tier else "")
    _append_event(state, "Underwriting", "approved", detail)
    return state


def sanction_agent(state: GraphState) -> GraphState:
    _ensure_state_defaults(state)
    if state.get("sanctioned") or not state.get("approved"):
        return state

    payload = {
        "name": state["customer"].get("name", "Customer"),
        "customer_id": state["customer"].get("customer_id", "PROSPECT"),
        "amount": str(state["loan"].get("amount", "")),
        "tenure_months": str(state["loan"].get("tenure_months", "")),
        "interest_rate": str(state["loan"].get("interest_rate") or ""),
        "rate_tier": str(state.get("rate_tier") or ""),
        "emi": str(state["loan"].get("emi") or ""),
        "pre_approved_limit": str(state.get("pre_approved_limit") or ""),
        "insurance_opted": "Yes" if state.get("insurance_opted") else "No",
    }

    pdf_bytes, filename, signature, secure_ref = sanction.generate_sanction_pdf(payload)
    storage = StorageClient()
    owner_id = state.get("owner_id") or None
    url = storage.upload_sanctions(pdf_bytes, filename, "application/pdf", owner_id=owner_id)
    state["sanction_url"] = url
    state["sanction_signature"] = signature
    state["sanction_ref"] = secure_ref
    state["sanctioned"] = True

    prompt = "Your signed loan slip is ready. You can download it from the secure link provided."
    state["reply"] = llm_client.generate_text(SANCTION_SYSTEM, prompt, fallback=prompt)
    _append_event(state, "Sanction", "generated", "Loan slip generated")
    state["halt"] = True
    return state


def route_from_master(state: GraphState) -> str:
    if state.get("halt"):
        return END
    if state.get("rejected"):
        return END
    if not state.get("info_collected"):
        return "sales"
    if not state.get("verified") or not state.get("documents_reviewed") or not state.get("loan_history_collected"):
        return "verification"
    if not state.get("underwritten"):
        return "underwriting"
    if state.get("approved") and not state.get("offer_confirmed"):
        return "sales"
    if state.get("approved") and state.get("offer_confirmed") and not state.get("sanctioned"):
        return "sanction"
    return END


def _faq_prompt(intent: str, state: GraphState) -> str:
    if intent == "greeting":
        docs = state.get("documents", {})
        any_uploaded = any(d.get("uploaded") for d in docs.values())
        if any_uploaded:
            uploaded_names = [k.replace("_", " ") for k, v in docs.items() if v.get("uploaded")]
            doc_msg = f"I see you have already uploaded your {', '.join(uploaded_names)}. Thanks! "
            return (
                f"Hi! Welcome to the EY Techathon Demo. {doc_msg}"
                "How much loan amount are you looking for?"
            )
        
        return (
            "Hi! I'm your NBFC digital assistant for personal loans and loan protection insurance. "
            "You can start by uploading your salary slip, bank statement, and address proof. "
            "Share your loan need and I will take it from there."
        )
    if intent == "off_topic":
        return (
            "I can help with personal loans and loan protection insurance only. "
            "What would you like to know about?"
        )
    if intent in {"insurance_faq", "insurance_note"}:
        return (
            "We offer loan protection insurance that helps cover EMIs during unexpected events. "
            "Premiums depend on loan amount and tenure. Would you like me to include insurance "
            "when we process your loan?"
        )
    if intent in {"loan_faq", "loan_note"}:
        return (
            "Personal loans are available for 12 to 60 months. Rates fall into four tiers: "
            "9%, 11%, 13%, or 14.7% p.a., based on income, existing EMIs, credit score, and "
            "salary slip verification. Typical documents include PAN, address proof, and salary slip. "
            "Would you like to check your eligibility?"
        )
    return ""


def build_graph() -> StateGraph:
    graph = StateGraph(GraphState)
    graph.add_node("master", master_node)
    graph.add_node("sales", sales_agent)
    graph.add_node("verification", verification_agent)
    graph.add_node("underwriting", underwriting_agent)
    graph.add_node("sanction", sanction_agent)

    graph.add_edge(START, "master")
    graph.add_conditional_edges("master", route_from_master)
    graph.add_edge("sales", "master")
    graph.add_edge("verification", "master")
    graph.add_edge("underwriting", "master")
    graph.add_edge("sanction", "master")
    return graph.compile()


GRAPH = build_graph()
