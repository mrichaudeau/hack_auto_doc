# Authentication API Documentation

## Overview

This document provides comprehensive documentation for the authentication endpoints in the Technology Watch Platform API (US-2: Standard Account Login).

**Base URL**: `http://localhost:8000/api`
**Authentication**: JWT (JSON Web Tokens)
**Content-Type**: `application/json`

## Table of Contents

1. [User Registration](#user-registration)
2. [Email Verification](#email-verification)
3. [Resend Verification Email](#resend-verification-email)
4. [User Login](#user-login)
5. [User Logout](#user-logout)
6. [Token Refresh](#token-refresh)
7. [Get User Details](#get-user-details)
8. [Error Responses](#error-responses)
9. [Rate Limiting](#rate-limiting)

---

## User Registration

Register a new user account with email and password.

### Endpoint

```
POST /api/auth/register/
```

### Request Headers

| Header | Value | Required |
|--------|-------|----------|
| Content-Type | application/json | Yes |

### Request Body

```json
{
  "email": "user@example.com",
  "password": "SecureP@ssw0rd123!",
  "password_confirm": "SecureP@ssw0rd123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | string | Yes | Valid email address (case-insensitive) |
| password | string | Yes | Strong password (min 8 chars, uppercase, lowercase, digit) |
| password_confirm | string | Yes | Must match password |
| first_name | string | Yes | User's first name |
| last_name | string | Yes | User's last name |

### Success Response

**Status Code**: `201 Created`

```json
{
  "message": "Inscription réussie ! Un email de vérification a été envoyé à votre adresse.",
  "email": "user@example.com"
}
```

### Error Responses

**Status Code**: `400 Bad Request`

- Missing required fields
- Invalid email format
- Weak password
- Passwords don't match

```json
{
  "email": ["Ce champ est obligatoire."],
  "password": ["Ce mot de passe est trop court."]
}
```

**Status Code**: `409 Conflict`

- Email already exists

```json
{
  "email": "Un compte avec cette adresse email existe déjà."
}
```

### Notes

- User account is created with `is_active=False`
- Verification email is sent automatically
- User must verify email before logging in

---

## Email Verification

Verify a user's email address using the verification key sent via email.

### Endpoint

```
GET /api/auth/verify-email/:key/
POST /api/auth/verify-email/:key/
```

### URL Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| key | string | Yes | Email verification key from email |

### Success Response

**Status Code**: `200 OK`

```json
{
  "message": "Email vérifié avec succès ! Vous pouvez maintenant vous connecter.",
  "verified": true
}
```

### Error Responses

**Status Code**: `400 Bad Request`

- Invalid or expired key

```json
{
  "error": "Token de vérification invalide ou expiré.",
  "code": "invalid_token"
}
```

### Notes

- Verification key expires after 3 days
- User account is activated (`is_active=True`) after verification
- Both GET and POST methods are supported for flexibility

---

## Resend Verification Email

Resend the email verification link to a user.

### Endpoint

```
POST /api/auth/resend-verification/
```

### Request Body

```json
{
  "email": "user@example.com"
}
```

### Success Response

**Status Code**: `200 OK`

```json
{
  "message": "Un nouvel email de vérification a été envoyé.",
  "email": "user@example.com"
}
```

### Error Responses

**Status Code**: `400 Bad Request`

- Email already verified
- Missing email field

```json
{
  "message": "Ce compte est déjà vérifié."
}
```

```json
{
  "email": "L'adresse email est requise."
}
```

### Notes

- Returns success even for non-existent emails (to prevent email enumeration)
- Rate limited to prevent abuse (10 requests/minute)

---

## User Login

Authenticate a user and receive JWT tokens.

### Endpoint

```
POST /api/auth/login/
```

### Request Body

```json
{
  "email": "user@example.com",
  "password": "SecureP@ssw0rd123!"
}
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | string | Yes | User's email address (case-insensitive) |
| password | string | Yes | User's password |

### Success Response

**Status Code**: `200 OK`

```json
{
  "message": "Connexion réussie.",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "auth_provider": "standard",
    "date_joined": "2025-01-15T10:30:00Z"
  }
}
```

### Error Responses

**Status Code**: `401 Unauthorized`

- Invalid credentials
- User doesn't exist

```json
{
  "detail": "Identifiants invalides."
}
```

**Status Code**: `403 Forbidden`

- Account not verified

```json
{
  "detail": "Votre compte n'a pas encore été vérifié. Veuillez consulter votre boîte de réception."
}
```

### Notes

- Access token expires after 15 minutes
- Refresh token expires after 7 days
- All login attempts are logged for security audit
- Rate limited: 10 attempts/minute, 3 attempts burst

---

## User Logout

Logout a user by blacklisting their refresh token.

### Endpoint

```
POST /api/auth/logout/
```

### Request Headers

| Header | Value | Required |
|--------|-------|----------|
| Authorization | Bearer <access_token> | Yes |
| Content-Type | application/json | Yes |

### Request Body

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Success Response

**Status Code**: `204 No Content`

(No response body)

### Error Responses

**Status Code**: `400 Bad Request`

- Missing refresh token
- Invalid or already blacklisted token

```json
{
  "refresh_token": "Ce champ est obligatoire."
}
```

**Status Code**: `401 Unauthorized`

- Missing or invalid access token

```json
{
  "detail": "Authentification requise."
}
```

### Notes

- Refresh token is blacklisted and cannot be reused
- Access token remains valid until expiration (15 minutes)
- Client should clear both tokens from storage

---

## Token Refresh

Refresh an expired access token using a valid refresh token.

### Endpoint

```
POST /api/auth/refresh/
```

### Request Body

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Success Response

**Status Code**: `200 OK`

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Error Responses

**Status Code**: `401 Unauthorized`

- Invalid, expired, or blacklisted refresh token

```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

**Status Code**: `400 Bad Request`

- Missing refresh token

```json
{
  "refresh": "Ce champ est obligatoire."
}
```

### Notes

- Returns both new access and refresh tokens
- Old refresh token is automatically blacklisted (token rotation)
- New refresh token should replace the old one in client storage

---

## Get User Details

Retrieve the authenticated user's profile information.

### Endpoint

```
GET /api/users/me/
```

### Request Headers

| Header | Value | Required |
|--------|-------|----------|
| Authorization | Bearer <access_token> | Yes |

### Success Response

**Status Code**: `200 OK`

```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "auth_provider": "standard",
  "date_joined": "2025-01-15T10:30:00Z"
}
```

### Error Responses

**Status Code**: `401 Unauthorized`

- Missing, invalid, or expired access token

```json
{
  "detail": "Authentification requise."
}
```

### Notes

- Password field is never returned
- Only authenticated users can access this endpoint
- Access token must be valid and not expired

---

## Error Responses

### Standard Error Format

All error responses follow a consistent structure:

```json
{
  "detail": "Human-readable error message",
  "code": "error_code"
}
```

or for field-specific errors:

```json
{
  "field_name": ["Error message 1", "Error message 2"]
}
```

### Common HTTP Status Codes

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| 200 | OK | Successful GET request |
| 201 | Created | Successful POST creating a resource |
| 204 | No Content | Successful DELETE or action with no response body |
| 400 | Bad Request | Invalid request data, missing required fields |
| 401 | Unauthorized | Missing, invalid, or expired authentication token |
| 403 | Forbidden | Valid authentication but insufficient permissions |
| 409 | Conflict | Resource already exists (e.g., duplicate email) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error (should be rare) |

---

## Rate Limiting

All authentication endpoints are rate-limited to prevent abuse.

### Rate Limit Configuration

| Endpoint | Anonymous Users | Authenticated Users |
|----------|-----------------|---------------------|
| `/auth/register/` | 10/minute, 3 burst | N/A |
| `/auth/login/` | 10/minute, 3 burst | N/A |
| `/auth/resend-verification/` | 10/minute | N/A |
| `/auth/logout/` | N/A | 1000/hour |
| `/auth/refresh/` | N/A | 1000/hour |
| `/users/me/` | N/A | 1000/hour |

### Rate Limit Response

**Status Code**: `429 Too Many Requests`

```json
{
  "detail": "Request was throttled. Expected available in X seconds."
}
```

### Rate Limit Headers

Responses include rate limit information in headers:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 8
X-RateLimit-Reset: 1705320000
```

---

## Authentication Flow

### Standard Registration and Login Flow

```
1. User registers:
   POST /api/auth/register/
   → Returns 201 with success message
   → Verification email sent

2. User clicks verification link in email:
   GET /api/auth/verify-email/:key/
   → Returns 200 with success message
   → Account activated

3. User logs in:
   POST /api/auth/login/
   → Returns 200 with access_token, refresh_token, and user data
   → Client stores tokens

4. User accesses protected resources:
   GET /api/users/me/
   Header: Authorization: Bearer <access_token>
   → Returns user data

5. Access token expires (15 minutes):
   POST /api/auth/refresh/
   Body: { "refresh": "<refresh_token>" }
   → Returns new access_token and refresh_token
   → Client updates stored tokens

6. User logs out:
   POST /api/auth/logout/
   Header: Authorization: Bearer <access_token>
   Body: { "refresh_token": "<refresh_token>" }
   → Returns 204
   → Client clears tokens
```

---

## Security Considerations

1. **Token Storage**:
   - Store tokens in httpOnly cookies or secure storage
   - Never store tokens in localStorage if XSS is a concern

2. **Token Expiration**:
   - Access tokens expire after 15 minutes
   - Refresh tokens expire after 7 days
   - Implement automatic token refresh before expiration

3. **Token Rotation**:
   - Refresh tokens are rotated on each use
   - Old refresh tokens are automatically blacklisted

4. **Rate Limiting**:
   - Authentication endpoints have strict rate limits
   - Implement client-side error handling for 429 responses

5. **HTTPS**:
   - Always use HTTPS in production
   - Tokens should never be transmitted over HTTP

6. **Password Requirements**:
   - Minimum 8 characters
   - At least 1 uppercase and 1 lowercase letter
   - At least 1 digit
   - At least 1 special character recommended

---

## Code Examples

### JavaScript/React Example

```javascript
// Login
async function login(email, password) {
  const response = await fetch('http://localhost:8000/api/auth/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });

  if (response.ok) {
    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data;
  }

  throw new Error('Login failed');
}

// Authenticated Request
async function getUserDetails() {
  const accessToken = localStorage.getItem('access_token');

  const response = await fetch('http://localhost:8000/api/users/me/', {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    }
  });

  if (response.ok) {
    return await response.json();
  }

  // Handle 401 - refresh token
  if (response.status === 401) {
    await refreshToken();
    return getUserDetails(); // Retry
  }

  throw new Error('Failed to get user details');
}

// Token Refresh
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');

  const response = await fetch('http://localhost:8000/api/auth/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: refreshToken })
  });

  if (response.ok) {
    const data = await response.json();
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    return data;
  }

  // Refresh failed - redirect to login
  localStorage.clear();
  window.location.href = '/login';
}

// Logout
async function logout() {
  const accessToken = localStorage.getItem('access_token');
  const refreshToken = localStorage.getItem('refresh_token');

  await fetch('http://localhost:8000/api/auth/logout/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ refresh_token: refreshToken })
  });

  // Clear tokens regardless of response
  localStorage.clear();
  window.location.href = '/login';
}
```

---

## Support

For questions or issues with the authentication API, please:
- Check the backend logs for detailed error messages
- Review the test cases in `backend/accounts/tests/`
- Contact the development team

**Documentation Version**: 1.0
**Last Updated**: 2025-01-25
**Related**: US-2 (Standard Account Login)
