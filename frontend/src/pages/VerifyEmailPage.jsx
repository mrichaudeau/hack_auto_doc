/**
 * Email Verification Page Component
 *
 * Handles the email verification flow when users click the verification link from their email.
 * Extracts token from URL, calls API, and displays appropriate state (loading, success, error).
 */

import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { verifyEmail, EmailVerificationError } from '../services/emailVerificationApi';
import './VerifyEmailPage.css';

/**
 * Verification state types
 * @typedef {'loading' | 'success' | 'error'} VerificationState
 */

/**
 * Error information structure
 * @typedef {Object} VerificationError
 * @property {string} code - Error code identifier
 * @property {string} message - Main error message
 * @property {string} subMessage - Additional context message
 * @property {'login' | 'resend' | 'retry'} action - Action button type
 */

const VerifyEmailPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [state, setState] = useState('loading');
  const [error, setError] = useState(null);

  const token = searchParams.get('token');

  /**
   * Handles email verification API call
   * Processes different error scenarios and updates UI state accordingly
   */
  const handleVerification = async () => {
    // Check for missing token
    if (!token) {
      setError({
        code: 'token_missing',
        message: 'Invalid verification link.',
        subMessage: 'The verification link is invalid or malformed.',
        action: 'resend',
      });
      setState('error');
      return;
    }

    setState('loading');
    setError(null);

    try {
      await verifyEmail(token);
      setState('success');
    } catch (err) {
      if (err instanceof EmailVerificationError) {
        const errorCode = err.errorCode;

        if (errorCode === 'token_invalid') {
          setError({
            code: errorCode,
            message: 'Invalid verification link.',
            subMessage: 'The verification link is invalid or malformed.',
            action: 'resend',
          });
        } else if (errorCode === 'token_used') {
          setError({
            code: errorCode,
            message: 'This verification link has already been used.',
            subMessage: 'Your email may already be verified.',
            action: 'login',
          });
        } else if (errorCode === 'token_expired') {
          setError({
            code: errorCode,
            message: 'Verification link expired.',
            subMessage: 'This verification link has expired. Please request a new one.',
            action: 'resend',
          });
        } else if (errorCode === 'token_required') {
          setError({
            code: errorCode,
            message: 'Invalid verification link.',
            subMessage: 'The verification link is invalid or malformed.',
            action: 'resend',
          });
        } else if (!err.statusCode) {
          // Network error (no status code means network failure)
          setError({
            code: errorCode || 'network_error',
            message: 'Connection error.',
            subMessage: 'Please check your internet connection and try again.',
            action: 'retry',
          });
        } else {
          // Unknown API error (has status code but unknown error code)
          setError({
            code: errorCode || 'unknown',
            message: 'Connection error.',
            subMessage: 'Please check your internet connection and try again.',
            action: 'retry',
          });
        }
      } else {
        // Unexpected error (not EmailVerificationError)
        setError({
          code: 'unknown',
          message: 'An unexpected error occurred.',
          subMessage: 'Please try again later.',
          action: 'retry',
        });
      }
      setState('error');
    }
  };

  // Run verification on component mount or when token changes
  useEffect(() => {
    handleVerification();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  /**
   * Handles action button clicks based on error state
   */
  const handleAction = () => {
    if (error?.action === 'login') {
      navigate('/login');
    } else if (error?.action === 'resend') {
      navigate('/resend-verification');
    } else if (error?.action === 'retry') {
      handleVerification();
    }
  };

  /**
   * Get button text based on action type
   */
  const getActionButtonText = () => {
    if (error?.action === 'login') return 'Go to Login';
    if (error?.action === 'resend') return 'Resend Verification Email';
    if (error?.action === 'retry') return 'Retry';
    return 'Continue';
  };

  return (
    <div className="verify-email-page">
      <div className="verify-email-container">
        {/* Loading State */}
        {state === 'loading' && (
          <div className="verify-email-content">
            <div className="loading-spinner">
              <div className="spinner"></div>
            </div>
            <h2 className="verify-email-title">Verifying your email address...</h2>
            <p className="verify-email-text">Please wait while we verify your account.</p>
          </div>
        )}

        {/* Success State */}
        {state === 'success' && (
          <div className="verify-email-content">
            <div className="icon-container success">
              <svg
                className="icon"
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
            <h2 className="verify-email-title">Email verified successfully!</h2>
            <p className="verify-email-text">You can now log in to your account.</p>
            <button onClick={() => navigate('/login')} className="action-button primary">
              Go to Login
            </button>
          </div>
        )}

        {/* Error State */}
        {state === 'error' && error && (
          <div className="verify-email-content">
            <div className={`icon-container ${error.action === 'retry' ? 'error' : 'warning'}`}>
              {error.action === 'retry' ? (
                // Error Icon (X Circle)
                <svg
                  className="icon"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="15" y1="9" x2="9" y2="15"></line>
                  <line x1="9" y1="9" x2="15" y2="15"></line>
                </svg>
              ) : (
                // Warning Icon (Exclamation Triangle)
                <svg
                  className="icon"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path>
                  <line x1="12" y1="9" x2="12" y2="13"></line>
                  <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
              )}
            </div>
            <h2 className="verify-email-title">{error.message}</h2>
            <p className="verify-email-text">{error.subMessage}</p>
            <button onClick={handleAction} className="action-button primary">
              {getActionButtonText()}
            </button>
            {error.action !== 'login' && (
              <div className="secondary-actions">
                <Link to="/" className="secondary-link">
                  Back to Home
                </Link>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default VerifyEmailPage;
