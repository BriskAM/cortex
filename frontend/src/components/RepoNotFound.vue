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
      <router-link to="/" class="btn btn-primary">Go Back Home</router-link>
    </div>
  </div>
</template>

<style scoped>
.not-found-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 4rem);
  background: #0d0d15;
  color: #f3f4f6;
  font-family: 'Inter', system-ui, sans-serif;
}

.card {
  text-align: center;
  max-width: 450px;
  padding: 3rem 2rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  backdrop-filter: blur(12px);
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
  color: #9ca3af;
  font-size: 0.95rem;
  margin-bottom: 0.5rem;
}

.hint {
  font-size: 0.85rem;
  color: #6b7280;
  margin-bottom: 2rem;
}

.btn-primary {
  display: inline-block;
  background: linear-gradient(135deg, #8b5cf6, #d946ef);
  color: white;
  text-decoration: none;
  padding: 10px 24px;
  border-radius: 6px;
  font-weight: 600;
}
</style>
