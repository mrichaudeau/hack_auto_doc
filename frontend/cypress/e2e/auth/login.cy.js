/**
 * E2E Tests for Login and Logout Flow - TASK-2.18
 * Tests the complete login/logout workflow including authentication and protected routes
 */

describe('Login and Logout Flow', () => {
  const testUser = {
    email: 'e2e.login.test@example.com',
    password: 'SecureP@ssw0rd123!',
    first_name: 'E2E',
    last_name: 'LoginTest'
  };

  before(() => {
    // Clean up any existing test user and create a fresh one
    const apiUrl = Cypress.env('apiUrl');

    // Note: In a real setup, you'd want a test API endpoint to delete users
    // For now, we'll just try to create the user (it may fail if exists)
    cy.request({
      method: 'POST',
      url: `${apiUrl}/api/auth/register/`,
      body: {
        email: testUser.email,
        password: testUser.password,
        password_confirm: testUser.password,
        first_name: testUser.first_name,
        last_name: testUser.last_name
      },
      failOnStatusCode: false
    });

    // For E2E testing, we'll need the user to be activated
    // In a real setup, you'd want a test API endpoint to activate users
    // For now, we'll assume the backend has a way to handle test users
  });

  beforeEach(() => {
    // Clear localStorage before each test
    cy.clearLocalStorage();

    // Visit the login page
    cy.visit('/login');
  });

  describe('Login Page Display', () => {
    it('should display the login form', () => {
      // Verify page title
      cy.contains('h1', 'Connexion').should('be.visible');

      // Verify all form fields are present
      cy.get('input#email').should('be.visible');
      cy.get('input#password').should('be.visible');

      // Verify submit button
      cy.get('button[type="submit"]').should('be.visible');
      cy.contains('button', 'Se connecter').should('be.visible');

      // Verify links to register and forgot password
      cy.contains('a', /créer.*compte/i).should('be.visible');
    });

    it('should display SSO button (disabled for now)', () => {
      // Verify Microsoft SSO button exists and is disabled
      cy.contains('button', 'Microsoft').should('be.visible').and('be.disabled');
    });
  });

  describe('Successful Login', () => {
    it('should login with valid credentials and redirect to dashboard', () => {
      // Fill login form
      cy.fillLoginForm({
        email: testUser.email,
        password: testUser.password
      });

      // Submit the form
      cy.get('button[type="submit"]').click();

      // Verify redirect to dashboard
      cy.url().should('include', '/dashboard', { timeout: 10000 });

      // Verify user is greeted on dashboard
      cy.contains(`Bienvenue, ${testUser.first_name}`, { timeout: 10000 }).should('be.visible');

      // Verify tokens are stored in localStorage
      cy.window().then((win) => {
        expect(win.localStorage.getItem('access_token')).to.exist;
        expect(win.localStorage.getItem('refresh_token')).to.exist;
        expect(win.localStorage.getItem('user')).to.exist;
      });
    });

    it('should handle case-insensitive email login', () => {
      // Login with uppercase email
      cy.fillLoginForm({
        email: testUser.email.toUpperCase(),
        password: testUser.password
      });

      cy.get('button[type="submit"]').click();

      // Should still succeed
      cy.url().should('include', '/dashboard', { timeout: 10000 });
    });

    it('should display user information on dashboard', () => {
      // Login first
      cy.fillLoginForm({
        email: testUser.email,
        password: testUser.password
      });

      cy.get('button[type="submit"]').click();

      // Wait for dashboard
      cy.url().should('include', '/dashboard', { timeout: 10000 });

      // Verify user info is displayed
      cy.contains(testUser.email.toLowerCase()).should('be.visible');
      cy.contains(`${testUser.first_name} ${testUser.last_name}`).should('be.visible');
    });
  });

  describe('Login Form Validation', () => {
    it('should show error for invalid email format', () => {
      cy.get('input#email').type('invalid-email').blur();

      // Verify error message
      cy.contains(/format.*email.*invalide/i).should('be.visible');

      // Submit button should be disabled
      cy.get('button[type="submit"]').should('be.disabled');
    });

    it('should show error for missing password', () => {
      cy.get('input#email').type(testUser.email);
      cy.get('input#password').focus().blur();

      // Verify password is required
      cy.get('button[type="submit"]').should('be.disabled');
    });

    it('should enable submit button only when form is valid', () => {
      // Initially, button should be disabled
      cy.get('button[type="submit"]').should('be.disabled');

      // Fill email only
      cy.get('input#email').type(testUser.email);
      cy.get('button[type="submit"]').should('be.disabled');

      // Fill password
      cy.get('input#password').type(testUser.password);
      cy.get('button[type="submit"]').should('not.be.disabled');
    });
  });

  describe('Login Error Handling', () => {
    it('should show error for invalid credentials', () => {
      cy.fillLoginForm({
        email: testUser.email,
        password: 'WrongPassword123!'
      });

      cy.get('button[type="submit"]').click();

      // Verify error message is displayed
      cy.contains(/identifiants.*invalides|incorrect/i, { timeout: 10000 }).should('be.visible');

      // Should remain on login page
      cy.url().should('include', '/login');
    });

    it('should show error for non-existent email', () => {
      cy.fillLoginForm({
        email: 'nonexistent@example.com',
        password: testUser.password
      });

      cy.get('button[type="submit"]').click();

      // Verify error message
      cy.contains(/identifiants.*invalides|incorrect/i, { timeout: 10000 }).should('be.visible');
    });

    it('should show error for unverified account', () => {
      // Create an unverified user
      const unverifiedEmail = `unverified_${Date.now()}@example.com`;
      const apiUrl = Cypress.env('apiUrl');

      cy.request({
        method: 'POST',
        url: `${apiUrl}/api/auth/register/`,
        body: {
          email: unverifiedEmail,
          password: testUser.password,
          password_confirm: testUser.password,
          first_name: 'Unverified',
          last_name: 'User'
        },
        failOnStatusCode: false
      });

      // Try to login with unverified account
      cy.fillLoginForm({
        email: unverifiedEmail,
        password: testUser.password
      });

      cy.get('button[type="submit"]').click();

      // Verify error message about verification
      cy.contains(/verifie|verifier/i, { timeout: 10000 }).should('be.visible');
    });

    it('should handle server errors gracefully', () => {
      // Intercept login API call and force a server error
      cy.intercept('POST', '**/api/auth/login/', {
        statusCode: 500,
        body: { detail: 'Internal Server Error' }
      }).as('loginError');

      cy.fillLoginForm({
        email: testUser.email,
        password: testUser.password
      });

      cy.get('button[type="submit"]').click();

      // Wait for the API call
      cy.wait('@loginError');

      // Verify error message is shown
      cy.get('[class*="error"]').should('be.visible');
    });
  });

  describe('Logout Flow', () => {
    beforeEach(() => {
      // Login before each logout test
      cy.fillLoginForm({
        email: testUser.email,
        password: testUser.password
      });

      cy.get('button[type="submit"]').click();

      // Wait for dashboard
      cy.url().should('include', '/dashboard', { timeout: 10000 });
    });

    it('should logout and redirect to login page', () => {
      // Click logout button
      cy.contains('button', 'Déconnexion').click();

      // Verify redirect to login page
      cy.url().should('include', '/login', { timeout: 10000 });

      // Verify tokens are cleared from localStorage
      cy.window().then((win) => {
        expect(win.localStorage.getItem('access_token')).to.be.null;
        expect(win.localStorage.getItem('refresh_token')).to.be.null;
        expect(win.localStorage.getItem('user')).to.be.null;
      });
    });

    it('should prevent access to dashboard after logout', () => {
      // Logout
      cy.contains('button', 'Déconnexion').click();

      // Wait for redirect to login
      cy.url().should('include', '/login', { timeout: 10000 });

      // Try to visit dashboard directly
      cy.visit('/dashboard');

      // Should be redirected back to login
      cy.url().should('include', '/login');
    });
  });

  describe('Protected Routes', () => {
    it('should redirect to login when accessing dashboard without authentication', () => {
      // Visit dashboard directly without logging in
      cy.visit('/dashboard');

      // Should be redirected to login
      cy.url().should('include', '/login');
    });

    it('should redirect to dashboard after login when initially accessing protected route', () => {
      // Try to access dashboard without auth
      cy.visit('/dashboard');

      // Should be redirected to login
      cy.url().should('include', '/login');

      // Login
      cy.fillLoginForm({
        email: testUser.email,
        password: testUser.password
      });

      cy.get('button[type="submit"]').click();

      // Should be redirected to dashboard
      cy.url().should('include', '/dashboard', { timeout: 10000 });
    });

    it('should allow access to dashboard when authenticated', () => {
      // Login first
      cy.fillLoginForm({
        email: testUser.email,
        password: testUser.password
      });

      cy.get('button[type="submit"]').click();

      cy.url().should('include', '/dashboard', { timeout: 10000 });

      // Verify dashboard content is accessible
      cy.contains('Bienvenue').should('be.visible');
    });
  });

  describe('User Interface', () => {
    it('should disable submit button while loading', () => {
      // Intercept and delay the login API call
      cy.intercept('POST', '**/api/auth/login/', (req) => {
        req.reply((res) => {
          res.delay = 1000; // Delay response by 1 second
        });
      }).as('loginDelayed');

      cy.fillLoginForm({
        email: testUser.email,
        password: testUser.password
      });

      cy.get('button[type="submit"]').click();

      // Button should be disabled during submission
      cy.get('button[type="submit"]').should('be.disabled');
    });

    it('should navigate to register page when clicking register link', () => {
      cy.contains('a', /créer.*compte/i).click();
      cy.url().should('include', '/register');
    });

    it('should clear errors when user starts typing', () => {
      // Trigger error
      cy.fillLoginForm({
        email: testUser.email,
        password: 'WrongPassword'
      });

      cy.get('button[type="submit"]').click();

      // Wait for error
      cy.contains(/identifiants.*invalides|incorrect/i, { timeout: 10000 }).should('be.visible');

      // Start typing in email field
      cy.get('input#email').clear().type('new@example.com');

      // Error should be cleared
      cy.contains(/identifiants.*invalides|incorrect/i).should('not.exist');
    });
  });

  describe('Session Persistence', () => {
    it('should maintain session on page refresh', () => {
      // Login
      cy.fillLoginForm({
        email: testUser.email,
        password: testUser.password
      });

      cy.get('button[type="submit"]').click();

      cy.url().should('include', '/dashboard', { timeout: 10000 });

      // Refresh the page
      cy.reload();

      // Should still be on dashboard
      cy.url().should('include', '/dashboard');

      // Should still see user info
      cy.contains('Bienvenue').should('be.visible');
    });
  });
});
