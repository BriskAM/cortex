<script setup>
defineProps({
  owner: String,
  repo: String
});
</script>

<template>
  <div class="not-found-container">
    <div class="card glass-card">
      <div class="icon">⚠️</div>
      <h2>Repository Not Found</h2>
      <p>We couldn't find <strong>{{ owner }}/{{ repo }}</strong> on GitHub.</p>
      <p class="hint">Make sure the repository is public and the spelling is correct.</p>
      <router-link to="/" class="btn-home">Go Back Home</router-link>
    </div>
  </div>
</template>

<style scoped>
.not-found-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 4rem);
  background: var(--background);
  color: var(--on-surface);
}

.card {
  text-align: center;
  max-width: 450px;
  padding: 3rem 2rem;
  background: var(--surface-container-low);
  border: 1px solid var(--outline-variant);
}

.icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

h2 {
  font-size: 1.5rem;
  font-weight: 700;
  margin-top: 0;
}

p {
  color: var(--on-surface-variant);
  font-size: 0.95rem;
  margin-bottom: 0.5rem;
}

.hint {
  font-size: 0.85rem;
  color: var(--outline);
  margin-bottom: 2rem;
  font-family: var(--mono);
}

.btn-home {
  display: inline-block;
  background: var(--primary);
  color: var(--on-primary);
  text-decoration: none;
  padding: 10px 24px;
  font-weight: 600;
  border: 1px solid var(--primary);
  transition: all 0.15s ease;
}

.btn-home:hover {
  background: var(--primary-container);
  border-color: var(--primary-container);
  color: var(--on-surface);
}
</style>
