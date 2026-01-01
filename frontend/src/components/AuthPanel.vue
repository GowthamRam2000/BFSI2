<template>
  <div class="card auth-card">
    <div class="auth-header">
      <span class="material-symbols-rounded auth-icon">lock</span>
      <h3>{{ mode === 'login' ? 'Welcome Back' : 'Create Account' }}</h3>
      <p class="auth-subtitle">
        {{ mode === 'login' ? 'Sign in to access your loan dashboard' : 'Join the EY Techathon 6.0 Demo' }}
      </p>
    </div>

    <div class="auth-toggle">
      <button
        class="chip"
        :class="{ active: mode === 'login' }"
        type="button"
        @click="mode = 'login'"
      >
        Sign in
      </button>
      <button
        class="chip"
        :class="{ active: mode === 'register' }"
        type="button"
        @click="mode = 'register'"
      >
        Register
      </button>
    </div>

    <div class="form-row">
      <label>Email Address</label>
      <div class="input-wrapper">
        <span class="material-symbols-rounded input-icon">mail</span>
        <input v-model="email" type="email" placeholder="you@example.com" />
      </div>
    </div>
    <div class="form-row">
      <label>Password</label>
      <div class="input-wrapper">
        <span class="material-symbols-rounded input-icon">key</span>
        <input v-model="password" type="password" placeholder="At least 6 characters" />
      </div>
    </div>

    <div v-if="mode === 'register'" class="terms-check">
      <label class="checkbox-label">
        <input type="checkbox" v-model="agreed" />
        <span class="checkbox-text">
          I agree to the
          <a href="#" @click.prevent="showTerms = true">Terms & Conditions</a>
          and
          <a href="#" @click.prevent="showPrivacy = true">Privacy Policy</a>.
          I acknowledge this is a <strong>Demo Application</strong>.
        </span>
      </label>
    </div>

    <div class="hero-actions column-actions">
      <button class="button primary full-width" :disabled="loading || (mode === 'register' && !agreed)" @click="submit">
        {{ loading ? 'Processing...' : actionLabel }}
      </button>

      <div class="divider">
        <span>OR</span>
      </div>

      <button class="button google-btn full-width" :disabled="loading" @click="handleGoogleLogin">
        <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google" class="google-icon" />
        Sign in with Google
      </button>
    </div>

    <div v-if="error" class="alert">{{ error }}</div>
  </div>

  <!-- Modals -->
  <div v-if="showTerms" class="modal-overlay" @click.self="showTerms = false">
    <div class="modal-card">
      <h3>Terms & Conditions</h3>
      <div class="modal-content">
        <p><strong>1. Demo Purpose Only</strong>: This application is a prototype for the EY Techathon 6.0 and is not a real financial service.</p>
        <p><strong>2. No Real Loans</strong>: No actual money is lent, processing is simulated.</p>
        <p><strong>3. Data Usage</strong>: Any data entered is for demonstration and will not be shared with third parties.</p>
      </div>
      <button class="button primary" @click="showTerms = false">Close</button>
    </div>
  </div>

  <div v-if="showPrivacy" class="modal-overlay" @click.self="showPrivacy = false">
    <div class="modal-card">
      <h3>Privacy Policy</h3>
      <div class="modal-content">
        <p><strong>1. Data Collection</strong>: We collect email for authentication purposes only.</p>
        <p><strong>2. Demo Environment</strong>: Do not enter real sensitive financial data (like real credit card numbers).</p>
        <p><strong>3. Deletion</strong>: You can request account deletion by contacting the developer.</p>
      </div>
      <button class="button primary" @click="showPrivacy = false">Close</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { login, register, loginWithGoogle } from "../services/firebase";

const mode = ref<"login" | "register">("login");
const email = ref("");
const password = ref("");
const agreed = ref(false);
const loading = ref(false);
const error = ref<string | null>(null);

const showTerms = ref(false);
const showPrivacy = ref(false);

const actionLabel = computed(() => (mode.value === "login" ? "Sign in" : "Create Account"));

async function submit() {
  error.value = null;
  if (!email.value || !password.value) {
    error.value = "Email and password are required.";
    return;
  }

  loading.value = true;
  try {
    if (mode.value === "login") {
      await login(email.value, password.value);
    } else {
      await register(email.value, password.value);
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Authentication failed";
  } finally {
    loading.value = false;
  }
}

async function handleGoogleLogin() {
  error.value = null;
  loading.value = true;
  try {
    await loginWithGoogle();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Google Sign-In failed";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.auth-card {
  max-width: 400px;
  margin: 0 auto;
  border-top: 4px solid var(--md-sys-color-secondary); /* Gold Top Border */
}

.auth-header {
  text-align: center;
  margin-bottom: 24px;
}

.auth-icon {
  font-size: 40px;
  color: var(--md-sys-color-primary);
  background: var(--md-sys-color-primary-container);
  padding: 12px;
  border-radius: 50%;
  margin-bottom: 12px;
}

.auth-subtitle {
  font-size: 0.9rem;
  color: var(--md-sys-color-outline);
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 12px;
  color: var(--md-sys-color-outline);
  font-size: 20px;
}

.input-wrapper input {
  padding-left: 40px; /* Space for icon */
  width: 100%;
}

.full-width {
  width: 100%;
  justify-content: center;
}

.divider {
  display: flex;
  align-items: center;
  text-align: center;
  margin: 16px 0;
  color: var(--md-sys-color-outline);
  font-size: 0.8rem;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid var(--md-sys-color-surface-variant);
}

.divider span {
  padding: 0 10px;
}

.google-btn {
  background-color: white;
  color: #757575;
  border: 1px solid var(--md-sys-color-outline);
  font-weight: 500;
}

.google-btn:hover {
  background-color: #f1f1f1;
}

.google-icon {
  width: 18px;
  height: 18px;
}

.terms-check {
  margin-bottom: 16px;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 0.85rem;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
}

.checkbox-text a {
  color: var(--md-sys-color-primary);
  text-decoration: underline;
  font-weight: 600;
}

.column-actions {
  flex-direction: column;
  gap: 0;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(4px);
}

.modal-card {
  background: white;
  padding: 24px;
  border-radius: var(--radius-lg);
  max-width: 500px;
  width: 90%;
  box-shadow: var(--md-sys-shadow-3);
  animation: slideUp 0.3s ease-out;
}

.modal-content {
  margin: 16px 0;
  font-size: 0.95rem;
  line-height: 1.6;
  max-height: 60vh;
  overflow-y: auto;
}
</style>
