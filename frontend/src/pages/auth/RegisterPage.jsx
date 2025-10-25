import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import RegisterForm from '../../components/auth/RegisterForm';
import authService from '../../services/authService';
import styles from './RegisterPage.module.css';

/**
 * RegisterPage Component - TASK-1.11
 * Page for user registration with email/password
 */
const RegisterPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState(null);
  const [generalError, setGeneralError] = useState(null);

  /**
   * Handle form submission
   */
  const handleSubmit = async (formData) => {
    setLoading(true);
    setErrors(null);
    setGeneralError(null);

    const result = await authService.register(formData);

    setLoading(false);

    if (result.success) {
      // Navigate to email confirmation pending page with email
      navigate('/email-confirmation-pending', {
        state: { email: formData.email }
      });
    } else {
      // Handle errors
      if (result.error.email) {
        setGeneralError(result.error.email);
      } else if (result.error.message) {
        setGeneralError(result.error.message);
      } else {
        setErrors(result.error);
      }
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <h1 className={styles.title}>Créer un compte</h1>
          <p className={styles.subtitle}>
            Rejoignez la Plateforme de Veille Technologique IA
          </p>
        </div>

        {generalError && (
          <div className={styles.errorAlert}>
            <strong>Erreur</strong>
            {generalError}
          </div>
        )}

        <RegisterForm
          onSubmit={handleSubmit}
          loading={loading}
          errors={errors}
        />

        <div className={styles.footer}>
          <p>
            Vous avez déjà un compte ?{' '}
            <Link to="/login" className={styles.loginLink}>
              Se connecter
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
