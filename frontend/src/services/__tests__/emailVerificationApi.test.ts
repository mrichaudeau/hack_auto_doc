/**
 * Tests for Email Verification API Service
 *
 * Uses Mock Service Worker (MSW) to mock HTTP responses from the backend API.
 * Tests cover success cases, various error scenarios, and edge cases.
 */

import { describe, it, expect, beforeAll, afterEach, afterAll } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import {
  verifyEmail,
  resendVerificationEmail,
  EmailVerificationError,
} from '../emailVerificationApi';

// ============================================================================
// MSW Server Setup
// ============================================================================

const BASE_URL = 'http://localhost:8000';
const server = setupServer();

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// ============================================================================
// verifyEmail() Tests
// ============================================================================

describe('verifyEmail', () => {
  it('should verify email successfully with valid token', async () => {
    server.use(
      http.get(`${BASE_URL}/api/auth/verify-email/`, () => {
        return HttpResponse.json({
          message: 'Email verified successfully. You can now log in.',
          is_active: true,
          is_email_verified: true,
        });
      })
    );

    const result = await verifyEmail('550e8400-e29b-41d4-a716-446655440000');

    expect(result).toEqual({
      message: 'Email verified successfully. You can now log in.',
      is_active: true,
      is_email_verified: true,
    });
    expect(result.is_email_verified).toBe(true);
    expect(result.is_active).toBe(true);
  });

  it('should handle invalid token error (400)', async () => {
    server.use(
      http.get(`${BASE_URL}/api/auth/verify-email/`, () => {
        return HttpResponse.json(
          {
            error: 'token_invalid',
            message: 'Invalid verification token.',
            resend_url: '/api/auth/resend-verification/',
          },
          { status: 400 }
        );
      })
    );

    await expect(verifyEmail('invalid-token-123')).rejects.toThrow(
      EmailVerificationError
    );

    try {
      await verifyEmail('invalid-token-123');
    } catch (error) {
      expect(error).toBeInstanceOf(EmailVerificationError);
      if (error instanceof EmailVerificationError) {
        expect(error.statusCode).toBe(400);
        expect(error.errorCode).toBe('token_invalid');
        expect(error.details?.message).toBe('Invalid verification token.');
        expect(error.details?.resend_url).toBe('/api/auth/resend-verification/');
      }
    }
  });

  it('should handle token already used error (400)', async () => {
    server.use(
      http.get(`${BASE_URL}/api/auth/verify-email/`, () => {
        return HttpResponse.json(
          {
            error: 'token_used',
            message: 'This verification token has already been used.',
            resend_url: '/api/auth/resend-verification/',
          },
          { status: 400 }
        );
      })
    );

    try {
      await verifyEmail('used-token');
    } catch (error) {
      expect(error).toBeInstanceOf(EmailVerificationError);
      if (error instanceof EmailVerificationError) {
        expect(error.statusCode).toBe(400);
        expect(error.errorCode).toBe('token_used');
        expect(error.message).toBe('This verification token has already been used.');
      }
    }
  });

  it('should handle token expired error (410)', async () => {
    server.use(
      http.get(`${BASE_URL}/api/auth/verify-email/`, () => {
        return HttpResponse.json(
          {
            error: 'token_expired',
            message: 'Verification link has expired. Please request a new one.',
            resend_url: '/api/auth/resend-verification/',
          },
          { status: 410 }
        );
      })
    );

    try {
      await verifyEmail('expired-token');
    } catch (error) {
      expect(error).toBeInstanceOf(EmailVerificationError);
      if (error instanceof EmailVerificationError) {
        expect(error.statusCode).toBe(410);
        expect(error.errorCode).toBe('token_expired');
        expect(error.message).toBe(
          'Verification link has expired. Please request a new one.'
        );
      }
    }
  });

  it('should handle missing token error (400)', async () => {
    server.use(
      http.get(`${BASE_URL}/api/auth/verify-email/`, () => {
        return HttpResponse.json(
          {
            error: 'token_required',
            message: 'Verification token is required.',
            resend_url: '/api/auth/resend-verification/',
          },
          { status: 400 }
        );
      })
    );

    try {
      await verifyEmail('');
    } catch (error) {
      expect(error).toBeInstanceOf(EmailVerificationError);
      if (error instanceof EmailVerificationError) {
        expect(error.statusCode).toBe(400);
        expect(error.errorCode).toBe('token_required');
      }
    }
  });

  it('should handle network errors', async () => {
    server.use(
      http.get(`${BASE_URL}/api/auth/verify-email/`, () => {
        return HttpResponse.error();
      })
    );

    try {
      await verifyEmail('some-token');
    } catch (error) {
      expect(error).toBeInstanceOf(EmailVerificationError);
      if (error instanceof EmailVerificationError) {
        expect(error.message).toBe('Network error. Please check your connection.');
        expect(error.statusCode).toBeUndefined();
      }
    }
  });
});

// ============================================================================
// resendVerificationEmail() Tests
// ============================================================================

