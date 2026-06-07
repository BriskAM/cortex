<script setup>
import { ref, onUpdated, nextTick } from 'vue';
import { useChatStore } from '../stores/chat';
import SourceDrawer from './SourceDrawer.vue';

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
          <div class="message-content">{{ msg.content }}</div>
          
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
          <div class="message-content">{{ chatStore.streamingContent }}<span class="cursor">|</span></div>
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
        <button type="submit" class="btn btn-send" :disabled="chatStore.isStreaming">
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
  background: #0f0f18;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
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
  color: #9ca3af;
}

.welcome-box h3 {
  color: #a78bfa;
  font-size: 1.4rem;
  margin-bottom: 0.5rem;
}

.message-bubble {
  display: flex;
  gap: 1rem;
  max-width: 85%;
  align-self: flex-start;
}

.message-bubble.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(167, 139, 250, 0.15);
  color: #a78bfa;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  border: 1px solid rgba(167, 139, 250, 0.3);
  flex-shrink: 0;
}

.message-bubble.user .avatar {
  background: rgba(236, 72, 153, 0.15);
  color: #ec4899;
  border-color: rgba(236, 72, 153, 0.3);
}

.content-wrapper {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  padding: 1rem;
  border-radius: 12px;
  border-top-left-radius: 0;
}

.message-bubble.user .content-wrapper {
  background: rgba(167, 139, 250, 0.08);
  border-color: rgba(167, 139, 250, 0.15);
  border-radius: 12px;
  border-top-right-radius: 0;
}

.message-content {
  line-height: 1.6;
  white-space: pre-wrap;
  font-size: 0.95rem;
}

.source-citation {
  margin-top: 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding-top: 0.5rem;
}

.btn-sources {
  background: transparent;
  border: none;
  color: #a78bfa;
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
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.chat-form {
  display: flex;
  gap: 0.75rem;
}

.chat-input {
  flex: 1;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 12px 16px;
  color: white;
  outline: none;
  font-size: 0.95rem;
  transition: border-color 0.2s ease;
}

.chat-input:focus {
  border-color: #8b5cf6;
}

.btn-send {
  background: linear-gradient(135deg, #8b5cf6, #d946ef);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0 24px;
  font-weight: 600;
  cursor: pointer;
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cursor {
  animation: blink 1s step-end infinite;
  color: #a78bfa;
  font-weight: bold;
}

@keyframes blink {
  from, to { color: transparent }
  50% { color: #a78bfa; }
}
</style>
