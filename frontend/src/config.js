/**
 * Centralized configuration for frontend application
 * Loads environment variables from .env.frontend
 * All environment variables must be prefixed with VITE_
 */

const config = {
  // API Configuration
  apiUrl: import.meta.env.VITE_API_URL || '/api',

  // Feature Flags
  enableSSO: import.meta.env.VITE_ENABLE_SSO === 'true',
  enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  debugMode: import.meta.env.VITE_DEBUG_MODE === 'true',

  // Environment
  environment: import.meta.env.VITE_ENV || 'development',
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
}

// Log configuration in development mode
if (config.isDevelopment && config.debugMode) {
  console.log('Application Configuration:', config)
}

export default config
