/**
 * Form Validation Utilities
 *
 * Client-side validation functions that mirror backend validation rules.
 */

/**
 * Validate email format (RFC 5322 compliant)
 *
 * @param {string} email - Email address to validate
 * @returns {Object} Validation result
 */
export const validateEmail = (email) => {
  if (!email) {
    return { isValid: false, error: 'Email is required' };
  }

  // Basic email regex (simplified RFC 5322)
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!emailRegex.test(email)) {
    return { isValid: false, error: 'Please enter a valid email address' };
  }

  // Check for common issues
  if (email.length > 254) {
    return { isValid: false, error: 'Email is too long (max 254 characters)' };
  }

  return { isValid: true, error: null };
};

/**
 * Validate password strength
 *
 * @param {string} password - Password to validate
 * @returns {Object} Validation result
 */
export const validatePassword = (password) => {
  if (!password) {
    return { isValid: false, error: 'Password is required' };
  }

  if (password.length < 8) {
    return { isValid: false, error: 'Password must be at least 8 characters' };
  }

  if (!/[A-Z]/.test(password)) {
    return {
      isValid: false,
      error: 'Password must contain at least one uppercase letter',
    };
  }

  if (!/[a-z]/.test(password)) {
    return {
      isValid: false,
      error: 'Password must contain at least one lowercase letter',
    };
  }

  if (!/[0-9]/.test(password)) {
    return { isValid: false, error: 'Password must contain at least one number' };
  }

  return { isValid: true, error: null };
};

/**
 * Validate password confirmation
 *
 * @param {string} password - Original password
 * @param {string} passwordConfirm - Password confirmation
 * @returns {Object} Validation result
 */
export const validatePasswordConfirm = (password, passwordConfirm) => {
  if (!passwordConfirm) {
    return { isValid: false, error: 'Please confirm your password' };
  }

  if (password !== passwordConfirm) {
    return { isValid: false, error: 'Passwords do not match' };
  }

  return { isValid: true, error: null };
};

/**
 * Validate name field
 *
 * @param {string} name - Name to validate
 * @param {string} fieldName - Field name for error messages
 * @param {boolean} required - Whether field is required
 * @returns {Object} Validation result
 */
export const validateName = (name, fieldName = 'Name', required = false) => {
  if (!name && required) {
    return { isValid: false, error: `${fieldName} is required` };
  }

  if (name && name.length > 150) {
    return { isValid: false, error: `${fieldName} is too long (max 150 characters)` };
  }

  return { isValid: true, error: null };
};
