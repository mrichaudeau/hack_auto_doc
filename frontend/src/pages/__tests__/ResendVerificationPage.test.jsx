/**
 * Tests for ResendVerificationPage Component
 *
 * Comprehensive tests covering all UI states and user interactions:
 * - Form rendering and validation
 * - Email format validation
 * - API submission and success state
 * - Error states (not found, already verified, rate limit, network)
 * - Rate limit countdown timer
 * - Navigation flows
 * - Accessibility
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ResendVerificationPage from '../ResendVerificationPage';
import { EmailVerificationError } from '../../services/emailVerificationApi';
import * as api from '../../services/emailVerificationApi';

// Mock only the functions, not the class
vi.mock('../../services/emailVerificationApi', async () => {
  const actual = await vi.importActual('../../services/emailVerificationApi');
  return {
    ...actual,
    verifyEmail: vi.fn(),
    resendVerificationEmail: vi.fn(),
  };
});

/**
 * Helper function to render ResendVerificationPage with router context
 * @param {string} initialUrl - Initial URL path
 */
const renderWithRouter = (initialUrl = '/resend-verification') => {
  const navigate = vi.fn();

  const result = render(
    <MemoryRouter initialEntries={[initialUrl]}>
      <Routes>
        <Route path="/resend-verification" element={<ResendVerificationPage />} />
        <Route path="/login" element={<div>Login Page</div>} />
        <Route path="/register" element={<div>Register Page</div>} />
        <Route path="/" element={<div>Home Page</div>} />
      </Routes>
    </MemoryRouter>
  );

  return { ...result, navigate };
};

