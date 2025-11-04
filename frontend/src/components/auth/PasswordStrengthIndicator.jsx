/**
 * Password Strength Indicator Component
 *
 * Displays real-time feedback on password strength showing which
 * requirements are met.
 *
 * Features:
 * - Visual checklist of requirements
 * - Color-coded strength indicator
 * - Real-time updates as user types
 * - ARIA accessibility
 */

import { useMemo } from 'react';
import {
  checkPasswordRequirements,
  calculatePasswordStrength,
  getPasswordStrengthLevel,
  getPasswordStrengthColor,
} from '../../utils/passwordStrength';
import './PasswordStrengthIndicator.css';

const PasswordStrengthIndicator = ({ password }) => {
  const requirements = useMemo(
    () => checkPasswordRequirements(password),
    [password]
  );

  const strength = useMemo(
    () => calculatePasswordStrength(password),
    [password]
  );

  const strengthLevel = useMemo(
    () => getPasswordStrengthLevel(strength),
    [strength]
  );

  const strengthColor = useMemo(
    () => getPasswordStrengthColor(strengthLevel),
    [strengthLevel]
  );

  if (!password) {
    return null;
  }

  const requirementsList = [
    {
      key: 'minLength',
      met: requirements.hasMinLength,
      text: 'At least 8 characters',
      required: true,
    },
    {
      key: 'uppercase',
      met: requirements.hasUppercase,
      text: 'Contains uppercase letter (A-Z)',
      required: true,
    },
    {
      key: 'lowercase',
      met: requirements.hasLowercase,
      text: 'Contains lowercase letter (a-z)',
      required: true,
    },
    {
      key: 'number',
      met: requirements.hasNumber,
      text: 'Contains number (0-9)',
      required: true,
    },
    {
      key: 'special',
      met: requirements.hasSpecial,
      text: 'Contains special character (recommended)',
      required: false,
    },
  ];

  return (
    <div className="password-strength-indicator" role="status" aria-live="polite">
      {/* Strength Bar */}
      <div className="strength-bar-container">
        <div
          className="strength-bar"
          style={{
            width: `${(strength / 5) * 100}%`,
            backgroundColor: strengthColor,
          }}
        />
      </div>

      {/* Strength Label */}
      <div className="strength-label" style={{ color: strengthColor }}>
        Password strength:{' '}
        <strong>
          {strengthLevel.charAt(0).toUpperCase() + strengthLevel.slice(1)}
        </strong>
      </div>

      {/* Requirements Checklist */}
      <ul className="requirements-list">
        {requirementsList.map((req) => (
          <li
            key={req.key}
            className={`requirement-item ${req.met ? 'requirement-met' : 'requirement-unmet'}`}
          >
            <span className="requirement-icon" aria-hidden="true">
              {req.met ? '✓' : '✗'}
            </span>
            <span className="requirement-text">
              {req.text}
              {!req.required && <span className="requirement-optional"> (Optional)</span>}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default PasswordStrengthIndicator;
