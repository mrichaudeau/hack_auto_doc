# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions
from rest_framework import serializers
from allauth.account.models import EmailAddress

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with email/password.
    Includes password confirmation and email verification trigger.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label="Confirmation du mot de passe"
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'password_confirm')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate_email(self, value):
        """
        Validate email uniqueness (case-insensitive).
        """
        email_lower = value.lower()
        if User.objects.filter(email__iexact=email_lower).exists():
            raise serializers.ValidationError(
                "Un compte avec cette adresse email existe d�j�."
            )
        return email_lower

    def validate(self, attrs):
        """
        Validate password confirmation and password complexity.
        """
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        # Check password confirmation
        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': "Les mots de passe ne correspondent pas."
            })

        # Validate password using Django's password validators
        try:
            validate_password(password)
        except exceptions.ValidationError as e:
            raise serializers.ValidationError({
                'password': list(e.messages)
            })

        return attrs

    def create(self, validated_data):
        """
        Create user with is_active=False and trigger email verification.
        """
        # Remove password_confirm as it's not a model field
        validated_data.pop('password_confirm')

        # Extract password
        password = validated_data.pop('password')

        # Create user with standard auth provider and inactive status
        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=password,
            auth_provider=User.AuthProvider.STANDARD,
            is_active=False
        )

        # Create EmailAddress object for allauth and mark as unverified
        EmailAddress.objects.create(
            user=user,
            email=user.email,
            primary=True,
            verified=False
        )

        # Send verification email (allauth handles this automatically)
        # when EmailAddress is created with verified=False
        EmailAddress.objects.get(user=user).send_confirmation()

        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user data retrieval (excluding sensitive information).
    """
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'auth_provider', 'date_joined')
        read_only_fields = ('id', 'email', 'auth_provider', 'date_joined')
