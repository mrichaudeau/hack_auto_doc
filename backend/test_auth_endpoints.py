#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for authentication endpoints (TASK-2.3, 2.4, 2.5, 2.7)
Tests login, logout, token refresh, and user detail endpoints.
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

User = get_user_model()

# Test configuration
BASE_URL = 'http://localhost:8000/api'
TEST_EMAIL = 'test.auth@example.com'
TEST_PASSWORD = 'TestPass123!@#'
TEST_FIRST_NAME = 'Test'
TEST_LAST_NAME = 'Auth'

def print_result(test_name, passed, details=''):
    """Print test result with consistent formatting."""
    status = '[PASS]' if passed else '[FAIL]'
    print(f'{status} {test_name}')
    if details:
        print(f'      {details}')

def setup_test_user():
    """Create or reset test user for authentication tests."""
    print('\n=== Setting Up Test User ===')

    # Delete existing test user if exists
    User.objects.filter(email__iexact=TEST_EMAIL).delete()

    # Create active test user with verified email
    user = User.objects.create_user(
        email=TEST_EMAIL,
        first_name=TEST_FIRST_NAME,
        last_name=TEST_LAST_NAME,
        password=TEST_PASSWORD,
        auth_provider=User.AuthProvider.STANDARD,
        is_active=True  # Active for login tests
    )

    # Create verified EmailAddress
    EmailAddress.objects.create(
        user=user,
        email=user.email,
        primary=True,
        verified=True
    )

    print(f'[OK] Test user created: {TEST_EMAIL}')
    return user

def test_login_valid():
    """Test POST /api/auth/login/ with valid credentials."""
    print('\n--- Test 1: Login with Valid Credentials ---')

    response = requests.post(
        f'{BASE_URL}/auth/login/',
        json={
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD
        },
        headers={'Content-Type': 'application/json'}
    )

    success = response.status_code == 200
    data = response.json() if success else {}

    if success:
        has_tokens = 'access_token' in data and 'refresh_token' in data
        has_user = 'user' in data and data['user']['email'] == TEST_EMAIL.lower()
        success = has_tokens and has_user

        if success:
            details = f"Access token: {data['access_token'][:20]}... | User: {data['user']['email']}"
            print_result('Login successful', True, details)
            return data  # Return tokens for subsequent tests
        else:
            print_result('Login successful but invalid response structure', False)
            return None
    else:
        error = data.get('detail', data)
        print_result('Login failed', False, f'Error: {error}')
        return None

def test_login_invalid_password():
    """Test POST /api/auth/login/ with invalid password."""
    print('\n--- Test 2: Login with Invalid Password ---')

    response = requests.post(
        f'{BASE_URL}/auth/login/',
        json={
            'email': TEST_EMAIL,
            'password': 'WrongPassword123!'
        },
        headers={'Content-Type': 'application/json'}
    )

    success = response.status_code == 401
    error = response.json() if not success else {}

    print_result('Invalid password rejected', success, f'Status: {response.status_code}')

def test_login_nonexistent_email():
    """Test POST /api/auth/login/ with non-existent email."""
    print('\n--- Test 3: Login with Non-existent Email ---')

    response = requests.post(
        f'{BASE_URL}/auth/login/',
        json={
            'email': 'nonexistent@example.com',
            'password': TEST_PASSWORD
        },
        headers={'Content-Type': 'application/json'}
    )

    success = response.status_code == 401
    print_result('Non-existent email rejected', success, f'Status: {response.status_code}')

def test_login_inactive_account():
    """Test POST /api/auth/login/ with inactive account."""
    print('\n--- Test 4: Login with Inactive Account ---')

    # Create inactive test user
    inactive_email = 'inactive@example.com'
    User.objects.filter(email__iexact=inactive_email).delete()

    user = User.objects.create_user(
        email=inactive_email,
        first_name='Inactive',
        last_name='User',
        password=TEST_PASSWORD,
        auth_provider=User.AuthProvider.STANDARD,
        is_active=False  # Inactive account
    )

    response = requests.post(
        f'{BASE_URL}/auth/login/',
        json={
            'email': inactive_email,
            'password': TEST_PASSWORD
        },
        headers={'Content-Type': 'application/json'}
    )

    success = response.status_code == 401
    data = response.json()
    has_correct_error = 'verifie' in str(data).lower() or 'verifier' in str(data).lower()

    print_result('Inactive account rejected', success and has_correct_error,
                f'Status: {response.status_code}')

    # Cleanup
    User.objects.filter(email__iexact=inactive_email).delete()

