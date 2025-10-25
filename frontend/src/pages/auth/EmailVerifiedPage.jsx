import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import authService from '../../services/authService';
import styles from './RegisterPage.module.css';

/**
 * EmailVerifiedPage Component - TASK-1.13
 * Page shown when user clicks email verification link
 */
const EmailVerifiedPage = () => {
  const { key } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('verifying'); // verifying, success, error
  const [message, setMessage] = useState('');
  const [countdown, setCountdown] = useState(3);

  useEffect(() => {
    verifyEmail();
  }, [key]);

  useEffect(() => {
    if (status === 'success' && countdown > 0) {
      const timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (status === 'success' && countdown === 0) {
      navigate('/login');
    }
  }, [status, countdown, navigate]);

  /**
   * Verify email with the provided key
   */
  const verifyEmail = async () => {
    if (!key) {
      setStatus('error');
      setMessage('Lien de vérification invalide');
      return;
    }

    const result = await authService.verifyEmail(key);

    if (result.success) {
      setStatus('success');
      setMessage(result.data.message || 'Email vérifié avec succès !');
    } else {
      setStatus('error');
      setMessage(result.error.error || 'Erreur lors de la vérification');
    }
  };

  /**
   * Render content based on verification status
   */
  const renderContent = () => {
    switch (status) {
      case 'verifying':
        return (
          <>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>
              <div className={styles.loading} style={{
                width: '48px',
                height: '48px',
                borderWidth: '4px',
                margin: '0 auto'
              }}></div>
            </div>
            <h1 className={styles.title}>Vérification en cours...</h1>
            <p className={styles.subtitle}>
              Veuillez patienter pendant que nous vérifions votre email
            </p>
          </>
        );

      case 'success':
        return (
          <>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✅</div>
            <h1 className={styles.title}>Email vérifié !</h1>
            <p className={styles.subtitle} style={{ marginBottom: '1.5rem' }}>
              {message}
            </p>
            <div style={{
              backgroundColor: '#D1FAE5',
              border: '1px solid #6EE7B7',
              borderRadius: '0.5rem',
              padding: '1rem',
              marginBottom: '1.5rem',
              color: '#065F46'
            }}>
              <p style={{ margin: 0 }}>
                Votre compte a été activé avec succès. Vous allez être redirigé vers la page de connexion dans <strong>{countdown}</strong> seconde{countdown > 1 ? 's' : ''}...
              </p>
            </div>
            <Link
              to="/login"
              style={{
                display: 'inline-block',
                padding: '0.875rem 1.5rem',
                backgroundColor: '#4F46E5',
                color: 'white',
                textDecoration: 'none',
                borderRadius: '0.5rem',
                fontWeight: '600',
                transition: 'all 0.2s'
              }}
            >
              Se connecter maintenant
            </Link>
          </>
        );

      case 'error':
        return (
          <>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>❌</div>
            <h1 className={styles.title}>Erreur de vérification</h1>
            <p className={styles.subtitle} style={{ marginBottom: '1.5rem' }}>
              {message}
            </p>
            <div style={{
              backgroundColor: '#FEE2E2',
              border: '1px solid #FCA5A5',
              borderRadius: '0.5rem',
              padding: '1rem',
              marginBottom: '1.5rem',
              color: '#991B1B'
            }}>
              <p style={{ margin: 0 }}>
                Le lien de vérification est peut-être expiré ou invalide. Vous pouvez demander un nouvel email de vérification sur la page d'inscription.
              </p>
            </div>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <Link
                to="/register"
                style={{
                  padding: '0.875rem 1.5rem',
                  backgroundColor: '#4F46E5',
                  color: 'white',
                  textDecoration: 'none',
                  borderRadius: '0.5rem',
                  fontWeight: '600'
                }}
              >
                Retour à l'inscription
              </Link>
              <Link
                to="/login"
                style={{
                  padding: '0.875rem 1.5rem',
                  backgroundColor: '#E5E7EB',
                  color: '#374151',
                  textDecoration: 'none',
                  borderRadius: '0.5rem',
                  fontWeight: '600'
                }}
              >
                Se connecter
              </Link>
            </div>
          </>
        );

      default:
        return null;
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header} style={{ textAlign: 'center' }}>
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default EmailVerifiedPage;
