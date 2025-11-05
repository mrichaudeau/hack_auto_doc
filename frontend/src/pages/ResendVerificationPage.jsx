/**
 * Resend Verification Email Page Component
 *
 * Allows users to request a new verification email if they haven't received
 * or lost the original one. Handles rate limiting, error states, and success feedback.
 */

import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { resendVerificationEmail, EmailVerificationError } from '../services/emailVerificationApi';
import './VerifyEmailPage.css';

/**
 * Form state types
 * @typedef {'idle' | 'submitting' | 'success' | 'error'} FormState
 */

/**
 * Error information structure
 * @typedef {Object} ErrorInfo
 * @property {string} type - Error type identifier
 * @property {string} message - Main error message
 * @property {string} [subMessage] - Additional context message
 * @property {number} [retryAfter] - Seconds until can retry (for rate limit)
 */

const ResendVerificationPage = () => {
  const navigate = useNavigate();

  // Form state
  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState('');
  const [formState, setFormState] = useState('idle');

  // Success state
  const [attemptsRemaining, setAttemptsRemaining] = useState(null);

  // Error state
  const [error, setError] = useState(null);
  const [rateLimitRetryAfter, setRateLimitRetryAfter] = useState(null);

  /**
   * Validates email format using regex
   * @param {string} email - Email address to validate
   * @returns {boolean} True if valid email format
   */
  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  /**
   * Handles email input blur - validates format
   */
  const handleEmailBlur = () => {
    if (email && !validateEmail(email)) {
      setEmailError('Please enter a valid email address.');
    } else {
      setEmailError('');
    }
  };

  /**
   * Handles form submission - calls API to resend verification email
   * @param {Event} e - Form submit event
   */
  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate before submission
    if (!email || !validateEmail(email)) {
      setEmailError('Please enter a valid email address.');
      return;
    }

    setFormState('submitting');
    setError(null);

    try {
      const result = await resendVerificationEmail(email);
      setFormState('success');
      setAttemptsRemaining(result.attempts_remaining);
      setEmail(''); // Clear form
      setEmailError('');
    } catch (err) {
      setFormState('error');

      if (err instanceof EmailVerificationError) {
        if (err.errorCode === 'rate_limit_exceeded') {
          setError({
            type: 'rate_limit',
            message: 'Too many requests. Please try again later.',
            subMessage: err.details?.retry_after_seconds
              ? `You can try again in ${formatTime(err.details.retry_after_seconds)}.`
              : 'Please wait before trying again.',
            retryAfter: err.details?.retry_after_seconds,
          });
          setRateLimitRetryAfter(err.details?.retry_after_seconds || 0);
        } else if (err.errorCode === 'user_not_found' || err.details?.email) {
          // Backend may return email field error for non-existent user
          setError({
            type: 'not_found',
            message: 'No account found with this email address.',
            subMessage: 'Please check your email or sign up for a new account.',
          });
        } else if (err.errorCode === 'already_verified') {
          setError({
            type: 'already_verified',
            message: 'This email address is already verified.',
            subMessage: 'You can proceed to login.',
          });
        } else if (!err.statusCode) {
          // Network error
          setError({
            type: 'network',
            message: 'Connection error. Please try again.',
            subMessage: 'Please check your internet connection.',
          });
        } else {
          // Unknown API error
          setError({
            type: 'unknown',
            message: 'An error occurred. Please try again.',
            subMessage: 'If the problem persists, please contact support.',
          });
        }
      } else {
        // Unexpected error
        setError({
          type: 'unknown',
          message: 'An unexpected error occurred.',
          subMessage: 'Please try again later.',
        });
      }
    }
  };

  /**
   * Countdown timer for rate limit cooldown
   */
  useEffect(() => {
    if (rateLimitRetryAfter > 0) {
      const timer = setInterval(() => {
        setRateLimitRetryAfter((prev) => {
          if (prev <= 1) {
            // Countdown finished, reset error state to allow retry
            setError(null);
            setFormState('idle');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [rateLimitRetryAfter]);

  /**
   * Formats seconds into human-readable time string
   * @param {number} seconds - Time in seconds
   * @returns {string} Formatted time (e.g., "2 hours and 15 minutes")
   */
  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return minutes > 0
        ? `${hours} hour${hours > 1 ? 's' : ''} and ${minutes} minute${minutes !== 1 ? 's' : ''}`
        : `${hours} hour${hours > 1 ? 's' : ''}`;
    }
    if (minutes > 0) {
      return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
    }
    return `${secs} second${secs !== 1 ? 's' : ''}`;
  };

  /**
   * Handles retry action - resets error state to show form again
   */
  const handleRetry = () => {
    setError(null);
    setFormState('idle');
  };

  /**
   * Handles send another email - resets success state to show form
   */
  const handleSendAnother = () => {
    setFormState('idle');
    setAttemptsRemaining(null);
  };

  return (
    <div className="verify-email-page">
      <div className="verify-email-container">
        <h1 className="verify-email-title">Resend Verification Email</h1>

        {/* Initial Form State */}
        {formState === 'idle' && (
          <div className="verify-email-content">
            <p className="verify-email-text">
              Enter your email address to receive a new verification link.
            </p>

            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: '1.5rem', textAlign: 'left' }}>
                <label
                  htmlFor="email"
                  style={{
                    display: 'block',
                    fontSize: '0.9375rem',
                    fontWeight: 600,
                    color: '#374151',
                    marginBottom: '0.5rem',
                  }}
                >
                  Email Address
                </label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onBlur={handleEmailBlur}
                  disabled={rateLimitRetryAfter > 0}
                  className="email-input"
                  style={{
                    width: '100%',
                    padding: '0.75rem 1rem',
                    fontSize: '1rem',
                    border: emailError ? '1px solid #ef4444' : '1px solid #d1d5db',
                    borderRadius: '0.5rem',
                    outline: 'none',
                    transition: 'border-color 0.2s',
                  }}
                  placeholder="you@example.com"
                  required
                  aria-invalid={emailError ? 'true' : 'false'}
                  aria-describedby={emailError ? 'email-error' : undefined}
                />
                {emailError && (
                  <p
                    id="email-error"
                    style={{
                      marginTop: '0.5rem',
                      fontSize: '0.875rem',
                      color: '#ef4444',
                    }}
                  >
                    {emailError}
                  </p>
                )}
              </div>

              <button
                type="submit"
                disabled={!email || !!emailError || rateLimitRetryAfter > 0}
                className="action-button primary"
                style={{
                  opacity: !email || emailError || rateLimitRetryAfter > 0 ? 0.5 : 1,
                  cursor:
                    !email || emailError || rateLimitRetryAfter > 0
                      ? 'not-allowed'
                      : 'pointer',
                }}
              >
                Send Verification Email
              </button>
            </form>

            <div className="secondary-actions">
              <Link to="/" className="secondary-link">
                Back to Home
              </Link>
            </div>
          </div>
        )}

        {/* Submitting State */}
        {formState === 'submitting' && (
          <div className="verify-email-content">
            <div className="loading-spinner">
              <div className="spinner"></div>
            </div>
            <h2 className="verify-email-title">Sending email...</h2>
            <p className="verify-email-text">Please wait while we send your verification email.</p>
          </div>
        )}

        {/* Success State */}
        {formState === 'success' && (
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
            <h2 className="verify-email-title">Verification email sent successfully!</h2>
            <p className="verify-email-text">Please check your inbox and spam folder.</p>

            {attemptsRemaining !== null && (
              <p
                style={{
                  fontSize: '0.9375rem',
                  color: '#6b7280',
                  marginBottom: '1.5rem',
                }}
              >
                You have {attemptsRemaining} attempt{attemptsRemaining !== 1 ? 's' : ''} remaining
                (out of 3).
              </p>
            )}

            {attemptsRemaining > 0 && (
              <button onClick={handleSendAnother} className="action-button primary">
                Send Another Email
              </button>
            )}

            <div className="secondary-actions">
              <Link to="/login" className="secondary-link">
                Go to Login
              </Link>
            </div>
          </div>
        )}

        {/* Error State */}
        {formState === 'error' && error && (
          <div className="verify-email-content">
            <div
              className={`icon-container ${
                error.type === 'rate_limit' || error.type === 'not_found'
                  ? 'warning'
                  : error.type === 'already_verified'
                  ? 'success'
                  : 'error'
              }`}
            >
              {error.type === 'already_verified' ? (
                // Success Icon (Check Circle)
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
              ) : error.type === 'network' || error.type === 'unknown' ? (
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

            {error.type === 'not_found' && (
              <div style={{ marginBottom: '1.5rem' }}>
                <Link to="/register" className="secondary-link">
                  Sign up for a new account
                </Link>
              </div>
            )}

            {error.type === 'already_verified' && (
              <button onClick={() => navigate('/login')} className="action-button primary">
                Go to Login
              </button>
            )}

            {(error.type === 'network' || error.type === 'unknown') && (
              <button onClick={handleRetry} className="action-button primary">
                Try Again
              </button>
            )}

            {error.type !== 'already_verified' && error.type !== 'rate_limit' && (
              <div className="secondary-actions">
                <Link to="/" className="secondary-link">
                  Back to Home
                </Link>
              </div>
            )}

            {error.type === 'rate_limit' && rateLimitRetryAfter > 0 && (
              <div className="secondary-actions">
                <p
                  style={{
                    fontSize: '0.9375rem',
                    color: '#ef4444',
                    marginBottom: '0.5rem',
                  }}
                >
                  You can try again in {formatTime(rateLimitRetryAfter)}.
                </p>
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

export default ResendVerificationPage;
