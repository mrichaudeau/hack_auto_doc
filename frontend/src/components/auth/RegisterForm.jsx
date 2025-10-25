import { useState } from 'react';
import styles from './RegisterForm.module.css';

/**
 * RegisterForm Component - TASK-1.10
 * Registration form with client-side validation
 */
const RegisterForm = ({ onSubmit, loading, errors }) => {
  const [formData, setFormData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    password: '',
    password_confirm: ''
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
   * Validate password strength
   */
  const validatePassword = (password) => {
    const errors = [];
    if (password.length < 8) {
      errors.push('Minimum 8 caractères');
    }
    if (!/[A-Z]/.test(password)) {
      errors.push('Au moins 1 majuscule');
    }
    if (!/[a-z]/.test(password)) {
      errors.push('Au moins 1 minuscule');
    }
    if (!/[0-9]/.test(password)) {
      errors.push('Au moins 1 chiffre');
    }
    return errors;
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

    // Clear field-specific error when user types
    if (localErrors[name]) {
      setLocalErrors(prev => ({
        ...prev,
        [name]: null
      }));
    }
  };

  /**
   * Handle input blur for validation
   */
  const handleBlur = (e) => {
    const { name } = e.target;
    setTouched(prev => ({
      ...prev,
      [name]: true
    }));
    validateField(name);
  };

  /**
   * Validate individual field
   */
  const validateField = (fieldName) => {
    let error = null;

    switch (fieldName) {
      case 'email':
        if (!formData.email) {
          error = 'L\'email est requis';
        } else if (!validateEmail(formData.email)) {
          error = 'Format d\'email invalide';
        }
        break;

      case 'first_name':
        if (!formData.first_name) {
          error = 'Le prénom est requis';
        }
        break;

      case 'last_name':
        if (!formData.last_name) {
          error = 'Le nom est requis';
        }
        break;

      case 'password':
        const passwordErrors = validatePassword(formData.password);
        if (passwordErrors.length > 0) {
          error = passwordErrors.join(', ');
        }
        break;

      case 'password_confirm':
        if (formData.password !== formData.password_confirm) {
          error = 'Les mots de passe ne correspondent pas';
        }
        break;

      default:
        break;
    }

    setLocalErrors(prev => ({
      ...prev,
      [fieldName]: error
    }));

    return !error;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = (e) => {
    e.preventDefault();

    // Mark all fields as touched
    const allTouched = Object.keys(formData).reduce((acc, key) => {
      acc[key] = true;
      return acc;
    }, {});
    setTouched(allTouched);

    // Validate all fields
    const fieldsValid = Object.keys(formData).every(field => validateField(field));

    if (fieldsValid) {
      onSubmit(formData);
    }
  };

  /**
   * Get error message for a field (prioritize server errors)
   */
  const getFieldError = (fieldName) => {
    if (errors && errors[fieldName]) {
      return Array.isArray(errors[fieldName]) ? errors[fieldName][0] : errors[fieldName];
    }
    return touched[fieldName] ? localErrors[fieldName] : null;
  };

  const isFormValid = () => {
    return Object.values(formData).every(value => value.trim() !== '') &&
           Object.values(localErrors).every(error => !error) &&
           formData.password === formData.password_confirm;
  };

  return (
    <div className={styles.formContainer}>
      <form onSubmit={handleSubmit} className={styles.form} noValidate>
        {/* Email */}
        <div className={styles.formGroup}>
          <label htmlFor="email" className={styles.label}>
            Email <span className={styles.required}>*</span>
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            onBlur={handleBlur}
            className={`${styles.input} ${getFieldError('email') ? styles.error : ''}`}
            placeholder="votre.email@example.com"
            disabled={loading}
            autoComplete="email"
          />
          {getFieldError('email') && (
            <span className={styles.errorMessage}>
              ⚠ {getFieldError('email')}
            </span>
          )}
        </div>

        {/* First Name and Last Name */}
        <div className={styles.nameRow}>
          <div className={styles.formGroup}>
            <label htmlFor="first_name" className={styles.label}>
              Prénom <span className={styles.required}>*</span>
            </label>
            <input
              type="text"
              id="first_name"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              onBlur={handleBlur}
              className={`${styles.input} ${getFieldError('first_name') ? styles.error : ''}`}
              placeholder="John"
              disabled={loading}
              autoComplete="given-name"
            />
            {getFieldError('first_name') && (
              <span className={styles.errorMessage}>
                ⚠ {getFieldError('first_name')}
              </span>
            )}
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="last_name" className={styles.label}>
              Nom <span className={styles.required}>*</span>
            </label>
            <input
              type="text"
              id="last_name"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              onBlur={handleBlur}
              className={`${styles.input} ${getFieldError('last_name') ? styles.error : ''}`}
              placeholder="Doe"
              disabled={loading}
              autoComplete="family-name"
            />
            {getFieldError('last_name') && (
              <span className={styles.errorMessage}>
                ⚠ {getFieldError('last_name')}
              </span>
            )}
          </div>
        </div>

        {/* Password */}
        <div className={styles.formGroup}>
          <label htmlFor="password" className={styles.label}>
            Mot de passe <span className={styles.required}>*</span>
          </label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            onBlur={handleBlur}
            className={`${styles.input} ${getFieldError('password') ? styles.error : ''}`}
            placeholder="••••••••"
            disabled={loading}
            autoComplete="new-password"
          />
          {getFieldError('password') && (
            <span className={styles.errorMessage}>
              ⚠ {getFieldError('password')}
            </span>
          )}
          {!getFieldError('password') && (
            <div className={styles.passwordHints}>
              <strong>Votre mot de passe doit contenir :</strong>
              <ul>
                <li>Au moins 8 caractères</li>
                <li>Au moins 1 majuscule et 1 minuscule</li>
                <li>Au moins 1 chiffre</li>
              </ul>
            </div>
          )}
        </div>

        {/* Password Confirmation */}
        <div className={styles.formGroup}>
          <label htmlFor="password_confirm" className={styles.label}>
            Confirmer le mot de passe <span className={styles.required}>*</span>
          </label>
          <input
            type="password"
            id="password_confirm"
            name="password_confirm"
            value={formData.password_confirm}
            onChange={handleChange}
            onBlur={handleBlur}
            className={`${styles.input} ${getFieldError('password_confirm') ? styles.error : ''}`}
            placeholder="••••••••"
            disabled={loading}
            autoComplete="new-password"
          />
          {getFieldError('password_confirm') && (
            <span className={styles.errorMessage}>
              ⚠ {getFieldError('password_confirm')}
            </span>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          className={styles.submitButton}
          disabled={loading || !isFormValid()}
        >
          {loading && <span className={styles.loading}></span>}
          {loading ? 'Inscription en cours...' : 'S\'inscrire'}
        </button>
      </form>
    </div>
  );
};

export default RegisterForm;
