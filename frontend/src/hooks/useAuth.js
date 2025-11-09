/**
 * useAuth Hook (US-3: Standard User Login, TASK-3.11)
 *
 * Custom React hook for accessing authentication context.
 * Provides type-safe access to authentication state and functions.
 *
 * Features:
 * - Access to user profile
 * - Authentication status
 * - Login/logout functions
 * - Loading and error states
 * - Throws error if used outside AuthProvider
 *
 * Usage:
 *   import { useAuth } from '../hooks/useAuth';
 *
 *   function MyComponent() {
 *     const { user, isAuthenticated, login, logout, loading, error } = useAuth();
 *
 *     if (loading) return <div>Loading...</div>;
 *     if (error) return <div>Error: {error}</div>;
 *
 *     return (
 *       <div>
 *         {isAuthenticated ? (
 *           <div>
 *             <p>Welcome, {user.first_name}!</p>
 *             <button onClick={logout}>Logout</button>
 *           </div>
 *         ) : (
 *           <button onClick={() => login(email, password)}>Login</button>
 *         )}
 *       </div>
 *     );
 *   }
 */

import { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';

/**
 * useAuth Hook
 * Provides access to authentication context
 *
 * @returns {Object} Authentication context
 * @returns {Object|null} context.user - Current user object or null
 * @returns {boolean} context.loading - Loading state
 * @returns {string|null} context.error - Error message or null
 * @returns {boolean} context.isAuthenticated - Authentication status
 * @returns {Function} context.login - Login function (email, password) => Promise
 * @returns {Function} context.logout - Logout function () => void
 * @returns {Function} context.clearError - Clear error function () => void
 * @returns {Function} context.updateUser - Update user function (userData) => void
 *
 * @throws {Error} If used outside of AuthProvider
 */
export function useAuth() {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error(
      'useAuth must be used within an AuthProvider. ' +
      'Make sure your component is wrapped with <AuthProvider>.'
    );
  }

  return context;
}

/**
 * Hook for accessing only user data
 * Useful when you only need user information
 *
 * @returns {Object|null} Current user object or null
 */
export function useUser() {
  const { user } = useAuth();
  return user;
}

/**
 * Hook for accessing authentication status
 * Useful for conditional rendering based on auth status
 *
 * @returns {boolean} True if user is authenticated
 */
export function useIsAuthenticated() {
  const { isAuthenticated } = useAuth();
  return isAuthenticated;
}

/**
 * Hook for accessing only loading state
 * Useful for showing loading indicators
 *
 * @returns {boolean} True if authentication operation is in progress
 */
export function useAuthLoading() {
  const { loading } = useAuth();
  return loading;
}

/**
 * Hook for accessing only error state
 * Useful for error handling and display
 *
 * @returns {string|null} Error message or null
 */
export function useAuthError() {
  const { error } = useAuth();
  return error;
}

// Export default useAuth hook
export default useAuth;
