/**
 * API Interceptors (US-3: Standard User Login, TASK-3.12)
 *
 * Axios request and response interceptors for automatic JWT token management.
 *
 * Features:
 * - Automatic Authorization header attachment
 * - Automatic token refresh on 401 Unauthorized
 * - Concurrent request queuing during token refresh
 * - Retry original request after token refresh
 * - Prevention of infinite retry loops
 * - Race condition handling (multiple 401s simultaneously)
 * - Automatic logout on refresh failure
 *
 * Flow:
 * 1. Request Interceptor: Attach Bearer token to all requests (except auth endpoints)
 * 2. Response Interceptor: Catch 401 errors
 * 3. Token Refresh: Attempt to refresh access token using refresh token
 * 4. Retry: Retry original request with new access token
 * 5. Logout: If refresh fails, clear tokens and redirect to login
 *
 * Usage:
 *   import { setupInterceptors } from './interceptors';
 *   setupInterceptors(apiClient, navigate);
 */

import {
  getAccessToken,
  getRefreshToken,
  updateAccessToken,
  clearTokens,
  isTokenExpired,
} from '../utils/tokenStorage';

// Token refresh state
let isRefreshing = false;
let refreshPromise = null;
let failedRequestsQueue = [];

/**
 * Process queued requests after token refresh
 * @param {Error|null} error - Error if refresh failed
 * @param {string|null} newToken - New access token if refresh succeeded
 */
const processFailedRequestsQueue = (error, newToken = null) => {
  failedRequestsQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(newToken);
    }
  });

  // Clear the queue
  failedRequestsQueue = [];
};

/**
 * Check if URL is an authentication endpoint that should not have token attached
 * @param {string} url - Request URL
 * @returns {boolean}
 */
const isAuthEndpoint = (url) => {
  const authEndpoints = [
    '/api/auth/login/',
    '/api/auth/register/',
    '/api/auth/token/refresh/',
    '/api/auth/verify-email/',
    '/api/auth/resend-verification/',
  ];

  return authEndpoints.some((endpoint) => url.includes(endpoint));
};

/**
 * Setup API interceptors
 * @param {Object} apiClient - Axios instance
 * @param {Function} navigate - React Router navigate function
 * @param {Function} onLogout - Optional callback for logout (e.g., clear auth context)
 */
