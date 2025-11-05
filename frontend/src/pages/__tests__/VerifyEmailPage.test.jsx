/**
 * Tests for VerifyEmailPage Component
 *
 * Comprehensive tests covering all UI states and user interactions:
 * - Loading state
 * - Success state with navigation
 * - Error states (invalid, used, expired, network errors)
 * - Action button behaviors
 * - URL parameter extraction
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import VerifyEmailPage from '../VerifyEmailPage';
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
 * Helper function to render VerifyEmailPage with router context
 * @param {string} initialUrl - Initial URL with query parameters
 */
const renderWithRouter = (initialUrl = '/verify-email?token=abc123') => {
  const navigate = vi.fn();

  const result = render(
    <MemoryRouter initialEntries={[initialUrl]}>
      <Routes>
        <Route path="/verify-email" element={<VerifyEmailPage />} />
        <Route path="/login" element={<div>Login Page</div>} />
        <Route path="/resend-verification" element={<div>Resend Page</div>} />
        <Route path="/" element={<div>Home Page</div>} />
      </Routes>
    </MemoryRouter>
  );

  return { ...result, navigate };
};

describe('VerifyEmailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ==========================================================================
  // Loading State Tests
  // ==========================================================================

  describe('Loading State', () => {
    it('should show loading state initially', () => {
      // Mock API to delay response
      vi.mocked(api.verifyEmail).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      );

      renderWithRouter();

      expect(screen.getByText(/verifying your email address/i)).toBeInTheDocument();
      expect(screen.getByText(/please wait while we verify your account/i)).toBeInTheDocument();
      expect(document.querySelector('.spinner')).toBeInTheDocument();
    });

    it('should call API with token from URL parameter', async () => {
      vi.mocked(api.verifyEmail).mockResolvedValue({
        message: 'Email verified successfully',
        is_active: true,
        is_email_verified: true,
      });

      renderWithRouter('/verify-email?token=test-token-123');

      await waitFor(() => {
        expect(api.verifyEmail).toHaveBeenCalledWith('test-token-123');
      });
    });
  });

  // ==========================================================================
  // Success State Tests
  // ==========================================================================

  describe('Success State', () => {
    it('should show success message on successful verification', async () => {
      vi.mocked(api.verifyEmail).mockResolvedValue({
        message: 'Email verified successfully. You can now log in.',
        is_active: true,
        is_email_verified: true,
      });

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByText(/email verified successfully/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/you can now log in to your account/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /go to login/i })).toBeInTheDocument();
    });

    it('should navigate to login page when button clicked', async () => {
      const user = userEvent.setup();

      vi.mocked(api.verifyEmail).mockResolvedValue({
        message: 'Email verified successfully',
        is_active: true,
        is_email_verified: true,
      });

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /go to login/i })).toBeInTheDocument();
      });

      const loginButton = screen.getByRole('button', { name: /go to login/i });
      await user.click(loginButton);

      // After navigation, should see login page
      await waitFor(() => {
        expect(screen.getByText('Login Page')).toBeInTheDocument();
      });
    });

    it('should display success icon', async () => {
      vi.mocked(api.verifyEmail).mockResolvedValue({
        message: 'Email verified successfully',
        is_active: true,
        is_email_verified: true,
      });

      renderWithRouter();

      await waitFor(() => {
        expect(document.querySelector('.icon-container.success')).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Error State Tests - Invalid Token
  // ==========================================================================

  describe('Error State - Invalid Token', () => {
    it('should show error for invalid token', async () => {
      vi.mocked(api.verifyEmail).mockRejectedValue(
        new EmailVerificationError('Invalid verification token.', 400, {
          error: 'token_invalid',
          message: 'Invalid verification token.',
        })
      );

      renderWithRouter('/verify-email?token=invalid');

      await waitFor(() => {
        expect(screen.getByText(/invalid verification link/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/the verification link is invalid or malformed/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /resend verification email/i })).toBeInTheDocument();
    });

    it('should navigate to resend page when resend button clicked', async () => {
      const user = userEvent.setup();

      vi.mocked(api.verifyEmail).mockRejectedValue(
        new EmailVerificationError('Invalid verification token.', 400, {
          error: 'token_invalid',
          message: 'Invalid verification token.',
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /resend verification email/i })).toBeInTheDocument();
      });

      const resendButton = screen.getByRole('button', { name: /resend verification email/i });
      await user.click(resendButton);

      await waitFor(() => {
        expect(screen.getByText('Resend Page')).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Error State Tests - Used Token
  // ==========================================================================

  describe('Error State - Used Token', () => {
    it('should show error for token already used', async () => {
      vi.mocked(api.verifyEmail).mockRejectedValue(
        new EmailVerificationError('This verification token has already been used.', 400, {
          error: 'token_used',
          message: 'This verification token has already been used.',
        })
      );

      renderWithRouter('/verify-email?token=used-token');

      await waitFor(() => {
        expect(screen.getByText(/this verification link has already been used/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/your email may already be verified/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /go to login/i })).toBeInTheDocument();
    });

    it('should display warning icon for used token', async () => {
      vi.mocked(api.verifyEmail).mockRejectedValue(
        new EmailVerificationError('Token already used', 400, {
          error: 'token_used',
          message: 'Token already used',
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(document.querySelector('.icon-container.warning')).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Error State Tests - Expired Token
  // ==========================================================================

  describe('Error State - Expired Token', () => {
    it('should show error for expired token', async () => {
      vi.mocked(api.verifyEmail).mockRejectedValue(
        new EmailVerificationError('Verification link has expired', 410, {
          error: 'token_expired',
          message: 'Verification link has expired. Please request a new one.',
        })
      );

      renderWithRouter('/verify-email?token=expired-token');

      await waitFor(() => {
        expect(screen.getByText(/verification link expired/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/this verification link has expired.*request a new one/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /resend verification email/i })).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Error State Tests - Missing Token
  // ==========================================================================

  describe('Error State - Missing Token', () => {
    it('should show error when token parameter is missing', async () => {
      renderWithRouter('/verify-email');

      await waitFor(() => {
        expect(screen.getByText(/invalid verification link/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/the verification link is invalid or malformed/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /resend verification email/i })).toBeInTheDocument();

      // API should not be called when token is missing
      expect(api.verifyEmail).not.toHaveBeenCalled();
    });

    it('should show error when token parameter is empty string', async () => {
      renderWithRouter('/verify-email?token=');

      await waitFor(() => {
        expect(screen.getByText(/invalid verification link/i)).toBeInTheDocument();
      });

      expect(api.verifyEmail).not.toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Error State Tests - Network Error
  // ==========================================================================

  describe('Error State - Network Error', () => {
    it('should show connection error for network failures', async () => {
      vi.mocked(api.verifyEmail).mockRejectedValue(
        new EmailVerificationError('Network error. Please check your connection.', undefined, {
          message: 'Network error. Please check your connection.',
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByText(/connection error/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/please check your internet connection and try again/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });

    it('should display error icon for network errors', async () => {
      vi.mocked(api.verifyEmail).mockRejectedValue(
        new EmailVerificationError('Network error', undefined, {
          message: 'Network error',
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(document.querySelector('.icon-container.error')).toBeInTheDocument();
      });
    });

    it('should retry API call when retry button clicked', async () => {
      const user = userEvent.setup();

      // First call fails
      vi.mocked(api.verifyEmail)
        .mockRejectedValueOnce(
          new EmailVerificationError('Network error', undefined, {
            message: 'Network error',
          })
        )
        // Second call succeeds
        .mockResolvedValueOnce({
          message: 'Email verified successfully',
          is_active: true,
          is_email_verified: true,
        });

      renderWithRouter();

      // Wait for error to appear
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });

      expect(api.verifyEmail).toHaveBeenCalledTimes(1);

      // Click retry button
      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      // Should show success after retry succeeds
      await waitFor(() => {
        expect(screen.getByText(/email verified successfully/i)).toBeInTheDocument();
      });

      // API should have been called twice (initial + retry)
      expect(api.verifyEmail).toHaveBeenCalledTimes(2);
    });
  });

  // ==========================================================================
  // Error State Tests - Unknown Error
  // ==========================================================================

  describe('Error State - Unknown Error', () => {
    it('should handle unexpected errors', async () => {
      // Throw a non-EmailVerificationError
      vi.mocked(api.verifyEmail).mockRejectedValue(new Error('Unexpected error'));

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByText(/an unexpected error occurred/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/please try again later/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });

    it('should handle EmailVerificationError with unknown error code', async () => {
      vi.mocked(api.verifyEmail).mockRejectedValue(
        new EmailVerificationError('Unknown error', 500, {
          error: 'unknown_error',
          message: 'Unknown error',
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByText(/connection error/i)).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Secondary Actions Tests
  // ==========================================================================

  describe('Secondary Actions', () => {
    it('should show "Back to Home" link for error states (not login)', async () => {
      vi.mocked(api.verifyEmail).mockRejectedValue(
        new EmailVerificationError('Invalid token', 400, {
          error: 'token_invalid',
          message: 'Invalid token',
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByText(/back to home/i)).toBeInTheDocument();
      });
    });

    it('should NOT show "Back to Home" link for used token (login action)', async () => {
      vi.mocked(api.verifyEmail).mockRejectedValue(
        new EmailVerificationError('Token used', 400, {
          error: 'token_used',
          message: 'Token used',
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByText(/this verification link has already been used/i)).toBeInTheDocument();
      });

      expect(screen.queryByText(/back to home/i)).not.toBeInTheDocument();
    });

    it('should navigate to home when "Back to Home" link clicked', async () => {
      const user = userEvent.setup();

      vi.mocked(api.verifyEmail).mockRejectedValue(
        new EmailVerificationError('Invalid token', 400, {
          error: 'token_invalid',
          message: 'Invalid token',
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByText(/back to home/i)).toBeInTheDocument();
      });

      const homeLink = screen.getByText(/back to home/i);
      await user.click(homeLink);

      await waitFor(() => {
        expect(screen.getByText('Home Page')).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Token Extraction Tests
  // ==========================================================================

  describe('Token Extraction', () => {
    it('should extract token from query parameter', async () => {
      vi.mocked(api.verifyEmail).mockResolvedValue({
        message: 'Success',
        is_active: true,
        is_email_verified: true,
      });

      renderWithRouter('/verify-email?token=my-special-token-123');

      await waitFor(() => {
        expect(api.verifyEmail).toHaveBeenCalledWith('my-special-token-123');
      });
    });

    it('should handle URL with multiple query parameters', async () => {
      vi.mocked(api.verifyEmail).mockResolvedValue({
        message: 'Success',
        is_active: true,
        is_email_verified: true,
      });

      renderWithRouter('/verify-email?foo=bar&token=correct-token&baz=qux');

      await waitFor(() => {
        expect(api.verifyEmail).toHaveBeenCalledWith('correct-token');
      });
    });
  });

  // ==========================================================================
  // Accessibility Tests
  // ==========================================================================

  describe('Accessibility', () => {
    it('should have accessible button labels', async () => {
      vi.mocked(api.verifyEmail).mockResolvedValue({
        message: 'Success',
        is_active: true,
        is_email_verified: true,
      });

      renderWithRouter();

      await waitFor(() => {
        const button = screen.getByRole('button', { name: /go to login/i });
        expect(button).toBeInTheDocument();
      });
    });

    it('should have semantic HTML structure', async () => {
      vi.mocked(api.verifyEmail).mockResolvedValue({
        message: 'Success',
        is_active: true,
        is_email_verified: true,
      });

      renderWithRouter();

      await waitFor(() => {
        // Check for heading
        expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
      });
    });
  });
});
