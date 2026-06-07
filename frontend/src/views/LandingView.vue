<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

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
</style>
