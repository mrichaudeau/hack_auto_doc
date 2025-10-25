#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for JWT error handling middleware (TASK-2.6)
Tests various JWT error scenarios and verifies standardized error responses.
"""

import os
import sys
import django

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import json
import requests
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta

User = get_user_model()

# Test configuration
BASE_URL = 'http://localhost:8000/api'
TEST_EMAIL = 'test.jwt@example.com'
TEST_PASSWORD = 'TestJWT123!@#'

def print_result(test_name, passed, details=''):
    """Print test result with consistent formatting."""
    status = '[PASS]' if passed else '[FAIL]'
    print(f'{status} {test_name}')
    if details:
        print(f'      {details}')

def setup_test_user():
    """Create test user for JWT error testing."""
    print('\n=== Setting Up Test User ===')

    # Delete existing test user
    User.objects.filter(email__iexact=TEST_EMAIL).delete()

    # Create active user
    user = User.objects.create_user(
        email=TEST_EMAIL,
        first_name='Test',
        last_name='JWT',
        password=TEST_PASSWORD,
        auth_provider=User.AuthProvider.STANDARD,
        is_active=True
    )

    EmailAddress.objects.create(
        user=user,
        email=user.email,
        primary=True,
        verified=True
    )

    print(f'[OK] Test user created: {TEST_EMAIL}')
    return user

def get_valid_tokens():
    """Login and get valid tokens."""
    response = requests.post(
        f'{BASE_URL}/auth/login/',
        json={'email': TEST_EMAIL, 'password': TEST_PASSWORD},
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code == 200:
        data = response.json()
        return data.get('access_token'), data.get('refresh_token')
    return None, None

def test_missing_authentication_header():
    """Test 1: Access protected endpoint without authentication header."""
    print('\n--- Test 1: Missing Authentication Header ---')

    response = requests.get(
        f'{BASE_URL}/users/me/',
        headers={'Content-Type': 'application/json'}
    )

    success = response.status_code == 401
    data = response.json() if response.status_code in [401, 403] else {}

    has_error = 'error' in data or 'detail' in data
    print_result('Missing auth header returns 401', success and has_error,
                f"Status: {response.status_code} | Response: {data.get('detail', data.get('error', ''))}")

def test_invalid_token_format():
    """Test 2: Access with malformed token."""
    print('\n--- Test 2: Invalid Token Format ---')

    response = requests.get(
        f'{BASE_URL}/users/me/',
        headers={
            'Authorization': 'Bearer invalid.token.format',
            'Content-Type': 'application/json'
        }
    )

    success = response.status_code == 401
    data = response.json() if response.status_code in [401, 403] else {}

    has_error_message = 'error' in data or 'detail' in data
    print_result('Invalid token format returns 401', success and has_error_message,
                f"Status: {response.status_code} | Error: {data.get('error', data.get('detail', ''))}")

def test_valid_token_access():
    """Test 3: Access with valid token (should succeed)."""
    print('\n--- Test 3: Valid Token Access ---')

    access_token, _ = get_valid_tokens()
    if not access_token:
        print_result('Valid token access', False, 'Could not get valid token')
        return

    response = requests.get(
        f'{BASE_URL}/users/me/',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    )

    success = response.status_code == 200
    data = response.json() if success else {}

    print_result('Valid token grants access', success,
                f"Status: {response.status_code} | User: {data.get('email', '')}")

def test_blacklisted_token():
    """Test 4: Access with blacklisted token (after logout)."""
    print('\n--- Test 4: Blacklisted Token ---')

    # Get fresh tokens
    access_token, refresh_token = get_valid_tokens()
    if not access_token or not refresh_token:
        print_result('Blacklisted token test', False, 'Could not get tokens')
        return

    # Blacklist the refresh token via logout
    logout_response = requests.post(
        f'{BASE_URL}/auth/logout/',
        json={'refresh_token': refresh_token},
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    )

    if logout_response.status_code != 204:
        print_result('Blacklisted token test', False, f'Logout failed: {logout_response.status_code}')
        return

    # Try to refresh with blacklisted token
    response = requests.post(
        f'{BASE_URL}/auth/refresh/',
        json={'refresh': refresh_token},
        headers={'Content-Type': 'application/json'}
    )

    success = response.status_code == 401
    data = response.json() if response.status_code in [401, 403] else {}

    has_blacklist_error = 'blacklist' in str(data).lower() or 'error' in data
    print_result('Blacklisted token rejected', success and has_blacklist_error,
                f"Status: {response.status_code} | Message: {data.get('detail', data.get('error', ''))}")

def test_invalid_authorization_header_format():
    """Test 5: Invalid Authorization header format (missing 'Bearer')."""
    print('\n--- Test 5: Invalid Authorization Header Format ---')

    access_token, _ = get_valid_tokens()
    if not access_token:
        print_result('Invalid header format test', False, 'Could not get token')
        return

    # Use token without 'Bearer' prefix
    response = requests.get(
        f'{BASE_URL}/users/me/',
        headers={
            'Authorization': access_token,  # Missing 'Bearer ' prefix
            'Content-Type': 'application/json'
        }
    )

    success = response.status_code == 401
    data = response.json() if response.status_code in [401, 403] else {}

    print_result('Invalid header format rejected', success,
                f"Status: {response.status_code} | Error: {data.get('detail', data.get('error', ''))}")

def test_tampered_token():
    """Test 6: Access with tampered token (modified signature)."""
    print('\n--- Test 6: Tampered Token ---')

    access_token, _ = get_valid_tokens()
    if not access_token:
        print_result('Tampered token test', False, 'Could not get token')
        return

    # Tamper with the token by modifying last few characters
    tampered_token = access_token[:-10] + 'TAMPERED12'

    response = requests.get(
        f'{BASE_URL}/users/me/',
        headers={
            'Authorization': f'Bearer {tampered_token}',
            'Content-Type': 'application/json'
        }
    )

    success = response.status_code == 401
    data = response.json() if response.status_code in [401, 403] else {}

    has_invalid_error = 'invalid' in str(data).lower() or 'error' in data
    print_result('Tampered token rejected', success and has_invalid_error,
                f"Status: {response.status_code} | Error: {data.get('error', data.get('detail', ''))}")

def test_expired_refresh_token():
    """Test 7: Try to use an invalid/expired refresh token."""
    print('\n--- Test 7: Invalid Refresh Token ---')

    # Use a completely fake refresh token
    fake_refresh = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTYwMDAwMDAwMCwianRpIjoiZmFrZSIsInVzZXJfaWQiOjk5OTk5fQ.fake_signature'

    response = requests.post(
        f'{BASE_URL}/auth/refresh/',
        json={'refresh': fake_refresh},
        headers={'Content-Type': 'application/json'}
    )

    success = response.status_code == 401
    data = response.json() if response.status_code in [401, 403] else {}

    has_error = 'error' in data or 'detail' in data
    print_result('Invalid refresh token rejected', success and has_error,
                f"Status: {response.status_code} | Error: {data.get('error', data.get('detail', ''))}")

def test_error_response_structure():
    """Test 8: Verify error response has standardized structure."""
    print('\n--- Test 8: Error Response Structure ---')

    response = requests.get(
        f'{BASE_URL}/users/me/',
        headers={
            'Authorization': 'Bearer invalid.token',
            'Content-Type': 'application/json'
        }
    )

    success = response.status_code == 401
    data = response.json() if response.status_code in [401, 403] else {}

    # Check if response has expected fields
    has_error_field = 'error' in data or 'detail' in data
    has_code_or_type = 'code' in data or 'type' in data or 'detail' in data

    print_result('Error response has standardized structure',
                success and has_error_field,
                f"Response fields: {list(data.keys())}")

def main():
    """Run all JWT error handling tests."""
    print('=' * 60)
    print('JWT Error Handling Test Suite')
    print('Testing TASK-2.6: Custom Exception Handler')
    print('=' * 60)

    # Setup
    try:
        user = setup_test_user()
    except Exception as e:
        print(f'[FAIL] Failed to setup test user: {e}')
        return

    # Run tests
    test_missing_authentication_header()
    test_invalid_token_format()
    test_valid_token_access()
    test_blacklisted_token()
    test_invalid_authorization_header_format()
    test_tampered_token()
    test_expired_refresh_token()
    test_error_response_structure()

    print('\n' + '=' * 60)
    print('Test Suite Complete')
    print('=' * 60)

    # Cleanup
    print('\n=== Cleanup ===')
    User.objects.filter(email__iexact=TEST_EMAIL).delete()
    print('[OK] Test user deleted')

if __name__ == '__main__':
    main()
