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
    <div class="progress-card glass-card pulse-active">
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
  background: var(--background);
  color: var(--on-surface);
}

.progress-card {
  text-align: center;
  width: 100%;
  max-width: 500px;
  padding: 3rem 2rem;
  background: var(--surface-container-low);
  border: 1px solid var(--outline-variant);
}

h2 {
  font-size: 1.5rem;
  font-weight: 700;
  margin-top: 0;
  margin-bottom: 0.5rem;
}

.current-stage {
  color: var(--primary);
  font-size: 0.95rem;
  margin-bottom: 2rem;
  font-weight: 600;
  font-family: var(--mono);
  text-transform: uppercase;
}

.progress-bar-wrapper {
  background: var(--surface-container-lowest);
  border: 1px solid var(--outline-variant);
  height: 12px;
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.progress-bar {
  background: var(--primary);
  height: 100%;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.progress-text {
  font-size: 0.85rem;
  color: var(--on-surface-variant);
  font-weight: 600;
  font-family: var(--mono);
}
</style>
