/**
 * Generic Storage Abstraction (US-3: Standard User Login, TASK-3.10)
 *
 * Provides a unified interface for browser storage (localStorage, sessionStorage)
 * with error handling, fallback mechanisms, and graceful degradation.
 *
 * Features:
 * - Automatic fallback to sessionStorage or in-memory storage
 * - Quota exceeded error handling
 * - Private browsing mode detection
 * - Type-safe get/set operations with JSON parsing
 *
 * Usage:
 *   import { storage } from '../utils/storage';
 *   storage.set('key', { data: 'value' });
 *   const data = storage.get('key');
 */

import { STORAGE_CONFIG, STORAGE_ERRORS } from '../constants/storage';

/**
 * In-memory storage fallback for environments without Web Storage API
 */
class MemoryStorage {
  constructor() {
    this.data = new Map();
  }

  setItem(key, value) {
    this.data.set(key, value);
  }

  getItem(key) {
    return this.data.get(key) || null;
  }

  removeItem(key) {
    this.data.delete(key);
  }

  clear() {
    this.data.clear();
  }

  key(index) {
    return Array.from(this.data.keys())[index] || null;
  }

  get length() {
    return this.data.size;
  }
}

/**
 * Storage wrapper class with error handling and fallback
 */
class StorageWrapper {
  constructor() {
    this.primaryStorage = null;
    this.fallbackStorage = null;
    this.memoryStorage = new MemoryStorage();
    this.storageAvailable = false;

    this._initializeStorage();
  }

  /**
   * Initialize storage with fallback mechanism
   * @private
   */
  _initializeStorage() {
    // Try localStorage first
    if (this._isStorageAvailable('localStorage')) {
      this.primaryStorage = window.localStorage;
      this.storageAvailable = true;
      console.info('[Storage] Using localStorage');
      return;
    }

    // Fall back to sessionStorage
    if (STORAGE_CONFIG.ENABLE_FALLBACK && this._isStorageAvailable('sessionStorage')) {
      this.primaryStorage = window.sessionStorage;
      this.storageAvailable = true;
      console.warn('[Storage] localStorage unavailable, using sessionStorage');
      return;
    }

    // Fall back to memory storage
    this.primaryStorage = this.memoryStorage;
    this.storageAvailable = false;
    console.warn('[Storage] Web Storage API unavailable, using in-memory storage (data will not persist)');
  }

  /**
   * Test if storage type is available
   * Handles private browsing mode and security restrictions
   * @private
   */
  _isStorageAvailable(type) {
    try {
      const storage = window[type];
      const testKey = '__storage_test__';
      storage.setItem(testKey, 'test');
      storage.removeItem(testKey);
      return true;
    } catch (error) {
      // Storage unavailable (private browsing, quota exceeded, etc.)
      return false;
    }
  }

  /**
   * Get storage error type from exception
   * @private
   */
  _getErrorType(error) {
    if (error.name === 'QuotaExceededError' ||
        error.code === 22 || // Firefox
        error.code === 1014) { // Firefox
      return STORAGE_ERRORS.QUOTA_EXCEEDED;
    }
    if (error.name === 'SecurityError') {
      return STORAGE_ERRORS.SECURITY_ERROR;
    }
    return STORAGE_ERRORS.UNKNOWN_ERROR;
  }

  /**
   * Set item in storage
   * @param {string} key - Storage key
   * @param {*} value - Value to store (will be JSON stringified)
   * @returns {boolean} Success status
   */
  set(key, value) {
    try {
      const serialized = JSON.stringify(value);
      this.primaryStorage.setItem(key, serialized);
      return true;
    } catch (error) {
      const errorType = this._getErrorType(error);

      if (errorType === STORAGE_ERRORS.QUOTA_EXCEEDED) {
        console.error('[Storage] Quota exceeded for key:', key);
        // Attempt to clear old data and retry
        this._clearOldestItems();
        try {
          this.primaryStorage.setItem(key, JSON.stringify(value));
          return true;
        } catch (retryError) {
          console.error('[Storage] Failed to set after clearing:', retryError);
        }
      } else {
        console.error('[Storage] Failed to set key:', key, error);
      }

      // Try fallback storage
      if (this.fallbackStorage) {
        try {
          this.fallbackStorage.setItem(key, JSON.stringify(value));
          return true;
        } catch (fallbackError) {
          console.error('[Storage] Fallback storage also failed:', fallbackError);
        }
      }

      return false;
    }
  }

