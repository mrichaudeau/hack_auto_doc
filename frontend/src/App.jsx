import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/routes/ProtectedRoute';
import RegisterPage from './pages/auth/RegisterPage';
import EmailConfirmationPendingPage from './pages/auth/EmailConfirmationPendingPage';
import EmailVerifiedPage from './pages/auth/EmailVerifiedPage';
import LoginPage from './pages/auth/LoginPage';
import DashboardPage from './pages/DashboardPage';
import './App.css';

/**
 * Main App Component - TASK-1.14 & TASK-2.15
 * Configures routing for authentication and protected pages
 * Wrapped with AuthProvider for global authentication state
 */
function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Routes */}
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/email-confirmation-pending" element={<EmailConfirmationPendingPage />} />
          <Route path="/verify-email/:key" element={<EmailVerifiedPage />} />
          <Route path="/login" element={<LoginPage />} />

          {/* Protected Routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />

          {/* Default redirect based on authentication status */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* Catch all - redirect to dashboard (will redirect to login if not authenticated) */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
