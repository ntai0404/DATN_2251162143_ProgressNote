import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const searchService = {
  /**
   * Truy vấn tìm kiếm ngữ nghĩa từ Vector DB
   * @param {string} query - Câu hỏi sinh viên
   * @param {number} topK - Số kết quả tối đa
   */
  async search(query, topK = 5) {
    try {
      const response = await apiClient.post('/search', {
        query: query,
        top_k: topK,
      });
      return response.data;
    } catch (error) {
      console.error('Search API Error:', error);
      throw error;
    }
  },

  /**
   * Kiểm tra trạng thái hệ thống
   */
  async checkHealth() {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      return { status: 'offline', error };
    }
  }
};
