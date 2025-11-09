/**
 * Authentication Service
 *
 * Handles all authentication-related API calls including registration,
 * login, email verification, and password reset.
 *
 * Updated for TASK-3.10: Now uses tokenStorage utilities for better
 * error handling and token management.
 */

import apiClient from './apiClient';
import {
  saveTokens,
  getAccessToken,
  getUserData,
  clearTokens,
  isAuthenticated as checkAuthenticated,
} from '../utils/tokenStorage';

const authService = {
  /**
   * Register a new user account
   *
   * @param {Object} userData - User registration data
   * @param {string} userData.email - User email address
   * @param {string} userData.password - User password
   * @param {string} userData.password_confirm - Password confirmation
   * @param {string} userData.first_name - User first name (optional)
   * @param {string} userData.last_name - User last name (optional)
   * @returns {Promise<Object>} User data and success message
   */
  async register(userData) {
    try {
      const response = await apiClient.post('/api/auth/register/', userData);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data || { message: error.message },
      };
    }
  },

  /**
   * Verify email address with token
   *
   * @param {string} token - Email verification token
   * @returns {Promise<Object>} Verification result
   */
  async verifyEmail(token) {
    try {
      const response = await apiClient.post('/api/auth/verify-email/', { token });
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data || { message: error.message },
      };
    }
  },

  /**
   * Resend verification email
   *
   * @param {string} email - User email address
   * @returns {Promise<Object>} Resend result
   */
  async resendVerificationEmail(email) {
    try {
      const response = await apiClient.post('/api/auth/resend-verification/', { email });
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data || { message: error.message },
      };
    }
  },

  /**
   * Login with email and password (US-3: Standard User Login, TASK-3.9)
   *
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise<Object>} Login result with tokens and user data
   * @throws {Error} with user-friendly error message
   */
  async login(email, password) {
    try {
      const response = await apiClient.post('/api/auth/login/', { email, password });

      // Store tokens using tokenStorage utilities (TASK-3.10)
      // API returns: { access_token, refresh_token, user }
      const { access_token, refresh_token, user } = response.data;

      if (access_token && refresh_token) {
        saveTokens(access_token, refresh_token, user);
      }

      return response.data;
    } catch (error) {
      // Enhanced error handling for all login error scenarios
      if (error.response) {
        const status = error.response.status;
        const data = error.response.data;

        switch (status) {
          case 400:
            // Validation error (missing/invalid fields)
            throw new Error(data.error || 'Please provide valid email and password');

          case 401:
            // Invalid credentials
            throw new Error(data.error || 'Invalid email or password');

          case 403:
            // Email not verified
            throw new Error(data.error || 'Please verify your email before logging in');

          case 429:
            // Rate limit exceeded
            const retryAfter = error.response.headers['retry-after'];
            if (retryAfter) {
              const seconds = parseInt(retryAfter, 10);
              const minutes = Math.ceil(seconds / 60);
              throw new Error(`Too many login attempts. Please try again in ${minutes} minute${minutes > 1 ? 's' : ''}`);
            }
            throw new Error(data.message || 'Too many login attempts. Please try again later');

          case 500:
          case 502:
          case 503:
            // Server error
            throw new Error('Server error. Please try again later');

          default:
            throw new Error(data.error || data.message || 'An unexpected error occurred');
        }
      } else if (error.request) {
        // Network error (request made but no response received)
        throw new Error('Connection error. Please check your internet connection');
      } else {
        // Other error (e.g., request setup error)
        throw new Error(error.message || 'An unexpected error occurred');
      }
    }
  },

  /**
   * Logout current user
   * Clears tokens using tokenStorage utilities (TASK-3.10)
   */
  logout() {
    clearTokens();
  },

  /**
   * Check if user is authenticated
   * Uses tokenStorage utilities with JWT expiration check (TASK-3.10)
   *
   * @returns {boolean} True if user has valid, non-expired token
   */
  isAuthenticated() {
    return checkAuthenticated();
  },

  /**
   * Get current user data from storage
   * Uses tokenStorage utilities (TASK-3.10)
   *
   * @returns {Object|null} User data or null
   */
  getCurrentUser() {
    return getUserData();
  },

  /**
   * Get access token
   * Uses tokenStorage utilities (TASK-3.10)
   *
   * @returns {string|null} Access token or null
   */
  getAccessToken() {
    return getAccessToken();
  },
};

export default authService;
