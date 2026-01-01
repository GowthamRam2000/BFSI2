<template>
  <div class="page">
    <section class="hero-card">
      <h2 class="section-title">Loan chat</h2>
      <p class="section-subtitle">Talk to the Master Agent and watch the worker agents complete each step.</p>
    </section>

    <section v-if="isAuthed" class="chat-layout">
      <div class="chat-panel">
        <div v-if="uploadNotice" class="alert">{{ uploadNotice }}</div>
        <div class="chat-messages" ref="messageList">
          <ChatMessage v-if="messages.length === 0" role="agent">
            Hi, I'm Krishna. I can help with personal loans and loan protection insurance. You can
            start by uploading your salary slip, bank statement, and address proof. Share your loan
            need and I will guide you through verification and approval.
          </ChatMessage>
          <ChatMessage
            v-for="message in messages"
            :key="message.id"
            :role="message.role"
          >
            {{ message.content }}
          </ChatMessage>
        </div>

        <div v-if="error" class="alert">{{ error }}</div>

        <div class="chip-group">
          <button class="chip" type="button" @click="usePrompt('I need a personal loan of 3 lakh for 24 months')">
            3 lakh for 24 months
          </button>
          <button class="chip" type="button" @click="usePrompt('My salary is 70000 and phone is 9876543210')">
            Share salary + phone
          </button>
          <button class="chip" type="button" @click="usePrompt('What documents are required?')">
            Documents required?
          </button>
          <button class="chip" type="button" @click="usePrompt('Please include loan protection insurance')">
            Add insurance
          </button>
        </div>

        <div class="chat-input">
          <input
            v-model="input"
            type="text"
            placeholder="Type your message..."
            @keydown.enter.prevent="sendMessage"
          />
          <button class="button primary" type="button" :disabled="isSending" @click="sendMessage">
            {{ isSending ? "Sending..." : "Send" }}
          </button>
          <button class="button outline-primary" type="button" :disabled="isSending" @click="startNewChat">
            Start new chat
          </button>
        </div>

        <div class="footer-note">
          Session ID: <strong>{{ sessionId || "Not started" }}</strong>
        </div>
      </div>

      <aside class="agent-panel">
        <div class="card">
          <h3>Agent flow</h3>
          <p class="section-subtitle">Watch each specialist take charge as you move forward.</p>
          <div class="agent-flow-grid">
            <div
              v-for="agent in agentFlow"
              :key="agent.key"
              class="agent-card"
              :class="[agent.statusClass, { active: agent.active }]"
            >
              <div class="agent-header">
                <span class="material-symbols-rounded agent-icon">{{ agent.icon }}</span>
                <div class="agent-name">{{ agent.name }}</div>
              </div>
              <div class="agent-role">{{ agent.role }}</div>
              <div class="agent-status">{{ agent.status }}</div>
              <div v-if="agent.active" class="agent-live">Active now</div>
              <p class="agent-desc">{{ agent.description }}</p>
            </div>
          </div>
        </div>

        <div class="card">
          <h3>Decision snapshot</h3>
          <div class="status-grid">
            <StatusPill label="Verification" :value="statusLabel(state?.verified, 'Verified', 'Pending')" />
            <StatusPill
              label="Underwriting"
              :value="underwritingStatus"
            />
            <StatusPill label="Documents" :value="documentsStatus" />
            <StatusPill label="Loan History" :value="loanHistoryStatus" />
            <StatusPill label="Rate Tier" :value="state?.loan_terms.rate_tier || 'TBD'" />
            <StatusPill label="EMI" :value="state?.loan_terms.emi ? `INR ${state?.loan_terms.emi}` : 'TBD'" />
            <StatusPill label="Salary Slip" :value="salarySlipStatus" />
            <StatusPill label="Insurance" :value="insuranceStatus" />
            <StatusPill
              label="Credit Score"
              :value="state?.credit_score ? `${state.credit_score}` : 'TBD'"
            />
            <StatusPill
              label="Pre-approved"
              :value="state?.pre_approved_limit ? `INR ${state.pre_approved_limit}` : 'TBD'"
            />
          </div>
          <div v-if="state?.sanction_url" class="hero-actions">
            <a class="button tonal" :href="state.sanction_url" target="_blank" rel="noopener">
              Download signed loan slip
            </a>
          </div>
          <div v-if="state?.sanction_ref" class="footer-note">
            Secure reference: <strong>{{ state.sanction_ref }}</strong>
          </div>
        </div>

        <div class="card">
          <h3>Agent activity</h3>
          <div class="agent-events">
            <AgentEventItem
              v-for="event in eventTimeline"
              :key="event.ts + event.action"
              :event="event"
              :display-name="event.displayAgent"
            />
            <p v-if="events.length === 0" class="footer-note">No events yet. Start the chat to see agents in action.</p>
          </div>
        </div>
      </aside>
    </section>

    <section v-else class="card">
      <h3>Sign in to start the chat</h3>
      <p class="section-subtitle">Authentication keeps your loan journey and uploads secure.</p>
      <AuthPanel />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import ChatMessage from "../components/ChatMessage.vue";
