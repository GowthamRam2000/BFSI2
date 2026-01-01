from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentEvent(BaseModel):
    agent: str
    action: str
    detail: str
    ts: str


class ChatMessageEntry(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    customer_hint: Optional[Dict[str, Any]] = None
    new_session: Optional[bool] = False


class LoanTerms(BaseModel):
    amount: Optional[int] = None
    tenure_months: Optional[int] = None
    interest_rate: Optional[float] = None
    emi: Optional[float] = None
    rate_tier: Optional[str] = None


class ChatStateSummary(BaseModel):
    verified: bool = False
    underwritten: bool = False
    approved: bool = False
    rejected: bool = False
    needs_salary_slip: bool = False
    salary_slip_uploaded: bool = False
    loan_terms_ready: bool = False
    terms_presented: bool = False
    terms_confirmed: bool = False
    info_collected: bool = False
    documents: Dict[str, Dict[str, bool]] = Field(default_factory=dict)
    documents_reviewed: bool = False
    loan_history_collected: bool = False
    offer_presented: bool = False
    offer_confirmed: bool = False
    insurance_opted: Optional[bool] = None
    pre_approved_limit: Optional[int] = None
    credit_score: Optional[int] = None
    sanction_url: Optional[str] = None
    sanction_signature: Optional[str] = None
    sanction_ref: Optional[str] = None
    loan_terms: LoanTerms = Field(default_factory=LoanTerms)


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    state: ChatStateSummary
    events: List[AgentEvent] = Field(default_factory=list)


class UploadResponse(BaseModel):
    session_id: str
    doc_type: str
    file_url: str


class SessionStateResponse(BaseModel):
    session_id: Optional[str] = None
    state: Optional[ChatStateSummary] = None
    events: List[AgentEvent] = Field(default_factory=list)
    messages: List[ChatMessageEntry] = Field(default_factory=list)


class MockCustomerResponse(BaseModel):
    customer_id: str
    data: Dict[str, Any]
