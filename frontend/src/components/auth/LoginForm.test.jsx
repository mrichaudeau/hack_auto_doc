/**
 * Tests for LoginForm Component (US-3: Standard User Login, TASK-3.18)
 *
 * Comprehensive tests covering all UI states and user interactions:
 * - Form rendering with email and password fields
 * - Client-side validation (email format, required fields)
 * - Form submission with valid credentials
 * - Loading states during authentication
 * - Error display for failed login attempts
 * - Password visibility toggle
 * - Validation error clearing on re-type
 * - Accessibility (labels, ARIA attributes, keyboard navigation)
 * - 85%+ code coverage target
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginForm from './LoginForm';

describe('LoginForm', () => {
  // Mock onSubmit handler
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ==========================================================================
  // Form Rendering Tests
  // ==========================================================================

  describe('Form Rendering', () => {
    it('should render email field with label', () => {
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const emailLabel = screen.getByLabelText(/email address/i);
      expect(emailLabel).toBeInTheDocument();
      expect(emailLabel).toHaveAttribute('type', 'email');
      expect(emailLabel).toHaveAttribute('id', 'email');
      expect(emailLabel).toHaveAttribute('name', 'email');
    });

    it('should render password field with label', () => {
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const passwordLabel = screen.getByLabelText(/^password/i);
      expect(passwordLabel).toBeInTheDocument();
      expect(passwordLabel).toHaveAttribute('type', 'password');
      expect(passwordLabel).toHaveAttribute('id', 'password');
      expect(passwordLabel).toHaveAttribute('name', 'password');
    });

    it('should render submit button with correct text', () => {
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      expect(submitButton).toBeInTheDocument();
      expect(submitButton).toHaveAttribute('type', 'submit');
    });

    it('should render password visibility toggle button', () => {
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const toggleButton = screen.getByRole('button', { name: /show password/i });
      expect(toggleButton).toBeInTheDocument();
      expect(toggleButton).toHaveAttribute('type', 'button');
    });

    it('should not display server error initially', () => {
      render(<LoginForm onSubmit={mockOnSubmit} />);

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('should have noValidate attribute on form', () => {
      const { container } = render(<LoginForm onSubmit={mockOnSubmit} />);

      const form = container.querySelector('form');
      expect(form).toHaveAttribute('noValidate');
    });
  });

  // ==========================================================================
  // Email Validation Tests
  // ==========================================================================

  describe('Email Validation', () => {
    it('should show error for empty email on blur', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const emailInput = screen.getByLabelText(/email address/i);
      await user.click(emailInput);
      await user.tab(); // Blur event

      await waitFor(() => {
        expect(screen.getByText(/email address is required/i)).toBeInTheDocument();
      });
    });

    it('should show error for invalid email format on blur', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'invalid-email');
      await user.tab(); // Blur event

      await waitFor(() => {
        expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument();
      });
    });

    it('should not show error for valid email format', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');
      await user.tab(); // Blur event

      await waitFor(() => {
        expect(screen.queryByText(/please enter a valid email address/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/email address is required/i)).not.toBeInTheDocument();
      });
    });

    it('should clear error when valid email entered after invalid', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

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

      await waitFor(() => {
        expect(screen.queryByText(/please enter a valid email address/i)).not.toBeInTheDocument();
      });
    });

    it('should validate email on change after field is touched', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const emailInput = screen.getByLabelText(/email address/i);

      // Touch field by blurring
      await user.click(emailInput);
      await user.tab();

      await waitFor(() => {
        expect(screen.getByText(/email address is required/i)).toBeInTheDocument();
      });

      // Type valid email - error should clear immediately
      await user.type(emailInput, 'test@example.com');

      await waitFor(() => {
        expect(screen.queryByText(/email address is required/i)).not.toBeInTheDocument();
      });
    });

    it('should show validation error on submit if email is empty', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/email address is required/i)).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('should show validation error on submit if email is invalid', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'invalid-email');

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Password Validation Tests
  // ==========================================================================

  describe('Password Validation', () => {
    it('should show error for empty password on blur', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const passwordInput = screen.getByLabelText(/^password/i);
      await user.click(passwordInput);
      await user.tab(); // Blur event

      await waitFor(() => {
        expect(screen.getByText(/password is required/i)).toBeInTheDocument();
      });
    });

    it('should not show error for non-empty password', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const passwordInput = screen.getByLabelText(/^password/i);
      await user.type(passwordInput, 'password123');
      await user.tab(); // Blur event

      await waitFor(() => {
        expect(screen.queryByText(/password is required/i)).not.toBeInTheDocument();
      });
    });

    it('should clear error when password entered after blur', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const passwordInput = screen.getByLabelText(/^password/i);

      // Blur without entering password
      await user.click(passwordInput);
      await user.tab();

      await waitFor(() => {
        expect(screen.getByText(/password is required/i)).toBeInTheDocument();
      });

      // Type password - error should clear
      await user.type(passwordInput, 'password123');

      await waitFor(() => {
        expect(screen.queryByText(/password is required/i)).not.toBeInTheDocument();
      });
    });

    it('should show validation error on submit if password is empty', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/password is required/i)).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Form Submission Tests
  // ==========================================================================

  describe('Form Submission', () => {
    it('should call onSubmit with email and password when form is valid', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password/i);

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledTimes(1);
        expect(mockOnSubmit).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
        });
      });
    });

    it('should not call onSubmit when email is invalid', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password/i);

      await user.type(emailInput, 'invalid-email');
      await user.type(passwordInput, 'password123');

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(submitButton);

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('should not call onSubmit when both fields are empty', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/email address is required/i)).toBeInTheDocument();
        expect(screen.getByText(/password is required/i)).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('should handle form submission via Enter key', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password/i);

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledTimes(1);
      });
    });
  });

  // ==========================================================================
  // Loading State Tests
  // ==========================================================================

  describe('Loading State', () => {
    it('should disable email input during loading', () => {
      render(<LoginForm onSubmit={mockOnSubmit} loading={true} />);

      const emailInput = screen.getByLabelText(/email address/i);
      expect(emailInput).toBeDisabled();
    });

    it('should disable password input during loading', () => {
      render(<LoginForm onSubmit={mockOnSubmit} loading={true} />);

      const passwordInput = screen.getByLabelText(/^password/i);
      expect(passwordInput).toBeDisabled();
    });

    it('should disable submit button during loading', () => {
      render(<LoginForm onSubmit={mockOnSubmit} loading={true} />);

      const submitButton = screen.getByRole('button', { name: /signing in/i });
      expect(submitButton).toBeDisabled();
    });

    it('should disable password toggle button during loading', () => {
      render(<LoginForm onSubmit={mockOnSubmit} loading={true} />);

      const toggleButton = screen.getByRole('button', { name: /show password/i });
      expect(toggleButton).toBeDisabled();
    });

    it('should display loading spinner during loading', () => {
      const { container } = render(<LoginForm onSubmit={mockOnSubmit} loading={true} />);

      expect(container.querySelector('.spinner')).toBeInTheDocument();
    });

    it('should change submit button text to "Signing In..." during loading', () => {
      render(<LoginForm onSubmit={mockOnSubmit} loading={true} />);

      expect(screen.getByRole('button', { name: /signing in/i })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /^sign in$/i })).not.toBeInTheDocument();
    });

    it('should have aria-busy attribute on submit button during loading', () => {
      render(<LoginForm onSubmit={mockOnSubmit} loading={true} />);

      const submitButton = screen.getByRole('button', { name: /signing in/i });
      expect(submitButton).toHaveAttribute('aria-busy', 'true');
    });
  });

  // ==========================================================================
  // Error Display Tests
  // ==========================================================================

  describe('Error Display', () => {
    it('should display server error when error prop provided', () => {
      const errorMessage = 'Invalid email or password';
      render(<LoginForm onSubmit={mockOnSubmit} error={errorMessage} />);

      const errorElement = screen.getByRole('alert');
      expect(errorElement).toBeInTheDocument();
      expect(errorElement).toHaveTextContent(errorMessage);
    });

    it('should have aria-live attribute on error message', () => {
      const errorMessage = 'Invalid credentials';
      render(<LoginForm onSubmit={mockOnSubmit} error={errorMessage} />);

      const errorElement = screen.getByRole('alert');
      expect(errorElement).toHaveAttribute('aria-live', 'assertive');
    });

    it('should not display error when error prop is null', () => {
      render(<LoginForm onSubmit={mockOnSubmit} error={null} />);

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('should not display error when error prop is empty string', () => {
      render(<LoginForm onSubmit={mockOnSubmit} error="" />);

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('should display error icon alongside error message', () => {
      const errorMessage = 'Server error';
      const { container } = render(<LoginForm onSubmit={mockOnSubmit} error={errorMessage} />);

      const errorIcon = container.querySelector('.error-icon');
      expect(errorIcon).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Password Visibility Toggle Tests
  // ==========================================================================

  describe('Password Visibility Toggle', () => {
    it('should toggle password visibility when toggle button clicked', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const passwordInput = screen.getByLabelText(/^password/i);
      const toggleButton = screen.getByRole('button', { name: /show password/i });

      // Initially password type
      expect(passwordInput).toHaveAttribute('type', 'password');

      // Click to show password
      await user.click(toggleButton);

      await waitFor(() => {
        expect(passwordInput).toHaveAttribute('type', 'text');
        expect(screen.getByRole('button', { name: /hide password/i })).toBeInTheDocument();
      });

      // Click again to hide password
      await user.click(screen.getByRole('button', { name: /hide password/i }));

      await waitFor(() => {
        expect(passwordInput).toHaveAttribute('type', 'password');
        expect(screen.getByRole('button', { name: /show password/i })).toBeInTheDocument();
      });
    });

    it('should have correct aria-label for password toggle button', () => {
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const toggleButton = screen.getByRole('button', { name: /show password/i });
      expect(toggleButton).toHaveAttribute('aria-label', 'Show password');
    });

    it('should update aria-label when password is shown', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const toggleButton = screen.getByRole('button', { name: /show password/i });
      await user.click(toggleButton);

      await waitFor(() => {
        const hideButton = screen.getByRole('button', { name: /hide password/i });
        expect(hideButton).toHaveAttribute('aria-label', 'Hide password');
      });
    });
  });

  // ==========================================================================
  // Accessibility Tests
  // ==========================================================================

  describe('Accessibility', () => {
    it('should have proper label association for email field', () => {
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const emailInput = screen.getByLabelText(/email address/i);
      const emailLabel = screen.getByText(/email address/i);

      expect(emailLabel).toHaveAttribute('for', 'email');
      expect(emailInput).toHaveAttribute('id', 'email');
    });

    it('should have proper label association for password field', () => {
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const passwordInput = screen.getByLabelText(/^password/i);
      const passwordLabel = screen.getByText(/^password$/i);

      expect(passwordLabel).toHaveAttribute('for', 'password');
      expect(passwordInput).toHaveAttribute('id', 'password');
    });

    it('should have required indicator for email field', () => {
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const requiredIndicators = screen.getAllByText('*');
      expect(requiredIndicators.length).toBeGreaterThan(0);
    });

    it('should have aria-required attribute on email field', () => {
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const emailInput = screen.getByLabelText(/email address/i);
      expect(emailInput).toHaveAttribute('aria-required', 'true');
    });

    it('should have aria-required attribute on password field', () => {
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const passwordInput = screen.getByLabelText(/^password/i);
      expect(passwordInput).toHaveAttribute('aria-required', 'true');
    });

    it('should have aria-invalid attribute when email has error', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'invalid');
      await user.tab();

      await waitFor(() => {
        expect(emailInput).toHaveAttribute('aria-invalid', 'true');
      });
    });

    it('should have aria-invalid attribute when password has error', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const passwordInput = screen.getByLabelText(/^password/i);
      await user.click(passwordInput);
      await user.tab();

      await waitFor(() => {
        expect(passwordInput).toHaveAttribute('aria-invalid', 'true');
      });
    });

    it('should have aria-describedby linking email error to input', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, 'invalid');
      await user.tab();

      await waitFor(() => {
        expect(emailInput).toHaveAttribute('aria-describedby', 'email-error');
        expect(screen.getByText(/please enter a valid email address/i)).toHaveAttribute('id', 'email-error');
      });
    });

    it('should have aria-describedby linking password error to input', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const passwordInput = screen.getByLabelText(/^password/i);
      await user.click(passwordInput);
      await user.tab();

      await waitFor(() => {
        expect(passwordInput).toHaveAttribute('aria-describedby', 'password-error');
        expect(screen.getByText(/password is required/i)).toHaveAttribute('id', 'password-error');
      });
    });

    it('should have autocomplete attributes on inputs', () => {
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password/i);

      expect(emailInput).toHaveAttribute('autoComplete', 'email');
      expect(passwordInput).toHaveAttribute('autoComplete', 'current-password');
    });

    it('should have placeholder text for inputs', () => {
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password/i);

      expect(emailInput).toHaveAttribute('placeholder', 'you@example.com');
      expect(passwordInput).toHaveAttribute('placeholder', 'Enter your password');
    });
  });

  // ==========================================================================
  // Keyboard Navigation Tests
  // ==========================================================================

  describe('Keyboard Navigation', () => {
    it('should allow tabbing through form fields in correct order', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const toggleButton = screen.getByRole('button', { name: /show password/i });
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      // Start from email input
      emailInput.focus();
      expect(emailInput).toHaveFocus();

      // Tab to password input
      await user.tab();
      expect(passwordInput).toHaveFocus();

      // Tab to password toggle button
      await user.tab();
      expect(toggleButton).toHaveFocus();

      // Tab to submit button
      await user.tab();
      expect(submitButton).toHaveFocus();
    });

    it('should allow password toggle button activation via keyboard', async () => {
      const user = userEvent.setup();
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const passwordInput = screen.getByLabelText(/^password/i);
      const toggleButton = screen.getByRole('button', { name: /show password/i });

      toggleButton.focus();
      expect(toggleButton).toHaveFocus();

      // Activate with Enter key
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(passwordInput).toHaveAttribute('type', 'text');
      });
    });

    it('should have tabIndex on password toggle button', () => {
      render(<LoginForm onSubmit={mockOnSubmit} />);

      const toggleButton = screen.getByRole('button', { name: /show password/i });
      expect(toggleButton).toHaveAttribute('tabIndex', '0');
    });
  });
});
