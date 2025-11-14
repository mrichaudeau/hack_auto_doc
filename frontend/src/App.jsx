/**
 * Main Application Component
 *
 * Configures routing for the Technology Watch Platform
 *
 * Updated for TASK-3.11: Wrapped with AuthProvider for global authentication state
 * Updated for TASK-3.12: Initialize API interceptors with navigate and logout
 * Updated for US-2: Added SubjectCatalog route for browsing active subjects
 */

import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { AuthProvider } from './contexts/AuthContext';
import { initializeApiClient } from './services/apiClient';
import { useAuth } from './hooks/useAuth';
import ProtectedRoute from './components/ProtectedRoute';
import RegisterPage from './pages/RegisterPage';
import LoginPage from './pages/LoginPage';
import VerifyEmailPage from './pages/VerifyEmailPage';
import ResendVerificationPage from './pages/ResendVerificationPage';
import HomePage from './pages/HomePage';
import DashboardPage from './pages/DashboardPage';
import SubjectCatalogPage from './pages/SubjectCatalogPage';
import './App.css';

/**
 * App Routes Component
 * Separated to access useNavigate and useAuth hooks inside Router context
 */
function AppRoutes() {
  const navigate = useNavigate();
  const { logout } = useAuth();

  console.log('[AppRoutes] Component rendering');

  // Initialize API interceptors on mount
  useEffect(() => {
    console.info('[App] Initializing API interceptors');
    initializeApiClient(navigate, logout);
  }, [navigate, logout]);

  return (
    <Routes>
      {/* Home Page */}
      <Route path="/" element={<HomePage />} />

      {/* Public Routes */}
      <Route path="/subjects" element={<SubjectCatalogPage />} />

      {/* Authentication Routes */}
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route path="/resend-verification" element={<ResendVerificationPage />} />

      {/* Protected Routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />

      {/* Redirect unknown routes to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  console.log('[App] Main App component rendering');

  return (
    <Router>
      {/* AuthProvider must be inside Router because it uses useNavigate */}
      <AuthProvider>
        {/* AppRoutes must be inside AuthProvider to access useAuth */}
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}

export default App;
