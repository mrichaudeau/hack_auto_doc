/**
 * Dashboard Page Component
 *
 * Main dashboard for authenticated users showing:
 * - Welcome message
 * - Subscribed subjects (placeholder)
 * - Recent reports (placeholder)
 * - Recommendations (placeholder)
 *
 * Future implementation: Integrate with subscription, reports, and recommendations APIs
 */

import { useAuth } from '../hooks/useAuth';
import './DashboardPage.css';

const DashboardPage = () => {
  const { user, logout } = useAuth();

  return (
    <div className="dashboard-page">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <h1 className="dashboard-title">Technology Watch Platform</h1>
          <div className="header-actions">
            <span className="user-greeting">Welcome, {user?.first_name || user?.email}!</span>
            <button onClick={logout} className="logout-button">
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="dashboard-content">
        <div className="dashboard-container">
          {/* Welcome Section */}
          <section className="welcome-section">
            <h2>Dashboard</h2>
            <p className="welcome-text">
              Welcome to your Technology Watch Platform. Track the latest technology trends,
              get personalized recommendations, and stay ahead of the curve.
            </p>
          </section>

          {/* Dashboard Grid */}
          <div className="dashboard-grid">
            {/* Subscriptions Card */}
            <div className="dashboard-card">
              <div className="card-header">
                <svg
                  className="card-icon"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                  <circle cx="9" cy="7" r="4"></circle>
                  <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                </svg>
                <h3>My Subscriptions</h3>
              </div>
              <p className="card-description">
                Manage your technology topics and subscriptions
              </p>
              <div className="card-content">
                <p className="placeholder-text">
                  No subscriptions yet. Start by subscribing to technology topics that interest you.
                </p>
              </div>
            </div>

            {/* Recent Reports Card */}
            <div className="dashboard-card">
              <div className="card-header">
                <svg
                  className="card-icon"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                  <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
                <h3>Recent Reports</h3>
              </div>
              <p className="card-description">
                View latest technology reports and insights
              </p>
              <div className="card-content">
                <p className="placeholder-text">
                  No reports available yet. Reports will appear here once you subscribe to topics.
                </p>
              </div>
            </div>

            {/* Recommendations Card */}
            <div className="dashboard-card">
              <div className="card-header">
                <svg
                  className="card-icon"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z"></path>
                  <line x1="16" y1="8" x2="2" y2="22"></line>
                  <line x1="17.5" y1="15" x2="9" y2="15"></line>
                </svg>
                <h3>Recommendations</h3>
              </div>
              <p className="card-description">
                Discover new topics based on your interests
              </p>
              <div className="card-content">
                <p className="placeholder-text">
                  Personalized recommendations will appear here based on your subscription history.
                </p>
              </div>
            </div>

            {/* Cost Tracking Card */}
            <div className="dashboard-card">
              <div className="card-header">
                <svg
                  className="card-icon"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="12" y1="1" x2="12" y2="23"></line>
                  <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                </svg>
                <h3>AI Usage Costs</h3>
              </div>
              <p className="card-description">
                Monitor AI processing costs and usage
              </p>
              <div className="card-content">
                <p className="placeholder-text">
                  Cost tracking data will be available in the admin dashboard.
                </p>
              </div>
            </div>
          </div>

          {/* Coming Soon Banner */}
          <div className="coming-soon-banner">
            <svg
              className="banner-icon"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            <div className="banner-content">
              <h4>More Features Coming Soon</h4>
              <p>
                Subject subscriptions, AI-powered content collection, personalized reports,
                and intelligent recommendations are currently in development.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default DashboardPage;
