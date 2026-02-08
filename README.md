<div align="center">

# 🏦 BFSI Agentic Loan Assistant

**AI-powered, multi-agent loan origination platform for NBFCs**

Built for [EY Techathon 6.0](https://www.ey.com/) &bull; Created by **Gowtham Ram**

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3.4-4FC08D?logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0-1C3C3C?logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Meet the AI Agents](#-meet-the-ai-agents)
- [Loan Processing Workflow](#-loan-processing-workflow)
- [Tech Stack](#-tech-stack)
- [Repository Structure](#-repository-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Configuration Reference](#-configuration-reference)
- [API Reference](#-api-reference)
- [Underwriting & Pricing Engine](#-underwriting--pricing-engine)
- [Docker Deployment](#-docker-deployment)
- [Demo Data](#-demo-data)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

The **BFSI Agentic Loan Assistant** is a full-stack NBFC (Non-Banking Financial Company) loan origination demo that showcases how **five specialised AI agents** collaborate through a LangGraph state machine to deliver an end-to-end personal loan experience — from the first greeting to a signed, HMAC-secured sanction letter PDF.

The system combines **rule-based decision logic** (eligibility scoring, EMI calculations, rate-tier pricing) with **optional LLM-powered natural language understanding** (OpenAI) and falls back gracefully to heuristic parsing when no API key is configured.

> **TL;DR** — Chat with the assistant, share a few details, upload documents, and walk away with a digitally signed loan sanction letter. All in one conversation.

---

## ✨ Key Features

| Category | Feature |
|----------|---------|
| **Multi-Agent Orchestration** | Five named agents (Master → Sales → Verification → Underwriting → Sanction) coordinated through a LangGraph state machine |
| **Natural Language Chat** | Conversational loan intake powered by OpenAI with automatic fallback to heuristic extraction |
| **KYC & CRM Lookup** | Automatic customer data enrichment from a mock CRM by phone number |
| **Document Upload** | Upload salary slip, bank statement, and address proof — reviewed by the Verification agent |
| **Credit Bureau Integration** | Mock credit score and existing loan lookup per customer |
| **Eligibility Engine** | Rule-based underwriting with credit score, income, EMI-to-income ratio, and pre-approved limit checks |
| **Dynamic Rate Tiers** | Four interest rate tiers (9 %, 11 %, 13 %, 14.7 %) assigned based on a composite risk band |
| **EMI Calculator** | Standard reducing-balance EMI formula applied in real time |
| **Insurance Opt-in** | Loan protection insurance offered during the sales flow |
| **Sanction Letter PDF** | Auto-generated PDF with HMAC-SHA256 digital signature and a secure reference ID |
| **Event Timeline UI** | Real-time visualisation of every agent action and decision in the frontend |
| **Session Persistence** | Conversations stored in Firestore (production) or in-memory (local dev) |
| **Firebase Auth** | Google Firebase authentication with a bypass toggle for local development |
| **Docker Ready** | Optimised Dockerfiles for both backend and frontend with multi-stage builds |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Vue 3 + Vite SPA                         │
│   HomeView ─ ChatView ─ UploadView ─ AboutView ─ AuthPanel      │
│         │              │                │                        │
│         └──────────────┴────────────────┘                        │
│                        HTTP / REST                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python)                      │
│                                                                  │
│  ┌──────────────────── LangGraph ────────────────────────────┐  │
│  │                                                            │  │
│  │   ┌─────────┐     ┌───────┐     ┌──────────────┐         │  │
│  │   │ Master  │────▶│ Sales │────▶│ Verification │         │  │
│  │   │(Krishna)│     │(Arjuna│     │   (Devi)     │         │  │
│  │   └────┬────┘     └───────┘     └──────┬───────┘         │  │
│  │        │                                │                  │  │
│  │        │          ┌──────────────┐      │                  │  │
│  │        └─────────▶│ Underwriting │◀─────┘                  │  │
│  │                   │   (Shreya)   │                         │  │
│  │                   └──────┬───────┘                         │  │
│  │                          │                                 │  │
│  │                   ┌──────▼───────┐                         │  │
│  │                   │   Sanction   │                         │  │
│  │                   │   (Aditi)    │                         │  │
│  │                   └──────────────┘                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Services: CRM · Credit Bureau · Offers · Underwriting ·        │
│            Pricing · Sanction PDF · Storage · State Store        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
         ┌──────────┐   ┌───────────┐   ┌───────────┐
         │ Firebase  │   │  Cloud    │   │  OpenAI   │
         │Auth + DB  │   │ Storage   │   │  LLM API  │
         └──────────┘   └───────────┘   └───────────┘
```

---

## 🤖 Meet the AI Agents

Each agent has a distinct persona, tone, and responsibility within the loan journey:

| Agent | Persona | Role | Tone |
|-------|---------|------|------|
| 🎭 **Krishna** | Concierge / Master | Orchestrates the entire journey, routes to the right agent, handles FAQs and greetings | Warm, helpful, professional — like a high-end hotel concierge |
| 💼 **Arjuna** | Sales Expert | Captures loan amount, tenure, salary, and presents the final offer with insurance options | Friendly, knowledgeable, conversational |
| 🔍 **Devi** | Verification Specialist | Validates KYC, reviews uploaded documents, and collects outstanding loan history | Efficient, polite, reassuring |
| 📊 **Shreya** | Senior Underwriter | Makes the approval/rejection decision based on credit, income, and policy rules | Transparent, clear, empathetic |
| 🎉 **Aditi** | Sanctioning Officer | Generates the signed PDF sanction letter and celebrates the approval | Celebratory, enthusiastic |

---

## 🔄 Loan Processing Workflow

```
Customer opens chat
        │
        ▼
   ┌─────────┐    Greeting / FAQ
   │  Master  │◄── ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
   │ (Krishna)│                         │
   └────┬─────┘                         │
        │                               │
        ▼                               │
   ┌─────────┐    Collects: name,       │
   │  Sales   │   phone, amount,        │
   │ (Arjuna) │   tenure, salary        │
   └────┬─────┘                         │
        │                               │
        ▼                               │
  ┌───────────────┐  CRM lookup,        │
  │ Verification  │  document review,   │
  │    (Devi)     │  loan history       │
  └──────┬────────┘                     │
         │                              │
         ▼                              │
  ┌──────────────┐  Credit score,       │
  │ Underwriting │  eligibility,        │
  │   (Shreya)   │  rate tier, EMI      │
  └──────┬───────┘                      │
         │                              │
    ┌────┴────┐                         │
    ▼         ▼                         │
Approved   Rejected ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
    │
    ▼
┌─────────┐   Offer presented
│  Sales  │   by Arjuna
│(Arjuna) │   Customer confirms
└────┬────┘
     │
     ▼
┌──────────┐   PDF generated,
│ Sanction │   HMAC signed,
│  (Aditi) │   download link shared
└──────────┘
```

**Step-by-step:**

1. **Greeting** — Krishna welcomes the user and invites them to share their loan needs.
2. **Data Collection** — Arjuna asks for name, phone, loan amount, tenure, and salary.
3. **KYC Verification** — Devi looks up the phone in the CRM, enriches customer data, and requests document uploads.
4. **Document Review** — Devi verifies salary slip, bank statement, and address proof.
5. **Loan History** — Devi asks about outstanding loans to factor into the EMI ratio.
6. **Underwriting** — Shreya evaluates eligibility using credit score, income, EMI ratio, and pre-approved limit.
7. **Offer Presentation** — Arjuna presents the approved loan terms (amount, tenure, rate, EMI, insurance).
8. **Confirmation** — The customer accepts or requests changes.
9. **Sanction** — Aditi generates a signed PDF sanction letter with an HMAC-SHA256 signature and a secure reference ID.

---

## 🛠 Tech Stack

### Backend

| Technology | Version | Purpose |
|-----------|---------|---------|
| [Python](https://www.python.org/) | 3.13 | Runtime |
| [FastAPI](https://fastapi.tiangolo.com/) | 0.128.0 | REST API framework |
| [LangGraph](https://langchain-ai.github.io/langgraph/) | 1.0.5 | Multi-agent state machine orchestration |
| [LangChain Core](https://python.langchain.com/) | 1.2.5 | LLM abstraction layer |
| [OpenAI SDK](https://platform.openai.com/) | 2.14.0 | LLM calls (optional — falls back to heuristics) |
| [Firebase Admin](https://firebase.google.com/) | 7.1.0 | Auth, Firestore, Cloud Storage |
| [Google Cloud Storage](https://cloud.google.com/storage) | 3.7.0 | Document & sanction letter storage |
| [fpdf2](https://py-pdf.github.io/fpdf2/) | 2.8.5 | PDF generation for sanction letters |
| [Pydantic](https://docs.pydantic.dev/) | 2.12.5 | Request/response data validation |
| [Gunicorn](https://gunicorn.org/) + [Uvicorn](https://www.uvicorn.org/) | 23.0.0 / 0.40.0 | Production ASGI server |
| [httpx](https://www.python-httpx.org/) | 0.28.1 | Async HTTP client |

### Frontend

| Technology | Version | Purpose |
|-----------|---------|---------|
| [Vue 3](https://vuejs.org/) | 3.4.38 | Reactive UI framework |
| [Vite](https://vitejs.dev/) | 5.4.0 | Dev server & build tool |
| [TypeScript](https://www.typescriptlang.org/) | 5.5.4 | Type-safe JavaScript |
| [Vue Router](https://router.vuejs.org/) | 4.4.4 | Client-side routing |
| [Firebase SDK](https://firebase.google.com/) | 10.14.1 | Authentication |
| [Nginx](https://nginx.org/) | Alpine | Production static file server & reverse proxy |

---

## 📁 Repository Structure

```
BFSI2/
├── README.md                              # This file
├── main.py                                # PyCharm sample entry point
├── .gitignore                             # Excludes .env, node_modules, uploads, sanctions
│
├── backend/                               # ── FastAPI Service ──────────────────────
│   ├── Dockerfile                         # Python 3.13-slim, gunicorn + uvicorn
│   ├── requirements.txt                   # Python dependencies
│   ├── .dockerignore
│   │
│   ├── app/
│   │   ├── main.py                        # FastAPI app, routes, CORS, auth middleware
│   │   ├── config.py                      # Settings from environment variables
│   │   ├── models.py                      # Pydantic request/response schemas
│   │   │
│   │   ├── agents/                        # ── Multi-Agent LangGraph Core ───────
│   │   │   ├── graph.py                   # State machine: 5 nodes, conditional routing
│   │   │   ├── llm.py                     # OpenAI client wrapper with fallback
│   │   │   ├── prompts.py                 # System prompts for each agent persona
│   │   │   └── tools.py                   # Heuristic NLP tools (parsing, classification)
│   │   │
│   │   ├── services/                      # ── Business Logic ───────────────────
│   │   │   ├── firebase.py                # Firebase Auth & Firestore integration
│   │   │   ├── storage.py                 # Cloud Storage / local file abstraction
│   │   │   ├── state_store.py             # Session state persistence
│   │   │   ├── session_registry.py        # Active session tracking per user
│   │   │   ├── underwriting.py            # Eligibility checks & EMI calculation
│   │   │   ├── pricing.py                 # Rate tier determination engine
│   │   │   ├── sanction.py                # PDF generation + HMAC signing
│   │   │   ├── credit_bureau.py           # Mock credit score lookups
│   │   │   ├── crm.py                     # Mock KYC / customer data by phone
│   │   │   ├── offers.py                  # Mock pre-approved offer generation
│   │   │   └── data_loader.py             # JSON data utilities
│   │   │
│   │   ├── data/
│   │   │   └── customers.json             # Mock customer database (10 profiles)
│   │   │
│   │   └── static/                        # Local file storage (when GCS is disabled)
│   │       ├── uploads/                   # Customer uploaded documents
│   │       └── sanctions/                 # Generated sanction letter PDFs
│   │
│   └── scripts/
│       └── env_check.py                   # Environment validation script
│
└── frontend/                              # ── Vue 3 + Vite SPA ─────────────────
    ├── Dockerfile                         # Multi-stage: Node 20 build → Nginx Alpine
    ├── nginx.conf                         # SPA routing & reverse proxy config
    ├── package.json                       # Dependencies & scripts
    ├── tsconfig.json                      # TypeScript configuration
    ├── vite.config.ts                     # Vite config (dev port 5173)
    ├── index.html                         # HTML entry point
    │
    └── src/
        ├── App.vue                        # Root component with router-view
        ├── main.ts                        # Vue bootstrap
        ├── router.ts                      # Route definitions
        ├── styles.css                     # Global stylesheet
        │
        ├── components/                    # ── Reusable Components ───────────
        │   ├── ChatMessage.vue            # Single message bubble
        │   ├── AgentEventItem.vue         # Timeline item for agent actions
        │   ├── StatusPill.vue             # State indicator badges
        │   └── AuthPanel.vue              # Firebase login/signup UI
        │
        ├── views/                         # ── Page-Level Views ─────────────
        │   ├── HomeView.vue               # Landing page
        │   ├── ChatView.vue               # Main loan chat interface
        │   ├── UploadView.vue             # Document upload flow
        │   └── AboutView.vue              # Project information
        │
        └── services/                      # ── Client Services ──────────────
            ├── api.ts                     # HTTP client for backend API
            └── firebase.ts                # Firebase Auth SDK wrapper
```

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.11+ | 3.13 (matches Dockerfile) |
| Node.js | 18+ | 20+ (matches Dockerfile) |
| npm | 8+ | 10+ |
| Docker | 20+ | Latest (optional, for containerised deployment) |
| Firebase Project | — | Required only if `DISABLE_AUTH=false` |

### Backend Setup

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your environment file
cp .env.example .env
# Edit .env with your values (see Configuration Reference below)

# 5. (Optional) Validate your environment
python scripts/env_check.py

# 6. Start the development server
uvicorn app.main:app --reload --port 8000
```

The API is now running at **http://localhost:8000**. Verify with:

```bash
curl http://localhost:8000/health
# → {"status": "ok"}
```

### Frontend Setup

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Create your environment file
cp .env.example .env
# Set VITE_API_BASE=http://localhost:8000

# 4. Start the dev server
npm run dev
```

Open **http://localhost:5173** in your browser to access the application.

> **💡 Quick Start Tip:** Set `DISABLE_AUTH=true` in the backend `.env` to skip Firebase setup entirely and use in-memory storage. No cloud credentials required!

---

## ⚙ Configuration Reference

### Backend Environment Variables (`backend/.env`)

#### Core Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ENV` | Runtime environment label | `local` | `local`, `staging`, `production` |
| `BASE_URL` | Base URL for local storage links | `http://localhost:8000` | `https://api.example.com` |
| `FRONTEND_ORIGIN` | Allowed CORS origin | `http://localhost:5173` | `https://app.example.com` |
| `DISABLE_AUTH` | Bypass Firebase auth & use in-memory storage | `true` | `true` or `false` |

#### LLM Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `OPENAI_API_KEY` | OpenAI API key (optional — heuristic fallback if absent) | _(empty)_ | `sk-...` |
| `OPENAI_MODEL` | Model name for chat completions | `gpt-5-mini` | `gpt-4o`, `gpt-4o-mini` |

#### Firebase / GCP

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `FIREBASE_PROJECT_ID` | Firebase project identifier | _(empty)_ | `my-nbfc-demo` |
| `GCP_PROJECT_ID` | GCP project override | _(empty)_ | `my-gcp-project` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | _(empty)_ | `/secrets/sa.json` |
| `FIREBASE_STORAGE_BUCKET` | Cloud Storage bucket (no `gs://`) | _(empty)_ | `my-nbfc-demo.appspot.com` |
| `FIREBASE_STORAGE_UPLOADS_PREFIX` | Uploads folder prefix in the bucket | `uploads` | `documents/uploads` |
| `FIREBASE_STORAGE_SANCTIONS_PREFIX` | Sanctions folder prefix in the bucket | `letters` | `documents/sanctions` |

#### Storage & Security

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `LOCAL_STORAGE_DIR` | Local file storage path (used when no bucket is set) | `backend/app/static` | `/data/storage` |
| `LOAN_SIGNATURE_SECRET` | HMAC-SHA256 secret for signing sanction letters | _(empty)_ | `my-super-secret-key` |
| `STORAGE_SIGNED_URL_MINUTES` | Signed URL expiry (minutes) | `60` | `30` |

### Frontend Environment Variables (`frontend/.env`)

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE` | Backend API URL | `http://localhost:8000` |
| `VITE_FIREBASE_API_KEY` | Firebase Web API key | `AIzaSy...` |
| `VITE_FIREBASE_AUTH_DOMAIN` | Firebase Auth domain | `my-app.firebaseapp.com` |
| `VITE_FIREBASE_PROJECT_ID` | Firebase project ID | `my-nbfc-demo` |
| `VITE_FIREBASE_STORAGE_BUCKET` | Firebase Storage bucket | `my-app.appspot.com` |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | Firebase Messaging sender ID | `123456789` |
| `VITE_FIREBASE_APP_ID` | Firebase App ID | `1:123:web:abc` |

---

## 📡 API Reference

All endpoints return JSON. When `DISABLE_AUTH=false`, include the header:

```
Authorization: Bearer <Firebase ID Token>
```

### Health Check

```
GET /health
```

**Response:** `{"status": "ok"}`

---

### Chat

```
POST /api/chat
```

Send a message to the loan assistant.

**Request Body:**

```json
{
  "message": "I need a personal loan of 3 lakhs",
  "session_id": "optional-uuid",
  "new_session": false
}
```

**Response:**

```json
{
  "session_id": "uuid",
  "reply": "Hi! I'd be happy to help. Could you share your name and phone number?",
  "state": {
    "verified": false,
    "approved": false,
    "documents": { ... },
    "loan_terms": { ... }
  },
  "events": [
    { "agent": "Sales", "action": "collect_info", "detail": "Requested missing details", "ts": "..." }
  ]
}
```

---

### Active Session

```
GET /api/session/active?session_id=optional-uuid
```

Retrieve the current session state, events, and message history.

---

### Document Upload

```
POST /api/upload
Content-Type: multipart/form-data
```

**Form Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `file` | File | The document file |
| `doc_type` | String | One of: `salary_slip`, `bank_statement`, `address_proof` |
| `session_id` | String | _(optional)_ Active session ID |

---

### Mock Data Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/mock/crm/{phone}` | Fetch KYC data by phone number |
| `GET /api/mock/offers/{customer_id}` | Fetch pre-approved offer details |
| `GET /api/mock/credit/{customer_id}` | Fetch credit score and loan history |

---

## 📊 Underwriting & Pricing Engine

### Eligibility Rules

The underwriting engine applies the following checks in order:

| # | Rule | Threshold | Outcome |
|---|------|-----------|---------|
| 1 | Credit score minimum | < 650 | ❌ Rejected |
| 2 | Minimum monthly salary | < ₹25,000 | ❌ Rejected |
| 3 | Amount vs. pre-approved limit | > 2× limit | ❌ Rejected |
| 4 | Amount exceeds limit without salary slip | > limit & no slip | ⏸ Needs salary slip upload |
| 5 | Total EMI-to-income ratio | > 50% of salary | ❌ Rejected |
| 6 | All checks pass within limit | ≤ limit | ✅ Instant approval |
| 7 | All checks pass with salary slip | > limit & slip uploaded | ✅ Approved with slip |

### Interest Rate Tiers

Rates are determined by a **composite band** — the worst of three risk dimensions:

| Tier | Annual Rate | Credit Score | Monthly Income | Existing EMI Ratio |
|------|------------|--------------|----------------|-------------------|
| **Tier A** | 9.0 % | ≥ 800 | ≥ ₹1,00,000 | ≤ 20 % |
| **Tier B** | 11.0 % | ≥ 750 | ≥ ₹70,000 | ≤ 30 % |
| **Tier C** | 13.0 % | ≥ 700 | ≥ ₹45,000 | ≤ 40 % |
| **Tier D** | 14.7 % | ≥ 650 | < ₹45,000 | > 40 % |

> **Note:** If the salary slip is not uploaded, the rate tier is capped at **Tier C** (13 %) minimum, regardless of other factors.

### EMI Formula

Standard reducing-balance EMI calculation:

```
EMI = P × r × (1 + r)^n / ((1 + r)^n − 1)

Where:
  P = Principal (loan amount)
  r = Monthly interest rate (annual rate / 1200)
  n = Tenure in months
```

---

## 🐳 Docker Deployment

### Build & Run the Backend

```bash
docker build -t bfsi-backend ./backend

docker run --rm -p 8080:8080 \
  --env-file backend/.env \
  bfsi-backend
```

The backend runs on port **8080** with Gunicorn + Uvicorn workers.

### Build & Run the Frontend

```bash
docker build -t bfsi-frontend \
  --build-arg VITE_API_BASE=http://localhost:8080 \
  ./frontend

docker run --rm -p 8081:8080 bfsi-frontend
```

The frontend is served via Nginx on port **8081**.

### Quick Docker Compose (example)

```yaml
# docker-compose.yml
version: "3.9"
services:
  backend:
    build: ./backend
    ports:
      - "8080:8080"
    env_file:
      - ./backend/.env

  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_BASE: http://localhost:8080
    ports:
      - "8081:8080"
    depends_on:
      - backend
```

```bash
docker compose up --build
```

---

## 🧪 Demo Data

The mock customer database lives in `backend/app/data/customers.json` and contains **10 test profiles** spanning different cities, income brackets, credit scores, and loan histories:

| Customer | City | Monthly Salary | Credit Score | Pre-Approved Limit | Existing Loans |
|----------|------|---------------|-------------|--------------------|--------------------|
| Ananya Rao | Bengaluru | ₹72,000 | 781 | ₹3,50,000 | Auto (₹7,800 EMI) |
| Rahul Mehta | Mumbai | ₹98,000 | 812 | ₹5,00,000 | Home (₹23,800 EMI) |
| Sneha Iyer | Chennai | ₹64,000 | 734 | ₹2,50,000 | None |
| Amit Singh | Delhi | ₹56,000 | 698 | ₹1,80,000 | Personal (₹5,100 EMI) |
| Priya Nair | Kochi | ₹88,000 | 765 | ₹4,20,000 | Education (₹4,300 EMI) |
| Karan Patel | Ahmedabad | ₹61,000 | 748 | ₹2,60,000 | None |
| Meera Kulkarni | Pune | ₹1,05,000 | 820 | ₹6,00,000 | Auto (₹6,200 EMI) |
| Vikram Das | Kolkata | ₹54,000 | 712 | ₹2,00,000 | None |
| Ritu Sharma | Jaipur | ₹48,000 | 705 | ₹1,50,000 | Personal (₹2,900 EMI) |
| Devika Menon | Hyderabad | ₹93,000 | 792 | ₹4,80,000 | Home (₹17,900 EMI) |

> **Tip:** Edit `customers.json` to simulate different scenarios — low credit scores for rejections, high salaries for Tier A rates, multiple existing loans for EMI ratio failures, etc.

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/my-feature`
3. **Commit** your changes: `git commit -m "Add my feature"`
4. **Push** to the branch: `git push origin feature/my-feature`
5. **Open** a Pull Request

Please ensure your code follows the existing project conventions.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**Built with ❤️ by [Gowtham Ram](https://github.com/GowthamRam2000) for EY Techathon 6.0**

</div>