describe('ResendVerificationPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  // ==========================================================================
  // Form Rendering Tests
  // ==========================================================================

  describe('Form Rendering', () => {
    it('should render form with email input and submit button', () => {
      renderWithRouter();

      expect(screen.getByRole('heading', { name: /resend verification email/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send verification email/i })).toBeInTheDocument();
      expect(screen.getByText(/enter your email address to receive a new verification link/i)).toBeInTheDocument();
    });

    it('should render "Back to Home" link', () => {
      renderWithRouter();

      const homeLink = screen.getByText(/back to home/i);
      expect(homeLink).toBeInTheDocument();
      expect(homeLink).toHaveAttribute('href', '/');
    });

    it('should have accessible form structure', () => {
      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      expect(emailInput).toHaveAttribute('type', 'email');
      expect(emailInput).toHaveAttribute('required');
      expect(emailInput).toHaveAttribute('placeholder', 'you@example.com');
    });
  });

  // ==========================================================================
  // Email Validation Tests
  // ==========================================================================

  describe('Email Validation', () => {
    it('should show error for invalid email format on blur', async () => {
      const user = userEvent.setup();
      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'invalid-email');
      await user.tab(); // Blur event

      await waitFor(() => {
        expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument();
      });
    });

    it('should not show error for valid email format', async () => {
      const user = userEvent.setup();
      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');
      await user.tab(); // Blur event

      await waitFor(() => {
        expect(screen.queryByText(/please enter a valid email address/i)).not.toBeInTheDocument();
      });
    });

    it('should clear validation error when valid email entered', async () => {
      const user = userEvent.setup();
      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);

      // Enter invalid email
      await user.type(emailInput, 'invalid');
      await user.tab();

      await waitFor(() => {
        expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument();
      });

      // Clear and enter valid email
      await user.clear(emailInput);
      await user.type(emailInput, 'valid@example.com');
      await user.tab();

      await waitFor(() => {
        expect(screen.queryByText(/please enter a valid email address/i)).not.toBeInTheDocument();
      });
    });

    it('should disable submit button when email is empty', () => {
      renderWithRouter();

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      expect(submitButton).toBeDisabled();
    });

    it('should disable submit button when email is invalid', async () => {
      const user = userEvent.setup();
      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'invalid-email');
      await user.tab();

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /send verification email/i });
        expect(submitButton).toBeDisabled();
      });
    });

    it('should enable submit button when valid email entered', async () => {
      const user = userEvent.setup();
      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /send verification email/i });
        expect(submitButton).not.toBeDisabled();
      });
    });
  });

  // ==========================================================================
  // Form Submission Tests
  // ==========================================================================

  describe('Form Submission', () => {
    it('should show loading state during API call', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      );

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/sending email/i)).toBeInTheDocument();
        expect(screen.getByText(/please wait while we send your verification email/i)).toBeInTheDocument();
        expect(document.querySelector('.spinner')).toBeInTheDocument();
      });
    });

    it('should call API with correct email', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockResolvedValue({
        message: 'Email sent',
        attempts_remaining: 2,
      });

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(api.resendVerificationEmail).toHaveBeenCalledWith('test@example.com');
      });
    });

    it('should prevent submission with invalid email', async () => {
      const user = userEvent.setup();
      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'invalid-email');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      expect(api.resendVerificationEmail).not.toHaveBeenCalled();
      expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Success State Tests
  // ==========================================================================

  describe('Success State', () => {
    it('should show success message after successful resend', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockResolvedValue({
        message: 'Email sent',
        attempts_remaining: 2,
      });

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/verification email sent successfully/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/please check your inbox and spam folder/i)).toBeInTheDocument();
    });

    it('should display attempts remaining', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockResolvedValue({
        message: 'Email sent',
        attempts_remaining: 2,
      });

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/you have 2 attempts remaining \(out of 3\)/i)).toBeInTheDocument();
      });
    });

    it('should handle singular attempt remaining correctly', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockResolvedValue({
        message: 'Email sent',
        attempts_remaining: 1,
      });

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/you have 1 attempt remaining \(out of 3\)/i)).toBeInTheDocument();
      });
    });

    it('should display success icon', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockResolvedValue({
        message: 'Email sent',
        attempts_remaining: 2,
      });

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(document.querySelector('.icon-container.success')).toBeInTheDocument();
      });
    });

    it('should show "Send Another Email" button after success', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockResolvedValue({
        message: 'Email sent',
        attempts_remaining: 2,
      });

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /send another email/i })).toBeInTheDocument();
      });
    });

    it('should return to form when "Send Another Email" clicked', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockResolvedValue({
        message: 'Email sent',
        attempts_remaining: 2,
      });

      renderWithRouter();

      // Submit form
      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /send another email/i })).toBeInTheDocument();
      });

      // Click "Send Another Email"
      const sendAnotherButton = screen.getByRole('button', { name: /send another email/i });
      await user.click(sendAnotherButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /send verification email/i })).toBeInTheDocument();
      });
    });

    it('should show "Go to Login" link after success', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockResolvedValue({
        message: 'Email sent',
        attempts_remaining: 2,
      });

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        const loginLink = screen.getByText(/go to login/i);
        expect(loginLink).toBeInTheDocument();
        expect(loginLink).toHaveAttribute('href', '/login');
      });
    });

    it('should clear email input after successful submission', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockResolvedValue({
        message: 'Email sent',
        attempts_remaining: 2,
      });

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/verification email sent successfully/i)).toBeInTheDocument();
      });

      // Click "Send Another Email" to return to form
      const sendAnotherButton = screen.getByRole('button', { name: /send another email/i });
      await user.click(sendAnotherButton);

      await waitFor(() => {
        const emailInputAgain = screen.getByLabelText(/email address/i);
        expect(emailInputAgain).toHaveValue('');
      });
    });
  });

  // ==========================================================================
  // Error State Tests - Email Not Found
  // ==========================================================================

  describe('Error State - Email Not Found', () => {
    it('should show error for non-existent email', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockRejectedValue(
        new EmailVerificationError('User not found', 400, {
          error: 'user_not_found',
          message: 'User not found',
        })
      );

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'nonexistent@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/no account found with this email address/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/please check your email or sign up for a new account/i)).toBeInTheDocument();
    });

    it('should display warning icon for not found error', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockRejectedValue(
        new EmailVerificationError('User not found', 400, {
          error: 'user_not_found',
          message: 'User not found',
        })
      );

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(document.querySelector('.icon-container.warning')).toBeInTheDocument();
      });
    });

    it('should show link to register page', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockRejectedValue(
        new EmailVerificationError('User not found', 400, {
          error: 'user_not_found',
          message: 'User not found',
        })
      );

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        const registerLink = screen.getByText(/sign up for a new account/i);
        expect(registerLink).toBeInTheDocument();
        expect(registerLink).toHaveAttribute('href', '/register');
      });
    });
  });

  // ==========================================================================
  // Error State Tests - Already Verified
  // ==========================================================================

  describe('Error State - Already Verified', () => {
    it('should show info message for already verified email', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockRejectedValue(
        new EmailVerificationError('Email already verified', 400, {
          error: 'already_verified',
          message: 'Email already verified',
        })
      );

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'verified@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/this email address is already verified/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/you can proceed to login/i)).toBeInTheDocument();
    });

    it('should display success icon for already verified', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockRejectedValue(
        new EmailVerificationError('Email already verified', 400, {
          error: 'already_verified',
          message: 'Email already verified',
        })
      );

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(document.querySelector('.icon-container.success')).toBeInTheDocument();
      });
    });

    it('should show "Go to Login" button for already verified', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockRejectedValue(
        new EmailVerificationError('Email already verified', 400, {
          error: 'already_verified',
          message: 'Email already verified',
        })
      );

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /go to login/i })).toBeInTheDocument();
      });
    });

    it('should navigate to login page when button clicked', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockRejectedValue(
        new EmailVerificationError('Email already verified', 400, {
          error: 'already_verified',
          message: 'Email already verified',
        })
      );

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /go to login/i })).toBeInTheDocument();
      });

      const loginButton = screen.getByRole('button', { name: /go to login/i });
      await user.click(loginButton);

      await waitFor(() => {
        expect(screen.getByText('Login Page')).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Error State Tests - Rate Limit
  // ==========================================================================

  describe('Error State - Rate Limit', () => {
    it('should show rate limit error', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockRejectedValue(
        new EmailVerificationError('Too many requests', 429, {
          error: 'rate_limit_exceeded',
          message: 'Too many requests',
          retry_after_seconds: 3600,
        })
      );

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/too many requests.*please try again later/i)).toBeInTheDocument();
      });
    });

    it('should display countdown timer for rate limit', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockRejectedValue(
        new EmailVerificationError('Too many requests', 429, {
          error: 'rate_limit_exceeded',
          message: 'Too many requests',
          retry_after_seconds: 3600, // 1 hour
        })
      );

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/you can try again in 1 hour/i)).toBeInTheDocument();
      });
    });

    it('should countdown timer and reset form when expired', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockRejectedValue(
        new EmailVerificationError('Too many requests', 429, {
          error: 'rate_limit_exceeded',
          message: 'Too many requests',
          retry_after_seconds: 2, // 2 seconds for testing
        })
      );

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/you can try again in 2 seconds/i)).toBeInTheDocument();
      });

      // Advance timer by 1 second
      vi.advanceTimersByTime(1000);

      await waitFor(() => {
        expect(screen.getByText(/you can try again in 1 second/i)).toBeInTheDocument();
      });

      // Advance timer by 1 more second (total 2 seconds)
      vi.advanceTimersByTime(1000);

      // After countdown expires, should return to idle state
      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /send verification email/i })).toBeInTheDocument();
      });
    });

    it('should format time correctly for hours and minutes', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockRejectedValue(
        new EmailVerificationError('Too many requests', 429, {
          error: 'rate_limit_exceeded',
          message: 'Too many requests',
          retry_after_seconds: 7500, // 2 hours and 5 minutes
        })
      );

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/you can try again in 2 hours and 5 minutes/i)).toBeInTheDocument();
      });
    });

    it('should display warning icon for rate limit', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockRejectedValue(
        new EmailVerificationError('Too many requests', 429, {
          error: 'rate_limit_exceeded',
          message: 'Too many requests',
          retry_after_seconds: 3600,
        })
      );

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(document.querySelector('.icon-container.warning')).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Error State Tests - Network Error
  // ==========================================================================

  describe('Error State - Network Error', () => {
    it('should show network error message', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockRejectedValue(
        new EmailVerificationError('Network error', undefined, {
          message: 'Network error. Please check your connection.',
        })
      );

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/connection error.*please try again/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/please check your internet connection/i)).toBeInTheDocument();
    });

    it('should display error icon for network error', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockRejectedValue(
        new EmailVerificationError('Network error', undefined, {
          message: 'Network error',
        })
      );

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(document.querySelector('.icon-container.error')).toBeInTheDocument();
      });
    });

    it('should show "Try Again" button for network error', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockRejectedValue(
        new EmailVerificationError('Network error', undefined, {
          message: 'Network error',
        })
      );

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
      });
    });

    it('should return to form when "Try Again" clicked', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockRejectedValue(
        new EmailVerificationError('Network error', undefined, {
          message: 'Network error',
        })
      );

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
      });

      const tryAgainButton = screen.getByRole('button', { name: /try again/i });
      await user.click(tryAgainButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /send verification email/i })).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Error State Tests - Unknown Error
  // ==========================================================================

  describe('Error State - Unknown Error', () => {
    it('should handle unexpected errors', async () => {
      const user = userEvent.setup();

      // Throw a non-EmailVerificationError
      vi.mocked(api.resendVerificationEmail).mockRejectedValue(new Error('Unexpected error'));

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/an unexpected error occurred/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/please try again later/i)).toBeInTheDocument();
    });

    it('should handle EmailVerificationError with unknown error code', async () => {
      const user = userEvent.setup();

      vi.mocked(api.resendVerificationEmail).mockRejectedValue(
        new EmailVerificationError('Unknown error', 500, {
          error: 'unknown_error',
          message: 'Unknown error',
        })
      );

      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/an error occurred.*please try again/i)).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Navigation Tests
  // ==========================================================================

  describe('Navigation', () => {
    it('should navigate to home when "Back to Home" clicked', async () => {
      const user = userEvent.setup();
      renderWithRouter();

      const homeLink = screen.getByText(/back to home/i);
      await user.click(homeLink);

      await waitFor(() => {
        expect(screen.getByText('Home Page')).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Accessibility Tests
  // ==========================================================================

  describe('Accessibility', () => {
    it('should have accessible form labels', () => {
      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      expect(emailInput).toBeInTheDocument();
    });

    it('should have proper ARIA attributes for invalid email', async () => {
      const user = userEvent.setup();
      renderWithRouter();

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'invalid');
      await user.tab();

      await waitFor(() => {
        expect(emailInput).toHaveAttribute('aria-invalid', 'true');
        expect(emailInput).toHaveAttribute('aria-describedby', 'email-error');
      });
    });

    it('should have semantic heading structure', () => {
      renderWithRouter();

      expect(screen.getByRole('heading', { name: /resend verification email/i })).toBeInTheDocument();
    });

    it('should have accessible button', () => {
      renderWithRouter();

      const submitButton = screen.getByRole('button', { name: /send verification email/i });
      expect(submitButton).toBeInTheDocument();
    });
  });
});
