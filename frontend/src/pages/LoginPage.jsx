/**
 * Login Page Component (US-3: Standard User Login)
 *
 * Provides user authentication via email/password login.
 * Integrated with AuthContext for global authentication state.
 * Supports post-login redirect to intended destination (TASK-3.13).
 */

import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import LoginForm from '../components/auth/LoginForm';
import Alert from '../components/common/Alert';
import './LoginPage.css';

const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, loading, error, clearError } = useAuth();

  // Get the intended destination from location state (set by ProtectedRoute)
  // Default to '/dashboard' if no intended destination
  const from = location.state?.from?.pathname || '/dashboard';

  /**
   * Handle login form submission
   */
  const handleLogin = async (email, password) => {
    try {
      await login(email, password);

      // On successful login, redirect to intended destination
      console.info('[LoginPage] Login successful, redirecting to:', from);
      navigate(from, { replace: true });
    } catch (err) {
      // Error is handled by AuthContext and displayed via error prop
      console.error('[LoginPage] Login failed:', err.message);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1 className="login-title">Sign In</h1>
          <p className="login-subtitle">Access your Technology Watch account</p>
        </div>

        {/* Show alert if redirected from protected route */}
        {location.state?.from && (
          <Alert type="info" onClose={clearError}>
            Please sign in to access {location.state.from.pathname}
          </Alert>
        )}

        {/* Show error alert if login failed */}
        {error && (
          <Alert type="error" onClose={clearError}>
            {error}
          </Alert>
        )}

        {/* Login Form */}
        <LoginForm onSubmit={handleLogin} loading={loading} error={error} />

        <div className="login-footer">
          <p className="footer-text">
            Don't have an account?{' '}
            <Link to="/register" className="footer-link">
              Create one
            </Link>
          </p>
          <p className="footer-text">
            <Link to="/" className="footer-link">
              Back to Home
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
