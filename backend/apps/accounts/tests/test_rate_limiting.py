"""
Tests for rate limiting functionality in accounts app.

Tests:
- Rate limiting utility functions
- Redis integration and error handling
- Email hashing for privacy
- ResendVerificationEmailView rate limiting
- Retry timing calculations
- Counter incrementation and expiry
- Graceful degradation on Redis failure
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.rate_limiting import (
    check_resend_rate_limit,
    increment_resend_counter,
    get_remaining_resends,
    get_rate_limit_ttl,
    reset_rate_limit,
    _hash_email,
    _get_rate_limit_key,
    RESEND_VERIFICATION_MAX_ATTEMPTS,
    RESEND_VERIFICATION_WINDOW_SECONDS
)
from apps.accounts.models import CustomUser


class TestRateLimitingUtilities:
    """Test rate limiting utility functions."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def teardown_method(self):
        """Clear cache after each test."""
        cache.clear()

    def test_email_hashing_consistency(self):
        """Test that email hashing produces consistent results."""
        email = 'user@example.com'
        hash1 = _hash_email(email)
        hash2 = _hash_email(email)

        # Same email should produce same hash
        assert hash1 == hash2

        # Hash should be 64 characters (SHA-256 hex)
        assert len(hash1) == 64
        assert all(c in '0123456789abcdef' for c in hash1)

    def test_email_hashing_case_insensitive(self):
        """Test that email hashing is case-insensitive."""
        hash1 = _hash_email('User@Example.com')
        hash2 = _hash_email('user@example.com')
        hash3 = _hash_email('USER@EXAMPLE.COM')

        # All should produce same hash
        assert hash1 == hash2 == hash3

    def test_email_hashing_privacy(self):
        """Test that email hash doesn't reveal original email."""
        email = 'sensitive@example.com'
        email_hash = _hash_email(email)

        # Hash should not contain any part of original email
        assert 'sensitive' not in email_hash
        assert 'example' not in email_hash
        assert '@' not in email_hash

    def test_get_rate_limit_key_format(self):
        """Test rate limit key format."""
        email = 'user@example.com'
        key = _get_rate_limit_key(email)

        # Key should start with prefix
        assert key.startswith('resend_verification:')

        # Key should contain hash
        assert len(key) == len('resend_verification:') + 64

    def test_check_resend_rate_limit_no_attempts(self):
        """Test rate limit check with no previous attempts."""
        email = 'user@example.com'
        is_limited, retry_after = check_resend_rate_limit(email)

        assert is_limited is False
        assert retry_after is None

    def test_check_resend_rate_limit_within_limit(self):
        """Test rate limit check with attempts within limit."""
        email = 'user@example.com'

        # Make 2 attempts (within limit of 3)
        increment_resend_counter(email)
        increment_resend_counter(email)

        is_limited, retry_after = check_resend_rate_limit(email)

        assert is_limited is False
        assert retry_after is None

    def test_check_resend_rate_limit_at_limit(self):
        """Test rate limit check at exactly the limit."""
        email = 'user@example.com'

        # Make 3 attempts (at limit)
        for _ in range(RESEND_VERIFICATION_MAX_ATTEMPTS):
            increment_resend_counter(email)

        is_limited, retry_after = check_resend_rate_limit(email)

        assert is_limited is True
        assert retry_after is not None
        assert retry_after > 0
        # Should be close to 24 hours (86400 seconds)
        assert retry_after <= RESEND_VERIFICATION_WINDOW_SECONDS

    def test_check_resend_rate_limit_over_limit(self):
        """Test rate limit check over the limit."""
        email = 'user@example.com'

        # Make 4 attempts (over limit)
        for _ in range(RESEND_VERIFICATION_MAX_ATTEMPTS + 1):
            increment_resend_counter(email)

        is_limited, retry_after = check_resend_rate_limit(email)

        assert is_limited is True
        assert retry_after is not None

    def test_increment_resend_counter_first_time(self):
        """Test incrementing counter for first time."""
        email = 'user@example.com'
        count = increment_resend_counter(email)

        assert count == 1

    def test_increment_resend_counter_multiple_times(self):
        """Test incrementing counter multiple times."""
        email = 'user@example.com'

        count1 = increment_resend_counter(email)
        count2 = increment_resend_counter(email)
        count3 = increment_resend_counter(email)

        assert count1 == 1
        assert count2 == 2
        assert count3 == 3

    def test_increment_resend_counter_different_emails(self):
        """Test that counters are isolated per email."""
        email1 = 'user1@example.com'
        email2 = 'user2@example.com'

        count1a = increment_resend_counter(email1)
        count1b = increment_resend_counter(email1)
        count2a = increment_resend_counter(email2)

        assert count1a == 1
        assert count1b == 2
        assert count2a == 1  # Separate counter for email2

    def test_get_remaining_resends_no_attempts(self):
        """Test getting remaining attempts with no previous attempts."""
        email = 'user@example.com'
        remaining = get_remaining_resends(email)

        assert remaining == RESEND_VERIFICATION_MAX_ATTEMPTS

    def test_get_remaining_resends_after_attempts(self):
        """Test getting remaining attempts after some attempts."""
        email = 'user@example.com'

        increment_resend_counter(email)
        remaining = get_remaining_resends(email)
        assert remaining == RESEND_VERIFICATION_MAX_ATTEMPTS - 1

        increment_resend_counter(email)
        remaining = get_remaining_resends(email)
        assert remaining == RESEND_VERIFICATION_MAX_ATTEMPTS - 2

    def test_get_remaining_resends_at_limit(self):
        """Test getting remaining attempts at limit."""
        email = 'user@example.com'

        for _ in range(RESEND_VERIFICATION_MAX_ATTEMPTS):
            increment_resend_counter(email)

        remaining = get_remaining_resends(email)
        assert remaining == 0

    def test_get_rate_limit_ttl_no_limit(self):
        """Test getting TTL when no rate limit exists."""
        email = 'user@example.com'
        ttl = get_rate_limit_ttl(email)

        # Django Redis returns 0 for non-existent keys
        assert ttl in (None, 0)

    def test_get_rate_limit_ttl_with_limit(self):
        """Test getting TTL with active rate limit."""
        email = 'user@example.com'
        increment_resend_counter(email)

        ttl = get_rate_limit_ttl(email)

        assert ttl is not None
        assert ttl > 0
        assert ttl <= RESEND_VERIFICATION_WINDOW_SECONDS

    def test_reset_rate_limit(self):
        """Test resetting rate limit counter."""
        email = 'user@example.com'

        # Create some attempts
        increment_resend_counter(email)
        increment_resend_counter(email)

        # Reset counter
        result = reset_rate_limit(email)
        assert result is True

        # Counter should be reset
        remaining = get_remaining_resends(email)
        assert remaining == RESEND_VERIFICATION_MAX_ATTEMPTS

    def test_reset_rate_limit_nonexistent(self):
        """Test resetting rate limit that doesn't exist."""
        email = 'user@example.com'
        result = reset_rate_limit(email)

        # Should succeed even if counter doesn't exist
        assert result is True


