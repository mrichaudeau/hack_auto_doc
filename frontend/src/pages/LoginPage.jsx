/**
 * Login Page Component (Placeholder)
 *
 * This is a placeholder page for the login functionality.
 * Will be implemented in a future User Story.
 */

import { Link } from 'react-router-dom';
import './LoginPage.css';

const LoginPage = () => {
  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1 className="login-title">Sign In</h1>
          <p className="login-subtitle">Access your Technology Watch account</p>
        </div>

        <div className="placeholder-content">
          <div className="placeholder-icon">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
          </div>
          <h2 className="placeholder-title">Login Feature Coming Soon</h2>
          <p className="placeholder-text">
            The login functionality will be implemented in a future User Story.
          </p>
          <p className="placeholder-text">
            For now, you can create a new account to get started.
          </p>
        </div>

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
