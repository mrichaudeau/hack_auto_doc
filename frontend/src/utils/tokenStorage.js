/**
 * Token Storage Utilities (US-3: Standard User Login, TASK-3.10)
 *
 * Secure token storage with JWT expiration checking and type-safe accessors.
 * Provides abstraction over browser storage for JWT access and refresh tokens.
 *
 * Features:
 * - Type-safe token get/set operations
 * - JWT expiration checking without backend call
 * - Automatic token cleanup on logout
 * - Graceful error handling
 * - User data persistence
 *
 * Usage:
 *   import { saveTokens, getAccessToken, isAuthenticated } from '../utils/tokenStorage';
 *
 *   // After login
 *   saveTokens(accessToken, refreshToken, userData);
 *
 *   // Check authentication
 *   if (isAuthenticated()) {
 *     const token = getAccessToken();
 *     // Make authenticated API call
 *   }
 *
 *   // Logout
 *   clearTokens();
 */

import { storage } from './storage';
import { STORAGE_KEYS } from '../constants/storage';

/**
 * Save authentication tokens and user data to storage
 *
 * @param {string} accessToken - JWT access token
 * @param {string} refreshToken - JWT refresh token
 * @param {Object} userData - User profile data
 * @param {number} userData.id - User ID
 * @param {string} userData.email - User email
 * @param {string} userData.first_name - User first name
 * @param {string} userData.last_name - User last name
 * @param {boolean} userData.is_sso_user - Whether user uses SSO
 * @returns {boolean} Success status
 */
export const saveTokens = (accessToken, refreshToken, userData = null) => {
  try {
    let success = true;

    // Save access token
    if (accessToken) {
      success = storage.set(STORAGE_KEYS.ACCESS_TOKEN, accessToken) && success;
    }

    // Save refresh token
    if (refreshToken) {
      success = storage.set(STORAGE_KEYS.REFRESH_TOKEN, refreshToken) && success;
    }

    // Save user data
    if (userData) {
      success = storage.set(STORAGE_KEYS.USER_DATA, userData) && success;
    }

    // Update authentication status
    if (success && accessToken) {
      storage.set(STORAGE_KEYS.IS_AUTHENTICATED, true);
    }

    return success;
  } catch (error) {
    console.error('[TokenStorage] Failed to save tokens:', error);
    return false;
  }
};

/**
 * Get access token from storage
 *
 * @returns {string|null} Access token or null if not found
 */
export const getAccessToken = () => {
  try {
    return storage.get(STORAGE_KEYS.ACCESS_TOKEN);
  } catch (error) {
    console.error('[TokenStorage] Failed to get access token:', error);
    return null;
  }
};

/**
 * Get refresh token from storage
 *
 * @returns {string|null} Refresh token or null if not found
 */
export const getRefreshToken = () => {
  try {
    return storage.get(STORAGE_KEYS.REFRESH_TOKEN);
  } catch (error) {
    console.error('[TokenStorage] Failed to get refresh token:', error);
    return null;
  }
};

/**
 * Get user data from storage
 *
 * @returns {Object|null} User data or null if not found
 */
export const getUserData = () => {
  try {
    return storage.get(STORAGE_KEYS.USER_DATA);
  } catch (error) {
    console.error('[TokenStorage] Failed to get user data:', error);
    return null;
  }
};

/**
 * Clear all authentication tokens and user data from storage
 *
 * @returns {boolean} Success status
 */
export const clearTokens = () => {
  try {
    storage.remove(STORAGE_KEYS.ACCESS_TOKEN);
    storage.remove(STORAGE_KEYS.REFRESH_TOKEN);
    storage.remove(STORAGE_KEYS.USER_DATA);
    storage.remove(STORAGE_KEYS.IS_AUTHENTICATED);
    return true;
  } catch (error) {
    console.error('[TokenStorage] Failed to clear tokens:', error);
    return false;
  }
};

/**
 * Parse JWT token payload without verification
 * Note: This does NOT verify the token signature
 *
 * @param {string} token - JWT token
 * @returns {Object|null} Decoded payload or null if invalid
 */
export const parseJWT = (token) => {
  try {
    if (!token || typeof token !== 'string') {
      return null;
    }

    // JWT format: header.payload.signature
    const parts = token.split('.');
    if (parts.length !== 3) {
      return null;
    }

    // Decode base64 payload (second part)
    const payload = parts[1];
    const decoded = atob(payload);
    return JSON.parse(decoded);
  } catch (error) {
    console.error('[TokenStorage] Failed to parse JWT:', error);
    return null;
  }
};

/**
 * Check if JWT token is expired
 *
 * @param {string} token - JWT token
 * @returns {boolean} True if expired, false if valid or unparseable
 */
