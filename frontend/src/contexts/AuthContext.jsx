import { createContext, useState, useEffect, useCallback } from 'react';
import authService from '../services/authService';

/**
 * Authentication Context
 * Provides global authentication state and functions to the entire app
 */
export const AuthContext = createContext({
  user: null,
  loading: true,
  isAuthenticated: false,
  login: async () => {},
  logout: async () => {},
  checkAuth: () => {}
});

/**
 * Authentication Provider Component
 * Wraps the application to provide authentication context to all children
 */
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  /**
   * Check authentication status on mount and update state
   * Reads from localStorage to restore authentication state
   */
  const checkAuth = useCallback(() => {
    try {
      const authenticated = authService.isAuthenticated();
      const userData = authService.getCurrentUser();

      setIsAuthenticated(authenticated);
      setUser(userData);
    } catch (error) {
      console.error('Error checking authentication:', error);
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Login function
   * Calls authService.login, updates context state, and handles errors
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise<Object>} Result with success status and data/error
   */
  const login = useCallback(async (email, password) => {
    try {
      const result = await authService.login(email, password);

      if (result.success) {
        // Update context state with new user data
        setUser(result.data.user);
        setIsAuthenticated(true);
      }

      return result;
    } catch (error) {
      console.error('Login error:', error);
      return {
        success: false,
        error: { message: 'Erreur de connexion' }
      };
    }
  }, []);

  /**
   * Logout function
   * Calls authService.logout, clears context state
   * @returns {Promise<Object>} Result with success status
   */
  const logout = useCallback(async () => {
    try {
      const result = await authService.logout();

      // Clear context state regardless of API call result
      setUser(null);
      setIsAuthenticated(false);

      return result;
    } catch (error) {
      console.error('Logout error:', error);

      // Still clear state even if API call fails
      setUser(null);
      setIsAuthenticated(false);

      return {
        success: false,
        error: { message: 'Erreur de déconnexion' }
      };
    }
  }, []);

  /**
   * Effect: Check authentication on component mount
   * Restores authentication state from localStorage
   */
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  /**
   * Effect: Listen for storage events (for multi-tab synchronization)
   * Updates auth state when localStorage changes in another tab
   */
  useEffect(() => {
    const handleStorageChange = (e) => {
      // Check if auth-related keys changed
      if (
        e.key === 'access_token' ||
        e.key === 'refresh_token' ||
        e.key === 'user_data'
      ) {
        checkAuth();
      }
    };

    window.addEventListener('storage', handleStorageChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [checkAuth]);

  // Context value to be provided to consumers
  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    logout,
    checkAuth
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
