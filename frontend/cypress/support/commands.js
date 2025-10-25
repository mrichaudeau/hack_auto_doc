// ***********************************************
// Custom commands for Cypress tests
// ***********************************************

/**
 * Custom command to fill the registration form
 * @example cy.fillRegistrationForm({ email: 'test@example.com', ... })
 */
Cypress.Commands.add('fillRegistrationForm', (userData) => {
  if (userData.email) {
    cy.get('input#email').clear().type(userData.email);
  }
  if (userData.first_name) {
    cy.get('input#first_name').clear().type(userData.first_name);
  }
  if (userData.last_name) {
    cy.get('input#last_name').clear().type(userData.last_name);
  }
  if (userData.password) {
    cy.get('input#password').clear().type(userData.password);
  }
  if (userData.password_confirm) {
    cy.get('input#password_confirm').clear().type(userData.password_confirm);
  }
});

/**
 * Custom command to generate a random email for testing
 * @example cy.generateTestEmail().then(email => { ... })
 */
Cypress.Commands.add('generateTestEmail', () => {
  const timestamp = Date.now();
  const randomStr = Math.random().toString(36).substring(7);
  return `test_${timestamp}_${randomStr}@example.com`;
});
