<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const statusText = ref('Connecting to GitHub...');
const errorMessage = ref('');

onMounted(async () => {
  const code = route.query.code;
  if (!code) {
    errorMessage.value = 'Authorization code not found. Please try logging in again.';
    return;
  }
  
  try {
    statusText.value = 'Exchanging token & logging in...';
    await authStore.loginWithGithub(code);
    statusText.value = 'Login successful! Redirecting...';
    router.push('/dashboard');
  } catch (err) {
    errorMessage.value = err.response?.data?.error || 'Failed to authenticate with GitHub.';
  }
});
</script>

<template>
  <div class="callback-container">
    <div class="card glass-card">
      <div v-if="!errorMessage" class="loading-state">
        <div class="loader"></div>
        <h2>GitHub Authentication</h2>
        <p>{{ statusText }}</p>
      </div>

      <div v-else class="error-state">
        <div class="icon">❌</div>
        <h2>Authentication Failed</h2>
        <p class="error-msg">{{ errorMessage }}</p>
        <router-link to="/" class="btn btn-primary">Go Back Home</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.callback-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: var(--background);
  color: var(--on-surface);
  padding: 1rem;
}

.glass-card {
  text-align: center;
  max-width: 450px;
  width: 100%;
  padding: 3rem 2rem;
  background: var(--surface-container-low);
  border: 1px solid var(--outline-variant);
}

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
}

.loader {
  width: 40px;
  height: 40px;
  border: 1px solid var(--outline-variant);
  border-top-color: var(--primary);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.icon {
  font-size: 3rem;
}

h2 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
}

p {
  color: var(--on-surface-variant);
  font-size: 0.95rem;
  margin: 0;
}

.error-msg {
  color: var(--error);
  font-family: var(--mono);
  font-size: 0.9rem;
  background: rgba(255, 180, 171, 0.1);
  border: 1px solid var(--error);
  padding: 12px;
  width: 100%;
  text-align: left;
  white-space: pre-wrap;
}

.btn {
  margin-top: 1rem;
  width: 100%;
}
</style>
