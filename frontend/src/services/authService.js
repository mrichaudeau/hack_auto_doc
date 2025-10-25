import apiClient from './api';

/**
 * Authentication service for handling user registration, login, and verification
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
  }
};

export default authService;
