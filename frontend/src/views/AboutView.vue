<template>
  <div class="page">
    <section class="hero-card">
      <h2 class="section-title">NBFC Pulse</h2>
      <p class="section-subtitle">
        A demonstration of Agentic AI for EY Techathon 6.0. <br>
        Built by <strong>Gowtham Ram</strong>.
      </p>
      <div class="tech-stack">
        <span class="chip">LangGraph</span>
        <span class="chip">GPT-5 Mini</span>
        <span class="chip">Vue 3</span>
        <span class="chip">Material 3 Expressive</span>
      </div>
    </section>

    <section class="card">
      <h3>Why this was made</h3>
      <p>
        Traditional banking chatbots are often rigid and frustrating. This project demonstrates how an <strong>Orchestrator-Worker</strong> agentic architecture can provide a fluid, human-like experience.
      </p>
      <p>
        The <strong>Master Agent (Krishna)</strong> acts as a concierge, understanding intent and routing tasks to specialized agents only when needed. This ensures context is maintained while domain-specific rules are applied rigorously by experts.
      </p>
    </section>

    <section class="card-grid">
      <div class="card agent-card-about">
        <span class="material-symbols-rounded icon">smart_toy</span>
        <h3>Krishna</h3>
        <p class="role">Master Agent</p>
        <p>Owns the dialogue, keeps context, and orchestrates the journey.</p>
      </div>
      <div class="card agent-card-about">
        <span class="material-symbols-rounded icon">support_agent</span>
        <h3>Arjuna</h3>
        <p class="role">Sales Agent</p>
        <p>Captures loan intent, recommends tiers, and positions insurance.</p>
      </div>
      <div class="card agent-card-about">
        <span class="material-symbols-rounded icon">verified</span>
        <h3>Devi</h3>
        <p class="role">Verification Agent</p>
        <p>Confirms KYC data with CRM and flags missing profile details.</p>
      </div>
      <div class="card agent-card-about">
        <span class="material-symbols-rounded icon">analytics</span>
        <h3>Shreya</h3>
        <p class="role">Underwriting Agent</p>
        <p>Applies eligibility rules, pricing tiers, and EMI affordability checks.</p>
      </div>
      <div class="card agent-card-about">
        <span class="material-symbols-rounded icon">assignment_turned_in</span>
        <h3>Aditi</h3>
        <p class="role">Sanction Agent</p>
        <p>Generates the signed loan slip and secure reference once approved.</p>
      </div>
    </section>

    <section class="card centered-footer">
      <p>
         <strong>refer my Portfolio below</strong> <br>
        <a href="https://new-project-6d8bf.firebaseapp.com" target="_blank">Live Demo Link</a>
      </p>
    </section>
  </div>
</template>

<style scoped>
.tech-stack {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: 16px;
}

.agent-card-about {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.agent-card-about .icon {
  font-size: 48px;
  color: var(--md-sys-color-primary);
  margin-bottom: 16px;
}

.role {
  text-transform: uppercase;
  font-size: 0.8rem;
  letter-spacing: 1px;
  color: var(--md-sys-color-secondary);
  margin-bottom: 8px;
  font-weight: 600;
}

.centered-footer {
  text-align: center;
}
</style>
