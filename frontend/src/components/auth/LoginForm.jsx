import { useState } from 'react';
import styles from './LoginForm.module.css';

/**
 * LoginForm Component - TASK-2.10
 * Login form with client-side validation
 *
 * @param {Function} onSubmit - Callback function when form is submitted
 * @param {boolean} loading - Loading state during submission
 * @param {Object} errors - Server-side validation errors
 */
const LoginForm = ({ onSubmit, loading, errors }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });

  const [localErrors, setLocalErrors] = useState({});
  const [touched, setTouched] = useState({});

  /**
   * Validate email format
   */
  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  /**
   * Validate form fields
   */
  const validateField = (name, value) => {
    const newErrors = { ...localErrors };

    switch (name) {
      case 'email':
        if (!value.trim()) {
          newErrors.email = 'L\'email est requis';
        } else if (!validateEmail(value)) {
          newErrors.email = 'Format d\'email invalide';
        } else {
          delete newErrors.email;
        }
        break;

      case 'password':
        if (!value) {
          newErrors.password = 'Le mot de passe est requis';
        } else {
          delete newErrors.password;
        }
        break;

      default:
        break;
    }

    setLocalErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handle input change
   */
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Validate if field has been touched
    if (touched[name]) {
      validateField(name, value);
    }
  };

  /**
   * Handle input blur
   */
  const handleBlur = (e) => {
    const { name, value } = e.target;
    setTouched(prev => ({
      ...prev,
      [name]: true
    }));
    validateField(name, value);
  };

  /**
   * Handle form submission
   */
  const handleSubmit = (e) => {
    e.preventDefault();

    // Mark all fields as touched
    setTouched({
      email: true,
      password: true
    });

    // Validate all fields
    const emailValid = validateField('email', formData.email);
    const passwordValid = validateField('password', formData.password);

    if (emailValid && passwordValid) {
      onSubmit(formData);
    }
  };

  /**
   * Check if form has errors (local or server-side)
   */
  const hasErrors = Object.keys(localErrors).length > 0 ||
                    (errors && Object.keys(errors).length > 0);

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      {/* Email Field */}
      <div className={styles.formGroup}>
        <label htmlFor="email" className={styles.label}>
          Email
        </label>
        <input
          type="email"
          id="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          onBlur={handleBlur}
          className={`${styles.input} ${
            (touched.email && localErrors.email) || errors?.email ? styles.inputError : ''
          }`}
          placeholder="votre.email@example.com"
          disabled={loading}
          autoComplete="email"
          required
        />
        {touched.email && localErrors.email && (
          <span className={styles.error}>{localErrors.email}</span>
        )}
      </div>

      {/* Password Field */}
      <div className={styles.formGroup}>
        <label htmlFor="password" className={styles.label}>
          Mot de passe
        </label>
        <input
          type="password"
          id="password"
          name="password"
          value={formData.password}
          onChange={handleChange}
          onBlur={handleBlur}
          className={`${styles.input} ${
            (touched.password && localErrors.password) || errors?.password ? styles.inputError : ''
          }`}
          placeholder="••••••••"
          disabled={loading}
          autoComplete="current-password"
          required
        />
        {touched.password && localErrors.password && (
          <span className={styles.error}>{localErrors.password}</span>
        )}
      </div>

      {/* Server-side errors (401, 403, etc.) */}
      {errors && !errors.email && !errors.password && (
        <div className={styles.serverError}>
          {typeof errors === 'string' ? errors : errors.non_field_errors || errors.detail || 'Erreur de connexion'}
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        className={styles.submitButton}
        disabled={loading || hasErrors}
      >
        {loading ? 'Connexion en cours...' : 'Se connecter'}
      </button>

      {/* Forgot Password Link */}
      <div className={styles.forgotPassword}>
        <a href="/reset-password" className={styles.link}>
          Mot de passe oublié ?
        </a>
      </div>

      {/* Register Link */}
      <div className={styles.registerLink}>
        Pas encore inscrit ?{' '}
        <a href="/register" className={styles.link}>
          Créer un compte
        </a>
      </div>
    </form>
  );
};

export default LoginForm;
