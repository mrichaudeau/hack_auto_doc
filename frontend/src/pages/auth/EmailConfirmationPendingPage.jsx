import { useState, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import authService from '../../services/authService';
import styles from './RegisterPage.module.css'; // Reuse the same styles

/**
 * EmailConfirmationPendingPage Component - TASK-1.12
 * Page shown after registration, prompting user to check their email
 */
const EmailConfirmationPendingPage = () => {
  const location = useLocation();
  const email = location.state?.email || '';
  const [cooldown, setCooldown] = useState(0);
  const [resendStatus, setResendStatus] = useState(null);

  useEffect(() => {
    let timer;
    if (cooldown > 0) {
      timer = setTimeout(() => setCooldown(cooldown - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [cooldown]);

  /**
   * Handle resend verification email
   */
  const handleResend = async () => {
    if (cooldown > 0) return;

    setResendStatus({ type: 'loading', message: 'Envoi en cours...' });

    const result = await authService.resendVerification(email);

    if (result.success) {
      setResendStatus({
        type: 'success',
        message: 'Email de vérification renvoyé avec succès !'
      });
      setCooldown(60); // 60 seconds cooldown
      setTimeout(() => setResendStatus(null), 5000);
    } else {
      setResendStatus({
        type: 'error',
        message: result.error.error || 'Erreur lors de l\'envoi'
      });
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📧</div>
          <h1 className={styles.title}>Vérifiez votre email</h1>
          <p className={styles.subtitle}>
            Un email de vérification a été envoyé
          </p>
        </div>

        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <p style={{ color: '#374151', marginBottom: '1rem' }}>
            Nous avons envoyé un email de vérification à :
          </p>
          <p style={{ fontWeight: '600', color: '#4F46E5', fontSize: '1.125rem' }}>
            {email}
          </p>
        </div>

        <div style={{
          backgroundColor: '#FEF3C7',
          border: '1px solid #FCD34D',
          borderRadius: '0.5rem',
          padding: '1rem',
          marginBottom: '1.5rem'
        }}>
          <p style={{ color: '#92400E', fontSize: '0.875rem', margin: 0 }}>
            <strong>Important :</strong> Si vous ne voyez pas l'email, vérifiez votre dossier spam ou courrier indésirable.
          </p>
        </div>

        {resendStatus && (
          <div style={{
            padding: '1rem',
            borderRadius: '0.5rem',
            marginBottom: '1rem',
            backgroundColor: resendStatus.type === 'success' ? '#D1FAE5' : '#FEE2E2',
            color: resendStatus.type === 'success' ? '#065F46' : '#991B1B'
          }}>
            {resendStatus.message}
          </div>
        )}

        <button
          onClick={handleResend}
          disabled={cooldown > 0 || resendStatus?.type === 'loading'}
          style={{
            width: '100%',
            padding: '0.875rem',
            backgroundColor: cooldown > 0 ? '#9CA3AF' : '#4F46E5',
            color: 'white',
            border: 'none',
            borderRadius: '0.5rem',
            fontSize: '1rem',
            fontWeight: '600',
            cursor: cooldown > 0 ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
            marginBottom: '1rem'
          }}
        >
          {cooldown > 0
            ? `Renvoyer l'email (${cooldown}s)`
            : 'Renvoyer l\'email de vérification'}
        </button>

        <div className={styles.footer}>
          <Link to="/login" className={styles.loginLink}>
            Retour à la connexion
          </Link>
        </div>
      </div>
    </div>
  );
};

export default EmailConfirmationPendingPage;