  /**
   * Get item from storage
   * @param {string} key - Storage key
   * @param {*} defaultValue - Default value if key not found
   * @returns {*} Parsed value or defaultValue
   */
  get(key, defaultValue = null) {
    try {
      const serialized = this.primaryStorage.getItem(key);
      if (serialized === null) {
        return defaultValue;
      }
      return JSON.parse(serialized);
    } catch (error) {
      console.error('[Storage] Failed to get key:', key, error);

      // Try fallback storage
      if (this.fallbackStorage) {
        try {
          const serialized = this.fallbackStorage.getItem(key);
          if (serialized !== null) {
            return JSON.parse(serialized);
          }
        } catch (fallbackError) {
          console.error('[Storage] Fallback storage also failed:', fallbackError);
        }
      }

      return defaultValue;
    }
  }

  /**
   * Remove item from storage
   * @param {string} key - Storage key
   * @returns {boolean} Success status
   */
  remove(key) {
    try {
      this.primaryStorage.removeItem(key);
      if (this.fallbackStorage) {
        this.fallbackStorage.removeItem(key);
      }
      return true;
    } catch (error) {
      console.error('[Storage] Failed to remove key:', key, error);
      return false;
    }
  }

  /**
   * Clear all storage
   * @returns {boolean} Success status
   */
  clear() {
    try {
      this.primaryStorage.clear();
      if (this.fallbackStorage) {
        this.fallbackStorage.clear();
      }
      return true;
    } catch (error) {
      console.error('[Storage] Failed to clear storage:', error);
      return false;
    }
  }

  /**
   * Check if key exists in storage
   * @param {string} key - Storage key
   * @returns {boolean}
   */
  has(key) {
    try {
      return this.primaryStorage.getItem(key) !== null;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get all keys in storage
   * @returns {string[]} Array of keys
   */
  keys() {
    try {
      const keys = [];
      for (let i = 0; i < this.primaryStorage.length; i++) {
        const key = this.primaryStorage.key(i);
        if (key) {
          keys.push(key);
        }
      }
      return keys;
    } catch (error) {
      console.error('[Storage] Failed to get keys:', error);
      return [];
    }
  }

  /**
   * Get storage size estimate in bytes
   * @returns {number} Estimated storage size
   */
  getSize() {
    try {
      let size = 0;
      const keys = this.keys();
      keys.forEach(key => {
        const value = this.primaryStorage.getItem(key);
        if (value) {
          size += key.length + value.length;
        }
      });
      return size;
    } catch (error) {
      console.error('[Storage] Failed to calculate size:', error);
      return 0;
    }
  }

  /**
   * Clear oldest items to free up space
   * @private
   */
  _clearOldestItems() {
    try {
      const keys = this.keys();
      // Remove first 25% of items (simple strategy, could be improved with LRU)
      const removeCount = Math.ceil(keys.length * 0.25);
      for (let i = 0; i < removeCount && i < keys.length; i++) {
        this.primaryStorage.removeItem(keys[i]);
      }
      console.info(`[Storage] Cleared ${removeCount} items to free space`);
    } catch (error) {
      console.error('[Storage] Failed to clear oldest items:', error);
    }
  }

  /**
   * Check if storage is available and persistent
   * @returns {boolean}
   */
  isAvailable() {
    return this.storageAvailable;
  }

  /**
   * Get storage type being used
   * @returns {string}
   */
  getStorageType() {
    if (this.primaryStorage === window.localStorage) {
      return 'localStorage';
    }
    if (this.primaryStorage === window.sessionStorage) {
      return 'sessionStorage';
    }
    return 'memory';
  }
}

// Export singleton instance
export const storage = new StorageWrapper();

// Export class for testing
export { StorageWrapper };
