<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { useReposStore } from '../stores/repos';

const router = useRouter();
const authStore = useAuthStore();
const reposStore = useReposStore();

const githubTokenInput = ref('');
const isSavingSettings = ref(false);
const settingsMessage = ref('');
const settingsError = ref('');

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.push('/');
    return;
  }
  try {
    await authStore.fetchMe();
    await reposStore.fetchRepos();
  } catch (err) {
    router.push('/');
  }
});

const handleLogout = () => {
  authStore.logout();
  router.push('/');
};

const navigateToRepo = (owner, repoName) => {
  router.push(`/${owner}/${repoName}`);
};

const handleDelete = async (id) => {
  if (confirm('Are you sure you want to delete this repo and all vector data?')) {
    await reposStore.deleteRepo(id);
  }
};

const handleReindex = async (id) => {
  await reposStore.triggerReindex(id);
  alert('Re-indexing task queued.');
};

const saveSettings = async () => {
  isSavingSettings.value = true;
  settingsMessage.value = '';
  settingsError.value = '';
  try {
    await authStore.updateSettings({ github_token: githubTokenInput.value });
    githubTokenInput.value = '';
    settingsMessage.value = 'Token saved successfully.';
  } catch (err) {
    settingsError.value = err.response?.data?.error || 'Failed to save settings.';
  } finally {
    isSavingSettings.value = false;
  }
};

const clearToken = async () => {
  if (confirm('Are you sure you want to clear your GitHub Access Token?')) {
    isSavingSettings.value = true;
    settingsMessage.value = '';
    settingsError.value = '';
    try {
      await authStore.updateSettings({ github_token: '' });
      settingsMessage.value = 'Token cleared successfully.';
    } catch (err) {
      settingsError.value = err.response?.data?.error || 'Failed to clear settings.';
    } finally {
      isSavingSettings.value = false;
    }
  }
};
</script>

<template>
  <div class="dashboard-container">
    <header class="dashboard-header">
      <div class="logo">
        <h1 @click="router.push('/')">Cortex</h1>
        <span class="badge">Dashboard</span>
      </div>
      <div class="user-menu">
        <span class="user-email">{{ authStore.user?.email }}</span>
        <button @click="handleLogout" class="btn btn-logout">Logout</button>
      </div>
    </header>

    <main class="dashboard-content grid-layout">
      <!-- Repositories List -->
      <section class="repos-section">
        <div class="section-title">
          <h2>Your Indexed Repositories</h2>
        </div>

        <div v-if="reposStore.repos.length === 0" class="empty-state glass-card">
          <p>No repositories indexed yet.</p>
          <button @click="router.push('/')" class="btn btn-primary">Index your first repository</button>
        </div>

        <div v-else class="repo-grid">
          <div v-for="repo in reposStore.repos" :key="repo.id" class="repo-card glass-card">
            <div class="repo-info">
              <h3 @click="navigateToRepo(repo.owner, repo.repo_name)" class="repo-name-link">
                {{ repo.owner }} / {{ repo.repo_name }}
              </h3>
              <p class="repo-url">{{ repo.github_url }}</p>
              <div class="repo-stats">
                <span>Files: <strong>{{ repo.file_count }}</strong></span>
                <span>Chunks: <strong>{{ repo.chunk_count }}</strong></span>
                <span>PRs: <strong>{{ repo.pr_count }}</strong></span>
              </div>
              <div class="status-row">
                <span class="label">Status:</span>
                <span :class="['status-badge', repo.status]">{{ repo.status }}</span>
              </div>
            </div>
            <div class="repo-actions">
              <button @click="handleReindex(repo.id)" class="btn btn-action">Re-Index</button>
              <button @click="handleDelete(repo.id)" class="btn btn-danger">Delete</button>
            </div>
          </div>
        </div>
      </section>

      <!-- Settings Panel -->
      <aside class="settings-section">
        <div class="section-title">
          <h2>Configuration Settings</h2>
        </div>

        <div class="settings-card glass-card">
          <h3>GitHub Token Settings</h3>
          <p class="settings-description">
            Configure a GitHub Personal Access Token (PAT) with <code>read:repo</code> scope. This is encrypted in the database and preferred during repository crawl operations.
          </p>

          <div class="status-indicator">
            <span class="label">Token Status:</span>
            <span v-if="authStore.user?.has_github_token" class="status-badge ready">✓ Active</span>
            <span v-else class="status-badge failed">✗ None Configured</span>
          </div>

          <form @submit.prevent="saveSettings" class="token-form">
            <div class="form-group">
              <label>Personal Access Token</label>
              <input 
                v-model="githubTokenInput" 
                type="password" 
                placeholder="ghp_..." 
                required
                class="token-input"
              />
            </div>

            <div class="btn-group">
              <button type="submit" class="btn btn-primary" :disabled="isSavingSettings">
                {{ isSavingSettings ? 'Saving...' : 'Save Token' }}
              </button>
              <button 
                v-if="authStore.user?.has_github_token" 
                type="button" 
                @click="clearToken" 
                class="btn btn-danger-outline" 
                :disabled="isSavingSettings"
              >
                Clear Token
              </button>
            </div>
          </form>

          <p v-if="settingsMessage" class="feedback-msg success">{{ settingsMessage }}</p>
          <p v-if="settingsError" class="feedback-msg error">{{ settingsError }}</p>
        </div>
      </aside>
    </main>
  </div>
