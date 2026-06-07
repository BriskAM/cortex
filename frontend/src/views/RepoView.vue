<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useReposStore } from '../stores/repos';
import { useChatStore } from '../stores/chat';
import IndexingProgress from '../components/IndexingProgress.vue';
import RepoNotFound from '../components/RepoNotFound.vue';
import ChatWindow from '../components/ChatWindow.vue';

const route = useRoute();
const router = useRouter();
const reposStore = useReposStore();
const chatStore = useChatStore();

const viewState = ref('loading'); // 'loading' | 'not_found' | 'indexing' | 'ready'
const owner = ref('');
const repo = ref('');
const repoId = ref(null);
const indexingStage = ref('');
const indexingProgress = ref(0);

let pollInterval = null;

const checkStatus = async () => {
  owner.value = route.params.owner;
  repo.value = route.params.repo;
  
  try {
    const data = await reposStore.checkRepoStatus(owner.value, repo.value);
    
    if (data.status === 'ready') {
      repoId.value = data.repo_id;
      viewState.value = 'ready';
      await loadChatSession();
    } else if (data.status === 'indexing') {
      viewState.value = 'indexing';
      startPolling(data.job_id);
    } else {
      viewState.value = 'not_found';
    }
  } catch (error) {
    viewState.value = 'not_found';
  }
};

const startPolling = (jobId) => {
  if (pollInterval) clearInterval(pollInterval);
  
  pollInterval = setInterval(async () => {
    try {
      const jobData = await reposStore.checkJobStatus(jobId);
      indexingStage.value = jobData.stage;
      indexingProgress.value = jobData.progress;
      
      if (jobData.status === 'SUCCESS' || jobData.progress === 100) {
        clearInterval(pollInterval);
        await checkStatus(); // Recheck status to transition to ready state
      } else if (jobData.status === 'FAILURE') {
        clearInterval(pollInterval);
        viewState.value = 'not_found';
      }
    } catch (err) {
      clearInterval(pollInterval);
    }
  }, 2000);
};

const loadChatSession = async () => {
  if (!repoId.value) return;
  await chatStore.fetchSessions(repoId.value);
  
  if (chatStore.sessions.length > 0) {
    // Load first session by default
    await chatStore.fetchSessionDetails(chatStore.sessions[0].id);
  } else {
    // Create new default session
    await chatStore.createSession(repoId.value);
  }
};

const createNewSession = async () => {
  if (!repoId.value) return;
  await chatStore.createSession(repoId.value);
};

const switchSession = async (sessionId) => {
  await chatStore.fetchSessionDetails(sessionId);
};

const deleteSession = async (sessionId) => {
  if (confirm('Delete this chat session?')) {
    await chatStore.deleteSession(sessionId);
    if (chatStore.sessions.length === 0) {
      await createNewSession();
    } else {
      await switchSession(chatStore.sessions[0].id);
    }
  }
};

onMounted(checkStatus);

watch(() => route.params.repo, checkStatus);

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval);
});
</script>

<template>
  <div class="repo-view-layout">
    <div v-if="viewState === 'loading'" class="loading-screen">
      <div class="loader"></div>
      <p>Resolving repository...</p>
    </div>

    <RepoNotFound v-else-if="viewState === 'not_found'" :owner="owner" :repo="repo" />

    <IndexingProgress 
      v-else-if="viewState === 'indexing'" 
      :stage="indexingStage" 
      :progress="indexingProgress" 
    />

    <div v-else-if="viewState === 'ready'" class="app-workspace">
      <!-- Sidebar -->
      <aside class="sidebar">
        <div class="sidebar-header">
          <h2 class="logo-title" @click="router.push('/')">Cortex</h2>
          <span class="repo-badge">{{ owner }}/{{ repo }}</span>
        </div>

        <button @click="createNewSession" class="btn btn-new-chat">+ New Chat</button>

        <div class="sessions-list">
          <div 
            v-for="session in chatStore.sessions" 
            :key="session.id" 
            :class="['session-tab', { active: chatStore.currentSession?.id === session.id }]"
            @click="switchSession(session.id)"
          >
            <span class="session-title">{{ session.title || 'Untitled Chat' }}</span>
            <button @click.stop="deleteSession(session.id)" class="btn-delete-session">&times;</button>
          </div>
        </div>
      </aside>

      <!-- Main chat workspace -->
      <main class="chat-workspace">
        <header class="workspace-header">
          <div class="title-section">
            <h3>{{ chatStore.currentSession?.title || 'Chat' }}</h3>
          </div>
          <div class="actions">
            <router-link :to="`/${owner}/${repo}/pr/1`" style="margin-right: 15px; color: #a78bfa; text-decoration: none; font-size: 0.9rem; font-weight: 600;">
              Try PR Chat
            </router-link>
            <router-link to="/dashboard" class="btn-dashboard-link">Dashboard</router-link>
          </div>
        </header>
        <div class="chat-container">
          <ChatWindow 
            v-if="chatStore.currentSession" 
            :session-id="chatStore.currentSession.id" 
          />
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.repo-view-layout {
  min-height: 100vh;
  background: #0d0d15;
  color: #f3f4f6;
  font-family: 'Inter', system-ui, sans-serif;
}

.loading-screen {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100vh;
  gap: 1rem;
}

.loader {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255,255,255,0.05);
  border-top-color: #a78bfa;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.app-workspace {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 280px;
  background: #09090e;
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  flex-direction: column;
  padding: 1.5rem 1rem;
  flex-shrink: 0;
}

.sidebar-header {
  margin-bottom: 2rem;
}

.logo-title {
  font-size: 1.5rem;
  font-weight: 800;
  margin: 0 0 0.5rem 0;
  cursor: pointer;
  background: linear-gradient(135deg, #a78bfa, #ec4899);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.repo-badge {
  font-size: 0.75rem;
  color: #9ca3af;
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-new-chat {
  background: rgba(167, 139, 250, 0.1);
  color: #a78bfa;
  border: 1px solid rgba(167, 139, 250, 0.2);
  border-radius: 6px;
  padding: 10px;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 1.5rem;
  width: 100%;
  transition: all 0.2s ease;
}

.btn-new-chat:hover {
  background: rgba(167, 139, 250, 0.2);
}

.sessions-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.session-tab {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  background: transparent;
  color: #9ca3af;
  transition: all 0.2s ease;
}

.session-tab:hover {
  background: rgba(255, 255, 255, 0.02);
  color: #ffffff;
}

.session-tab.active {
  background: rgba(167, 139, 250, 0.08);
  color: #a78bfa;
  font-weight: 500;
}

.session-title {
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  padding-right: 8px;
}

.btn-delete-session {
  background: transparent;
  border: none;
  color: #6b7280;
  font-size: 1.1rem;
  cursor: pointer;
  padding: 0;
  display: none;
}

.session-tab:hover .btn-delete-session {
  display: block;
}

.session-tab:hover .btn-delete-session:hover {
  color: #ef4444;
}

.chat-workspace {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.workspace-header {
  height: 64px;
  background: #0c0c14;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
}

.workspace-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.btn-dashboard-link {
  color: #9ca3af;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 600;
}

.btn-dashboard-link:hover {
  color: #ffffff;
}

.chat-container {
  flex: 1;
  padding: 1.5rem;
  overflow: hidden;
}
</style>