import StatusPill from "../components/StatusPill.vue";
import AgentEventItem from "../components/AgentEventItem.vue";
import AuthPanel from "../components/AuthPanel.vue";
import { fetchActiveSession, sendChat, type AgentEvent, type ChatState } from "../services/api";
import { authReady, user } from "../services/firebase";

const messages = ref<{ id: string; role: "user" | "agent"; content: string }[]>([]);
const input = ref("");
const isSending = ref(false);
const error = ref<string | null>(null);
const sessionId = ref<string | null>(null);
const state = ref<ChatState | null>(null);
const events = ref<AgentEvent[]>([]);
const messageList = ref<HTMLDivElement | null>(null);
const isAuthed = computed(() => authReady.value && !!user.value);
const newSessionRequested = ref(false);
const uploadNotice = ref<string | null>(null);
const SESSION_STORAGE_KEY = "bfsi.activeSession";

const agentDirectory = [
  {
    key: "Master",
    name: "Krishna",
    icon: "smart_toy",
    role: "Master Agent",
    description: "Orchestrates the journey and keeps the chat human.",
  },
  {
    key: "Sales",
    name: "Arjuna",
    icon: "support_agent",
    role: "Sales Agent",
    description: "Understands needs and positions the right tier.",
  },
  {
    key: "Verification",
    name: "Devi",
    icon: "verified",
    role: "Verification Agent",
    description: "Validates KYC and confirms profile details.",
  },
  {
    key: "Underwriting",
    name: "Shreya",
    icon: "analytics",
    role: "Underwriting Agent",
    description: "Checks eligibility, credit score, and EMI fit.",
  },
  {
    key: "Sanction",
    name: "Aditi",
    icon: "assignment_turned_in",
    role: "Sanction Agent",
    description: "Generates the signed loan slip and secure reference.",
  },
];

const agentNameMap = agentDirectory.reduce<Record<string, string>>((acc, agent) => {
  acc[agent.key] = agent.name;
  return acc;
}, {});

const eventTimeline = computed(() =>
  events.value.map((event) => ({
    ...event,
    displayAgent: agentNameMap[event.agent] || event.agent,
  })),
);

const agentFlow = computed(() => {
  const lastAgent = events.value.length ? events.value[events.value.length - 1].agent : "";
  const sessionActive = !!sessionId.value;

  return agentDirectory.map((agent) => {
    const status = agentStatus(agent.key, sessionActive);
    return {
      ...agent,
      status: status.label,
      statusClass: status.className,
      active: lastAgent === agent.key,
    };
  });
});

function agentStatus(key: string, sessionActive: boolean) {
  if (!sessionActive) {
    return { label: "Waiting", className: "idle" };
  }
  if (!state.value) {
    return { label: "Ready", className: "idle" };
  }
  const hasEvent = events.value.some((event) => event.agent === key);

  if (key === "Master") {
    if (state.value.sanction_url || state.value.rejected) {
      return { label: "Completed", className: "done" };
    }
    return { label: hasEvent ? "Orchestrating" : "Active", className: "working" };
  }
  if (key === "Sales") {
    if (state.value.offer_confirmed) {
      return { label: "Completed", className: "done" };
    }
    if (state.value.offer_presented) {
      return { label: "Awaiting confirmation", className: "working" };
    }
    if (state.value.info_collected) {
      return { label: "Intake complete", className: "done" };
    }
    return { label: hasEvent ? "Collecting details" : "Waiting", className: hasEvent ? "working" : "idle" };
  }
  if (key === "Verification") {
    if (state.value.documents_reviewed && state.value.loan_history_collected) {
      return { label: "Completed", className: "done" };
    }
    if (state.value.verified || hasEvent) {
      return { label: "In progress", className: "working" };
    }
    return { label: "Waiting", className: "idle" };
  }
  if (key === "Underwriting") {
    if (state.value.underwritten) {
      return { label: "Completed", className: "done" };
    }
    return { label: hasEvent ? "In progress" : "Waiting", className: hasEvent ? "working" : "idle" };
  }
  if (key === "Sanction") {
    if (state.value.sanction_url) {
      return { label: "Completed", className: "done" };
    }
    if (state.value.approved && state.value.offer_confirmed) {
      return { label: "In progress", className: "working" };
    }
    return { label: "Waiting", className: "idle" };
  }
  return { label: "Waiting", className: "idle" };
}

const underwritingStatus = computed(() => {
  if (!state.value) return "Pending";
  if (state.value.rejected) return "Rejected";
  if (state.value.approved) return "Approved";
  if (state.value.underwritten) return "Reviewed";
  return "Pending";
});

const salarySlipStatus = computed(() => {
  if (!state.value) return "Unknown";
  if (state.value.salary_slip_uploaded) return "Received";
  if (state.value.needs_salary_slip) return "Needed";
  return "Not required";
});

