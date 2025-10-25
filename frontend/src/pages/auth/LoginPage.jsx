import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import LoginForm from '../../components/auth/LoginForm';
import { useAuth } from '../../hooks/useAuth';
import styles from './LoginPage.module.css';

/**
 * LoginPage Component - TASK-2.11
 * Login page that uses LoginForm and handles authentication
 */
const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState(null);

  /**
   * Handle login form submission
   */
  const handleLogin = async (formData) => {
    setLoading(true);
    setErrors(null);

    try {
      const result = await login(formData.email, formData.password);

      if (result.success) {
        // Redirect to dashboard on successful login
        navigate('/dashboard');
      } else {
        // Handle error responses
        if (result.error) {
          // Check for specific error codes
          const errorData = result.error;

          // Handle different error scenarios
          if (errorData.non_field_errors) {
            // Generic authentication error (401)
            const errorMessage = Array.isArray(errorData.non_field_errors)
              ? errorData.non_field_errors[0]
              : errorData.non_field_errors;

            // Check for inactive account (403)
            if (errorMessage.toLowerCase().includes('verifie') || errorMessage.toLowerCase().includes('verifier')) {
              setErrors({
                detail: 'Compte non vérifié. Veuillez vérifier votre email avant de vous connecter.'
              });
            } else {
              setErrors({ detail: errorMessage });
            }
          } else if (errorData.detail) {
            // Direct detail message
            setErrors({ detail: errorData.detail });
          } else if (typeof errorData === 'string') {
            setErrors({ detail: errorData });
          } else {
            // Field-specific errors (email, password)
            setErrors(errorData);
          }
        } else {
          setErrors({ detail: 'Erreur de connexion. Veuillez réessayer.' });
        }
      }
    } catch (error) {
      console.error('Login error:', error);
      setErrors({ detail: 'Une erreur est survenue. Veuillez réessayer.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.content}>
        {/* Header */}
        <div className={styles.header}>
          <h1 className={styles.title}>Connexion</h1>
          <p className={styles.subtitle}>
            Accédez à votre compte de veille technologique
          </p>
        </div>

        {/* Login Form */}
        <div className={styles.formContainer}>
          <LoginForm
            onSubmit={handleLogin}
            loading={loading}
            errors={errors}
          />
        </div>

        {/* SSO Option (Placeholder for US-3) */}
        <div className={styles.ssoSection}>
          <div className={styles.divider}>
            <span className={styles.dividerText}>ou</span>
          </div>
          <button className={styles.ssoButton} disabled>
            <svg className={styles.microsoftIcon} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path fill="#f25022" d="M0 0h11.377v11.372H0z"/>
              <path fill="#00a4ef" d="M12.623 0H24v11.372H12.623z"/>
              <path fill="#7fba00" d="M0 12.628h11.377V24H0z"/>
              <path fill="#ffb900" d="M12.623 12.628H24V24H12.623z"/>
            </svg>
            Se connecter avec Microsoft
          </button>
          <p className={styles.ssoNote}>
            Disponible prochainement
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
