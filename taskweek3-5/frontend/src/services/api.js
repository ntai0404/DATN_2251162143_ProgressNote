import axios from 'axios';

const API_BASE_URL = 'http://localhost:8003'; 

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const searchService = {
  async search(query, topK = 5) {
    try {
      const response = await apiClient.post('/search', { query, top_k: topK });
      return { results: response.data };
    } catch (error) {
      console.error('Search Error:', error);
      throw error;
    }
  },

  async refreshIndex() {
    const response = await apiClient.post('/refresh');
    return response.data;
  },

  async checkHealth() {
    try {
      const response = await apiClient.get('/');
      return { status: 'ok', data: response.data };
    } catch (error) {
      return { status: 'offline' };
    }
  }
};

export const adminService = {
  async listFiles() {
    const response = await apiClient.get('/admin/files');
    return response.data;
  },

  async triggerOCR(filePath, mode = 'cloud') {
    const response = await apiClient.post('/admin/ocr', { path: filePath, mode });
    return response.data;
  },

  async getOCRContent(fileName) {
    const response = await apiClient.get(`/admin/ocr-content/${fileName}`);
    return response.data;
  },

  async triggerEmbed(fileName) {
    const response = await apiClient.post('/admin/embed', { filename: fileName });
    return response.data;
  }
};
