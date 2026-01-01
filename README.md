# BFSI Agentic Loan Assistant

NBFC-style loan origination demo with a multi-agent workflow. The backend is a FastAPI
service orchestrated with LangGraph and optional OpenAI extraction. The frontend is a
Vue 3 + Vite experience that guides users through chat, verification, document upload,
and a signed sanction letter.

## What this does

- Multi-agent flow: Master, Sales, Verification, Underwriting, Sanction.
- Loan chat that captures KYC, income, tenure, and loan intent.
- Mock CRM, credit score, and offer data from local JSON.
- Eligibility checks, rate tiers, and EMI calculation.
- Document upload flow (salary slip, bank statement, address proof).
- Sanction letter PDF with HMAC signature and secure reference.
- Event timeline and decision snapshot UI.

## Tech stack

- Backend: FastAPI, LangGraph, OpenAI SDK, Firebase Admin, Google Cloud Storage.
- Frontend: Vue 3, Vite, Firebase Auth.

## Repository layout

- `backend/`: FastAPI service, agents, mock data, PDF generation.
- `frontend/`: Vue application with chat and upload flows.
- `data/`: Local demo documents (ignored by git).

## Prerequisites

- Python 3.11+ (Dockerfile uses 3.13)
- Node.js 20+
- Firebase project (Auth + Firestore + Storage) if `DISABLE_AUTH=false`

## Setup (local)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `backend/.env` (see configuration below), then run:

```bash
uvicorn app.main:app --reload --port 8000
```

Optional environment check:

```bash
python scripts/env_check.py
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`.

## Configuration

### Backend (`backend/.env`)

Core:
- `ENV`: runtime label, e.g. `local`
- `BASE_URL`: used for local storage URLs, e.g. `http://localhost:8000`
- `FRONTEND_ORIGIN`: CORS origin, e.g. `http://localhost:5173`
- `DISABLE_AUTH`: `true` to bypass Firebase auth and use in-memory storage

LLM:
- `OPENAI_MODEL`: model name, e.g. `gpt-5-mini`
- `OPENAI_API_KEY`: optional; without it, the app falls back to heuristics

Firebase / GCP:
- `FIREBASE_PROJECT_ID`: Firebase project id
- `GCP_PROJECT_ID`: optional override for GCP
- `GOOGLE_APPLICATION_CREDENTIALS`: path to Firebase service account JSON (keep outside repo)
- `FIREBASE_STORAGE_BUCKET`: bucket name (no `gs://` prefix)
- `FIREBASE_STORAGE_UPLOADS_PREFIX`: uploads folder prefix
- `FIREBASE_STORAGE_SANCTIONS_PREFIX`: sanction letters prefix

Storage + signing:
- `LOCAL_STORAGE_DIR`: local storage path when no bucket is set
- `LOAN_SIGNATURE_SECRET`: HMAC secret for sanction letter signing
- `STORAGE_SIGNED_URL_MINUTES`: signed URL TTL in minutes

### Frontend (`frontend/.env`)

- `VITE_API_BASE`: backend URL, e.g. `http://localhost:8000`
- `VITE_FIREBASE_*`: Firebase web config values

## API endpoints

- `GET /health`
- `POST /api/chat`
- `GET /api/session/active`
- `POST /api/upload`
- `GET /api/mock/crm/{phone}`
- `GET /api/mock/offers/{customer_id}`
- `GET /api/mock/credit/{customer_id}`

When `DISABLE_AUTH=false`, include `Authorization: Bearer <Firebase ID token>`.

## Docker

Backend:

```bash
docker build -t bfsi-backend ./backend
docker run --rm -p 8080:8080 --env-file backend/.env bfsi-backend
```

Frontend:

```bash
docker build -t bfsi-frontend --build-arg VITE_API_BASE=http://localhost:8000 ./frontend
docker run --rm -p 8081:8080 bfsi-frontend
```

## Demo data

Mock customer data lives in `backend/app/data/customers.json`. Update it to simulate
different KYC and credit profiles.

