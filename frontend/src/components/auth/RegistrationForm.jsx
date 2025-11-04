/**
 * Registration Form Component
 *
 * Form for user registration with real-time validation.
 *
 * Features:
 * - Real-time email and password validation
 * - Password strength indicator
 * - Visual feedback for validation state
 * - Form submission with loading state
 * - Accessible form controls
 */

import { useState } from 'react';
import PasswordStrengthIndicator from './PasswordStrengthIndicator';
import {
  validateEmail,
  validatePassword,
  validatePasswordConfirm,
  validateName,
} from '../../utils/validators';
import './RegistrationForm.css';

const RegistrationForm = ({ onSubmit, isLoading = false }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
  });

  const [touched, setTouched] = useState({
    email: false,
    password: false,
    password_confirm: false,
    first_name: false,
    last_name: false,
  });

  const [errors, setErrors] = useState({});

  // Handle input change
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // Validate field if it has been touched
    if (touched[name]) {
      validateField(name, value);
    }
  };

  // Handle input blur
  const handleBlur = (e) => {
    const { name, value } = e.target;
    setTouched((prev) => ({ ...prev, [name]: true }));
    validateField(name, value);
  };

  // Validate individual field
  const validateField = (name, value) => {
    let validation = { isValid: true, error: null };

    switch (name) {
      case 'email':
        validation = validateEmail(value);
        break;
      case 'password':
        validation = validatePassword(value);
        break;
      case 'password_confirm':
        validation = validatePasswordConfirm(formData.password, value);
        break;
      case 'first_name':
        validation = validateName(value, 'First name', false);
        break;
      case 'last_name':
        validation = validateName(value, 'Last name', false);
        break;
      default:
        break;
    }

    setErrors((prev) => ({
      ...prev,
      [name]: validation.error,
    }));

    return validation.isValid;
  };

  // Validate all fields
  const validateForm = () => {
    const emailValid = validateField('email', formData.email);
    const passwordValid = validateField('password', formData.password);
    const passwordConfirmValid = validateField(
      'password_confirm',
      formData.password_confirm
    );
    const firstNameValid = validateField('first_name', formData.first_name);
    const lastNameValid = validateField('last_name', formData.last_name);

    // Mark all fields as touched
    setTouched({
      email: true,
      password: true,
      password_confirm: true,
      first_name: true,
      last_name: true,
    });

    return (
      emailValid &&
      passwordValid &&
      passwordConfirmValid &&
      firstNameValid &&
      lastNameValid
    );
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();

    if (validateForm() && onSubmit) {
      onSubmit(formData);
    }
  };

  // Get field validation class
  const getFieldClass = (fieldName) => {
    if (!touched[fieldName]) return '';
    return errors[fieldName] ? 'field-invalid' : 'field-valid';
  };

  return (
    <form className="registration-form" onSubmit={handleSubmit} noValidate>
      {/* Email Field */}
      <div className="form-group">
        <label htmlFor="email" className="form-label">
          Email Address <span className="required">*</span>
        </label>
        <input
          type="email"
          id="email"
          name="email"
          className={`form-input ${getFieldClass('email')}`}
          value={formData.email}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={isLoading}
          required
          aria-required="true"
          aria-invalid={!!errors.email}
          aria-describedby={errors.email ? 'email-error' : undefined}
        />
        {touched.email && errors.email && (
          <div id="email-error" className="field-error" role="alert">
            {errors.email}
          </div>
        )}
      </div>

      {/* Password Field */}
      <div className="form-group">
        <label htmlFor="password" className="form-label">
          Password <span className="required">*</span>
        </label>
        <input
          type="password"
          id="password"
          name="password"
          className={`form-input ${getFieldClass('password')}`}
          value={formData.password}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={isLoading}
          required
          aria-required="true"
          aria-invalid={!!errors.password}
          aria-describedby={errors.password ? 'password-error' : undefined}
        />
        {touched.password && errors.password && (
          <div id="password-error" className="field-error" role="alert">
            {errors.password}
          </div>
        )}

        {/* Password Strength Indicator */}
        {formData.password && <PasswordStrengthIndicator password={formData.password} />}
      </div>

      {/* Password Confirm Field */}
      <div className="form-group">
        <label htmlFor="password_confirm" className="form-label">
          Confirm Password <span className="required">*</span>
        </label>
        <input
          type="password"
          id="password_confirm"
          name="password_confirm"
          className={`form-input ${getFieldClass('password_confirm')}`}
          value={formData.password_confirm}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={isLoading}
          required
          aria-required="true"
          aria-invalid={!!errors.password_confirm}
          aria-describedby={
            errors.password_confirm ? 'password-confirm-error' : undefined
          }
        />
        {touched.password_confirm && errors.password_confirm && (
          <div id="password-confirm-error" className="field-error" role="alert">
            {errors.password_confirm}
          </div>
        )}
      </div>

      {/* First Name Field */}
      <div className="form-group">
        <label htmlFor="first_name" className="form-label">
          First Name
        </label>
        <input
          type="text"
          id="first_name"
          name="first_name"
          className={`form-input ${getFieldClass('first_name')}`}
          value={formData.first_name}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={isLoading}
          aria-invalid={!!errors.first_name}
          aria-describedby={errors.first_name ? 'first-name-error' : undefined}
        />
        {touched.first_name && errors.first_name && (
          <div id="first-name-error" className="field-error" role="alert">
            {errors.first_name}
          </div>
        )}
      </div>

      {/* Last Name Field */}
      <div className="form-group">
        <label htmlFor="last_name" className="form-label">
          Last Name
        </label>
        <input
          type="text"
          id="last_name"
          name="last_name"
          className={`form-input ${getFieldClass('last_name')}`}
          value={formData.last_name}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={isLoading}
          aria-invalid={!!errors.last_name}
          aria-describedby={errors.last_name ? 'last-name-error' : undefined}
        />
        {touched.last_name && errors.last_name && (
          <div id="last-name-error" className="field-error" role="alert">
            {errors.last_name}
          </div>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        className="submit-button"
        disabled={isLoading}
        aria-busy={isLoading}
      >
        {isLoading ? 'Creating Account...' : 'Create Account'}
      </button>
    </form>
  );
};

export default RegistrationForm;
