<script setup>
import { computed } from 'vue';

const props = defineProps({
  stage: {
    type: String,
    default: 'fetching_files'
  },
  progress: {
    type: Number,
    default: 0
  }
});

const stageLabel = computed(() => {
  const labels = {
    'fetching_files': 'Fetching Repository Files',
    'chunking_code': 'Parsing and Chunking Code (tree-sitter)',
    'fetching_prs': 'Fetching and Scraping Pull Request History',
    'embedding': 'Generating Embeddings (gemini-embedding-001)',
    'storing': 'Storing in Vector Database (ChromaDB)',
    'done': 'Repository Ready'
  };
  return labels[props.stage] || 'Indexing Repository...';
});
</script>

<template>
  <div class="progress-container">
    <div class="progress-card glass-card">
      <div class="spinner"></div>
      <h2>Indexing Codebase</h2>
      <p class="current-stage">{{ stageLabel }}</p>
      
      <div class="progress-bar-wrapper">
        <div class="progress-bar" :style="{ width: progress + '%' }"></div>
      </div>
      <div class="progress-text">{{ progress }}% Completed</div>
    </div>
  </div>
</template>

<style scoped>
.progress-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 4rem);
  background: #0d0d15;
  color: #f3f4f6;
  font-family: 'Inter', system-ui, sans-serif;
}

.progress-card {
  text-align: center;
  width: 100%;
  max-width: 500px;
  padding: 3rem 2rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  backdrop-filter: blur(12px);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
}

.spinner {
  width: 50px;
  height: 50px;
  border: 3px solid rgba(167, 139, 250, 0.1);
  border-top-color: #a78bfa;
  border-radius: 50%;
  margin: 0 auto 1.5rem auto;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

h2 {
  font-size: 1.5rem;
  font-weight: 700;
  margin-top: 0;
  margin-bottom: 0.5rem;
}

.current-stage {
  color: #a78bfa;
  font-size: 0.95rem;
  margin-bottom: 2rem;
  font-weight: 500;
}

.progress-bar-wrapper {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 9999px;
  height: 8px;
  overflow: hidden;
  margin-bottom: 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.progress-bar {
  background: linear-gradient(90deg, #8b5cf6, #d946ef);
  height: 100%;
  border-radius: 9999px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 10px rgba(139, 92, 246, 0.5);
}

.progress-text {
  font-size: 0.85rem;
  color: #6b7280;
  font-weight: 600;
}
</style>
