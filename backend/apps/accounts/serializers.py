"""
Serializers for the accounts app.

Handles serialization and validation for user registration, login, etc.
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import CustomUser, EmailVerificationToken


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Validates email, password, and creates new user accounts.
    Enforces password strength requirements and email uniqueness.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Password must be at least 8 characters with uppercase, lowercase, and number"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Re-enter password for confirmation"
    )

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'password', 'password_confirm', 'first_name', 'last_name')
        read_only_fields = ('id',)
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {
                'required': True,
                'help_text': 'Valid email address required for registration'
            }
        }

    def validate_email(self, value):
        """
        Validate that the email is unique and properly formatted.
        """
        # Convert to lowercase for case-insensitive uniqueness
        value = value.lower()

        # Check if email already exists
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        return value

    def validate_password(self, value):
        """
        Validate password strength using Django's password validators.
        """
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))

        return value

    def validate(self, attrs):
        """
        Validate that passwords match.
        """
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm', None)

        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })

        return attrs

    def create(self, validated_data):
        """
        Create a new user with the validated data.

        The user is created as inactive until email verification is complete.
        Password is hashed using Argon2.
        """
        # Email should already be lowercase from validate_email
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_active=False,  # Account inactive until email verified
            is_verified=False,
        )

        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user details (read-only).

    Used for displaying user information after registration/login.
    """
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'first_name', 'last_name', 'full_name',
                  'is_active', 'is_verified', 'date_joined')
        read_only_fields = fields

    def get_full_name(self, obj):
        """Get the user's full name."""
        return obj.get_full_name()


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification.

    Validates the verification token.
    """
    token = serializers.UUIDField(
        required=True,
        help_text="Email verification token sent to user's email"
    )

    def validate_token(self, value):
        """
        Validate that the token exists and is valid.
        """
        try:
            token_obj = EmailVerificationToken.objects.get(token=value)
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid verification token."
            )

        if token_obj.is_used:
            raise serializers.ValidationError(
                "This verification token has already been used."
            )

        if token_obj.is_expired():
            raise serializers.ValidationError(
                "This verification token has expired. Please request a new one."
            )

        # Store the token object for use in the view
        self.context['token_obj'] = token_obj

        return value


class ResendVerificationEmailSerializer(serializers.Serializer):
    """
    Serializer for resending verification email.

    Validates the email and checks if a new verification email can be sent.
    """
    email = serializers.EmailField(
        required=True,
        help_text="Email address to resend verification email to"
    )

    def validate_email(self, value):
        """
        Validate that the email exists and needs verification.
        """
        value = value.lower()

        try:
            user = CustomUser.objects.get(email=value)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError(
                "No account found with this email address."
            )

        if user.is_verified:
            raise serializers.ValidationError(
                "This email address is already verified."
            )

        # Store the user for use in the view
        self.context['user'] = user

        return value
