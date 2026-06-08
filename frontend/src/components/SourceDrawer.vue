<script setup>
import { ref, computed } from 'vue';
import hljs from 'highlight.js';

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

const getLanguageFromFilename = (filename) => {
  if (!filename) return 'text';
  const ext = filename.split('.').pop().toLowerCase();
  const mapping = {
    'py': 'python',
    'js': 'javascript',
    'ts': 'typescript',
    'jsx': 'javascript',
    'tsx': 'typescript',
    'vue': 'xml',
    'html': 'xml',
    'java': 'java',
    'go': 'go',
    'rs': 'rust',
    'md': 'markdown',
    'sql': 'sql',
    'tex': 'latex',
    'sh': 'bash'
  };
  return mapping[ext] || 'text';
};

const highlightCode = (code, language) => {
  const lang = language || 'text';
  if (lang && hljs.getLanguage(lang)) {
    try {
      return hljs.highlight(code, { language: lang }).value;
    } catch (__) {}
  }
  return hljs.highlightAuto(code).value;
};
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
            <pre class="snippet"><code class="hljs" v-html="highlightCode(source.snippet, source.language || getLanguageFromFilename(source.file))"></code></pre>
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
  background: var(--surface-container-low);
  border-left: 1px solid var(--outline-variant);
  display: flex;
  flex-direction: column;
  transition: right 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 100;
  color: var(--on-surface);
}

.drawer-container.open {
  right: 0;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--outline-variant);
}

.drawer-header h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
}

.btn-close {
  background: transparent;
  border: none;
  color: var(--on-surface-variant);
  font-size: 1.5rem;
  cursor: pointer;
}

.tabs {
  display: flex;
  background: var(--surface-container-lowest);
  border-bottom: 1px solid var(--outline-variant);
}

.tab-btn {
  flex: 1;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--on-surface-variant);
  padding: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.tab-btn.active {
  color: var(--primary);
  border-bottom-color: var(--primary);
  background: var(--surface-container);
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.empty-tab {
  color: var(--outline);
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
  background: var(--surface-container-lowest);
  border: 1px solid var(--outline-variant);
  padding: 1rem;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: var(--on-surface-variant);
  margin-bottom: 0.75rem;
}

.file-path {
  font-weight: 600;
  color: var(--primary);
}

.snippet {
  background: var(--surface-container);
  padding: 8px 12px;
  overflow-x: auto;
  margin: 0;
  border: 1px solid var(--outline-variant);
}

.snippet code {
  font-family: var(--mono);
  font-size: 0.8rem;
  color: var(--on-surface);
}

.pr-card {
  border-left: 3px solid var(--primary);
}

.pr-title-link {
  color: var(--on-surface);
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
  transition: color 0.15s ease;
}

.pr-title-link:hover {
  color: var(--primary);
}

.pr-meta {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.8rem;
  color: var(--on-surface-variant);
  margin-top: 0.5rem;
}
</style>
