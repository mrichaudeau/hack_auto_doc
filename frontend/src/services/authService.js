import apiClient from './api';

// Local storage keys for JWT tokens and user data
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_DATA_KEY = 'user_data';

/**
 * Authentication service for handling user registration, login, verification, and JWT management
 */
const authService = {
  /**
   * Register a new user
   * @param {Object} userData - User registration data
   * @param {string} userData.email - User email
   * @param {string} userData.first_name - User first name
   * @param {string} userData.last_name - User last name
   * @param {string} userData.password - User password
   * @param {string} userData.password_confirm - Password confirmation
   * @returns {Promise} API response
   */
  register: async (userData) => {
    try {
      const response = await apiClient.post('/auth/register/', userData);
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data || { message: 'Une erreur est survenue' }
      };
    }
  },

  /**
   * Verify email with confirmation key
   * @param {string} key - Email verification key from URL
   * @returns {Promise} API response
   */
  verifyEmail: async (key) => {
    try {
      const response = await apiClient.post(`/auth/verify-email/${key}/`);
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data || { message: 'Erreur de vérification' }
      };
    }
  },

  /**
   * Resend verification email
   * @param {string} email - User email address
   * @returns {Promise} API response
   */
  resendVerification: async (email) => {
    try {
      const response = await apiClient.post('/auth/resend-verification/', { email });
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data || { message: 'Erreur lors de l\'envoi' }
      };
    }
  },

  /**
   * Login user with email and password
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise} API response with tokens and user data
   */
  login: async (email, password) => {
    try {
      const response = await apiClient.post('/auth/login/', { email, password });

      // Store tokens and user data in localStorage
      if (response.data.access_token) {
        localStorage.setItem(ACCESS_TOKEN_KEY, response.data.access_token);
      }
      if (response.data.refresh_token) {
        localStorage.setItem(REFRESH_TOKEN_KEY, response.data.refresh_token);
      }
      if (response.data.user) {
        localStorage.setItem(USER_DATA_KEY, JSON.stringify(response.data.user));
      }

      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data || { message: 'Erreur de connexion' }
      };
    }
  },

  /**
   * Logout user and clear all stored tokens and data
   * @returns {Promise} API response
   */
  logout: async () => {
    try {
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

      if (refreshToken) {
        // Call logout endpoint to blacklist the refresh token
        await apiClient.post('/auth/logout/', { refresh_token: refreshToken });
      }

      // Clear all stored data regardless of API call success
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      localStorage.removeItem(USER_DATA_KEY);

      return { success: true };
    } catch (error) {
      // Even if API call fails, clear local storage
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      localStorage.removeItem(USER_DATA_KEY);

      return {
        success: false,
        error: error.response?.data || { message: 'Erreur de déconnexion' }
      };
    }
  },

  /**
   * Refresh access token using refresh token
   * @returns {Promise} New access token
   */
  refreshToken: async () => {
    try {
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await apiClient.post('/auth/refresh/', { refresh: refreshToken });

      // Update stored tokens (access token and possibly new refresh token if rotation enabled)
      if (response.data.access) {
        localStorage.setItem(ACCESS_TOKEN_KEY, response.data.access);
      }
      if (response.data.refresh) {
        localStorage.setItem(REFRESH_TOKEN_KEY, response.data.refresh);
      }

      return { success: true, data: response.data };
    } catch (error) {
      // If refresh fails, clear everything and force re-login
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      localStorage.removeItem(USER_DATA_KEY);

      return {
        success: false,
        error: error.response?.data || { message: 'Session expirée' }
      };
    }
  },

  /**
   * Get current user data from localStorage
   * @returns {Object|null} User data or null if not logged in
   */
  getCurrentUser: () => {
    const userDataStr = localStorage.getItem(USER_DATA_KEY);
    if (userDataStr) {
      try {
        return JSON.parse(userDataStr);
      } catch (error) {
        console.error('Failed to parse user data:', error);
        return null;
      }
    }
    return null;
  },

  /**
   * Get access token from localStorage
   * @returns {string|null} Access token or null if not available
   */
  getAccessToken: () => {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  /**
   * Get refresh token from localStorage
   * @returns {string|null} Refresh token or null if not available
   */
  getRefreshToken: () => {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  /**
   * Check if user is authenticated (has valid tokens)
   * Note: This only checks for token presence, not validity
   * @returns {boolean} True if tokens exist, false otherwise
   */
  isAuthenticated: () => {
    const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    return !!(accessToken && refreshToken);
  }
};

export default authService;
