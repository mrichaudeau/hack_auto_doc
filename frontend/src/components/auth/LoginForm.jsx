/**
 * Login Form Component (US-3: Standard User Login)
 *
 * A responsive login form with email/password authentication.
 * Implements client-side validation, loading states, and error handling.
 *
 * Features:
 * - Email and password input fields
 * - Client-side validation with error messages
 * - Loading state during authentication
 * - Error display for failed login attempts
 * - Password visibility toggle
 * - Responsive design for mobile/tablet/desktop
 * - Accessibility (WCAG 2.1 Level AA)
 */

import { useState } from 'react';
import './LoginForm.css';

const LoginForm = ({ onSubmit, loading, error }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const [fieldErrors, setFieldErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [touched, setTouched] = useState({});

  // Email validation regex (RFC 5322 simplified)
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  /**
   * Validate individual field
   */
  const validateField = (name, value) => {
    switch (name) {
      case 'email':
        if (!value) {
          return 'Email address is required';
        }
        if (!emailRegex.test(value)) {
          return 'Please enter a valid email address';
        }
        return '';

      case 'password':
        if (!value) {
          return 'Password is required';
        }
        return '';

      default:
        return '';
    }
  };

  /**
   * Handle input change
   */
  const handleChange = (e) => {
    const { name, value } = e.target;

    // Update form data
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    // Validate if field has been touched
    if (touched[name]) {
      const error = validateField(name, value);
      setFieldErrors((prev) => ({
        ...prev,
        [name]: error,
      }));
    }
  };

  /**
   * Handle input blur (mark field as touched)
   */
  const handleBlur = (e) => {
    const { name, value } = e.target;

    // Mark field as touched
    setTouched((prev) => ({
      ...prev,
      [name]: true,
    }));

    // Validate field
    const error = validateField(name, value);
    setFieldErrors((prev) => ({
      ...prev,
      [name]: error,
    }));
  };

  /**
   * Validate entire form
   */
  const validateForm = () => {
    const errors = {};
    Object.keys(formData).forEach((key) => {
      const error = validateField(key, formData[key]);
      if (error) {
        errors[key] = error;
      }
    });
    return errors;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = (e) => {
    e.preventDefault();

    // Mark all fields as touched
    setTouched({
      email: true,
      password: true,
    });

    // Validate entire form
    const errors = validateForm();
    setFieldErrors(errors);

    // If no errors, submit form
    if (Object.keys(errors).length === 0) {
      onSubmit(formData.email, formData.password);
    }
  };

  /**
   * Toggle password visibility
   */
  const togglePasswordVisibility = () => {
    setShowPassword((prev) => !prev);
  };

  return (
    <form className="login-form" onSubmit={handleSubmit} noValidate>
      {/* Server Error Display */}
      {error && (
        <div className="form-error" role="alert" aria-live="assertive">
          <svg
            className="error-icon"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Email Field */}
      <div className="form-group">
        <label htmlFor="email" className="form-label">
          Email Address
          <span className="required-indicator" aria-label="required">
            *
          </span>
        </label>
        <input
          type="email"
          id="email"
          name="email"
          className={`form-input ${fieldErrors.email ? 'input-error' : ''}`}
          value={formData.email}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={loading}
          required
          autoComplete="email"
          aria-required="true"
          aria-invalid={fieldErrors.email ? 'true' : 'false'}
          aria-describedby={fieldErrors.email ? 'email-error' : undefined}
          placeholder="you@example.com"
        />
        {fieldErrors.email && (
          <span id="email-error" className="field-error" role="alert">
            {fieldErrors.email}
          </span>
        )}
      </div>

      {/* Password Field */}
      <div className="form-group">
        <label htmlFor="password" className="form-label">
          Password
          <span className="required-indicator" aria-label="required">
            *
          </span>
        </label>
        <div className="password-input-wrapper">
          <input
            type={showPassword ? 'text' : 'password'}
            id="password"
            name="password"
            className={`form-input ${fieldErrors.password ? 'input-error' : ''}`}
            value={formData.password}
            onChange={handleChange}
            onBlur={handleBlur}
            disabled={loading}
            required
            autoComplete="current-password"
            aria-required="true"
            aria-invalid={fieldErrors.password ? 'true' : 'false'}
            aria-describedby={fieldErrors.password ? 'password-error' : undefined}
            placeholder="Enter your password"
          />
          <button
            type="button"
            className="password-toggle"
            onClick={togglePasswordVisibility}
            disabled={loading}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            tabIndex={0}
          >
            {showPassword ? (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                <line x1="1" y1="1" x2="23" y2="23"></line>
              </svg>
            ) : (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
            )}
          </button>
        </div>
        {fieldErrors.password && (
          <span id="password-error" className="field-error" role="alert">
            {fieldErrors.password}
          </span>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        className="submit-button"
        disabled={loading}
        aria-busy={loading}
      >
        {loading ? (
          <>
            <span className="spinner" aria-hidden="true"></span>
            <span>Signing In...</span>
          </>
        ) : (
          <span>Sign In</span>
        )}
      </button>

      {/* Forgot Password Link (Future US) */}
      <div className="form-footer">
        <a href="#" className="forgot-password-link" tabIndex={0}>
          Forgot your password?
        </a>
      </div>
    </form>
  );
};

export default LoginForm;
