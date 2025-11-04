/**
 * Verify Email Page Component (Placeholder)
 *
 * This is a placeholder page for email verification functionality.
 * Will be implemented in a future User Story.
 */

import { useLocation, Link } from 'react-router-dom';
import './VerifyEmailPage.css';

const VerifyEmailPage = () => {
  const location = useLocation();
  const email = location.state?.email || 'your email';

  return (
    <div className="verify-email-page">
      <div className="verify-email-container">
        <div className="verify-email-header">
          <h1 className="verify-email-title">Check Your Email</h1>
          <p className="verify-email-subtitle">Verification email sent to {email}</p>
        </div>

        <div className="placeholder-content">
          <div className="placeholder-icon success">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
          </div>
          <h2 className="placeholder-title">Registration Successful!</h2>
          <p className="placeholder-text">
            We've sent a verification email to <strong>{email}</strong>.
          </p>
          <p className="placeholder-text">
            Please check your inbox and click the verification link to activate your account.
          </p>
          <p className="placeholder-text info">
            The email verification feature will be fully implemented in a future User Story.
          </p>
        </div>

        <div className="action-section">
          <div className="action-card">
            <h3>Didn't receive the email?</h3>
            <p>Check your spam folder or request a new verification email.</p>
            <button className="action-button" disabled>
              Resend Verification Email (Coming Soon)
            </button>
          </div>
        </div>

        <div className="verify-email-footer">
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

export default VerifyEmailPage;
