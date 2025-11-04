/**
 * API Client Configuration
 *
 * Configures Axios instance with default settings for API communication.
 */

import axios from 'axios';

// Get API base URL from environment or config
// Note: Do NOT include /api in the base URL - it's added in authService
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Request interceptor - add auth token if available
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors globally
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response;

      // Handle specific status codes
      if (status === 401) {
        // Unauthorized - clear token and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        // Optionally redirect to login
        // window.location.href = '/login';
      } else if (status === 429) {
        // Rate limit exceeded
        error.message = data.error || 'Too many requests. Please try again later.';
      }
    } else if (error.request) {
      // Request made but no response received
      error.message = 'Network error. Please check your connection.';
    } else {
      // Something else happened
      error.message = 'An unexpected error occurred.';
    }

    return Promise.reject(error);
  }
);

export default apiClient;
