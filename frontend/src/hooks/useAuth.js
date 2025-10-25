import { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';

/**
 * Custom hook to access authentication context
 * Provides easy access to auth state and functions from any component
 *
 * @returns {Object} Authentication context with user, loading, isAuthenticated, login, logout, checkAuth
 * @throws {Error} If used outside of AuthProvider
 *
 * @example
 * const { user, isAuthenticated, login, logout } = useAuth();
 *
 * // Check if user is authenticated
 * if (isAuthenticated) {
 *   console.log('User:', user.email);
 * }
 *
 * // Login
 * const result = await login(email, password);
 * if (result.success) {
 *   // Handle successful login
 * }
 *
 * // Logout
 * await logout();
 */
export const useAuth = () => {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
};

export default useAuth;