export const setupInterceptors = (apiClient, navigate, onLogout = null) => {
  // ========================================================================
  // REQUEST INTERCEPTOR
  // ========================================================================
  apiClient.interceptors.request.use(
    (config) => {
      // Skip token attachment for authentication endpoints
      if (isAuthEndpoint(config.url)) {
        return config;
      }

      // Get access token from storage
      const token = getAccessToken();

      // Attach token if available
      if (token) {
        // Check if token is expired (with buffer)
        if (isTokenExpired(token)) {
          console.warn('[Interceptors] Access token is expired, request may fail with 401');
        }

        config.headers.Authorization = `Bearer ${token}`;
      }

      return config;
    },
    (error) => {
      console.error('[Interceptors] Request error:', error);
      return Promise.reject(error);
    }
  );

  // ========================================================================
  // RESPONSE INTERCEPTOR
  // ========================================================================
  apiClient.interceptors.response.use(
    // Success response - pass through
    (response) => response,

    // Error response - handle 401 and token refresh
    async (error) => {
      const originalRequest = error.config;

      // If no response (network error), reject immediately
      if (!error.response) {
        console.error('[Interceptors] Network error:', error.message);
        return Promise.reject(error);
      }

      const { status } = error.response;

      // ========================================================================
      // HANDLE 401 UNAUTHORIZED - ATTEMPT TOKEN REFRESH
      // ========================================================================
      if (status === 401) {
        // Skip refresh for auth endpoints (login, register, etc.)
        if (isAuthEndpoint(originalRequest.url)) {
          console.info('[Interceptors] 401 on auth endpoint, not attempting refresh');
          return Promise.reject(error);
        }

        // Prevent infinite retry loop (only retry once)
        if (originalRequest._retry) {
          console.warn('[Interceptors] Request already retried, not attempting refresh again');

          // Clear tokens and logout
          clearTokens();
          if (onLogout) {
            onLogout();
          }
          navigate('/login', { state: { from: window.location.pathname } });

          return Promise.reject(error);
        }

        // Mark request as retried
        originalRequest._retry = true;

        // ========================================================================
        // HANDLE CONCURRENT REQUESTS DURING TOKEN REFRESH
        // ========================================================================
        if (isRefreshing) {
          console.info('[Interceptors] Token refresh in progress, queuing request');

          // Queue this request to be retried after token refresh completes
          return new Promise((resolve, reject) => {
            failedRequestsQueue.push({ resolve, reject });
          })
            .then((newToken) => {
              // Retry request with new token
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              return apiClient(originalRequest);
            })
            .catch((err) => {
              return Promise.reject(err);
            });
        }

        // ========================================================================
        // INITIATE TOKEN REFRESH
        // ========================================================================
        console.info('[Interceptors] 401 detected, attempting token refresh');

        isRefreshing = true;

        // Get refresh token
        const refreshToken = getRefreshToken();

        if (!refreshToken) {
          console.warn('[Interceptors] No refresh token available, logging out');
          isRefreshing = false;

          clearTokens();
          if (onLogout) {
            onLogout();
          }
          navigate('/login', { state: { from: window.location.pathname } });

          return Promise.reject(error);
        }

        try {
          // Call token refresh endpoint
          // Note: We use apiClient directly (not through authService) to avoid circular dependencies
          const response = await apiClient.post('/api/auth/token/refresh/', {
            refresh: refreshToken,
          });

          const { access } = response.data;

          if (!access) {
            throw new Error('No access token in refresh response');
          }

          console.info('[Interceptors] Token refresh successful');

          // Update stored access token
          updateAccessToken(access);

          // Process all queued requests with new token
          processFailedRequestsQueue(null, access);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return apiClient(originalRequest);
        } catch (refreshError) {
          console.error('[Interceptors] Token refresh failed:', refreshError.message);

          // Process queued requests with error
          processFailedRequestsQueue(refreshError, null);

          // Clear tokens and logout
          clearTokens();
          if (onLogout) {
            onLogout();
          }
          navigate('/login', { state: { from: window.location.pathname } });

          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
          refreshPromise = null;
        }
      }

      // ========================================================================
      // HANDLE OTHER ERROR STATUS CODES
      // ========================================================================

      // 403 Forbidden - Different from 401, don't attempt refresh
      if (status === 403) {
        console.warn('[Interceptors] 403 Forbidden - Access denied');
        // Could be email not verified, insufficient permissions, etc.
      }

      // 429 Too Many Requests - Rate limiting
      if (status === 429) {
        console.warn('[Interceptors] 429 Too Many Requests - Rate limit exceeded');
        const retryAfter = error.response.headers['retry-after'];
        if (retryAfter) {
          console.info(`[Interceptors] Retry after ${retryAfter} seconds`);
        }
      }

      // 500/502/503 Server Errors
      if (status >= 500) {
        console.error('[Interceptors] Server error:', status, error.message);
      }

      // Reject with original error
      return Promise.reject(error);
    }
  );

  console.info('[Interceptors] API interceptors initialized');
};

/**
 * Remove all interceptors (useful for testing or cleanup)
 * @param {Object} apiClient - Axios instance
 */
export const removeInterceptors = (apiClient) => {
  apiClient.interceptors.request.clear();
  apiClient.interceptors.response.clear();

  // Reset state
  isRefreshing = false;
  refreshPromise = null;
  failedRequestsQueue = [];

  console.info('[Interceptors] API interceptors removed');
};

export default setupInterceptors;
