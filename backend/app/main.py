from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.agents.graph import GRAPH
from app.config import get_settings
from app.models import (
    ChatMessageEntry,
    ChatRequest,
    ChatResponse,
    ChatStateSummary,
    SessionStateResponse,
    UploadResponse,
)
from app.services import credit_bureau, crm, offers
from app.services.firebase import FirebaseService
from app.services.state_store import StateStore
from app.services.session_registry import SessionRegistry
from app.services.storage import StorageClient

settings = get_settings()
firebase_service = FirebaseService()
state_store = StateStore(firebase_service)
storage_client = StorageClient()
session_registry = SessionRegistry(firebase_service)

app = FastAPI(title="NBFC Agentic Loan Assistant")

static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_user(authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    if settings.disable_auth:
        return {"uid": "local-user"}
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing auth token")
    token = authorization.split(" ", 1)[1]
    verified = firebase_service.verify_token(token)
    if not verified:
        raise HTTPException(status_code=401, detail="Invalid auth token")
    return verified


def _default_state(session_id: str) -> Dict[str, Any]:
    return {
        "session_id": session_id,
        "messages": [],
        "events": [],
        "owner_id": "",
        "customer": {},
        "loan": {},
        "verified": False,
        "underwritten": False,
        "approved": False,
        "rejected": False,
        "needs_salary_slip": False,
        "salary_slip_uploaded": False,
        "info_collected": False,
        "documents_requested": False,
        "documents_reviewed": False,
        "documents": {
            "salary_slip": {"uploaded": False, "reviewed": False},
            "bank_statement": {"uploaded": False, "reviewed": False},
            "address_proof": {"uploaded": False, "reviewed": False},
        },
        "loan_history_requested": False,
        "loan_history_collected": False,
        "offer_presented": False,
        "offer_confirmed": False,
        "loan_terms_ready": False,
        "terms_presented": False,
        "terms_confirmed": False,
        "insurance_opted": None,
        "insurance_prompted": False,
        "sanctioned": False,
        "sanction_signature": None,
        "sanction_ref": None,
        "rate_tier": None,
        "master_pass": False,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }


def _state_summary(state: Dict[str, Any]) -> ChatStateSummary:
    loan = state.get("loan", {})
    return ChatStateSummary(
        verified=state.get("verified", False),
        underwritten=state.get("underwritten", False),
        approved=state.get("approved", False),
        rejected=state.get("rejected", False),
        needs_salary_slip=state.get("needs_salary_slip", False),
        salary_slip_uploaded=state.get("salary_slip_uploaded", False),
        info_collected=state.get("info_collected", False),
        documents=state.get("documents", {}),
        documents_reviewed=state.get("documents_reviewed", False),
        loan_history_collected=state.get("loan_history_collected", False),
        offer_presented=state.get("offer_presented", False),
        offer_confirmed=state.get("offer_confirmed", False),
        loan_terms_ready=state.get("loan_terms_ready", False),
        terms_presented=state.get("terms_presented", False),
        terms_confirmed=state.get("terms_confirmed", False),
        insurance_opted=state.get("insurance_opted"),
        pre_approved_limit=state.get("pre_approved_limit"),
        credit_score=state.get("credit_score"),
        sanction_url=state.get("sanction_url"),
        sanction_signature=state.get("sanction_signature"),
        sanction_ref=state.get("sanction_ref"),
        loan_terms={
            "amount": loan.get("amount"),
            "tenure_months": loan.get("tenure_months"),
            "interest_rate": loan.get("interest_rate"),
            "emi": loan.get("emi"),
            "rate_tier": state.get("rate_tier"),
        },
    )


def _state_messages(state: Dict[str, Any], limit: int = 50) -> list[ChatMessageEntry]:
    messages = state.get("messages", [])
    trimmed = messages[-limit:] if isinstance(messages, list) else []
    return [
        ChatMessageEntry(role=msg.get("role", "assistant"), content=msg.get("content", ""))
        for msg in trimmed
        if isinstance(msg, dict)
    ]


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest, user: Dict[str, Any] = Depends(get_current_user)) -> ChatResponse:
    uid = user.get("uid", "local-user")
    if request.new_session:
        session_id = str(uuid4())
    else:
        session_id = (
            request.session_id
            or session_registry.get_active_session(uid)
            or str(uuid4())
        )
    state = state_store.load(session_id) or _default_state(session_id)
    state["owner_id"] = uid

    state["last_user_message"] = request.message
    state.setdefault("messages", []).append({"role": "user", "content": request.message})
    state["master_pass"] = False

    before_events = len(state.get("events", []))
    new_state = GRAPH.invoke(state)
    session_registry.set_active_session(uid, session_id)

    reply = new_state.get("reply") or "Thanks! Could you share a bit more detail?"
    new_state.setdefault("messages", []).append({"role": "assistant", "content": reply})
    state_store.save(session_id, new_state)

    events = new_state.get("events", [])[before_events:]
    return ChatResponse(
        session_id=session_id,
        reply=reply,
        state=_state_summary(new_state),
        events=events,
    )


@app.get("/api/session/active", response_model=SessionStateResponse)
def get_active_session(
    session_id: str | None = None,
    user: Dict[str, Any] = Depends(get_current_user),
) -> SessionStateResponse:
    uid = user.get("uid", "local-user")
    target_session = session_id or session_registry.get_active_session(uid)
    if not target_session:
        return SessionStateResponse()
    state = state_store.load(target_session)
    if not state:
        return SessionStateResponse(session_id=target_session)
    owner_id = state.get("owner_id")
    if owner_id and owner_id != uid:
        raise HTTPException(status_code=403, detail="Session not accessible")
    return SessionStateResponse(
        session_id=target_session,
        state=_state_summary(state),
        events=state.get("events", []),
        messages=_state_messages(state),
    )


@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(
    session_id: str | None = Form(default=None),
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(get_current_user),
) -> UploadResponse:
    uid = user.get("uid", "local-user")
    active_session = session_id or session_registry.get_active_session(uid)
    if not active_session:
        raise HTTPException(status_code=400, detail="Start a chat session before uploading.")

    state = state_store.load(active_session)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    contents = await file.read()
    filename = f"{doc_type}_{active_session}_{file.filename}"
    file_url = storage_client.upload_uploads(
        contents,
        filename,
        file.content_type,
        owner_id=uid,
    )

    documents = state.get("documents")
    if not documents:
        documents = {
            "salary_slip": {"uploaded": False, "reviewed": False},
            "bank_statement": {"uploaded": False, "reviewed": False},
            "address_proof": {"uploaded": False, "reviewed": False},
        }
        state["documents"] = documents
    if doc_type in documents:
        documents[doc_type]["uploaded"] = True
        documents[doc_type]["reviewed"] = False
        state["documents_requested"] = True

    if doc_type == "salary_slip":
        state["salary_slip_uploaded"] = True
        state["needs_salary_slip"] = False
        state_store.save(active_session, state)
    else:
        state_store.save(active_session, state)

    return UploadResponse(session_id=active_session, doc_type=doc_type, file_url=file_url)


@app.get("/api/mock/crm/{phone}")
def mock_crm(phone: str, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    data = crm.fetch_kyc_by_phone(phone)
    if not data:
        raise HTTPException(status_code=404, detail="Customer not found")
    return data


@app.get("/api/mock/offers/{customer_id}")
def mock_offers(customer_id: str, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return offers.fetch_offer(customer_id)


@app.get("/api/mock/credit/{customer_id}")
def mock_credit(customer_id: str, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return credit_bureau.fetch_credit_score(customer_id)
