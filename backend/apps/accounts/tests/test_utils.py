"""
Unit tests for accounts utility functions.

This module tests the utility functions in accounts.utils, particularly
focusing on the security properties of token generation.
"""

import re
from unittest import TestCase

from apps.accounts.utils import generate_verification_token


class GenerateVerificationTokenTestCase(TestCase):
    """Test cases for the generate_verification_token function."""

    def test_token_length(self):
        """
        Test that generated tokens have the expected length.

        secrets.token_urlsafe(32) should generate 43 characters
        (32 bytes * 4/3 base64 encoding ≈ 42.67, rounded to 43).
        """
        token = generate_verification_token()
        self.assertEqual(
            len(token),
            43,
            f"Token length should be 43 characters, got {len(token)}"
        )

    def test_token_is_string(self):
        """Test that the generated token is a string."""
        token = generate_verification_token()
        self.assertIsInstance(
            token,
            str,
            f"Token should be a string, got {type(token)}"
        )

    def test_token_url_safe_characters(self):
        """
        Test that tokens contain only URL-safe characters.

        URL-safe base64 encoding uses: [A-Za-z0-9_-]
        No special characters that require URL encoding.
        """
        token = generate_verification_token()
        url_safe_pattern = r'^[A-Za-z0-9_-]+$'

        self.assertTrue(
            re.match(url_safe_pattern, token),
            f"Token '{token}' contains non-URL-safe characters. "
            f"Expected only [A-Za-z0-9_-]"
        )

    def test_token_no_padding(self):
        """
        Test that tokens don't contain base64 padding characters.

        token_urlsafe() should not include '=' padding.
        """
        token = generate_verification_token()
        self.assertNotIn(
            '=',
            token,
            f"Token should not contain base64 padding '=' character"
        )

    def test_token_uniqueness_small_sample(self):
        """
        Test that generated tokens are unique in a small sample.

        Generate 100 tokens and verify all are unique.
        """
        num_tokens = 100
        tokens = [generate_verification_token() for _ in range(num_tokens)]

        unique_tokens = set(tokens)

        self.assertEqual(
            len(unique_tokens),
            num_tokens,
            f"Expected {num_tokens} unique tokens, got {len(unique_tokens)}. "
            f"Collision detected in small sample!"
        )

    def test_token_uniqueness_large_sample(self):
        """
        Test that generated tokens are unique in a larger sample.

        Generate 1000 tokens and verify all are unique.
        This provides stronger evidence of proper entropy.
        """
        num_tokens = 1000
        tokens = [generate_verification_token() for _ in range(num_tokens)]

        unique_tokens = set(tokens)

        self.assertEqual(
            len(unique_tokens),
            num_tokens,
            f"Expected {num_tokens} unique tokens, got {len(unique_tokens)}. "
            f"Collision detected! This suggests insufficient entropy."
        )

    def test_token_randomness(self):
        """
        Test that consecutive tokens are different.

        Generate two tokens immediately after each other and verify
        they are not identical (basic randomness check).
        """
        token1 = generate_verification_token()
        token2 = generate_verification_token()

        self.assertNotEqual(
            token1,
            token2,
            "Consecutive tokens should be different"
        )

    def test_token_entropy(self):
        """
        Test that tokens have sufficient character variety.

        A good token should contain a mix of different characters,
        not just repetitions of a few characters.
        """
        token = generate_verification_token()
        unique_chars = len(set(token))

        # With 43 characters and base64url alphabet (64 chars),
        # we expect at least 20 unique characters in a random token
        min_unique_chars = 20

        self.assertGreaterEqual(
            unique_chars,
            min_unique_chars,
            f"Token should have at least {min_unique_chars} unique characters "
            f"for good entropy, got {unique_chars}"
        )

    def test_token_character_distribution(self):
        """
        Test that tokens use characters from different categories.

        A secure token should include uppercase, lowercase, and
        digits/special chars (not just one category).
        """
        token = generate_verification_token()

        has_uppercase = any(c.isupper() for c in token)
        has_lowercase = any(c.islower() for c in token)
        has_digit_or_special = any(c.isdigit() or c in '_-' for c in token)

        # Most tokens should have at least 2 of the 3 categories
        categories_present = sum([has_uppercase, has_lowercase, has_digit_or_special])

        self.assertGreaterEqual(
            categories_present,
            2,
            f"Token should use characters from multiple categories "
            f"(uppercase, lowercase, digits/special). Got {categories_present}/3"
        )

    def test_token_no_whitespace(self):
        """Test that tokens don't contain whitespace characters."""
        token = generate_verification_token()

        self.assertFalse(
            any(c.isspace() for c in token),
            "Token should not contain any whitespace characters"
        )

    def test_token_determinism(self):
        """
        Test that the function is non-deterministic.

        Verify that multiple calls don't produce the same sequence
        (not seeded with a fixed value).
        """
        # Generate two sets of tokens
        set1 = [generate_verification_token() for _ in range(10)]
        set2 = [generate_verification_token() for _ in range(10)]

        # The sets should not be identical (would indicate fixed seed)
        self.assertNotEqual(
            set1,
            set2,
            "Multiple token generation runs should produce different sequences"
        )

    def test_token_suitable_for_urls(self):
        """
        Test that tokens can be safely used in URLs without encoding.

        Verify that the token doesn't require URL encoding by checking
        it doesn't contain characters that need escaping.
        """
        token = generate_verification_token()

        # Characters that would require URL encoding
        forbidden_chars = ['/', '?', '#', '&', '=', '+', ' ', '%']

        for char in forbidden_chars:
            self.assertNotIn(
                char,
                token,
                f"Token should not contain '{char}' which requires URL encoding"
            )

    def test_multiple_tokens_batch(self):
        """
        Test generating a batch of tokens for practical usage scenario.

        Simulate generating tokens for multiple users simultaneously
        and verify they're all unique.
        """
        # Simulate 50 concurrent user registrations
        batch_size = 50
        tokens = [generate_verification_token() for _ in range(batch_size)]

        self.assertEqual(
            len(set(tokens)),
            batch_size,
            f"All {batch_size} tokens in batch should be unique"
        )

        # Verify each token meets basic requirements
        for i, token in enumerate(tokens):
            with self.subTest(token_index=i):
                self.assertEqual(len(token), 43)
                self.assertTrue(re.match(r'^[A-Za-z0-9_-]+$', token))
