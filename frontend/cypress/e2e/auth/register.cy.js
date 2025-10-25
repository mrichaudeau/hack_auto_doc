/**
 * E2E Tests for User Registration Flow - TASK-1.17
 * Tests the complete registration workflow including form validation and error handling
 */

describe('User Registration Flow', () => {
  beforeEach(() => {
    // Visit the registration page before each test
    cy.visit('/register');
  });

  describe('Successful Registration', () => {
    it('should display the registration form', () => {
      // Verify page title
      cy.contains('h1', 'Créer un compte').should('be.visible');

      // Verify all form fields are present
      cy.get('input#email').should('be.visible');
      cy.get('input#first_name').should('be.visible');
      cy.get('input#last_name').should('be.visible');
      cy.get('input#password').should('be.visible');
      cy.get('input#password_confirm').should('be.visible');

      // Verify submit button
      cy.get('button[type="submit"]').should('be.visible');

      // Verify link to login
      cy.contains('a', 'Se connecter').should('be.visible');
    });

    it('should successfully register a new user and redirect to email confirmation page', () => {
      // Generate unique email for this test
      cy.generateTestEmail().then((email) => {
        // Fill the registration form
        cy.fillRegistrationForm({
          email: email,
          first_name: 'John',
          last_name: 'Doe',
          password: 'SecureP@ssw0rd123!',
          password_confirm: 'SecureP@ssw0rd123!'
        });

        // Submit the form
        cy.get('button[type="submit"]').click();

        // Verify redirect to email confirmation pending page
        cy.url().should('include', '/email-confirmation-pending');

        // Verify confirmation message is displayed
        cy.contains('Vérifiez votre boîte de réception').should('be.visible');
      });
    });
  });

  describe('Form Validation', () => {
    it('should show error for invalid email format', () => {
      cy.fillRegistrationForm({
        email: 'invalid-email',
        first_name: 'John',
        last_name: 'Doe',
        password: 'SecureP@ssw0rd123!',
        password_confirm: 'SecureP@ssw0rd123!'
      });

      // Blur email field to trigger validation
      cy.get('input#email').blur();

      // Verify error message
      cy.contains('Format d\'email invalide').should('be.visible');

      // Submit button should be disabled
      cy.get('button[type="submit"]').should('be.disabled');
    });

    it('should show error for weak password', () => {
      cy.get('input#password').type('weak').blur();

      // Verify error messages for password strength
      cy.get('input#password').parent().within(() => {
        cy.contains('Minimum 8 caractères').should('exist');
      });
    });

    it('should show error when passwords do not match', () => {
      cy.fillRegistrationForm({
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe',
        password: 'SecureP@ssw0rd123!',
        password_confirm: 'DifferentPassword456!'
      });

      // Blur password confirm field
      cy.get('input#password_confirm').blur();

      // Verify error message
      cy.contains('Les mots de passe ne correspondent pas').should('be.visible');
    });

    it('should show error for missing required fields', () => {
      // Try to submit empty form
      cy.get('button[type="submit"]').should('be.disabled');

      // Fill only email and trigger blur on other fields
      cy.get('input#email').type('test@example.com');
      cy.get('input#first_name').focus().blur();

      // Verify error for first_name
      cy.contains('Le prénom est requis').should('be.visible');

      cy.get('input#last_name').focus().blur();

      // Verify error for last_name
      cy.contains('Le nom est requis').should('be.visible');
    });
  });

  describe('Error Handling', () => {
    it('should show error when email already exists', () => {
      // First, register a user
      const existingEmail = 'existing@example.com';

      cy.fillRegistrationForm({
        email: existingEmail,
        first_name: 'First',
        last_name: 'User',
        password: 'SecureP@ssw0rd123!',
        password_confirm: 'SecureP@ssw0rd123!'
      });

      cy.get('button[type="submit"]').click();

      // Wait for the first registration to complete
      cy.url().should('include', '/email-confirmation-pending');

      // Go back to registration page
      cy.visit('/register');

      // Try to register with the same email
      cy.fillRegistrationForm({
        email: existingEmail,
        first_name: 'Second',
        last_name: 'User',
        password: 'AnotherP@ssw0rd456!',
        password_confirm: 'AnotherP@ssw0rd456!'
      });

      cy.get('button[type="submit"]').click();

      // Verify error message is displayed
      cy.contains(/Un compte.*existe déjà|email.*déjà/).should('be.visible');

      // Verify we stay on the registration page
      cy.url().should('include', '/register');
    });

    it('should handle server errors gracefully', () => {
      // Intercept the registration API call and force a server error
      cy.intercept('POST', '**/api/auth/register/', {
        statusCode: 500,
        body: { message: 'Internal Server Error' }
      }).as('registerError');

      cy.fillRegistrationForm({
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe',
        password: 'SecureP@ssw0rd123!',
        password_confirm: 'SecureP@ssw0rd123!'
      });

      cy.get('button[type="submit"]').click();

      // Wait for the API call
      cy.wait('@registerError');

      // Verify error message is shown
      cy.get('[class*="errorAlert"]').should('be.visible');
    });
  });

  describe('User Interface', () => {
    it('should disable submit button while loading', () => {
      // Intercept and delay the registration API call
      cy.intercept('POST', '**/api/auth/register/', (req) => {
        req.reply((res) => {
          res.delay = 1000; // Delay response by 1 second
        });
      }).as('registerDelayed');

      cy.generateTestEmail().then((email) => {
        cy.fillRegistrationForm({
          email: email,
          first_name: 'John',
          last_name: 'Doe',
          password: 'SecureP@ssw0rd123!',
          password_confirm: 'SecureP@ssw0rd123!'
        });

        cy.get('button[type="submit"]').click();

        // Button should be disabled during submission
        cy.get('button[type="submit"]').should('be.disabled');

        // Button text should change
        cy.contains('button', 'Inscription en cours...').should('be.visible');
      });
    });

    it('should navigate to login page when clicking login link', () => {
      cy.contains('a', 'Se connecter').click();
      cy.url().should('include', '/login');
    });

    it('should clear field errors when user starts typing', () => {
      // Trigger validation error
      cy.get('input#email').type('invalid').blur();
      cy.contains('Format d\'email invalide').should('be.visible');

      // Start typing again
      cy.get('input#email').type('@example.com');

      // Error should be cleared
      cy.contains('Format d\'email invalide').should('not.exist');
    });
  });

  describe('Password Strength Indicators', () => {
    it('should display password requirements', () => {
      cy.get('input#password').focus();

      // Verify password requirements are displayed
      cy.contains('Au moins 8 caractères').should('be.visible');
      cy.contains('Au moins 1 majuscule et 1 minuscule').should('be.visible');
      cy.contains('Au moins 1 chiffre').should('be.visible');
    });
  });
});

/**
 * Note on Email Verification Testing:
 *
 * The complete E2E flow including email verification link click is not tested here
 * because:
 * 1. The backend uses console email backend in development (emails not sent to real inbox)
 * 2. There's no test API endpoint to retrieve verification keys
 * 3. Setting up a full email testing infrastructure (MailHog, etc.) is beyond the scope
 *
 * To fully test email verification in E2E:
 * - Option 1: Set up MailHog or similar service and parse emails
 * - Option 2: Create a test-only API endpoint that returns verification keys
 * - Option 3: Mock the verification endpoint in Cypress
 *
 * For now, we test everything up to the email being sent (registration → confirmation page).
 * Email verification itself is thoroughly tested in backend integration tests (test_views.py).
 */
