<template>
  <div class="page">
    <section class="hero-card">
      <h2 class="section-title">Upload documents</h2>
      <p class="section-subtitle">
        Upload supporting files to complete underwriting. Files are secured to your login session.
      </p>
    </section>

    <section v-if="isAuthed" class="upload-grid">
      <div v-for="doc in docConfigs" :key="doc.key" class="card upload-card">
        <h3>{{ doc.title }}</h3>
        <p class="section-subtitle">{{ doc.hint }}</p>
        <input type="file" :accept="doc.accept" @change="onFileChange(doc.key, $event)" />
        <button
          class="button primary"
          type="button"
          :disabled="uploads[doc.key].uploading"
          @click="uploadDoc(doc.key)"
        >
          {{ uploads[doc.key].uploading ? "Uploading..." : "Upload" }}
        </button>
        <div
          v-if="uploads[doc.key].status"
          class="alert"
          :class="{ 'alert-success': uploads[doc.key].isSuccess, 'alert-error': !uploads[doc.key].isSuccess }"
        >
          {{ uploads[doc.key].status }}
        </div>
      </div>
    </section>

    <section v-else class="card">
      <h3>Sign in to upload documents</h3>
      <p class="section-subtitle">Uploads are linked to your authenticated loan session.</p>
      <AuthPanel />
    </section>

    <p class="footer-note">
      Salary slips unlock higher limits and better rate tiers. Bank statements are optional, but
      help with faster approvals.
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, onMounted, watch } from "vue";
import AuthPanel from "../components/AuthPanel.vue";
import { uploadDocument, fetchActiveSession } from "../services/api";
import { authReady, user } from "../services/firebase";

const isAuthed = computed(() => authReady.value && !!user.value);

const docConfigs = [
  {
    key: "salary_slip",
    title: "Salary slip",
    hint: "Latest 1-2 months. PDF or image accepted.",
    accept: ".pdf,image/*",
  },
  {
    key: "bank_statement",
    title: "Bank statement",
    hint: "Optional. Last 3-6 months preferred.",
    accept: ".pdf,image/*",
  },
  {
    key: "address_proof",
    title: "Address proof",
    hint: "Aadhaar, utility bill, or rent agreement.",
    accept: ".pdf,image/*",
  },
];

const uploads = reactive<Record<string, { file: File | null; status: string | null; uploading: boolean; isSuccess: boolean }>>({
  salary_slip: { file: null, status: null, uploading: false, isSuccess: false },
  bank_statement: { file: null, status: null, uploading: false, isSuccess: false },
  address_proof: { file: null, status: null, uploading: false, isSuccess: false },
});

async function refreshState() {
  if (!isAuthed.value) return;
  try {
    const session = await fetchActiveSession();
    if (session.state && session.state.documents) {
      for (const [key, info] of Object.entries(session.state.documents)) {
        if (info.uploaded && uploads[key]) {
          uploads[key].isSuccess = true;
          uploads[key].status = "Uploaded previously ✅";
        }
      }
    }
  } catch (err) {
    console.error("Failed to sync uploads", err);
  }
}

watch(isAuthed, (newVal) => {
  if (newVal) refreshState();
});

onMounted(() => {
  if (isAuthed.value) refreshState();
});

function onFileChange(key: string, event: Event) {
  const target = event.target as HTMLInputElement;
  uploads[key].status = null;
  uploads[key].isSuccess = false;
  if (target.files && target.files.length > 0) {
    uploads[key].file = target.files[0];
  }
}

async function uploadDoc(key: string) {
  const entry = uploads[key];
  entry.status = null;
  entry.isSuccess = false;
  if (!entry.file) {
    entry.status = "Please select a file.";
    return;
  }

  entry.uploading = true;
  try {
    const response = await uploadDocument(key, entry.file);
    entry.status = "Uploaded successfully!";
    entry.isSuccess = true;
    window.dispatchEvent(
      new CustomEvent("document-uploaded", { detail: { docType: key, fileUrl: response.file_url } }),
    );
  } catch (err) {
    entry.status = err instanceof Error ? err.message : "Upload failed.";
    entry.isSuccess = false;
  } finally {
    entry.uploading = false;
  }
}
</script>