export const isTokenExpired = (token) => {
  try {
    const payload = parseJWT(token);
    if (!payload || !payload.exp) {
      return true; // Invalid token is considered expired
    }

    // JWT exp is in seconds, Date.now() is in milliseconds
    const expirationTime = payload.exp * 1000;
    const currentTime = Date.now();

    // Add 60 second buffer to refresh before actual expiration
    const bufferTime = 60 * 1000;
    return currentTime >= (expirationTime - bufferTime);
  } catch (error) {
    console.error('[TokenStorage] Failed to check token expiration:', error);
    return true;
  }
};

/**
 * Get token expiration time
 *
 * @param {string} token - JWT token
 * @returns {Date|null} Expiration date or null if invalid
 */
export const getTokenExpiration = (token) => {
  try {
    const payload = parseJWT(token);
    if (!payload || !payload.exp) {
      return null;
    }
    return new Date(payload.exp * 1000);
  } catch (error) {
    console.error('[TokenStorage] Failed to get token expiration:', error);
    return null;
  }
};

/**
 * Get time until token expires (in seconds)
 *
 * @param {string} token - JWT token
 * @returns {number} Seconds until expiration, or 0 if expired/invalid
 */
export const getTimeUntilExpiration = (token) => {
  try {
    const payload = parseJWT(token);
    if (!payload || !payload.exp) {
      return 0;
    }

    const expirationTime = payload.exp * 1000;
    const currentTime = Date.now();
    const timeRemaining = expirationTime - currentTime;

    return Math.max(0, Math.floor(timeRemaining / 1000));
  } catch (error) {
    console.error('[TokenStorage] Failed to get time until expiration:', error);
    return 0;
  }
};

/**
 * Check if user is authenticated
 * Validates that access token exists and is not expired
 *
 * @returns {boolean} True if authenticated with valid token
 */
export const isAuthenticated = () => {
  try {
    const token = getAccessToken();
    if (!token) {
      return false;
    }

    // Check if token is expired
    return !isTokenExpired(token);
  } catch (error) {
    console.error('[TokenStorage] Failed to check authentication:', error);
    return false;
  }
};

/**
 * Check if refresh token exists and is valid
 *
 * @returns {boolean} True if refresh token exists and is not expired
 */
export const hasValidRefreshToken = () => {
  try {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      return false;
    }

    return !isTokenExpired(refreshToken);
  } catch (error) {
    console.error('[TokenStorage] Failed to check refresh token:', error);
    return false;
  }
};

/**
 * Get user ID from access token
 *
 * @returns {number|null} User ID or null if not available
 */
export const getUserIdFromToken = () => {
  try {
    const token = getAccessToken();
    if (!token) {
      return null;
    }

    const payload = parseJWT(token);
    return payload?.user_id || null;
  } catch (error) {
    console.error('[TokenStorage] Failed to get user ID from token:', error);
    return null;
  }
};

/**
 * Update access token (used during token refresh)
 *
 * @param {string} newAccessToken - New access token
 * @returns {boolean} Success status
 */
export const updateAccessToken = (newAccessToken) => {
  try {
    return storage.set(STORAGE_KEYS.ACCESS_TOKEN, newAccessToken);
  } catch (error) {
    console.error('[TokenStorage] Failed to update access token:', error);
    return false;
  }
};

/**
 * Update user data
 *
 * @param {Object} userData - Updated user data
 * @returns {boolean} Success status
 */
export const updateUserData = (userData) => {
  try {
    return storage.set(STORAGE_KEYS.USER_DATA, userData);
  } catch (error) {
    console.error('[TokenStorage] Failed to update user data:', error);
    return false;
  }
};

/**
 * Get authentication state summary
 * Useful for debugging and logging
 *
 * @returns {Object} Authentication state summary
 */
export const getAuthState = () => {
  const token = getAccessToken();
  const refreshToken = getRefreshToken();
  const userData = getUserData();

  return {
    hasAccessToken: !!token,
    hasRefreshToken: !!refreshToken,
    hasUserData: !!userData,
    isAuthenticated: isAuthenticated(),
    hasValidRefreshToken: hasValidRefreshToken(),
    accessTokenExpiration: token ? getTokenExpiration(token) : null,
    refreshTokenExpiration: refreshToken ? getTokenExpiration(refreshToken) : null,
    timeUntilAccessTokenExpires: token ? getTimeUntilExpiration(token) : 0,
    userId: getUserIdFromToken(),
    storageType: storage.getStorageType(),
  };
};

// Export all functions
export default {
  saveTokens,
  getAccessToken,
  getRefreshToken,
  getUserData,
  clearTokens,
  parseJWT,
  isTokenExpired,
  getTokenExpiration,
  getTimeUntilExpiration,
  isAuthenticated,
  hasValidRefreshToken,
  getUserIdFromToken,
  updateAccessToken,
  updateUserData,
  getAuthState,
};
