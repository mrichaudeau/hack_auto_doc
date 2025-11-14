/**
 * API Client Configuration
 *
 * Configures Axios instance with default settings for API communication.
 *
 * Updated for TASK-3.12: Removed basic interceptors in favor of advanced
 * interceptors with automatic token refresh (see interceptors.js)
 */

import axios from 'axios';

// Get API base URL from environment or config
// Note: When empty, requests are relative and go through Vite dev server proxy
// The proxy forwards /api/* requests to the backend service
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Note: Interceptors are now configured via setupInterceptors() in interceptors.js
// This allows proper integration with React Router's navigate function
// Call initializeApiClient() from App.jsx to set up interceptors

/**
 * Initialize API client with interceptors
 * Must be called from App component with React Router's navigate function
 *
 * @param {Function} navigate - React Router navigate function
 * @param {Function} onLogout - Optional callback for logout (e.g., clear auth context)
 */
export const initializeApiClient = (navigate, onLogout = null) => {
  // Import dynamically to avoid circular dependencies
  import('./interceptors').then(({ setupInterceptors }) => {
    setupInterceptors(apiClient, navigate, onLogout);
  });
};

export default apiClient;
