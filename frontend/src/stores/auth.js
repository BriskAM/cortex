import { defineStore } from 'pinia';
import apiClient from '../api/axios';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('cortex_user')) || null,
    token: localStorage.getItem('cortex_token') || null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
  },
  actions: {
    async login(email, password) {
      try {
        const response = await apiClient.post('/auth/login', { email, password });
        this.token = response.data.token;
        this.user = response.data.user;
        
        localStorage.setItem('cortex_token', this.token);
        localStorage.setItem('cortex_user', JSON.stringify(this.user));
        return true;
      } catch (error) {
        console.error('Login failed:', error);
        throw error;
      }
    },
    async register(email, password) {
      try {
        await apiClient.post('/auth/register', { email, password });
        return true;
      } catch (error) {
        console.error('Registration failed:', error);
        throw error;
      }
    },
    logout() {
      this.token = null;
      this.user = null;
      localStorage.removeItem('cortex_token');
      localStorage.removeItem('cortex_user');
    },
    async fetchMe() {
      if (!this.token) return;
      try {
        const response = await apiClient.get('/auth/me');
        this.user = response.data.user;
        localStorage.setItem('cortex_user', JSON.stringify(this.user));
      } catch (error) {
        this.logout();
      }
    },
    async updateSettings(settings) {
      if (!this.token) return;
      try {
        const response = await apiClient.post('/auth/settings', settings);
        this.user = response.data.user;
        localStorage.setItem('cortex_user', JSON.stringify(this.user));
        return response.data;
      } catch (error) {
        console.error('Failed to update settings:', error);
        throw error;
      }
    },
    async loginWithGithub(code) {
      try {
        const response = await apiClient.post('/auth/github/callback', { code });
        this.token = response.data.token;
        this.user = response.data.user;
        
        localStorage.setItem('cortex_token', this.token);
        localStorage.setItem('cortex_user', JSON.stringify(this.user));
        return true;
      } catch (error) {
        console.error('GitHub login failed:', error);
        throw error;
      }
    }
  },
});
