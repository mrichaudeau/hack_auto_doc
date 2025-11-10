/**
 * Authentication Context Provider (US-3: Standard User Login, TASK-3.11)
 *
 * Centralized authentication state management using React Context API.
 * Provides global access to user state, authentication status, and auth functions.
 *
 * Features:
 * - Global authentication state (user, loading, error)
 * - Login/logout functions
 * - Session restoration from stored tokens
 * - Automatic token validation
 * - Optimized with useMemo to prevent unnecessary re-renders
 *
 * Usage:
 *   // Wrap app with AuthProvider in App.jsx
 *   <AuthProvider>
 *     <YourApp />
 *   </AuthProvider>
 *
 *   // Use in components with useAuth hook
 *   const { user, login, logout, loading, error } = useAuth();
 */

import React, { createContext, useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../services/authService';
import {
  saveTokens,
  clearTokens,
  getUserData,
  isAuthenticated as checkAuthenticated,
} from '../utils/tokenStorage';

/**
 * Authentication Context
 * Provides authentication state and functions to all child components
 */
export const AuthContext = createContext({
  user: null,
  loading: false,
  error: null,
  isAuthenticated: false,
  login: async () => {},
  logout: () => {},
  clearError: () => {},
  updateUser: () => {},
});

/**
 * Authentication Provider Component
 * Manages authentication state and provides it to the component tree
 *
 * @param {Object} props
 * @param {React.ReactNode} props.children - Child components
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // Start with loading true for session restoration
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  /**
   * Restore session from stored tokens on mount
   * Runs once when provider mounts
   */
  useEffect(() => {
    const restoreSession = async () => {
      try {
        // Check if user has valid token
        if (checkAuthenticated()) {
          // Get user data from storage
          const userData = getUserData();

          if (userData) {
            setUser(userData);
            console.info('[AuthContext] Session restored from storage');
          } else {
            // Token exists but no user data - clear invalid state
            console.warn('[AuthContext] Token found but no user data, clearing session');
            clearTokens();
          }
        } else {
          console.info('[AuthContext] No valid session found');
        }
      } catch (error) {
        console.error('[AuthContext] Failed to restore session:', error);
        // Clear potentially corrupted tokens
        clearTokens();
      } finally {
        setLoading(false);
      }
    };

    restoreSession();
  }, []); // Empty dependency array - run once on mount

  /**
   * Login function
   * Authenticates user and updates state
   *
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise<Object>} Login response data
   * @throws {Error} Login error with user-friendly message
   */
  const login = useCallback(async (email, password) => {
    setLoading(true);
    setError(null);

    try {
      console.info('[AuthContext] Attempting login for:', email);

      // Call authService login (which handles API call and token storage)
      const response = await authService.login(email, password);

      // Update user state with returned user data
      if (response.user) {
        setUser(response.user);
        console.info('[AuthContext] Login successful for user:', response.user.email);
      }

      return response;
    } catch (err) {
      console.error('[AuthContext] Login failed:', err.message);
      setError(err.message);
      throw err; // Re-throw so components can handle it
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Logout function
   * Clears authentication state and redirects to login
   */
  const logout = useCallback(() => {
    console.info('[AuthContext] Logging out user:', user?.email);

    // Clear tokens and user state
    clearTokens();
    setUser(null);
    setError(null);

    // Redirect to login page
    navigate('/login');
  }, [user, navigate]);

  /**
   * Clear error state
   * Useful for dismissing error messages
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Update user data
   * Updates user state with new data (e.g., after profile update)
   *
   * @param {Object} userData - Updated user data
   */
  const updateUser = useCallback((userData) => {
    setUser(userData);
    // Also update in storage
    saveTokens(null, null, userData); // Only update user data, keep tokens
  }, []);

  /**
   * Derived authentication status
   * Computed from user state
   */
  const isAuthenticated = useMemo(() => {
    return !!user && checkAuthenticated();
  }, [user]);

  /**
   * Context value object
   * Memoized to prevent unnecessary re-renders of consuming components
   */
  const value = useMemo(
    () => ({
      user,
      loading,
      error,
      isAuthenticated,
      login,
      logout,
      clearError,
      updateUser,
    }),
    [user, loading, error, isAuthenticated, login, logout, clearError, updateUser]
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * PropTypes for AuthProvider
 */
AuthProvider.propTypes = {
  children: React.ReactNode,
};

export default AuthContext;
