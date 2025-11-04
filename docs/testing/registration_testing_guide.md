# Registration Testing Guide

This guide provides comprehensive instructions for testing the user registration feature (US-1).

## Table of Contents

1. [Test Environment Setup](#test-environment-setup)
2. [Manual Testing](#manual-testing)
3. [Automated Testing](#automated-testing)
4. [API Testing](#api-testing)
5. [Security Testing](#security-testing)
6. [Performance Testing](#performance-testing)

## Test Environment Setup

### Prerequisites

- Docker and Docker Compose installed
- Services running: `docker-compose up -d db redis backend frontend`
- Database migrations applied: `docker-compose exec backend python manage.py migrate`

### Verification

Check all services are healthy:

```bash
docker-compose ps
```

Expected output:
- `backend`: Up and healthy on port 8000
- `frontend`: Up on port 3000
- `db`: Up and healthy on port 5432 (internal)
- `redis`: Up and healthy on port 6379 (internal)

## Manual Testing

### Frontend Testing

#### Test Case 1: Access Registration Page

1. Navigate to: http://localhost:3000
2. Click "Get Started" button
3. Verify redirect to: http://localhost:3000/register

**Expected Result:**
- Registration form displays with all fields
- Form has clean, professional design
- "Already have an account? Sign in" link visible

#### Test Case 2: Client-Side Validation

**Email Validation:**
1. Enter invalid email: `test@`
2. Tab out of field
3. Verify error: "Please enter a valid email address"

**Password Validation:**
1. Enter weak password: `abc`
2. Verify password strength indicator shows requirements
3. Requirements should display:
   - ✗ At least 8 characters
   - ✗ Contains uppercase letter (A-Z)
   - ✗ Contains lowercase letter (a-z)
   - ✗ Contains number (0-9)
   - ✗ Contains special character (Optional)

**Password Match Validation:**
1. Enter password: `TestPassword123`
2. Enter different confirm password: `TestPassword456`
3. Tab out of confirm field
4. Verify error: "Passwords do not match"

#### Test Case 3: Successful Registration

**Steps:**
1. Navigate to registration page
2. Fill in form:
   - Email: `newuser@example.com`
   - Password: `TestPassword123`
   - Confirm Password: `TestPassword123`
   - First Name: `John`
   - Last Name: `Doe`
3. Click "Create Account"

**Expected Result:**
- Success alert appears: "Registration successful! Please check your email..."
- After 2 seconds, redirect to `/verify-email`
- Verify email page shows: "Verification email sent to newuser@example.com"

#### Test Case 4: Duplicate Email

**Steps:**
1. Register with email: `duplicate@example.com`
2. Try registering again with same email

**Expected Result:**
- Error alert: "An account with this email already exists."
- Form remains on registration page
- No redirect occurs

#### Test Case 5: Rate Limiting

**Steps:**
1. Submit registration form 5 times within 1 minute
2. Attempt 6th registration

**Expected Result:**
- First 5 attempts: Normal processing
- 6th attempt: Error alert with rate limit message
- HTTP 429 status code

### Backend Testing

#### Test Case 6: API Response Format

Test registration endpoint directly:

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "apitest@example.com",
    "password": "TestPassword123",
    "password_confirm": "TestPassword123",
    "first_name": "API",
    "last_name": "Test"
  }'
```

**Expected Response (201 Created):**
```json
{
  "id": "uuid-here",
  "email": "apitest@example.com",
  "first_name": "API",
  "last_name": "Test",
  "full_name": "API Test",
  "is_active": false,
  "is_verified": false,
  "date_joined": "2025-11-04T22:00:00Z",
  "message": "Registration successful. Please check your email to verify your account."
}
```

**Verify Database:**
```bash
docker-compose exec backend python manage.py shell
```

```python
from apps.accounts.models import CustomUser
user = CustomUser.objects.get(email='apitest@example.com')
print(f"User ID: {user.id}")
print(f"Active: {user.is_active}")
print(f"Verified: {user.is_verified}")
print(f"Password hashed: {user.password.startswith('argon2')}")
```

## Automated Testing

### Running Unit Tests

**Backend Tests (73 tests total):**

```bash
# Run all accounts tests
docker-compose exec backend pytest apps/accounts/tests/ -v

# Run specific test files
docker-compose exec backend pytest apps/accounts/tests/test_models.py -v
docker-compose exec backend pytest apps/accounts/tests/test_validators.py -v
docker-compose exec backend pytest apps/accounts/tests/test_serializers.py -v
```

**Test Coverage by Category:**
- Model tests: 14 tests (test_models.py)
- Validator tests: 17 tests (test_validators.py)
- Serializer tests: 17 tests (test_serializers.py)
- Integration tests: 10 tests (test_integration.py)
- Security tests: 15 tests (test_security.py)

### Running Integration Tests

```bash
# Full registration workflow tests
docker-compose exec backend pytest apps/accounts/tests/test_integration.py -v

# Specific integration test
docker-compose exec backend pytest apps/accounts/tests/test_integration.py::TestRegistrationIntegration::test_complete_registration_flow -v
```

### Running Security Tests

```bash
# All security tests
docker-compose exec backend pytest apps/accounts/tests/test_security.py -v

# Rate limiting test
docker-compose exec backend pytest apps/accounts/tests/test_security.py::TestSecurityFeatures::test_rate_limiting -v

# SQL injection prevention test
docker-compose exec backend pytest apps/accounts/tests/test_security.py::TestSecurityFeatures::test_sql_injection_prevention -v
```

### Test Coverage Report

Generate test coverage report:

```bash
docker-compose exec backend pytest apps/accounts/tests/ --cov=apps.accounts --cov-report=html
```

View report: Open `backend/htmlcov/index.html` in browser

**Target Coverage:** >80% for registration logic

## API Testing

### Postman/Insomnia Collection

**Registration Request:**

```http
POST http://localhost:8000/api/auth/register/
Content-Type: application/json

{
  "email": "postman@example.com",
  "password": "TestPassword123",
  "password_confirm": "TestPassword123",
  "first_name": "Postman",
  "last_name": "Test"
}
```

**Test Scenarios:**

1. **Valid Registration**: Expect 201 with user data
2. **Invalid Email**: Expect 400 with email error
3. **Weak Password**: Expect 400 with password requirements
4. **Password Mismatch**: Expect 400 with match error
5. **Duplicate Email**: Expect 409 with conflict error
6. **Rate Limit Exceeded**: Expect 429 after 5 attempts
7. **Missing Fields**: Expect 400 with field errors

### API Documentation

Access interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## Security Testing

### Password Security Tests

**Test Case 1: Password Hashing**

Verify passwords are hashed with Argon2:

```bash
docker-compose exec backend python manage.py shell
```

```python
from apps.accounts.models import CustomUser
user = CustomUser.objects.first()
print(user.password)  # Should start with 'argon2'
```

**Test Case 2: Password Not Logged**

1. Trigger validation error
2. Check logs: `docker-compose logs backend | grep password`
3. Verify: No plaintext passwords in logs

**Test Case 3: Password Not in Response**

1. Make registration request
2. Check response JSON
3. Verify: `password` field not present in response

### XSS Prevention Tests

**Test Case 4: Script Injection in Names**

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "xss@example.com",
    "password": "TestPassword123",
    "password_confirm": "TestPassword123",
    "first_name": "<script>alert(\"XSS\")</script>",
    "last_name": "Test"
  }'
```

**Expected:** Script tags sanitized/escaped in response

### SQL Injection Prevention Tests

**Test Case 5: SQL Injection in Email**

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com' OR '1'='1",
    "password": "TestPassword123",
    "password_confirm": "TestPassword123",
    "first_name": "SQL",
    "last_name": "Injection"
  }'
```

**Expected:** 400 error with "invalid email format" (not SQL error)

### Rate Limiting Tests

**Test Case 6: IP-Based Rate Limiting**

```bash
# Script to test rate limiting
for i in {1..6}; do
  echo "Request $i:"
  curl -X POST http://localhost:8000/api/auth/register/ \
    -H "Content-Type: application/json" \
    -d "{
      \"email\": \"ratelimit$i@example.com\",
      \"password\": \"TestPassword123\",
      \"password_confirm\": \"TestPassword123\",
      \"first_name\": \"Rate\",
      \"last_name\": \"Limit\"
    }" -w "\nHTTP Status: %{http_code}\n\n"
  sleep 1
done
```

**Expected:**
- Requests 1-5: HTTP 201 (success)
- Request 6: HTTP 429 (rate limit exceeded)

## Performance Testing

### Response Time Tests

**Test Case 1: Registration Endpoint Performance**

Use Apache Bench to test:

```bash
# Create test data file
echo '{
  "email": "perf@example.com",
  "password": "TestPassword123",
  "password_confirm": "TestPassword123",
  "first_name": "Perf",
  "last_name": "Test"
}' > /tmp/registration.json

# Run 10 requests
ab -n 10 -c 1 -p /tmp/registration.json -T application/json \
  http://localhost:8000/api/auth/register/
```

**Target:** P95 response time < 300ms

### Load Testing

**Test Case 2: Concurrent Registrations**

```bash
# Use hey or similar tool
hey -n 50 -c 5 -m POST \
  -H "Content-Type: application/json" \
  -d '{"email":"load{random}@example.com","password":"TestPassword123","password_confirm":"TestPassword123","first_name":"Load","last_name":"Test"}' \
  http://localhost:8000/api/auth/register/
```

**Expected:** All requests complete within 5 seconds

## Test Data Cleanup

### Reset Test Database

```bash
# Drop all users
docker-compose exec backend python manage.py shell
```

```python
from apps.accounts.models import CustomUser
CustomUser.objects.all().delete()
```

### Reset Rate Limits

```bash
# Clear Redis cache
docker-compose exec redis redis-cli FLUSHDB
```

## Continuous Integration

### GitHub Actions Workflow

Create `.github/workflows/test-registration.yml`:

```yaml
name: Test Registration Feature

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: pgvector/pgvector:pg15
      redis:
        image: redis:latest

    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          cd backend
          pip install poetry
          poetry install
      - name: Run tests
        run: |
          cd backend
          poetry run pytest apps/accounts/tests/ -v --cov=apps.accounts
```

## Troubleshooting Tests

See [Troubleshooting Guide](./registration_troubleshooting.md) for common test failures and solutions.

## Test Reports

### Generate Test Report

```bash
# HTML report
docker-compose exec backend pytest apps/accounts/tests/ --html=report.html --self-contained-html

# JUnit XML (for CI)
docker-compose exec backend pytest apps/accounts/tests/ --junitxml=junit.xml
```

## Checklist

Use this checklist before marking registration feature as complete:

- [ ] All 73 automated tests pass
- [ ] Test coverage >80%
- [ ] Manual registration flow works end-to-end
- [ ] Rate limiting enforced (6th request blocked)
- [ ] Passwords hashed with Argon2
- [ ] XSS prevention verified
- [ ] SQL injection prevention verified
- [ ] API documentation accessible
- [ ] Response times <300ms (P95)
- [ ] No sensitive data in logs
- [ ] Email verification workflow tested
