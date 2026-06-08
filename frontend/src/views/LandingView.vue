<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import apiClient from '../api/axios';

const router = useRouter();
const authStore = useAuthStore();

const repoInput = ref('');
const email = ref('');
const password = ref('');
const isLoginMode = ref(true);
const authError = ref('');

const handleExplore = () => {
  if (!repoInput.value) return;
  let path = repoInput.value.replace(/https:\/\/github\.com\//, '').trim();
  const parts = path.split('/');
  if (parts.length >= 2) {
    const owner = parts[0];
    const repo = parts[1];
    router.push(`/${owner}/${repo}`);
  } else {
    alert('Please enter a valid format like "owner/repo"');
  }
};

const handleAuth = async () => {
  authError.value = '';
  try {
    if (isLoginMode.value) {
      await authStore.login(email.value, password.value);
      router.push('/dashboard');
    } else {
      await authStore.register(email.value, password.value);
      isLoginMode.value = true;
      alert('Registration successful! Please login.');
    }
  } catch (err) {
    authError.value = err.response?.data?.error || 'Authentication failed';
  }
};

const handleGithubLogin = async () => {
  authError.value = '';
  try {
    const response = await apiClient.get('/auth/github/login');
    if (response.data.url) {
      window.location.href = response.data.url;
    }
  } catch (err) {
    authError.value = err.response?.data?.error || 'Failed to initialize GitHub login.';
  }
};
</script>

<template>
  <div class="landing-container">
    <div class="glass-card hero">
      <h1>Cortex</h1>
      <p class="subtitle">Chat with your codebase and its engineering history.</p>
      
      <div class="explore-section">
        <div class="input-group">
          <span class="prefix">cortex.dev/</span>
          <input 
            v-model="repoInput" 
            placeholder="owner/repo" 
            @keyup.enter="handleExplore"
            class="glow-input"
          />
          <button @click="handleExplore" class="btn-explore">Explore</button>
        </div>
      </div>
    </div>

    <div class="glass-card auth-card">
      <h2>{{ isLoginMode ? 'Sign In' : 'Sign Up' }}</h2>
      <form @submit.prevent="handleAuth" class="auth-form">
        <div class="form-group">
          <label>Email</label>
          <input v-model="email" type="email" required placeholder="name@domain.com" />
        </div>
        <div class="form-group">
          <label>Password</label>
          <input v-model="password" type="password" required placeholder="••••••••" />
        </div>
        <p v-if="authError" class="error-msg">{{ authError }}</p>
        <button type="submit" class="btn-auth">
          {{ isLoginMode ? 'Sign In' : 'Sign Up' }}
        </button>
      </form>

      <div class="oauth-divider">
        <span>or</span>
      </div>

      <button @click="handleGithubLogin" class="btn-github-auth">
        <svg class="github-icon" viewBox="0 0 16 16" width="16" height="16">
          <path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
        </svg>
        Sign In with GitHub
      </button>

      <div class="toggle-mode">
        <a href="#" @click.prevent="isLoginMode = !isLoginMode">
          {{ isLoginMode ? "Need an account? Sign Up" : "Have an account? Sign In" }}
        </a>
      </div>
    </div>
  </div>
</template>

<style scoped>
.landing-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 2rem;
  background: var(--background);
  color: var(--on-surface);
  padding: 1rem;
}

.glass-card {
  background: var(--surface-container-low);
  border: 1px solid var(--outline-variant);
  padding: 2.5rem;
  width: 100%;
  max-width: 500px;
  transition: border-color 0.15s ease;
}

.glass-card:hover {
  border-color: var(--outline);
}

.hero {
  text-align: center;
}

.hero h1 {
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0;
  color: var(--primary);
}

.subtitle {
  color: var(--on-surface-variant);
  font-size: 1rem;
  margin-top: 0.5rem;
  margin-bottom: 2rem;
}

.explore-section {
  display: flex;
  justify-content: center;
  width: 100%;
}

.input-group {
  display: flex;
  align-items: center;
  background: var(--surface-container-lowest);
  border: 1px solid var(--outline-variant);
  width: 100%;
}

.prefix {
  padding-left: 12px;
  color: var(--outline);
  font-weight: 600;
  font-family: var(--mono);
}

.glow-input {
  background: transparent;
  border: none;
  color: var(--on-surface);
  padding: 12px 8px;
  flex: 1;
  outline: none;
  font-size: 1rem;
}

.btn-explore {
  border: none;
  background: var(--primary);
  color: var(--on-primary);
  font-weight: 600;
  padding: 12px 24px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-explore:hover {
  background: var(--primary-container);
  color: var(--on-surface);
}

.auth-card h2 {
  margin-top: 0;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: var(--on-surface);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.875rem;
  color: var(--on-surface-variant);
  font-weight: 500;
}

.form-group input {
  background: var(--surface-container-lowest);
  border: 1px solid var(--outline-variant);
  padding: 10px 12px;
  color: var(--on-surface);
  outline: none;
  font-size: 0.95rem;
  transition: border-color 0.15s ease;
}

.form-group input:focus {
  border-color: var(--primary);
}

.btn-auth {
  background: var(--surface-container-high);
  color: var(--on-surface);
  border: 1px solid var(--outline-variant);
  padding: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-auth:hover {
  border-color: var(--outline);
  background: var(--surface-container-highest);
}

.error-msg {
  color: var(--error);
  font-size: 0.85rem;
  margin: 0;
}

.toggle-mode {
  text-align: center;
  margin-top: 1.25rem;
}

.toggle-mode a {
  color: var(--primary);
  font-size: 0.875rem;
  text-decoration: none;
  transition: color 0.15s ease;
}

.toggle-mode a:hover {
  color: var(--on-surface);
}

.oauth-divider {
  display: flex;
  align-items: center;
  text-align: center;
  margin: 1.25rem 0;
  color: var(--outline);
  font-size: 0.8rem;
  font-family: var(--mono);
  text-transform: uppercase;
}

.oauth-divider::before,
.oauth-divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid var(--outline-variant);
}

.oauth-divider:not(:empty)::before {
  margin-right: .5em;
}

.oauth-divider:not(:empty)::after {
  margin-left: .5em;
}

.btn-github-auth {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background: transparent;
  color: var(--on-surface);
  border: 1px solid var(--outline-variant);
  padding: 12px;
  font-weight: 600;
  cursor: pointer;
  width: 100%;
  font-size: 0.9rem;
  transition: all 0.15s ease;
}

.btn-github-auth:hover {
  border-color: var(--primary);
  background: rgba(173, 198, 255, 0.1);
  color: var(--primary);
}

.github-icon {
  flex-shrink: 0;
}
</style>
