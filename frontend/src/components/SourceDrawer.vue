<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  isOpen: Boolean,
  sources: {
    type: Array,
    default: () => []
  }
});

defineEmits(['close']);

const activeTab = ref('code'); // 'code' | 'prs'

const codeSources = computed(() => props.sources.filter(s => s.type === 'code'));
const prSources = computed(() => props.sources.filter(s => s.type === 'pr'));
</script>

<template>
  <div :class="['drawer-container', { open: isOpen }]">
    <div class="drawer-header">
      <h3>Sources Cited</h3>
      <button @click="$emit('close')" class="btn-close">&times;</button>
    </div>
    
    <div class="tabs">
      <button 
        :class="['tab-btn', { active: activeTab === 'code' }]" 
        @click="activeTab = 'code'"
      >
        Code ({{ codeSources.length }})
      </button>
      <button 
        :class="['tab-btn', { active: activeTab === 'prs' }]" 
        @click="activeTab = 'prs'"
      >
        PR History ({{ prSources.length }})
      </button>
    </div>

    <div class="drawer-body">
      <div v-if="activeTab === 'code'">
        <div v-if="codeSources.length === 0" class="empty-tab">No code files cited.</div>
        <div v-else class="source-list">
          <div v-for="(source, idx) in codeSources" :key="idx" class="source-item card">
            <div class="meta-row">
              <span class="file-path">{{ source.file }}</span>
              <span class="lines">Lines {{ source.start_line }}-{{ source.end_line }}</span>
            </div>
            <pre class="snippet"><code>{{ source.snippet }}</code></pre>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'prs'">
        <div v-if="prSources.length === 0" class="empty-tab">No PR history cited.</div>
        <div v-else class="source-list">
          <div v-for="(source, idx) in prSources" :key="idx" class="source-item card pr-card">
            <div class="pr-header">
              <a :href="source.pr_url" target="_blank" class="pr-title-link">
                #{{ source.pr_number }}: {{ source.pr_title }}
              </a>
            </div>
            <div class="pr-meta">
              <span>Author: <strong>{{ source.pr_author }}</strong></span>
              <span>Merged: <strong>{{ source.merged_at }}</strong></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.drawer-container {
  position: fixed;
  top: 0;
  right: -400px;
  width: 400px;
  height: 100vh;
  background: #12121e;
  border-left: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: -8px 0 32px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  transition: right 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 100;
  font-family: 'Inter', system-ui, sans-serif;
  color: #f3f4f6;
}

.drawer-container.open {
  right: 0;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.drawer-header h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
}

.btn-close {
  background: transparent;
  border: none;
  color: #9ca3af;
  font-size: 1.5rem;
  cursor: pointer;
}

.tabs {
  display: flex;
  background: rgba(0, 0, 0, 0.15);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.tab-btn {
  flex: 1;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: #9ca3af;
  padding: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn.active {
  color: #a78bfa;
  border-bottom-color: #a78bfa;
  background: rgba(167, 139, 250, 0.05);
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.empty-tab {
  color: #6b7280;
  text-align: center;
  padding-top: 3rem;
  font-size: 0.9rem;
}

.source-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 1rem;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #9ca3af;
  margin-bottom: 0.75rem;
}

.file-path {
  font-weight: 600;
  color: #a78bfa;
}

.snippet {
  background: rgba(0, 0, 0, 0.25);
  padding: 8px 12px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 0;
}

.snippet code {
  font-family: 'Fira Code', monospace;
  font-size: 0.8rem;
  color: #e5e7eb;
}

.pr-card {
  border-left: 3px solid #ec4899;
}

.pr-title-link {
  color: #ffffff;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
  transition: color 0.2s ease;
}

.pr-title-link:hover {
  color: #ec4899;
}

.pr-meta {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.8rem;
  color: #9ca3af;
  margin-top: 0.5rem;
}
</style>
