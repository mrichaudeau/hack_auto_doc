// ***********************************************************
// This support file is processed and loaded automatically before test files.
// ***********************************************************

// Import commands.js
import './commands';

// Hide fetch/XHR logs to reduce noise (optional)
Cypress.on('uncaught:exception', (err, runnable) => {
  // Returning false prevents Cypress from failing the test
  // Useful for third-party script errors
  return false;
});
