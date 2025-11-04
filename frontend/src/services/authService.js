/**
 * Authentication Service
 *
 * Handles all authentication-related API calls including registration,
 * login, email verification, and password reset.
 */

import apiClient from './apiClient';

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
   * Login with email and password
   *
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise<Object>} Login result with tokens
   */
  async login(email, password) {
    try {
      const response = await apiClient.post('/api/auth/login/', { email, password });

      // Store tokens in localStorage
      if (response.data.access) {
        localStorage.setItem('access_token', response.data.access);
      }
      if (response.data.refresh) {
        localStorage.setItem('refresh_token', response.data.refresh);
      }

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
   * Logout current user
   * Clears tokens from localStorage
   */
  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },

  /**
   * Check if user is authenticated
   *
   * @returns {boolean} True if user has valid token
   */
  isAuthenticated() {
    return !!localStorage.getItem('access_token');
  },

  /**
   * Get current user data from localStorage
   *
   * @returns {Object|null} User data or null
   */
  getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },
};

export default authService;
