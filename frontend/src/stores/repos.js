import { defineStore } from 'pinia';
import apiClient from '../api/axios';

export const useReposStore = defineStore('repos', {
  state: () => ({
    repos: [],
    currentRepo: null,
    indexingJobs: {}, // job_id -> progress status
  }),
  actions: {
    async fetchRepos() {
      try {
        const response = await apiClient.get('/repos');
        this.repos = response.data;
      } catch (error) {
        console.error('Failed to fetch repositories:', error);
      }
    },
    async deleteRepo(id) {
      try {
        await apiClient.delete(`/repos/${id}`);
        this.repos = this.repos.filter(r => r.id !== id);
      } catch (error) {
        console.error('Failed to delete repository:', error);
        throw error;
      }
    },
    async checkRepoStatus(owner, repo) {
      try {
        const response = await apiClient.get(`/gh/${owner}/${repo}`);
        return response.data;
      } catch (error) {
        console.error('Failed to check repository status:', error);
        throw error;
      }
    },
    async checkJobStatus(jobId) {
      try {
        const response = await apiClient.get(`/status/job/${jobId}`);
        this.indexingJobs[jobId] = response.data;
        return response.data;
      } catch (error) {
        console.error('Failed to check job status:', error);
        throw error;
      }
    },
    async triggerReindex(repoId) {
      try {
        const response = await apiClient.post(`/repos/${repoId}/reindex`);
        return response.data;
      } catch (error) {
        console.error('Failed to reindex repository:', error);
        throw error;
      }
    }
  },
});
