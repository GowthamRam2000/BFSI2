export type AgentEvent = {
  agent: string;
  action: string;
  detail: string;
  ts: string;
};

export type ChatState = {
  verified: boolean;
  underwritten: boolean;
  approved: boolean;
  rejected: boolean;
  needs_salary_slip: boolean;
  salary_slip_uploaded: boolean;
  loan_terms_ready: boolean;
  terms_presented: boolean;
  terms_confirmed: boolean;
  info_collected: boolean;
  documents: Record<string, { uploaded: boolean; reviewed: boolean }>;
  documents_reviewed: boolean;
  loan_history_collected: boolean;
  offer_presented: boolean;
  offer_confirmed: boolean;
  insurance_opted: boolean | null;
  pre_approved_limit: number | null;
  credit_score: number | null;
  sanction_url: string | null;
  sanction_signature: string | null;
  sanction_ref: string | null;
  loan_terms: {
    amount: number | null;
    tenure_months: number | null;
    interest_rate: number | null;
    emi: number | null;
    rate_tier: string | null;
  };
};

export type ChatResponse = {
  session_id: string;
  reply: string;
  state: ChatState;
  events: AgentEvent[];
};

export type SessionStateResponse = {
  session_id?: string | null;
  state?: ChatState | null;
  events?: AgentEvent[];
  messages?: { role: string; content: string }[];
};

import { getIdToken } from "./firebase";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function authHeaders() {
  const token = await getIdToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

export async function sendChat(
  sessionId: string | null,
  message: string,
  newSession = false,
): Promise<ChatResponse> {
  const auth = await authHeaders();
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...auth,
    },
    body: JSON.stringify({
      session_id: sessionId || undefined,
      message,
      new_session: newSession || undefined,
    }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Chat request failed");
  }

  return response.json();
}

export async function uploadDocument(
  docType: string,
  file: File,
): Promise<{ file_url: string }> {
  const form = new FormData();
  form.append("doc_type", docType);
  form.append("file", file);

  const auth = await authHeaders();
  const response = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    headers: auth,
    body: form,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Upload failed");
  }

  return response.json();
}

export async function fetchActiveSession(sessionId?: string | null): Promise<SessionStateResponse> {
  const auth = await authHeaders();
  const query = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : "";
  const response = await fetch(`${API_BASE}/api/session/active${query}`, {
    method: "GET",
    headers: {
      ...auth,
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Failed to fetch session");
  }

  return response.json();
}
