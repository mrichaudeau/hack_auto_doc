/**
 * Registration Page Component
 *
 * Main registration page that integrates the registration form and handles
 * the registration flow including API calls, success/error states, and
 * navigation.
 */

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import RegistrationForm from '../components/auth/RegistrationForm';
import Alert from '../components/common/Alert';
import authService from '../services/authService';
import './RegisterPage.css';

const RegisterPage = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [alert, setAlert] = useState(null);

  const handleRegistration = async (formData) => {
    setIsLoading(true);
    setAlert(null);

    try {
      const result = await authService.register(formData);

      if (result.success) {
        // Show success message
        setAlert({
          type: 'success',
          message:
            result.data.message ||
            'Registration successful! Please check your email to verify your account.',
        });

        // Redirect to verification page after 2 seconds
        setTimeout(() => {
          navigate('/verify-email', {
            state: { email: formData.email },
          });
        }, 2000);
      } else {
        // Handle error
        const errorData = result.error;

        if (errorData.email && Array.isArray(errorData.email)) {
          // Duplicate email or email validation error
          setAlert({
            type: 'error',
            message: errorData.email[0],
          });
        } else if (errorData.password && Array.isArray(errorData.password)) {
          // Password validation error
          setAlert({
            type: 'error',
            message: errorData.password[0],
          });
        } else if (errorData.error) {
          // Rate limiting or other error
          setAlert({
            type: 'error',
            message: errorData.error,
          });
        } else if (errorData.detail) {
          // Generic error
          setAlert({
            type: 'error',
            message: errorData.detail,
          });
        } else {
          // Unknown error
          setAlert({
            type: 'error',
            message: 'Registration failed. Please try again.',
          });
        }
      }
    } catch (error) {
      console.error('Registration error:', error);
      setAlert({
        type: 'error',
        message: 'An unexpected error occurred. Please try again later.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="register-page">
      <div className="register-container">
        {/* Header */}
        <div className="register-header">
          <h1 className="register-title">Create Your Account</h1>
          <p className="register-subtitle">
            Join Tech Watch Platform to start monitoring technology trends
          </p>
        </div>

        {/* Alert Messages */}
        {alert && (
          <Alert
            type={alert.type}
            message={alert.message}
            dismissible={true}
            onDismiss={() => setAlert(null)}
          />
        )}

        {/* Registration Form */}
        <RegistrationForm onSubmit={handleRegistration} isLoading={isLoading} />

        {/* Footer */}
        <div className="register-footer">
          <p className="footer-text">
            Already have an account?{' '}
            <Link to="/login" className="footer-link">
              Sign in
            </Link>
          </p>
        </div>

        {/* Additional Information */}
        <div className="register-info">
          <p className="info-text">
            By creating an account, you agree to our Terms of Service and Privacy Policy.
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