const documentsStatus = computed(() => {
  if (!state.value) return "Pending";
  const docs = state.value.documents || {};
  const total = Object.keys(docs).length || 3;
  const uploaded = Object.values(docs).filter((doc) => doc.uploaded).length;
  const reviewed = Object.values(docs).filter((doc) => doc.reviewed).length;
  if (reviewed === total && total > 0) return "Reviewed";
  if (uploaded > 0) return `${uploaded}/${total} uploaded`;
  return "Pending";
});

const loanHistoryStatus = computed(() => {
  if (!state.value) return "Pending";
  return state.value.loan_history_collected ? "Captured" : "Pending";
});

const insuranceStatus = computed(() => {
  if (state.value?.insurance_opted === true) return "Opted in";
  if (state.value?.insurance_opted === false) return "Declined";
  return "Not asked";
});

function statusLabel(flag: boolean | undefined, yes: string, no: string) {
  return flag ? yes : no;
}

function usePrompt(text: string) {
  input.value = text;
}

async function sendMessage() {
  if (!input.value.trim() || isSending.value) return;
  error.value = null;

  const userMessage = input.value.trim();
  const id = `m-${Date.now()}`;
  messages.value.push({ id, role: "user", content: userMessage });
  input.value = "";

  await nextTick();
  scrollToBottom();

  isSending.value = true;
  try {
    const response = await sendChat(sessionId.value, userMessage, newSessionRequested.value);
    sessionId.value = response.session_id;
    localStorage.setItem(SESSION_STORAGE_KEY, response.session_id);
    state.value = response.state;
    events.value = [...events.value, ...response.events];
    newSessionRequested.value = false;
    messages.value.push({
      id: `a-${Date.now()}`,
      role: "agent",
      content: response.reply,
    });
    await nextTick();
    scrollToBottom();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Something went wrong";
  } finally {
    isSending.value = false;
  }
}

function startNewChat() {
  messages.value = [];
  events.value = [];
  state.value = null;
  sessionId.value = null;
  error.value = null;
  uploadNotice.value = null;
  newSessionRequested.value = true;
  localStorage.removeItem(SESSION_STORAGE_KEY);
}

function scrollToBottom() {
  if (!messageList.value) return;
  messageList.value.scrollTop = messageList.value.scrollHeight;
}

function handleDocumentUploaded(event: Event) {
  const detail = (event as CustomEvent).detail as { docType?: string } | undefined;
  const docType = detail?.docType ? detail.docType.replace("_", " ") : "document";
  uploadNotice.value = `Uploaded ${docType}. Krishna will review it in the chat.`;
  refreshSession();
}

async function refreshSession() {
  if (!isAuthed.value) return;
  try {
    const response = await fetchActiveSession();
    if (response.session_id) {
      sessionId.value = response.session_id;
      localStorage.setItem(SESSION_STORAGE_KEY, response.session_id);
    } else {
      const stored = localStorage.getItem(SESSION_STORAGE_KEY);
      if (stored) {
        await refreshSessionById(stored);
        return;
      }
    }
    if (response.state) {
      state.value = response.state;
      const docs = response.state.documents || {};
      const uploaded = Object.values(docs).filter((doc) => doc.uploaded).length;
      if (uploaded > 0 && !response.state.documents_reviewed) {
        uploadNotice.value = `Documents received (${uploaded}). Krishna will review them shortly.`;
      }
    }
    if (response.messages && response.messages.length > 0) {
      messages.value = response.messages.map((msg, index) => ({
        id: `hist-${index}`,
        role: msg.role === "user" ? "user" : "agent",
        content: msg.content,
      }));
      await nextTick();
      scrollToBottom();
    }
    if (response.events) {
      events.value = response.events;
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to refresh session";
  }
}

async function refreshSessionById(sessionIdValue: string) {
  try {
    const response = await fetchActiveSession(sessionIdValue);
    if (response.session_id) {
      sessionId.value = response.session_id;
      localStorage.setItem(SESSION_STORAGE_KEY, response.session_id);
    }
    if (response.state) {
      state.value = response.state;
    }
    if (response.messages && response.messages.length > 0) {
      messages.value = response.messages.map((msg, index) => ({
        id: `hist-${index}`,
        role: msg.role === "user" ? "user" : "agent",
        content: msg.content,
      }));
      await nextTick();
      scrollToBottom();
    } else {
      localStorage.removeItem(SESSION_STORAGE_KEY);
    }
    if (response.events) {
      events.value = response.events;
    }
  } catch (err) {
    localStorage.removeItem(SESSION_STORAGE_KEY);
  }
}

onMounted(() => {
  window.addEventListener("document-uploaded", handleDocumentUploaded as EventListener);
});

onUnmounted(() => {
  window.removeEventListener("document-uploaded", handleDocumentUploaded as EventListener);
});

watch(isAuthed, (value) => {
  if (value) {
    refreshSession();
  }
}, { immediate: true });
</script>
