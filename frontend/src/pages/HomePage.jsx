/**
 * Home Page Component
 *
 * Landing page for the Technology Watch Platform
 * Redirects authenticated users to dashboard
 */

import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import './HomePage.css';

const HomePage = () => {
  const { isAuthenticated, loading } = useAuth();

  console.log('[HomePage] Rendering - isAuthenticated:', isAuthenticated, 'loading:', loading);

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="home-page">
        <div className="home-container" style={{ textAlign: 'center' }}>
          <div className="loading-spinner">
            <div className="spinner"></div>
          </div>
          <p style={{ color: '#667eea', marginTop: '1rem', fontSize: '1.1rem' }}>
            Loading...
          </p>
        </div>
      </div>
    );
  }

  // Redirect authenticated users to dashboard
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  // Show landing page for unauthenticated users
  return (
    <div className="home-page">
      <div className="home-container">
        <header className="home-header">
          <h1 className="home-title">Plateforme de Veille Technologique IA</h1>
          <p className="home-subtitle">
            Automated technology monitoring powered by AI agents
          </p>
        </header>

        <div className="home-content">
          <div className="feature-grid">
            <div className="feature-card">
              <h3>AI-Powered Collection</h3>
              <p>Automated content gathering using Langgraph agents and Firecrawl</p>
            </div>
            <div className="feature-card">
              <h3>Smart Synthesis</h3>
              <p>Intelligent analysis and report generation with quality verification</p>
            </div>
            <div className="feature-card">
              <h3>Personalized Recommendations</h3>
              <p>Vector-based recommendations tailored to your interests</p>
            </div>
            <div className="feature-card">
              <h3>Cost Tracking</h3>
              <p>FinOps dashboard for monitoring AI usage and costs</p>
            </div>
          </div>

          <div className="cta-section">
            <Link to="/subjects" className="cta-button primary">
              Browse Subjects
            </Link>
            <Link to="/register" className="cta-button secondary">
              Get Started
            </Link>
            <Link to="/login" className="cta-button secondary">
              Sign In
            </Link>
          </div>
        </div>

        <footer className="home-footer">
          <p className="footer-text">
            Tech Watch Platform - Monitoring technology trends for professionals
          </p>
        </footer>
      </div>
    </div>
  );
};

export default HomePage;