</template>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background: var(--background);
  color: var(--on-surface);
  padding: 2rem;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--outline-variant);
  padding-bottom: 1.5rem;
  margin-bottom: 3rem;
}

.logo {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo h1 {
  font-size: 2rem;
  font-weight: 700;
  margin: 0;
  cursor: pointer;
  color: var(--primary);
}

.badge {
  background: var(--surface-container-high);
  color: var(--primary);
  border: 1px solid var(--outline-variant);
  padding: 2px 8px;
  font-size: 0.75rem;
  font-weight: 600;
  font-family: var(--mono);
  text-transform: uppercase;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.user-email {
  color: var(--on-surface-variant);
  font-size: 0.9rem;
}

.btn-logout {
  background: transparent;
  color: var(--error);
  border: 1px solid var(--error);
  padding: 8px 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-logout:hover {
  background: rgba(255, 180, 171, 0.15);
}

.dashboard-content {
  max-width: 1200px;
  margin: 0 auto;
}

.grid-layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
}

@media (max-width: 900px) {
  .grid-layout {
    grid-template-columns: 1fr;
  }
}

.settings-card {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.settings-card h3 {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
  color: var(--on-surface);
}

.settings-description {
  font-size: 0.85rem;
  color: var(--on-surface-variant);
  line-height: 1.4;
  margin: 0;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.status-indicator .label {
  color: var(--on-surface-variant);
}

.token-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.token-input {
  width: 100%;
  background: var(--surface-container-lowest);
  border: 1px solid var(--outline-variant);
  padding: 10px 12px;
  color: var(--on-surface);
  outline: none;
  font-size: 0.9rem;
  transition: border-color 0.15s ease;
}

.token-input:focus {
  border-color: var(--primary);
}

.btn-group {
  display: flex;
  gap: 1rem;
}

.btn-group .btn {
  flex: 1;
}

.btn-danger-outline {
  background: transparent;
  color: var(--error);
  border: 1px solid var(--error);
  padding: 8px 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
}

.btn-danger-outline:hover {
  background: rgba(255, 180, 171, 0.1);
}

.feedback-msg {
  font-size: 0.85rem;
  margin: 0;
  padding: 8px 12px;
  border: 1px solid transparent;
}

.feedback-msg.success {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.3);
}

.feedback-msg.error {
  background: rgba(239, 68, 68, 0.1);
  color: var(--error);
  border-color: rgba(239, 68, 68, 0.3);
}

.section-title {
  margin-bottom: 2rem;
}

.section-title h2 {
  font-size: 1.75rem;
  font-weight: 600;
  margin: 0;
}

.glass-card {
  background: var(--surface-container-low);
  border: 1px solid var(--outline-variant);
  padding: 1.5rem;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.empty-state p {
  color: var(--on-surface-variant);
  margin-bottom: 1.5rem;
}

.repo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.repo-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 1.5rem;
  transition: border-color 0.15s ease;
}

.repo-card:hover {
  border-color: var(--primary);
}

.repo-name-link {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.15s ease;
}

.repo-name-link:hover {
  color: var(--primary);
}

.repo-url {
  font-size: 0.85rem;
  color: var(--on-surface-variant);
  margin: 0.25rem 0 1rem 0;
  font-family: var(--mono);
}

.repo-stats {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: var(--on-surface-variant);
  border-top: 1px solid var(--outline-variant);
  padding-top: 1rem;
  margin-bottom: 0.75rem;
  font-family: var(--mono);
}

.status-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.status-row .label {
  color: var(--on-surface-variant);
}

.status-badge {
  padding: 2px 6px;
  font-size: 0.75rem;
  font-weight: 700;
  font-family: var(--mono);
  text-transform: uppercase;
  border: 1px solid var(--outline-variant);
}

.status-badge.ready {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.3);
}

.status-badge.indexing {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
  border-color: rgba(245, 158, 11, 0.3);
}

.status-badge.failed {
  background: rgba(239, 68, 68, 0.1);
  color: var(--error);
  border-color: rgba(239, 68, 68, 0.3);
}

.repo-actions {
  display: flex;
  gap: 1rem;
  border-top: 1px solid var(--outline-variant);
  padding-top: 1rem;
}

.btn-action {
  background: var(--surface-container-high);
  color: var(--on-surface);
  border: 1px solid var(--outline-variant);
  flex: 1;
  padding: 8px 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-action:hover {
  background: var(--surface-container-highest);
  border-color: var(--outline);
}

.btn-danger {
  background: rgba(255, 180, 171, 0.1);
  color: var(--error);
  border: 1px solid var(--error);
  padding: 8px 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-danger:hover {
  background: var(--error);
  color: var(--on-primary);
}
</style>
