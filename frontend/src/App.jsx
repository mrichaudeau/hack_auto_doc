import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import RegisterPage from './pages/auth/RegisterPage';
import EmailConfirmationPendingPage from './pages/auth/EmailConfirmationPendingPage';
import EmailVerifiedPage from './pages/auth/EmailVerifiedPage';
import './App.css';

/**
 * Main App Component - TASK-1.14
 * Configures routing for authentication pages
 */
function App() {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/email-confirmation-pending" element={<EmailConfirmationPendingPage />} />
        <Route path="/verify-email/:key" element={<EmailVerifiedPage />} />

        {/* Temporary login placeholder (will be implemented in US-2) */}
        <Route
          path="/login"
          element={
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '100vh',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              textAlign: 'center',
              padding: '2rem'
            }}>
              <div>
                <h1>Page de connexion</h1>
                <p>Cette page sera implémentée dans US-2 (JWT Login)</p>
                <a href="/register" style={{ color: 'white', textDecoration: 'underline' }}>
                  Retour à l'inscription
                </a>
              </div>
            </div>
          }
        />

        {/* Default redirect to register */}
        <Route path="/" element={<Navigate to="/register" replace />} />

        {/* Catch all - redirect to register */}
        <Route path="*" element={<Navigate to="/register" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
