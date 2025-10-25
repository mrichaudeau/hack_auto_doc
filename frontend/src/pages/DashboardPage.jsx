import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import styles from './DashboardPage.module.css';

/**
 * DashboardPage Component - TASK-2.14
 * Protected dashboard page accessible only after authentication
 * Displays user information and logout functionality
 */
const DashboardPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  /**
   * Handle logout button click
   */
  const handleLogout = async () => {
    try {
      await logout();
      // Redirect to login page after logout
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <div className={styles.container}>
      {/* Header with Logout */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.logo}>Veille Technologique</h1>
          <button
            onClick={handleLogout}
            className={styles.logoutButton}
          >
            Déconnexion
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className={styles.main}>
        <div className={styles.content}>
          {/* Welcome Section */}
          <section className={styles.welcomeSection}>
            <h2 className={styles.welcomeTitle}>
              Bienvenue, {user?.first_name || 'Utilisateur'} !
            </h2>
            <p className={styles.welcomeSubtitle}>
              Tableau de bord de votre plateforme de veille technologique
            </p>
          </section>

          {/* User Info Card */}
          <section className={styles.userCard}>
            <h3 className={styles.cardTitle}>Informations de compte</h3>
            <div className={styles.userInfo}>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>Email:</span>
                <span className={styles.infoValue}>{user?.email}</span>
              </div>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>Nom complet:</span>
                <span className={styles.infoValue}>
                  {user?.first_name} {user?.last_name}
                </span>
              </div>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>Méthode d'authentification:</span>
                <span className={styles.infoValue}>
                  {user?.auth_provider === 'STANDARD' ? 'Email/Mot de passe' : user?.auth_provider}
                </span>
              </div>
              {user?.date_joined && (
                <div className={styles.infoRow}>
                  <span className={styles.infoLabel}>Membre depuis:</span>
                  <span className={styles.infoValue}>
                    {new Date(user.date_joined).toLocaleDateString('fr-FR', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </span>
                </div>
              )}
            </div>
          </section>

          {/* Coming Soon Section */}
          <section className={styles.comingSoonCard}>
            <h3 className={styles.cardTitle}>À venir</h3>
            <ul className={styles.featureList}>
              <li>Abonnement à des sujets de veille</li>
              <li>Consultation de rapports personnalisés</li>
              <li>Recommandations intelligentes</li>
              <li>Suivi des coûts FinOps</li>
            </ul>
          </section>
        </div>
      </main>
    </div>
  );
};

export default DashboardPage;
