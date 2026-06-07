import { defineStore } from 'pinia';
import apiClient from '../api/axios';

export const useChatStore = defineStore('chat', {
  state: () => ({
    sessions: [],
    currentSession: null,
    messages: [],
    isStreaming: false,
    streamingContent: '',
  }),
  actions: {
    async fetchSessions(repoId) {
      try {
        const response = await apiClient.get(`/chat/sessions?repo_id=${repoId}`);
        this.sessions = response.data;
      } catch (error) {
        console.error('Failed to fetch chat sessions:', error);
      }
    },
    async createSession(repoId, scope = 'repo', prNumber = null) {
      try {
        const response = await apiClient.post('/chat/sessions', {
          repo_id: repoId,
          scope,
          pr_number: prNumber
        });
        const newSession = response.data;
        this.sessions.unshift(newSession);
        this.currentSession = newSession;
        this.messages = [];
        return newSession;
      } catch (error) {
        console.error('Failed to create session:', error);
        throw error;
      }
    },
    async fetchSessionDetails(sessionId) {
      try {
        const response = await apiClient.get(`/chat/sessions/${sessionId}`);
        this.currentSession = response.data;
        this.messages = response.data.messages || [];
      } catch (error) {
        console.error('Failed to fetch session details:', error);
      }
    },
    async deleteSession(sessionId) {
      try {
        await apiClient.delete(`/chat/sessions/${sessionId}`);
        this.sessions = this.sessions.filter(s => s.id !== sessionId);
        if (this.currentSession?.id === sessionId) {
          this.currentSession = null;
          this.messages = [];
        }
      } catch (error) {
        console.error('Failed to delete session:', error);
      }
    },
    sendMessageStream(sessionId, messageText) {
      this.isStreaming = true;
      this.streamingContent = '';
      
      // Push the user message immediately to the UI
      this.messages.push({
        id: Date.now(),
        role: 'user',
        content: messageText,
        created_at: new Date().toISOString()
      });

      // Construct SSE URL with query parameters
      const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
      const token = localStorage.getItem('cortex_token');
      const url = `${baseUrl}/chat/sessions/${sessionId}/message?q=${encodeURIComponent(messageText)}` + 
                  (token ? `&token=${encodeURIComponent(token)}` : '');

      const eventSource = new EventSource(url);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.token) {
            this.streamingContent += data.token;
          }
          
          if (data.done) {
            // Push completed assistant message to history and reset streaming
            this.messages.push({
              id: Date.now() + 1,
              role: 'assistant',
              content: this.streamingContent,
              sources: data.sources || [],
              created_at: new Date().toISOString()
            });
            this.isStreaming = false;
            this.streamingContent = '';
            eventSource.close();
          }
        } catch (e) {
          console.error('Error parsing SSE message:', e);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
        this.isStreaming = false;
        eventSource.close();
      };
    }
  },
});