def test_token_refresh(refresh_token):
    """Test POST /api/auth/refresh/ with valid refresh token."""
    print('\n--- Test 5: Token Refresh ---')

    if not refresh_token:
        print_result('Token refresh', False, 'No refresh token available')
        return None

    response = requests.post(
        f'{BASE_URL}/auth/refresh/',
        json={'refresh': refresh_token},
        headers={'Content-Type': 'application/json'}
    )

    success = response.status_code == 200
    data = response.json() if success else {}

    if success:
        has_access_token = 'access' in data
        has_new_refresh = 'refresh' in data  # Due to ROTATE_REFRESH_TOKENS=True
        success = has_access_token

        details = f"New access token: {data.get('access', '')[:20]}..."
        print_result('Token refresh successful', True, details)
        return data
    else:
        error = data.get('detail', data)
        print_result('Token refresh failed', False, f'Error: {error}')
        return None

def test_user_detail_with_token(access_token):
    """Test GET /api/users/me/ with valid access token."""
    print('\n--- Test 6: Get User Detail with Valid Token ---')

    if not access_token:
        print_result('Get user detail', False, 'No access token available')
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

    if success:
        correct_user = data.get('email') == TEST_EMAIL.lower()
        success = correct_user

        details = f"Email: {data.get('email')} | ID: {data.get('id')}"
        print_result('User detail retrieved', success, details)
    else:
        error = data.get('detail', data)
        print_result('User detail failed', False, f'Error: {error}')

def test_user_detail_without_token():
    """Test GET /api/users/me/ without access token."""
    print('\n--- Test 7: Get User Detail without Token ---')

    response = requests.get(
        f'{BASE_URL}/users/me/',
        headers={'Content-Type': 'application/json'}
    )

    success = response.status_code == 401
    print_result('Unauthorized access blocked', success, f'Status: {response.status_code}')

def test_logout_with_token(refresh_token, access_token):
    """Test POST /api/auth/logout/ with valid refresh token."""
    print('\n--- Test 8: Logout with Valid Refresh Token ---')

    if not refresh_token or not access_token:
        print_result('Logout', False, 'No tokens available')
        return

    response = requests.post(
        f'{BASE_URL}/auth/logout/',
        json={'refresh_token': refresh_token},
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    )

    success = response.status_code == 204
    print_result('Logout successful', success, f'Status: {response.status_code}')

def test_logout_with_blacklisted_token(refresh_token, access_token):
    """Test POST /api/auth/logout/ with already blacklisted token."""
    print('\n--- Test 9: Logout with Blacklisted Token ---')

    if not refresh_token or not access_token:
        print_result('Logout with blacklisted token', False, 'No tokens available')
        return

    response = requests.post(
        f'{BASE_URL}/auth/logout/',
        json={'refresh_token': refresh_token},
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    )

    # Should return 400 because token is already blacklisted
    success = response.status_code == 400
    print_result('Blacklisted token rejected', success, f'Status: {response.status_code}')

def test_logout_without_refresh_token(access_token):
    """Test POST /api/auth/logout/ without refresh token."""
    print('\n--- Test 10: Logout without Refresh Token ---')

    if not access_token:
        print_result('Logout without refresh token', False, 'No access token available')
        return

    response = requests.post(
        f'{BASE_URL}/auth/logout/',
        json={},
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    )

    success = response.status_code == 400
    data = response.json() if not success else {}
    has_error = 'refresh_token' in data

    print_result('Missing refresh token rejected', success and has_error,
                f'Status: {response.status_code}')

def main():
    """Run all authentication endpoint tests."""
    print('=' * 60)
    print('Authentication Endpoints Test Suite')
    print('Testing TASK-2.3, 2.4, 2.5, 2.7')
    print('=' * 60)

    # Setup
    try:
        setup_test_user()
    except Exception as e:
        print(f'[FAIL] Failed to setup test user: {e}')
        return

    # Test login
    login_data = test_login_valid()
    test_login_invalid_password()
    test_login_nonexistent_email()
    test_login_inactive_account()

    if not login_data:
        print('\n[FAIL] Cannot continue tests without valid login')
        return

    access_token = login_data.get('access_token')
    refresh_token = login_data.get('refresh_token')

    # Test token refresh
    refresh_data = test_token_refresh(refresh_token)

    # Test user detail endpoint
    test_user_detail_with_token(access_token)
    test_user_detail_without_token()

    # Get new tokens for logout tests
    new_login_data = test_login_valid()
    if new_login_data:
        new_access = new_login_data.get('access_token')
        new_refresh = new_login_data.get('refresh_token')

        # Test logout
        test_logout_with_token(new_refresh, new_access)
        test_logout_with_blacklisted_token(new_refresh, new_access)

        # Get another set for the missing token test
        final_login = test_login_valid()
        if final_login:
            test_logout_without_refresh_token(final_login.get('access_token'))

    print('\n' + '=' * 60)
    print('Test Suite Complete')
    print('=' * 60)

    # Cleanup
    print('\n=== Cleanup ===')
    User.objects.filter(email__iexact=TEST_EMAIL).delete()
    print('[OK] Test user deleted')

if __name__ == '__main__':
    main()
