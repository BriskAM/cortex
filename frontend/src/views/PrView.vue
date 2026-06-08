<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useChatStore } from '../stores/chat';
import ChatWindow from '../components/ChatWindow.vue';
import apiClient from '../api/axios';

const route = useRoute();
const router = useRouter();
const chatStore = useChatStore();

const owner = ref('');
const repo = ref('');
const prNumber = ref(null);
const prData = ref(null);
const isLoading = ref(true);
const activeSessionId = ref(null);

const panelWidth = ref(parseInt(localStorage.getItem('cortex-pr-panel-width')) || 380);

const startResize = (e) => {
  e.preventDefault();
  const startX = e.clientX;
  const startWidth = panelWidth.value;

  const doDrag = (dragEvent) => {
    const newWidth = startWidth + (dragEvent.clientX - startX);
    if (newWidth >= 250 && newWidth <= 800) {
      panelWidth.value = newWidth;
    }
  };

  const stopDrag = () => {
    document.removeEventListener('mousemove', doDrag);
    document.removeEventListener('mouseup', stopDrag);
    localStorage.setItem('cortex-pr-panel-width', panelWidth.value);
  };

  document.addEventListener('mousemove', doDrag);
  document.addEventListener('mouseup', stopDrag);
};

const starterQuestions = [
  "Explain this PR's overall goals.",
  "Are there any architectural concerns or potential breaking changes?",
  "Analyze security vulnerabilities or performance issues in these diffs.",
];

const loadPrDetails = async () => {
  owner.value = route.params.owner;
  repo.value = route.params.repo;
  prNumber.value = parseInt(route.params.number);

  try {
    const response = await apiClient.get(`/gh/${owner.value}/${repo.value}/pr/${prNumber.value}`);
    prData.value = response.data;
    
    // Create a PR-scoped chat session
    const session = await chatStore.createSession(prData.value.repo_id, 'pr', prNumber.value);
    activeSessionId.value = session.id;
  } catch (error) {
    console.error('Failed to load PR details:', error);
  } finally {
    isLoading.value = false;
  }
};

const sendStarterQuestion = (question) => {
  if (activeSessionId.value) {
    chatStore.sendMessageStream(activeSessionId.value, question);
  }
};

onMounted(loadPrDetails);
</script>

<template>
  <div class="pr-view-container">
    <div v-if="isLoading" class="loading-screen">
      <div class="loader"></div>
      <p>Loading Pull Request context...</p>
    </div>

    <div v-else class="pr-workspace">
      <!-- Left Metadata Panel -->
      <aside class="metadata-panel" :style="{ width: panelWidth + 'px' }">
        <div class="panel-header">
          <router-link :to="`/${owner}/${repo}`" class="back-link">
            &larr; Back to full repo chat
          </router-link>
          <h2 class="title">PR #{{ prNumber }}</h2>
        </div>

        <div v-if="prData" class="pr-details glass-card">
          <h3 class="pr-title">{{ prData.pr_title }}</h3>
          <div class="pr-author-meta">
            <span>Author: <strong>{{ prData.pr_author }}</strong></span>
            <span>Merged: <strong>{{ prData.merged_at }}</strong></span>
          </div>
          
          <div class="divider"></div>

          <h4>Description</h4>
          <p class="pr-body">{{ prData.pr_body }}</p>
          
          <div class="divider"></div>

          <h4>Files Changed</h4>
          <ul class="file-list">
            <li v-for="file in prData.files_changed" :key="file">{{ file }}</li>
          </ul>
        </div>
      </aside>

      <!-- Splitter drag handle -->
      <div class="resize-handle" @mousedown="startResize"></div>

      <!-- Right Chat Area -->
      <main class="chat-area">
        <header class="workspace-header">
          <h3>Review Companion</h3>
        </header>

        <div class="chat-container">
          <ChatWindow v-if="activeSessionId" :session-id="activeSessionId" />
        </div>

        <!-- Suggestion box -->
        <div class="starter-box" v-if="chatStore.messages.length === 0 && !chatStore.isStreaming">
          <p class="label">Suggested starter questions:</p>
          <div class="question-pills">
            <button 
              v-for="q in starterQuestions" 
              :key="q" 
              @click="sendStarterQuestion(q)"
              class="pill-btn"
            >
              {{ q }}
            </button>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.pr-view-container {
  min-height: 100vh;
  background: var(--background);
  color: var(--on-surface);
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
  border: 1px solid var(--outline-variant);
  border-top-color: var(--primary);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.pr-workspace {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.metadata-panel {
  background: var(--surface-container-low);
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
  overflow-y: auto;
  flex-shrink: 0;
}

.resize-handle {
  width: 6px;
  cursor: col-resize;
  position: relative;
  z-index: 10;
  flex-shrink: 0;
  background: transparent;
  margin-left: -3px;
  margin-right: -3px;
  user-select: none;
}

.resize-handle::after {
  content: '';
  position: absolute;
  top: 0;
  left: 2px;
  width: 2px;
  height: 100%;
  background: var(--outline-variant);
  transition: background-color 0.15s ease;
}

.resize-handle:hover::after,
.resize-handle:active::after {
  background: var(--primary);
}

.panel-header {
  margin-bottom: 2rem;
}

.back-link {
  color: var(--primary);
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 600;
  display: inline-block;
  margin-bottom: 0.75rem;
}

.back-link:hover {
  color: var(--on-surface);
}

.title {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0;
  color: var(--on-surface);
}

.glass-card {
  background: var(--surface-container-lowest);
  border: 1px solid var(--outline-variant);
  padding: 1.25rem;
}

.pr-title {
  font-size: 1.15rem;
  font-weight: 700;
  margin-top: 0;
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.pr-author-meta {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.8rem;
  color: var(--on-surface-variant);
  font-family: var(--mono);
}

.divider {
  height: 1px;
  background: var(--outline-variant);
  margin: 1.25rem 0;
}

h4 {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--primary);
  margin-top: 0;
  margin-bottom: 0.5rem;
  font-family: var(--mono);
  text-transform: uppercase;
}

.pr-body {
  font-size: 0.875rem;
  color: var(--on-surface-variant);
  line-height: 1.5;
  margin: 0;
  white-space: pre-wrap;
}

.file-list {
  padding-left: 1.25rem;
  margin: 0;
  font-size: 0.85rem;
  color: var(--on-surface-variant);
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-family: var(--mono);
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.workspace-header {
  height: 64px;
  background: var(--surface-container-lowest);
  border-bottom: 1px solid var(--outline-variant);
  display: flex;
  align-items: center;
  padding: 0 1.5rem;
}

.workspace-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.chat-container {
  flex: 1;
  padding: 1.5rem 1.5rem 0.5rem 1.5rem;
  overflow: hidden;
  background: var(--background);
}

.starter-box {
  padding: 0 1.5rem 1.5rem 1.5rem;
}

.starter-box .label {
  font-size: 0.8rem;
  color: var(--outline);
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.question-pills {
  display: flex;
  gap: 0.75rem;
  overflow-x: auto;
}

.pill-btn {
  background: var(--surface-container-low);
  border: 1px solid var(--outline-variant);
  color: var(--on-surface-variant);
  padding: 8px 16px;
  font-size: 0.85rem;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.pill-btn:hover {
  background: var(--surface-container-high);
  border-color: var(--primary);
  color: var(--primary);
}
</style>
