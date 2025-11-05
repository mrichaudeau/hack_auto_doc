/**
 * Email Verification API Service
 *
 * Handles all email verification-related API calls from the React frontend.
 * Provides type-safe functions for email verification and resend verification email.
 *
 * @module emailVerificationApi
 */

import axios, { AxiosError } from 'axios';

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Request body for resending verification email
 */
export interface ResendVerificationRequest {
  email: string;
}

/**
 * Success response from email verification endpoint
 */
export interface VerifyEmailResponse {
  message: string;
  is_active: boolean;
  is_email_verified: boolean;
}

/**
 * Success response from resend verification email endpoint
 */
export interface ResendVerificationResponse {
  message: string;
  attempts_remaining: number;
}

/**
 * Error response structure from API
 */
export interface ApiError {
  error?: string;
  message: string;
  retry_after_seconds?: number;
  max_attempts?: number;
  attempts_remaining?: number;
  resend_url?: string;
  email?: string[];
}

// ============================================================================
// Custom Error Class
// ============================================================================

/**
 * Custom error class for email verification API errors
 * Provides structured error information including status codes and details
 */
export class EmailVerificationError extends Error {
  public statusCode?: number;
  public errorCode?: string;
  public details?: ApiError;

  constructor(message: string, statusCode?: number, details?: ApiError) {
    super(message);
    this.name = 'EmailVerificationError';
    this.statusCode = statusCode;
    this.errorCode = details?.error;
    this.details = details;

    // Maintains proper stack trace for where error was thrown (V8 only)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, EmailVerificationError);
    }
  }
}

// ============================================================================
// Axios Configuration
// ============================================================================

/**
 * Configured axios instance for email verification API calls
 * Uses environment variable for base URL with fallback to localhost
 */
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

/**
 * Response interceptor for centralized error handling
 * Converts axios errors into EmailVerificationError instances
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    // Server responded with error status
    if (error.response) {
      const { status, data } = error.response;
      const message = data.message || 'An error occurred';
      throw new EmailVerificationError(message, status, data);
    }
    // Request was made but no response received (network error)
    else if (error.request) {
      throw new EmailVerificationError(
        'Network error. Please check your connection.',
        undefined,
        { message: 'Network error. Please check your connection.' }
      );
    }
    // Something else happened in setting up the request
    else {
      throw new EmailVerificationError(
        'An unexpected error occurred.',
        undefined,
        { message: 'An unexpected error occurred.' }
      );
    }
  }
);

// ============================================================================
// API Functions
// ============================================================================

/**
 * Verify email address using token from verification link
 *
 * Makes a GET request to /api/auth/verify-email/ with token as query parameter.
 * On success, the user account is activated and email is marked as verified.
 *
 * @param token - UUID verification token from email link
 * @returns Promise resolving to verification result with user status
 * @throws {EmailVerificationError} If verification fails
 *
 * @example
 * ```typescript
 * try {
 *   const result = await verifyEmail('550e8400-e29b-41d4-a716-446655440000');
 *   console.log(result.message); // "Email verified successfully..."
 *   console.log(result.is_email_verified); // true
 * } catch (error) {
 *   if (error instanceof EmailVerificationError) {
 *     console.error(error.errorCode); // "token_expired", "token_invalid", etc.
 *     console.error(error.details?.resend_url); // "/api/auth/resend-verification/"
 *   }
 * }
 * ```
 *
 * Error Codes:
 * - `token_required` (400): Token parameter missing
 * - `token_invalid` (400): Invalid token format or doesn't exist
 * - `token_used` (400): Token already used
 * - `token_expired` (410): Token expired (> 24 hours old)
 */
export async function verifyEmail(token: string): Promise<VerifyEmailResponse> {
  const response = await apiClient.get<VerifyEmailResponse>(
    '/api/auth/verify-email/',
    { params: { token } }
  );
  return response.data;
}

/**
 * Resend verification email to user
 *
 * Makes a POST request to /api/auth/resend-verification/ with email in request body.
 * Creates a new verification token and sends email asynchronously.
 * Rate limited to 3 requests per 24 hours per email address.
 *
 * @param email - User's email address
 * @returns Promise resolving to resend result including attempts remaining
 * @throws {EmailVerificationError} If resend fails or rate limit exceeded
 *
 * @example
 * ```typescript
 * try {
 *   const result = await resendVerificationEmail('user@example.com');
 *   console.log(result.message); // "Verification email sent successfully..."
 *   console.log(result.attempts_remaining); // 2
 * } catch (error) {
 *   if (error instanceof EmailVerificationError) {
 *     if (error.errorCode === 'rate_limit_exceeded') {
 *       console.error('Retry after:', error.details?.retry_after_seconds);
 *     }
 *   }
 * }
 * ```
 *
 * Error Codes:
 * - `email` (400): Invalid email format or email not found
 * - `email` (400): Email already verified
 * - `rate_limit_exceeded` (429): Too many resend requests (max 3 per 24h)
 */
export async function resendVerificationEmail(
  email: string
): Promise<ResendVerificationResponse> {
  const response = await apiClient.post<ResendVerificationResponse>(
    '/api/auth/resend-verification/',
    { email }
  );
  return response.data;
}
