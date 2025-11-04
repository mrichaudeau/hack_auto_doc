/**
 * Password Strength Utilities
 *
 * Functions to evaluate password strength based on requirements:
 * - Minimum 8 characters
 * - At least one uppercase letter
 * - At least one lowercase letter
 * - At least one number
 * - Special characters (recommended but not required)
 */

/**
 * Check password requirements
 *
 * @param {string} password - Password to check
 * @returns {Object} Object with requirement status
 */
export const checkPasswordRequirements = (password) => {
  if (!password) {
    return {
      hasMinLength: false,
      hasUppercase: false,
      hasLowercase: false,
      hasNumber: false,
      hasSpecial: false,
    };
  }

  return {
    hasMinLength: password.length >= 8,
    hasUppercase: /[A-Z]/.test(password),
    hasLowercase: /[a-z]/.test(password),
    hasNumber: /[0-9]/.test(password),
    hasSpecial: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password),
  };
};

/**
 * Calculate password strength score
 *
 * @param {string} password - Password to evaluate
 * @returns {number} Strength score (0-5)
 */
export const calculatePasswordStrength = (password) => {
  const requirements = checkPasswordRequirements(password);

  let score = 0;

  if (requirements.hasMinLength) score++;
  if (requirements.hasUppercase) score++;
  if (requirements.hasLowercase) score++;
  if (requirements.hasNumber) score++;
  if (requirements.hasSpecial) score++;

  return score;
};

/**
 * Get password strength level
 *
 * @param {number} score - Strength score (0-5)
 * @returns {string} Strength level (weak, medium, strong)
 */
export const getPasswordStrengthLevel = (score) => {
  if (score < 3) return 'weak';
  if (score === 3 || score === 4) return 'medium';
  return 'strong';
};

/**
 * Get password strength color
 *
 * @param {string} level - Strength level
 * @returns {string} Color code
 */
export const getPasswordStrengthColor = (level) => {
  switch (level) {
    case 'weak':
      return '#ef4444'; // red
    case 'medium':
      return '#f59e0b'; // yellow/orange
    case 'strong':
      return '#10b981'; // green
    default:
      return '#9ca3af'; // gray
  }
};

/**
 * Validate password meets all requirements
 *
 * @param {string} password - Password to validate
 * @returns {boolean} True if all required criteria met
 */
export const isPasswordValid = (password) => {
  const requirements = checkPasswordRequirements(password);

  return (
    requirements.hasMinLength &&
    requirements.hasUppercase &&
    requirements.hasLowercase &&
    requirements.hasNumber
    // Special characters not required
  );
};
