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
  // Parse input format: e.g. "owner/repo" or "https://github.com/owner/repo"
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
      <h1 class="gradient-text">Cortex</h1>
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
          <button @click="handleExplore" class="btn btn-primary">Explore</button>
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
        <button type="submit" class="btn btn-secondary">
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
  background: radial-gradient(circle at top left, #1e1e38, #0d0d15);
  color: #f3f4f6;
  font-family: 'Inter', system-ui, sans-serif;
  padding: 1rem;
}

.glass-card {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 2.5rem;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  transition: transform 0.3s ease, border-color 0.3s ease;
}

.glass-card:hover {
  transform: translateY(-4px);
  border-color: rgba(255, 255, 255, 0.15);
}

.hero {
  text-align: center;
}

.gradient-text {
  background: linear-gradient(135deg, #a78bfa, #ec4899);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-size: 3.5rem;
  font-weight: 800;
  margin: 0;
}

.subtitle {
  color: #9ca3af;
  font-size: 1.1rem;
  margin-top: 0.5rem;
  margin-bottom: 2rem;
}

.explore-section {
  display: flex;
  justify-content: center;
}

.input-group {
  display: flex;
  align-items: center;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 4px;
  width: 100%;
}

.prefix {
  padding-left: 12px;
  color: #6b7280;
  font-weight: 500;
}

.glow-input {
  background: transparent;
  border: none;
  color: #ffffff;
  padding: 8px;
  flex: 1;
  outline: none;
  font-size: 1rem;
}

.btn {
  border: none;
  border-radius: 6px;
  padding: 10px 20px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #8b5cf6, #d946ef);
  color: white;
}

.btn-primary:hover {
  opacity: 0.9;
  box-shadow: 0 0 15px rgba(139, 92, 246, 0.4);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.2);
}

.auth-card h2 {
  margin-top: 0;
  font-weight: 700;
  margin-bottom: 1.5rem;
  background: linear-gradient(135deg, #ffffff, #a3a3a3);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
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
  color: #9ca3af;
  font-weight: 500;
}

.form-group input {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 10px 12px;
  color: white;
  outline: none;
  font-size: 0.95rem;
  transition: border-color 0.2s ease;
}

.form-group input:focus {
  border-color: #8b5cf6;
}

.error-msg {
  color: #f87171;
  font-size: 0.85rem;
  margin: 0;
}

.toggle-mode {
  text-align: center;
  margin-top: 1.25rem;
}

.toggle-mode a {
  color: #a78bfa;
  font-size: 0.875rem;
  text-decoration: none;
  transition: color 0.2s ease;
}

.toggle-mode a:hover {
  color: #c084fc;
}
</style>
