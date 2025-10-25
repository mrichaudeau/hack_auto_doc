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

/**
 * Custom command to fill the login form
 * @example cy.fillLoginForm({ email: 'test@example.com', password: 'password' })
 */
Cypress.Commands.add('fillLoginForm', (credentials) => {
  if (credentials.email) {
    cy.get('input#email').clear().type(credentials.email);
  }
  if (credentials.password) {
    cy.get('input#password').clear().type(credentials.password);
  }
});

/**
 * Custom command to create a test user via API
 * @example cy.createTestUser({ email: 'test@example.com', password: 'Pass123!' })
 */
Cypress.Commands.add('createTestUser', (userData) => {
  const apiUrl = Cypress.env('apiUrl');

  return cy.request({
    method: 'POST',
    url: `${apiUrl}/api/auth/register/`,
    body: {
      email: userData.email,
      password: userData.password,
      password_confirm: userData.password,
      first_name: userData.first_name || 'Test',
      last_name: userData.last_name || 'User'
    },
    failOnStatusCode: false
  }).then((response) => {
    // Activate the user directly via database if needed
    // For now, return the response
    return response;
  });
});

/**
 * Custom command to login via API and set tokens in localStorage
 * @example cy.loginViaAPI('test@example.com', 'password')
 */
Cypress.Commands.add('loginViaAPI', (email, password) => {
  const apiUrl = Cypress.env('apiUrl');

  return cy.request({
    method: 'POST',
    url: `${apiUrl}/api/auth/login/`,
    body: { email, password }
  }).then((response) => {
    // Store tokens in localStorage
    window.localStorage.setItem('access_token', response.body.access_token);
    window.localStorage.setItem('refresh_token', response.body.refresh_token);
    window.localStorage.setItem('user', JSON.stringify(response.body.user));
    return response.body;
  });
});

/**
 * Custom command to logout and clear tokens
 * @example cy.logoutViaAPI()
 */
Cypress.Commands.add('logoutViaAPI', () => {
  const apiUrl = Cypress.env('apiUrl');
  const accessToken = window.localStorage.getItem('access_token');
  const refreshToken = window.localStorage.getItem('refresh_token');

  if (accessToken && refreshToken) {
    return cy.request({
      method: 'POST',
      url: `${apiUrl}/api/auth/logout/`,
      headers: {
        'Authorization': `Bearer ${accessToken}`
      },
      body: { refresh_token: refreshToken },
      failOnStatusCode: false
    }).then(() => {
      window.localStorage.clear();
    });
  } else {
    window.localStorage.clear();
  }
});
