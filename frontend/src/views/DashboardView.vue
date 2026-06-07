<script setup>
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { useReposStore } from '../stores/repos';

const router = useRouter();
const authStore = useAuthStore();
const reposStore = useReposStore();

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
</script>

<template>
  <div class="dashboard-container">
    <header class="dashboard-header">
      <div class="logo">
        <h1 class="gradient-text" @click="router.push('/')">Cortex</h1>
        <span class="badge">Dashboard</span>
      </div>
      <div class="user-menu">
        <span class="user-email">{{ authStore.user?.email }}</span>
        <button @click="handleLogout" class="btn btn-logout">Logout</button>
      </div>
    </header>

    <main class="dashboard-content">
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
    </main>
  </div>
</template>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background: #0d0d15;
  color: #f3f4f6;
  font-family: 'Inter', system-ui, sans-serif;
  padding: 2rem;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
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
  font-weight: 800;
  margin: 0;
  cursor: pointer;
}

.gradient-text {
  background: linear-gradient(135deg, #a78bfa, #ec4899);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.badge {
  background: rgba(167, 139, 250, 0.15);
  color: #a78bfa;
  border: 1px solid rgba(167, 139, 250, 0.3);
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.user-email {
  color: #9ca3af;
  font-size: 0.9rem;
}

.btn {
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
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
}

.btn-logout {
  background: transparent;
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.25);
}

.btn-logout:hover {
  background: rgba(239, 68, 68, 0.1);
}

.dashboard-content {
  max-width: 1200px;
  margin: 0 auto;
}

.section-title {
  margin-bottom: 2rem;
}

.section-title h2 {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0;
}

.glass-card {
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 1.5rem;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.empty-state p {
  color: #9ca3af;
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
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.repo-card:hover {
  border-color: rgba(167, 139, 250, 0.2);
  transform: translateY(-2px);
}

.repo-name-link {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  cursor: pointer;
  transition: color 0.2s ease;
}

.repo-name-link:hover {
  color: #a78bfa;
}

.repo-url {
  font-size: 0.85rem;
  color: #6b7280;
  margin: 0.25rem 0 1rem 0;
}

.repo-stats {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: #9ca3af;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding-top: 1rem;
  margin-bottom: 0.75rem;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.status-row .label {
  color: #9ca3af;
}

.status-badge {
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.ready {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.status-badge.indexing {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.status-badge.failed {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.repo-actions {
  display: flex;
  gap: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding-top: 1rem;
}

.btn-action {
  background: rgba(255, 255, 255, 0.05);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.08);
  flex: 1;
}

.btn-action:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn-danger {
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.btn-danger:hover {
  background: rgba(239, 68, 68, 0.2);
}
</style>