describe('resendVerificationEmail', () => {
  it('should resend verification email successfully', async () => {
    server.use(
      http.post(`${BASE_URL}/api/auth/resend-verification/`, () => {
        return HttpResponse.json({
          message: 'Verification email sent successfully. Please check your inbox.',
          attempts_remaining: 2,
        });
      })
    );

    const result = await resendVerificationEmail('user@example.com');

    expect(result).toEqual({
      message: 'Verification email sent successfully. Please check your inbox.',
      attempts_remaining: 2,
    });
    expect(result.attempts_remaining).toBe(2);
  });

  it('should handle rate limit exceeded (429)', async () => {
    server.use(
      http.post(`${BASE_URL}/api/auth/resend-verification/`, () => {
        return HttpResponse.json(
          {
            error: 'rate_limit_exceeded',
            message: 'Too many verification email requests. Please try again later.',
            retry_after_seconds: 43200,
            max_attempts: 3,
            attempts_remaining: 0,
          },
          { status: 429 }
        );
      })
    );

    try {
      await resendVerificationEmail('user@example.com');
    } catch (error) {
      expect(error).toBeInstanceOf(EmailVerificationError);
      if (error instanceof EmailVerificationError) {
        expect(error.statusCode).toBe(429);
        expect(error.errorCode).toBe('rate_limit_exceeded');
        expect(error.details?.retry_after_seconds).toBe(43200);
        expect(error.details?.max_attempts).toBe(3);
        expect(error.details?.attempts_remaining).toBe(0);
      }
    }
  });

  it('should handle non-existent email error (400)', async () => {
    server.use(
      http.post(`${BASE_URL}/api/auth/resend-verification/`, () => {
        return HttpResponse.json(
          {
            message: 'Validation error',
            email: ['No account found with this email address.'],
          },
          { status: 400 }
        );
      })
    );

    try {
      await resendVerificationEmail('nonexistent@example.com');
    } catch (error) {
      expect(error).toBeInstanceOf(EmailVerificationError);
      if (error instanceof EmailVerificationError) {
        expect(error.statusCode).toBe(400);
        expect(error.details?.email).toContain('No account found with this email address.');
      }
    }
  });

  it('should handle already verified email error (400)', async () => {
    server.use(
      http.post(`${BASE_URL}/api/auth/resend-verification/`, () => {
        return HttpResponse.json(
          {
            message: 'Validation error',
            email: ['This email address is already verified.'],
          },
          { status: 400 }
        );
      })
    );

    try {
      await resendVerificationEmail('verified@example.com');
    } catch (error) {
      expect(error).toBeInstanceOf(EmailVerificationError);
      if (error instanceof EmailVerificationError) {
        expect(error.statusCode).toBe(400);
        expect(error.details?.email).toContain('This email address is already verified.');
      }
    }
  });

  it('should handle invalid email format error (400)', async () => {
    server.use(
      http.post(`${BASE_URL}/api/auth/resend-verification/`, () => {
        return HttpResponse.json(
          {
            message: 'Validation error',
            email: ['Enter a valid email address.'],
          },
          { status: 400 }
        );
      })
    );

    try {
      await resendVerificationEmail('invalid-email');
    } catch (error) {
      expect(error).toBeInstanceOf(EmailVerificationError);
      if (error instanceof EmailVerificationError) {
        expect(error.statusCode).toBe(400);
        expect(error.details?.email).toContain('Enter a valid email address.');
      }
    }
  });

  it('should handle network errors', async () => {
    server.use(
      http.post(`${BASE_URL}/api/auth/resend-verification/`, () => {
        return HttpResponse.error();
      })
    );

    try {
      await resendVerificationEmail('user@example.com');
    } catch (error) {
      expect(error).toBeInstanceOf(EmailVerificationError);
      if (error instanceof EmailVerificationError) {
        expect(error.message).toBe('Network error. Please check your connection.');
        expect(error.statusCode).toBeUndefined();
      }
    }
  });

  it('should handle timeout errors', async () => {
    server.use(
      http.post(`${BASE_URL}/api/auth/resend-verification/`, async () => {
        // Simulate timeout by delaying response beyond axios timeout (10s)
        await new Promise((resolve) => setTimeout(resolve, 11000));
        return HttpResponse.json({ message: 'Should not reach here' });
      })
    );

    // This test will timeout, which triggers axios timeout handling
    // The axios config has a 10s timeout, so this should throw
    try {
      await resendVerificationEmail('user@example.com');
    } catch (error) {
      expect(error).toBeInstanceOf(EmailVerificationError);
    }
  }, 15000); // Increase test timeout to 15s to allow for axios timeout

  it('should handle server error (500)', async () => {
    server.use(
      http.post(`${BASE_URL}/api/auth/resend-verification/`, () => {
        return HttpResponse.json(
          {
            message: 'Internal server error',
          },
          { status: 500 }
        );
      })
    );

    try {
      await resendVerificationEmail('user@example.com');
    } catch (error) {
      expect(error).toBeInstanceOf(EmailVerificationError);
      if (error instanceof EmailVerificationError) {
        expect(error.statusCode).toBe(500);
        expect(error.message).toBe('Internal server error');
      }
    }
  });
});

// ============================================================================
// EmailVerificationError Class Tests
// ============================================================================

describe('EmailVerificationError', () => {
  it('should create error with all properties', () => {
    const details = {
      error: 'token_expired',
      message: 'Token expired',
      retry_after_seconds: 3600,
    };

    const error = new EmailVerificationError('Token expired', 410, details);

    expect(error).toBeInstanceOf(Error);
    expect(error).toBeInstanceOf(EmailVerificationError);
    expect(error.name).toBe('EmailVerificationError');
    expect(error.message).toBe('Token expired');
    expect(error.statusCode).toBe(410);
    expect(error.errorCode).toBe('token_expired');
    expect(error.details).toEqual(details);
  });

  it('should create error with minimal properties', () => {
    const error = new EmailVerificationError('Network error');

    expect(error.message).toBe('Network error');
    expect(error.statusCode).toBeUndefined();
    expect(error.errorCode).toBeUndefined();
    expect(error.details).toBeUndefined();
  });

  it('should maintain proper error stack trace', () => {
    const error = new EmailVerificationError('Test error');

    expect(error.stack).toBeDefined();
    expect(error.stack).toContain('EmailVerificationError');
  });
});
