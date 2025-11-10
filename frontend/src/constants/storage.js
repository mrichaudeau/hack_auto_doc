/**
 * Storage Keys Constants (US-3: Standard User Login, TASK-3.10)
 *
 * Centralized storage key definitions with prefixes to avoid collisions.
 * All keys are prefixed with 'veille_tech_' to namespace the application data.
 *
 * Usage:
 *   import { STORAGE_KEYS } from '../constants/storage';
 *   localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, token);
 */

export const STORAGE_KEYS = {
  /**
   * JWT access token key
   * Used for: API authentication
   * Expiration: Short-lived (typically 15-60 minutes)
   */
  ACCESS_TOKEN: 'veille_tech_access_token',

  /**
   * JWT refresh token key
   * Used for: Refreshing expired access tokens
   * Expiration: Long-lived (typically 7-30 days)
   */
  REFRESH_TOKEN: 'veille_tech_refresh_token',

  /**
   * User profile data key
   * Stores: { id, email, first_name, last_name, is_sso_user }
   */
  USER_DATA: 'veille_tech_user',

  /**
   * Authentication state key
   * Stores: Boolean indicating if user is authenticated
   */
  IS_AUTHENTICATED: 'veille_tech_is_authenticated',
};

/**
 * Storage configuration
 */
export const STORAGE_CONFIG = {
  /**
   * Default storage type
   * Options: 'localStorage', 'sessionStorage', 'memory'
   */
  DEFAULT_TYPE: 'localStorage',

  /**
   * Enable encryption for sensitive data
   * Note: Client-side encryption provides limited security against XSS
   * For production, consider httpOnly cookies for tokens
   */
  ENABLE_ENCRYPTION: false,

  /**
   * Storage quota warning threshold (in bytes)
   * localStorage typically has 5-10MB limit
   */
  QUOTA_WARNING_THRESHOLD: 4 * 1024 * 1024, // 4 MB

  /**
   * Fallback to sessionStorage if localStorage unavailable
   */
  ENABLE_FALLBACK: true,
};

/**
 * Storage error types
 */
export const STORAGE_ERRORS = {
  QUOTA_EXCEEDED: 'QUOTA_EXCEEDED',
  NOT_AVAILABLE: 'NOT_AVAILABLE',
  SECURITY_ERROR: 'SECURITY_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
};
