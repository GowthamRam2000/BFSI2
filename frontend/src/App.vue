<template>
  <div class="app-shell">
    <header class="top-nav">
      <div class="brand">
        EY Techathon 6.0 <span class="brand-subtitle"> | NBFC Project</span>
      </div>
      <nav class="nav-links">
        <router-link class="nav-link" to="/">Home</router-link>
        <router-link class="nav-link" to="/loan">Loan Chat</router-link>
        <router-link class="nav-link" to="/upload">Upload Docs</router-link>
        <router-link class="nav-link" to="/about">About</router-link>
      </nav>
      <div class="nav-actions">
        <div v-if="authReady && user" class="user-pill">{{ user.email || user.uid }}</div>
        <button v-if="authReady && user" class="button outline-primary" type="button" @click="logout">
          Sign out
        </button>
        <router-link v-if="authReady && !user" class="button tonal" to="/loan">Sign in</router-link>
      </div>
    </header>

    <main class="main-content">
      <router-view />
    </main>

    <nav class="mobile-nav">
      <router-link to="/">Home</router-link>
      <router-link to="/loan">Chat</router-link>
      <router-link to="/upload">Upload</router-link>
      <router-link to="/about">About</router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { authReady, logout, user } from "./services/firebase";
</script>
