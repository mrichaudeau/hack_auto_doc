import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // For CORS with credentials
});

// Flag to prevent infinite refresh loops
let isRefreshing = false;
// Queue of failed requests to retry after token refresh
let failedRequestsQueue = [];

/**
 * Process the queue of failed requests after successful token refresh
 * @param {string} newAccessToken - The new access token
 */
const processQueue = (error, newAccessToken = null) => {
  failedRequestsQueue.forEach(promise => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(newAccessToken);
    }
  });
  failedRequestsQueue = [];
};

/**
 * Request interceptor to add Authorization header with JWT token
 */
apiClient.interceptors.request.use(
  (config) => {
    const accessToken = localStorage.getItem('access_token');

    // Add Authorization header if token exists and not already set
    if (accessToken && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor to handle 401 errors and refresh token automatically
 */
apiClient.interceptors.response.use(
  (response) => {
    // Return successful responses as-is
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Check if error is 401 and we haven't already tried to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Prevent retrying auth endpoints to avoid infinite loops
      if (
        originalRequest.url?.includes('/auth/login') ||
        originalRequest.url?.includes('/auth/refresh') ||
        originalRequest.url?.includes('/auth/register')
      ) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // If already refreshing, queue this request to retry after refresh completes
        return new Promise((resolve, reject) => {
          failedRequestsQueue.push({ resolve, reject });
        })
          .then(newAccessToken => {
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            return apiClient(originalRequest);
          })
          .catch(err => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');

        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        // Attempt to refresh the token
        const response = await axios.post(
          `${API_BASE_URL}/auth/refresh/`,
          { refresh: refreshToken },
          {
            headers: {
              'Content-Type': 'application/json'
            }
          }
        );

        const { access, refresh } = response.data;

        // Update stored tokens
        if (access) {
          localStorage.setItem('access_token', access);
        }
        if (refresh) {
          localStorage.setItem('refresh_token', refresh);
        }

        // Update the failed request with new token
        originalRequest.headers.Authorization = `Bearer ${access}`;

        // Process queued requests
        processQueue(null, access);

        isRefreshing = false;

        // Retry the original request with new token
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed - clear tokens and redirect to login
        processQueue(refreshError, null);
        isRefreshing = false;

        // Clear all authentication data
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');

        // Redirect to login page
        // Check if we're not already on the login page to avoid redirect loop
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }

        return Promise.reject(refreshError);
      }
    }

    // For all other errors, reject as-is
    return Promise.reject(error);
  }
);

export default apiClient;
