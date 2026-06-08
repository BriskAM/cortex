<script setup>
import { ref, onUpdated, nextTick } from 'vue';
import { useChatStore } from '../stores/chat';
import SourceDrawer from './SourceDrawer.vue';
import { marked } from 'marked';

marked.setOptions({
  gfm: true,
  breaks: true
});

const renderMarkdown = (text) => {
  if (!text) return '';
  return marked.parse(text);
};

const props = defineProps({
  sessionId: {
    type: Number,
    required: true
  }
});

const chatStore = useChatStore();
const inputText = ref('');
const messageContainer = ref(null);
const drawerOpen = ref(false);
const drawerSources = ref([]);

const scrollToBottom = () => {
  if (messageContainer.value) {
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
  }
};

const handleSend = () => {
  if (!inputText.value.trim() || chatStore.isStreaming) return;
  chatStore.sendMessageStream(props.sessionId, inputText.value);
  inputText.value = '';
  nextTick(() => {
    scrollToBottom();
  });
};

onUpdated(() => {
  scrollToBottom();
});

const openSources = (sources) => {
  drawerSources.value = sources || [];
  drawerOpen.value = true;
};
</script>

<template>
  <div class="chat-window-container">
    <div class="messages-area" ref="messageContainer">
      <div v-if="chatStore.messages.length === 0" class="welcome-box">
        <h3>Ask anything about this codebase</h3>
        <p>You can ask technical structure questions or history/PR questions.</p>
      </div>
      
      <div 
        v-for="msg in chatStore.messages" 
        :key="msg.id" 
        :class="['message-bubble', msg.role]"
      >
        <div class="avatar">{{ msg.role === 'user' ? 'U' : 'AI' }}</div>
        <div class="content-wrapper">
          <div class="message-content markdown-body" v-html="renderMarkdown(msg.content)"></div>
          
          <div v-if="msg.sources && msg.sources.length > 0" class="source-citation">
            <button @click="openSources(msg.sources)" class="btn-sources">
              View {{ msg.sources.length }} Citations
            </button>
          </div>
        </div>
      </div>

      <!-- Streaming block -->
      <div v-if="chatStore.isStreaming" class="message-bubble assistant streaming">
        <div class="avatar">AI</div>
        <div class="content-wrapper">
          <div class="message-content markdown-body" v-html="renderMarkdown(chatStore.streamingContent) + '<span class=&quot;cursor&quot;>|</span>'"></div>
        </div>
      </div>
    </div>

    <div class="input-area">
      <form @submit.prevent="handleSend" class="chat-form">
        <input 
          v-model="inputText" 
          placeholder="Ask a question about the code or history..." 
          :disabled="chatStore.isStreaming"
          class="chat-input"
        />
        <button type="submit" class="btn-send" :disabled="chatStore.isStreaming">
          {{ chatStore.isStreaming ? 'Thinking...' : 'Send' }}
        </button>
      </form>
    </div>

    <SourceDrawer 
      :is-open="drawerOpen" 
      :sources="drawerSources" 
      @close="drawerOpen = false" 
    />
  </div>
</template>

<style scoped>
.chat-window-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--surface-container-lowest);
  border: 1px solid var(--outline-variant);
  overflow: hidden;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.welcome-box {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--on-surface-variant);
}

.welcome-box h3 {
  color: var(--primary);
  font-size: 1.4rem;
  margin-bottom: 0.5rem;
}

.message-bubble {
  display: flex;
  gap: 1rem;
  max-width: 85%;
  align-self: flex-start;
  animation: message-slide-up 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
}

@keyframes message-slide-up {
  0% {
    opacity: 0;
    transform: translateY(8px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-bubble.assistant.streaming .content-wrapper {
  animation: thinking-pulse 1.8s infinite ease-in-out;
}

@keyframes thinking-pulse {
  0%, 100% {
    border-color: var(--outline-variant);
  }
  50% {
    border-color: var(--primary);
  }
}

.message-bubble.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  background: var(--surface-container-high);
  color: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  border: 1px solid var(--outline-variant);
  flex-shrink: 0;
  font-family: var(--mono);
}

.message-bubble.user .avatar {
  background: var(--surface-container-highest);
  color: var(--on-surface);
  border-color: var(--outline);
}

.content-wrapper {
  background: var(--surface-container-low);
  border: 1px solid var(--outline-variant);
  padding: 1rem;
}

.message-bubble.user .content-wrapper {
  background: var(--surface-container-high);
  border-color: var(--primary);
}

.message-content {
  line-height: 1.6;
  white-space: pre-wrap;
  font-size: 0.95rem;
}

.source-citation {
  margin-top: 0.75rem;
  border-top: 1px solid var(--outline-variant);
  padding-top: 0.5rem;
}

.btn-sources {
  background: transparent;
  border: none;
  color: var(--primary);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}

.btn-sources:hover {
  text-decoration: underline;
}

.input-area {
  padding: 1.25rem;
  background: var(--surface-container-low);
  border-top: 1px solid var(--outline-variant);
}

.chat-form {
  display: flex;
  gap: 0.75rem;
}

.chat-input {
  flex: 1;
  background: var(--surface-container-lowest);
  border: 1px solid var(--outline-variant);
  padding: 12px 16px;
  color: var(--on-surface);
  outline: none;
  font-size: 0.95rem;
  transition: border-color 0.15s ease;
}

.chat-input:focus {
  border-color: var(--primary);
}

.btn-send {
  background: var(--primary);
  color: var(--on-primary);
  border: 1px solid var(--primary);
  padding: 0 24px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-send:hover:not(:disabled) {
  background: var(--primary-container);
  border-color: var(--primary-container);
  color: var(--on-surface);
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cursor {
  animation: blink 1s step-end infinite;
  color: var(--primary);
  font-weight: bold;
}

@keyframes blink {
  from, to { color: transparent }
  50% { color: var(--primary); }
}

.markdown-body :deep(h1), 
.markdown-body :deep(h2), 
.markdown-body :deep(h3), 
.markdown-body :deep(h4) {
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  color: var(--primary);
  font-family: var(--sans);
  font-weight: 600;
}

.markdown-body :deep(h1) { font-size: 1.3rem; }
.markdown-body :deep(h2) { font-size: 1.15rem; }
.markdown-body :deep(h3) { font-size: 1.05rem; }
.markdown-body :deep(h4) { font-size: 0.95rem; }

.markdown-body :deep(p) {
  margin-bottom: 0.75rem;
  line-height: 1.6;
  color: var(--on-surface-variant);
}

.markdown-body :deep(ul), 
.markdown-body :deep(ol) {
  margin-left: 1.25rem;
  margin-bottom: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.markdown-body :deep(li) {
  color: var(--on-surface-variant);
  line-height: 1.5;
}

.markdown-body :deep(strong) {
  color: var(--on-surface);
  font-weight: 600;
}

.markdown-body :deep(code) {
  font-family: var(--mono);
  font-size: 0.85rem;
  background: var(--surface-container-high);
  border: 1px solid var(--outline-variant);
  padding: 2px 6px;
  color: var(--primary);
}

.markdown-body :deep(pre) {
  background: var(--surface-container);
  border: 1px solid var(--outline-variant);
  padding: 12px;
  overflow-x: auto;
  margin: 0.75rem 0;
}

.markdown-body :deep(pre code) {
  background: transparent;
  border: none;
  padding: 0;
  color: var(--on-surface);
}

.markdown-body :deep(a) {
  color: var(--primary);
  text-decoration: underline;
}

.markdown-body :deep(a:hover) {
  color: var(--on-surface);
}
</style>