class TestRateLimitingRedisFailure:
    """Test graceful degradation when Redis fails."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def teardown_method(self):
        """Clear cache after each test."""
        cache.clear()

    @patch('apps.accounts.rate_limiting.cache.get')
    def test_check_rate_limit_fails_open_on_redis_error(self, mock_get):
        """Test that rate limit check fails open on Redis error."""
        mock_get.side_effect = Exception('Redis connection failed')

        email = 'user@example.com'
        is_limited, retry_after = check_resend_rate_limit(email)

        # Should fail open (allow request)
        assert is_limited is False
        assert retry_after is None

    @patch('apps.accounts.rate_limiting.cache.add')
    @patch('apps.accounts.rate_limiting.cache.incr')
    def test_increment_counter_fails_open_on_redis_error(self, mock_incr, mock_add):
        """Test that counter increment fails open on Redis error."""
        mock_add.side_effect = Exception('Redis connection failed')
        mock_incr.side_effect = Exception('Redis connection failed')

        email = 'user@example.com'
        count = increment_resend_counter(email)

        # Should fail open (return 1)
        assert count == 1

    @patch('apps.accounts.rate_limiting.cache.get')
    def test_get_remaining_resends_fails_open_on_redis_error(self, mock_get):
        """Test that remaining check fails open on Redis error."""
        mock_get.side_effect = Exception('Redis connection failed')

        email = 'user@example.com'
        remaining = get_remaining_resends(email)

        # Should fail open (return max attempts)
        assert remaining == RESEND_VERIFICATION_MAX_ATTEMPTS

    @patch('apps.accounts.rate_limiting.cache.ttl')
    def test_get_ttl_fails_open_on_redis_error(self, mock_ttl):
        """Test that TTL check fails open on Redis error."""
        mock_ttl.side_effect = Exception('Redis connection failed')

        email = 'user@example.com'
        ttl = get_rate_limit_ttl(email)

        # Should fail open (return None)
        assert ttl is None


@pytest.mark.django_db
class TestResendVerificationEmailRateLimiting:
    """Test rate limiting integration with ResendVerificationEmailView."""

    def setup_method(self):
        """Set up test client and clear cache."""
        self.client = APIClient()
        self.resend_url = '/api/auth/resend-verification/'
        cache.clear()

        # Create unverified user
        self.user = CustomUser.objects.create_user(
            email='unverified@example.com',
            password='SecurePass123!',
            first_name='Test',
            last_name='User',
            is_active=False,
            is_email_verified=False
        )

    def teardown_method(self):
        """Clear cache after each test."""
        cache.clear()

    @patch('apps.accounts.tasks.send_verification_email.delay')
    def test_resend_verification_first_attempt_succeeds(self, mock_email_task):
        """Test that first resend attempt succeeds."""
        data = {'email': 'unverified@example.com'}
        response = self.client.post(self.resend_url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        assert response.data['attempts_remaining'] == RESEND_VERIFICATION_MAX_ATTEMPTS - 1
        mock_email_task.assert_called_once()

    @patch('apps.accounts.tasks.send_verification_email.delay')
    def test_resend_verification_within_limit_succeeds(self, mock_email_task):
        """Test that resend attempts within limit succeed."""
        data = {'email': 'unverified@example.com'}

        # Make 3 attempts (at limit)
        for i in range(RESEND_VERIFICATION_MAX_ATTEMPTS):
            response = self.client.post(self.resend_url, data, format='json')
            assert response.status_code == status.HTTP_200_OK

        # Verify email task called 3 times
        assert mock_email_task.call_count == RESEND_VERIFICATION_MAX_ATTEMPTS

    @patch('apps.accounts.tasks.send_verification_email.delay')
    def test_resend_verification_over_limit_blocked(self, mock_email_task):
        """Test that resend attempts over limit are blocked."""
        data = {'email': 'unverified@example.com'}

        # Make 3 attempts (at limit)
        for _ in range(RESEND_VERIFICATION_MAX_ATTEMPTS):
            response = self.client.post(self.resend_url, data, format='json')
            assert response.status_code == status.HTTP_200_OK

        # 4th attempt should be rate limited
        response = self.client.post(self.resend_url, data, format='json')

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.data['error'] == 'rate_limit_exceeded'
        assert 'retry_after_seconds' in response.data
        assert response.data['retry_after_seconds'] > 0
        assert response.data['max_attempts'] == RESEND_VERIFICATION_MAX_ATTEMPTS
        assert response.data['attempts_remaining'] == 0

        # Email should not be sent for 4th attempt
        assert mock_email_task.call_count == RESEND_VERIFICATION_MAX_ATTEMPTS

    @patch('apps.accounts.tasks.send_verification_email.delay')
    def test_resend_verification_rate_limit_per_email(self, mock_email_task):
        """Test that rate limiting is per email address."""
        # Create another unverified user
        user2 = CustomUser.objects.create_user(
            email='unverified2@example.com',
            password='SecurePass123!',
            first_name='Test2',
            last_name='User2',
            is_active=False,
            is_email_verified=False
        )

        # Exhaust rate limit for first user
        data1 = {'email': 'unverified@example.com'}
        for _ in range(RESEND_VERIFICATION_MAX_ATTEMPTS):
            response = self.client.post(self.resend_url, data1, format='json')
            assert response.status_code == status.HTTP_200_OK

        # First user should be rate limited
        response = self.client.post(self.resend_url, data1, format='json')
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        # Second user should not be affected
        data2 = {'email': 'unverified2@example.com'}
        response = self.client.post(self.resend_url, data2, format='json')
        assert response.status_code == status.HTTP_200_OK

    @patch('apps.accounts.tasks.send_verification_email.delay')
    def test_resend_verification_attempts_remaining_decrements(self, mock_email_task):
        """Test that attempts_remaining decrements correctly."""
        data = {'email': 'unverified@example.com'}

        # First attempt
        response = self.client.post(self.resend_url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['attempts_remaining'] == 2

        # Second attempt
        response = self.client.post(self.resend_url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['attempts_remaining'] == 1

        # Third attempt
        response = self.client.post(self.resend_url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['attempts_remaining'] == 0

    @patch('apps.accounts.tasks.send_verification_email.delay')
    def test_resend_verification_retry_after_timing(self, mock_email_task):
        """Test that retry_after timing is correct."""
        data = {'email': 'unverified@example.com'}

        # Exhaust rate limit
        for _ in range(RESEND_VERIFICATION_MAX_ATTEMPTS):
            response = self.client.post(self.resend_url, data, format='json')

        # Check rate limited response
        response = self.client.post(self.resend_url, data, format='json')
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        retry_after = response.data['retry_after_seconds']
        assert retry_after > 0
        # Should be close to 24 hours (within 10 seconds tolerance)
        assert abs(retry_after - RESEND_VERIFICATION_WINDOW_SECONDS) < 10

    @patch('apps.accounts.tasks.send_verification_email.delay')
    def test_resend_verification_case_insensitive_rate_limiting(self, mock_email_task):
        """Test that rate limiting is case-insensitive for email."""
        # Make attempts with different case variations
        emails = [
            'Unverified@Example.com',
            'unverified@example.com',
            'UNVERIFIED@EXAMPLE.COM'
        ]

        for email in emails:
            data = {'email': email}
            response = self.client.post(self.resend_url, data, format='json')
            assert response.status_code == status.HTTP_200_OK

        # All three attempts should count toward same rate limit
        # 4th attempt should be rate limited
        data = {'email': 'unverified@example.com'}
        response = self.client.post(self.resend_url, data, format='json')
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @patch('apps.accounts.tasks.send_verification_email.delay')
    @patch('apps.accounts.rate_limiting.cache.get')
    def test_resend_verification_graceful_degradation_on_redis_failure(
        self, mock_cache_get, mock_email_task
    ):
        """Test that endpoint works even when Redis fails."""
        # Simulate Redis failure
        mock_cache_get.side_effect = Exception('Redis connection failed')

        data = {'email': 'unverified@example.com'}
        response = self.client.post(self.resend_url, data, format='json')

        # Should succeed (fail open) and send email
        assert response.status_code == status.HTTP_200_OK
        mock_email_task.assert_called_once()


@pytest.mark.django_db
class TestRateLimitingEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def teardown_method(self):
        """Clear cache after each test."""
        cache.clear()

    def test_rate_limit_with_empty_email(self):
        """Test rate limiting with empty email."""
        email = ''
        # Should not crash, just hash empty string
        hash_result = _hash_email(email)
        assert len(hash_result) == 64

    def test_rate_limit_with_unicode_email(self):
        """Test rate limiting with unicode email."""
        email = 'user@例え.com'
        # Should handle unicode correctly
        hash_result = _hash_email(email)
        assert len(hash_result) == 64

        # Should be able to increment counter
        count = increment_resend_counter(email)
        assert count == 1

    def test_rate_limit_with_very_long_email(self):
        """Test rate limiting with very long email."""
        email = 'a' * 1000 + '@example.com'
        # Should handle long emails correctly
        hash_result = _hash_email(email)
        assert len(hash_result) == 64

        count = increment_resend_counter(email)
        assert count == 1

    def test_concurrent_increments_same_email(self):
        """Test that concurrent increments are handled correctly."""
        email = 'user@example.com'

        # Simulate rapid successive increments
        counts = []
        for _ in range(5):
            count = increment_resend_counter(email)
            counts.append(count)

        # All increments should succeed and be sequential
        assert counts == [1, 2, 3, 4, 5]

    def test_rate_limit_reset_allows_new_attempts(self):
        """Test that resetting rate limit allows new attempts."""
        email = 'user@example.com'

        # Exhaust rate limit
        for _ in range(RESEND_VERIFICATION_MAX_ATTEMPTS):
            increment_resend_counter(email)

        # Should be limited
        is_limited, _ = check_resend_rate_limit(email)
        assert is_limited is True

        # Reset rate limit
        reset_rate_limit(email)

        # Should not be limited anymore
        is_limited, _ = check_resend_rate_limit(email)
        assert is_limited is False

        # Should be able to make new attempts
        remaining = get_remaining_resends(email)
        assert remaining == RESEND_VERIFICATION_MAX_ATTEMPTS
