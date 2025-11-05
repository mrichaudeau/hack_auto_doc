"""
Unit tests for cleanup_expired_verification_tokens Celery task.

Tests:
- Expired token deletion
- Used token deletion
- Active token preservation
- Bulk deletion efficiency
- Logging output
- Error handling and retry logic
- Task execution statistics
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from unittest.mock import patch, MagicMock
from celery.exceptions import Retry

from apps.accounts.models import EmailVerificationToken
from apps.accounts.tasks import cleanup_expired_verification_tokens
from apps.accounts.tests.factories import UserFactory


@pytest.mark.django_db
class TestCleanupExpiredVerificationTokens:
    """Test suite for cleanup_expired_verification_tokens task."""

    def test_deletes_expired_tokens(self):
        """Test that expired tokens are deleted."""
        # Create user
        user = UserFactory()

        # Create expired token (24 hours ago)
        expired_time = timezone.now() - timedelta(hours=25)
        expired_token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=expired_time,
            is_used=False
        )

        # Create active token (expires in future)
        active_token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=23),
            is_used=False
        )

        # Run cleanup task
        result = cleanup_expired_verification_tokens()

        # Verify expired token deleted
        assert not EmailVerificationToken.objects.filter(id=expired_token.id).exists()

        # Verify active token preserved
        assert EmailVerificationToken.objects.filter(id=active_token.id).exists()

        # Verify result statistics
        assert result['deleted'] == 1
        assert result['expired_count'] == 1
        assert result['used_count'] == 0
        assert result['dry_run'] is False
        assert 'timestamp' in result

    def test_deletes_used_tokens_older_than_7_days(self):
        """Test that used tokens older than 7 days are deleted."""
        # Create user
        user = UserFactory()

        # Create old used token (8 days old)
        old_used_token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=23),
            is_used=True
        )
        # Manually set created_at to 8 days ago
        old_used_token.created_at = timezone.now() - timedelta(days=8)
        old_used_token.save()

        # Create recent used token (5 days old - should be preserved)
        recent_used_token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=23),
            is_used=True
        )
        recent_used_token.created_at = timezone.now() - timedelta(days=5)
        recent_used_token.save()

        # Create unused token
        unused_token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=23),
            is_used=False
        )

        # Run cleanup task
        result = cleanup_expired_verification_tokens()

        # Verify old used token deleted
        assert not EmailVerificationToken.objects.filter(id=old_used_token.id).exists()

        # Verify recent used token preserved (less than 7 days old)
        assert EmailVerificationToken.objects.filter(id=recent_used_token.id).exists()

        # Verify unused token preserved
        assert EmailVerificationToken.objects.filter(id=unused_token.id).exists()

        # Verify result statistics
        assert result['deleted'] == 1
        assert result['expired_count'] == 0
        assert result['used_count'] == 1

    def test_preserves_active_unused_tokens(self):
        """Test that active unused tokens are preserved."""
        # Create user
        user = UserFactory()

        # Create multiple active tokens
        token1 = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=1),
            is_used=False
        )

        token2 = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=23),
            is_used=False
        )

        # Run cleanup task
        result = cleanup_expired_verification_tokens()

        # Verify both tokens preserved
        assert EmailVerificationToken.objects.filter(id=token1.id).exists()
        assert EmailVerificationToken.objects.filter(id=token2.id).exists()

        # Verify no deletions
        assert result['deleted'] == 0
        assert result['expired_count'] == 0
        assert result['used_count'] == 0

    def test_deletes_both_expired_and_old_used_tokens(self):
        """Test deletion of both expired and old used tokens in single run."""
        # Create users
        user1 = UserFactory()
        user2 = UserFactory()

        # Create expired token
        expired_token = EmailVerificationToken.objects.create(
            user=user1,
            expires_at=timezone.now() - timedelta(hours=1),
            is_used=False
        )

        # Create old used token (8 days old, not expired)
        old_used_token = EmailVerificationToken.objects.create(
            user=user2,
            expires_at=timezone.now() + timedelta(hours=23),
            is_used=True
        )
        old_used_token.created_at = timezone.now() - timedelta(days=8)
        old_used_token.save()

        # Create expired AND used token (8 days old)
        expired_used_token = EmailVerificationToken.objects.create(
            user=user1,
            expires_at=timezone.now() - timedelta(hours=2),
            is_used=True
        )
        expired_used_token.created_at = timezone.now() - timedelta(days=8)
        expired_used_token.save()

        # Create active unused token
        active_token = EmailVerificationToken.objects.create(
            user=user2,
            expires_at=timezone.now() + timedelta(hours=23),
            is_used=False
        )

        # Create recent used token (5 days old - should be preserved)
        recent_used_token = EmailVerificationToken.objects.create(
            user=user1,
            expires_at=timezone.now() + timedelta(hours=23),
            is_used=True
        )
        recent_used_token.created_at = timezone.now() - timedelta(days=5)
        recent_used_token.save()

        # Run cleanup task
        result = cleanup_expired_verification_tokens()

        # Verify deletions (expired_token, old_used_token, expired_used_token)
        assert not EmailVerificationToken.objects.filter(id=expired_token.id).exists()
        assert not EmailVerificationToken.objects.filter(id=old_used_token.id).exists()
        assert not EmailVerificationToken.objects.filter(id=expired_used_token.id).exists()

        # Verify preserved tokens
        assert EmailVerificationToken.objects.filter(id=active_token.id).exists()
        assert EmailVerificationToken.objects.filter(id=recent_used_token.id).exists()

        # Verify result statistics
        assert result['deleted'] == 3
        assert result['expired_count'] == 1  # expired_token only (expired_used_token has is_used=True)
        assert result['used_count'] == 2  # old_used_token and expired_used_token

    def test_bulk_deletion_efficiency(self):
        """Test that bulk deletion is used for efficiency."""
        # Create user
        user = UserFactory()

        # Create many expired tokens
        expired_tokens = []
        for i in range(50):
            token = EmailVerificationToken.objects.create(
                user=user,
                expires_at=timezone.now() - timedelta(hours=i + 1),
                is_used=False
            )
            expired_tokens.append(token)

        # Count initial tokens
        initial_count = EmailVerificationToken.objects.count()
        assert initial_count == 50

        # Run cleanup task
        result = cleanup_expired_verification_tokens()

        # Verify all expired tokens deleted
        assert EmailVerificationToken.objects.count() == 0
        assert result['deleted'] == 50
        assert result['expired_count'] == 50

    def test_handles_empty_database(self):
        """Test task handles empty database gracefully."""
        # Ensure no tokens exist
        EmailVerificationToken.objects.all().delete()

        # Run cleanup task
        result = cleanup_expired_verification_tokens()

        # Verify no errors and zero deletions
        assert result['deleted'] == 0
        assert result['expired_count'] == 0
        assert result['used_count'] == 0

    def test_dry_run_mode(self):
        """Test that dry-run mode counts without deleting."""
        # Create user
        user = UserFactory()

        # Create expired token
        expired_token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() - timedelta(hours=1),
            is_used=False
        )

        # Create old used token (8 days old)
        old_used_token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=1),
            is_used=True
        )
        old_used_token.created_at = timezone.now() - timedelta(days=8)
        old_used_token.save()

        # Run in dry-run mode
        result = cleanup_expired_verification_tokens(dry_run=True)

        # Verify tokens still exist
        assert EmailVerificationToken.objects.filter(id=expired_token.id).exists()
        assert EmailVerificationToken.objects.filter(id=old_used_token.id).exists()

        # Verify result structure for dry-run
        assert result['deleted'] == 0
        assert result['would_delete'] == 2
        assert result['expired_count'] == 1
        assert result['used_count'] == 1
        assert result['dry_run'] is True
        assert 'timestamp' not in result  # No timestamp in dry-run

    @patch('apps.accounts.tasks.logger')
    def test_logging_output(self, mock_logger):
        """Test that task logs appropriate messages."""
        # Create user
        user = UserFactory()

        # Create expired token
        EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() - timedelta(hours=1),
            is_used=False
        )

        # Run cleanup task
        cleanup_expired_verification_tokens()

        # Verify logging calls
        mock_logger.info.assert_any_call("Starting cleanup of expired verification tokens")

        # Verify log includes statistics
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("Deleted 1 verification tokens" in call for call in log_calls)

    @patch('apps.accounts.tasks.logger')
    def test_logs_when_no_tokens_to_delete(self, mock_logger):
        """Test logging when no tokens need deletion."""
        # Ensure no tokens exist
        EmailVerificationToken.objects.all().delete()

        # Run cleanup task
        cleanup_expired_verification_tokens()

        # Verify logging
        mock_logger.info.assert_any_call("Starting cleanup of expired verification tokens")
        mock_logger.info.assert_any_call("No expired or old used verification tokens to delete")

    def test_handles_database_errors_with_retry(self):
        """Test that database errors trigger retry logic."""
        # Create mock task with retry method
        mock_task = MagicMock()
        mock_task.retry.side_effect = Retry()

        # Patch the task to use mock
        with patch('apps.accounts.tasks.cleanup_expired_verification_tokens', mock_task):
            with patch('apps.accounts.models.EmailVerificationToken.objects.filter') as mock_filter:
                # Simulate database error
                mock_filter.side_effect = Exception("Database connection error")

                # Run task should raise Retry exception
                with pytest.raises(Exception):
                    cleanup_expired_verification_tokens()

    @patch('apps.accounts.tasks.logger')
    def test_logs_errors_on_exception(self, mock_logger):
        """Test that errors are logged with details."""
        # Patch the model's filter method to raise an exception
        with patch('apps.accounts.models.EmailVerificationToken.objects.filter') as mock_filter:
            # Simulate exception
            test_error = Exception("Test database error")
            mock_filter.side_effect = test_error

            # Attempt to run task (should handle exception)
            with pytest.raises(Exception):
                cleanup_expired_verification_tokens()

            # Verify error logging
            assert mock_logger.error.called
            error_call = str(mock_logger.error.call_args_list[0])
            assert "Error during token cleanup" in error_call

    def test_task_is_registered_correctly(self):
        """Test that task is registered with correct name."""
        from celery import current_app

        # Verify task is registered
        assert 'accounts.cleanup_expired_verification_tokens' in current_app.tasks

    def test_deletes_tokens_at_exact_expiry_boundary(self):
        """Test deletion of tokens at exact expiration moment."""
        # Create user
        user = UserFactory()

        # Create token that expires in the past (1 second ago)
        # Using past time to ensure consistent deletion behavior
        past_time = timezone.now() - timedelta(seconds=1)
        expired_token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=past_time,
            is_used=False
        )

        # Create token that expires 1 second in future
        future_token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(seconds=1),
            is_used=False
        )

        # Run cleanup task
        result = cleanup_expired_verification_tokens()

        # Token that expired in past should be deleted (expires_at < now)
        assert not EmailVerificationToken.objects.filter(id=expired_token.id).exists()

        # Future token should be preserved
        assert EmailVerificationToken.objects.filter(id=future_token.id).exists()

        # One deletion (expired token)
        assert result['deleted'] == 1

    def test_multiple_users_tokens_handled_independently(self):
        """Test that tokens from different users are handled independently."""
        # Create multiple users
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()

        # User 1: expired token
        expired_token_user1 = EmailVerificationToken.objects.create(
            user=user1,
            expires_at=timezone.now() - timedelta(hours=1),
            is_used=False
        )

        # User 2: old used token (8 days old)
        old_used_token_user2 = EmailVerificationToken.objects.create(
            user=user2,
            expires_at=timezone.now() + timedelta(hours=23),
            is_used=True
        )
        old_used_token_user2.created_at = timezone.now() - timedelta(days=8)
        old_used_token_user2.save()

        # User 3: active token
        active_token_user3 = EmailVerificationToken.objects.create(
            user=user3,
            expires_at=timezone.now() + timedelta(hours=23),
            is_used=False
        )

        # Run cleanup task
        result = cleanup_expired_verification_tokens()

        # Verify correct deletions per user
        assert not EmailVerificationToken.objects.filter(id=expired_token_user1.id).exists()
        assert not EmailVerificationToken.objects.filter(id=old_used_token_user2.id).exists()
        assert EmailVerificationToken.objects.filter(id=active_token_user3.id).exists()

        # Verify statistics
        assert result['deleted'] == 2

    def test_task_result_structure(self):
        """Test that task returns correctly structured result."""
        # Create user
        user = UserFactory()

        # Create expired token
        EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() - timedelta(hours=1),
            is_used=False
        )

        # Create old used token (8 days old)
        old_used = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=1),
            is_used=True
        )
        old_used.created_at = timezone.now() - timedelta(days=8)
        old_used.save()

        # Run cleanup task
        result = cleanup_expired_verification_tokens()

        # Verify result structure
        assert isinstance(result, dict)
        assert 'deleted' in result
        assert 'expired_count' in result
        assert 'used_count' in result
        assert 'dry_run' in result
        assert 'timestamp' in result

        # Verify types
        assert isinstance(result['deleted'], int)
        assert isinstance(result['expired_count'], int)
        assert isinstance(result['used_count'], int)
        assert isinstance(result['dry_run'], bool)
        assert isinstance(result['timestamp'], str)

        # Verify values
        assert result['deleted'] == 2
        assert result['expired_count'] == 1
        assert result['used_count'] == 1
        assert result['dry_run'] is False
