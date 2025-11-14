/**
 * Protected Route Component (US-3: Standard User Login, TASK-3.13)
 *
 * Wraps protected routes and ensures only authenticated users can access them.
 *
 * Features:
 * - Checks authentication status from AuthContext
 * - Redirects unauthenticated users to login page
 * - Preserves intended destination URL for post-login redirect
 * - Shows loading state during authentication check
 * - Prevents flash of content during authentication verification
 * - Works with React Router v6 Navigate component
 * - Supports nested routes
 *
 * Usage:
 *   <Route
 *     path="/dashboard"
 *     element={
 *       <ProtectedRoute>
 *         <DashboardPage />
 *       </ProtectedRoute>
 *     }
 *   />
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

/**
 * Loading Spinner Component
 * Displayed while authentication status is being verified
 */
function LoadingSpinner() {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: '#f5f5f5',
      }}
    >
      <div
        style={{
          width: '48px',
          height: '48px',
          border: '4px solid #e0e0e0',
          borderTop: '4px solid #3b82f6',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
        }}
      />
      <p
        style={{
          marginTop: '16px',
          fontSize: '16px',
          color: '#666',
        }}
      >
        Verifying authentication...
      </p>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

/**
 * Protected Route Component
 *
 * @param {Object} props
 * @param {React.ReactNode} props.children - Child components to render if authenticated
 * @returns {React.ReactElement} Children if authenticated, Navigate to login if not, or LoadingSpinner
 */
export default function ProtectedRoute({ children }) {
  const { user, loading, isAuthenticated } = useAuth();
  const location = useLocation();

  // Show loading spinner while checking authentication
  // This prevents flash of login redirect or content
  if (loading) {
    console.info('[ProtectedRoute] Checking authentication status...');
    return <LoadingSpinner />;
  }

  // If not authenticated, redirect to login with return URL
  if (!isAuthenticated || !user) {
    console.warn(
      '[ProtectedRoute] User not authenticated, redirecting to login',
      'Intended destination:',
      location.pathname
    );

    // Preserve the intended destination in location state
    // After successful login, user can be redirected back here
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // User is authenticated, render protected content
  console.info('[ProtectedRoute] User authenticated, rendering protected content');
  return children;
}
