<template>
  <div class="page">
    <section class="hero">
      <div class="hero-card">
        <h1 class="hero-title">Intelligent Lending for the Modern Era</h1>
        <p class="hero-subtitle">
          Experience the future of banking with our Agentic AI.
          Instant verification, personalized rates, and seamless interaction.
          <strong>EY Techathon 6.0 Demo</strong>
        </p>
        <div class="hero-actions">
          <router-link class="button primary" to="/loan">Start Application</router-link>
          <router-link class="button outline" to="/about">Learn More</router-link>
        </div>
      </div>
      <div class="card">
        <h3>Four smart rate tiers</h3>
        <p>Rates are personalized using income, credit score, existing EMIs, and salary slips.</p>
        <div class="card-grid">
          <div class="card">
            <h3>9.0%</h3>
            <p>Top-tier eligibility</p>
          </div>
          <div class="card">
            <h3>11.0%</h3>
            <p>Strong credit + stable income</p>
          </div>
          <div class="card">
            <h3>13.0%</h3>
            <p>Balanced profile</p>
          </div>
          <div class="card">
            <h3>14.7%</h3>
            <p>Entry tier with slip validation</p>
          </div>
        </div>
      </div>
    </section>

    <section>
      <h2 class="section-title">Agentic workflow at a glance</h2>
      <p class="section-subtitle">Every step is orchestrated in one continuous conversation.</p>
      <div class="card-grid">
        <div class="card">
          <h3>Krishna - Master Agent</h3>
          <p>Guides the conversation, keeps the flow natural, and syncs every step.</p>
        </div>
        <div class="card">
          <h3>Arjuna - Sales Agent</h3>
          <p>Captures loan intent, recommends tiers, and positions insurance.</p>
        </div>
        <div class="card">
          <h3>Devi - Verification Agent</h3>
          <p>Validates KYC from CRM or flags missing profile details.</p>
        </div>
        <div class="card">
          <h3>Shreya - Underwriting Agent</h3>
          <p>Calculates eligibility, applies tiered pricing, and checks EMI affordability.</p>
        </div>
        <div class="card">
          <h3>Aditi - Sanction Agent</h3>
          <p>Generates the signed loan slip and creates a secure reference.</p>
        </div>
      </div>
    </section>

    <section>
      <h2 class="section-title">Built for sales conversions</h2>
      <p class="section-subtitle">Warm messaging, clear policy logic, and instant next steps.</p>
      <div class="chip-group">
        <span class="chip">Insurance add-on prompts</span>
        <span class="chip">Dynamic eligibility checks</span>
        <span class="chip">Secure letter generation</span>
        <span class="chip">Audit-ready event trail</span>
      </div>
    </section>

    <section v-if="authReady && !user" class="card">
      <h2 class="section-title">Sign in to continue</h2>
      <p class="section-subtitle">Use your email to access the chat and document uploads.</p>
      <AuthPanel />
    </section>
  </div>
</template>

<script setup lang="ts">
import AuthPanel from "../components/AuthPanel.vue";
import { authReady, user } from "../services/firebase";
</script>
