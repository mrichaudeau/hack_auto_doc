# -*- coding: utf-8 -*-
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
from allauth.account.utils import perform_login
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
import logging

from .serializers import RegisterSerializer, UserSerializer, LoginSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


# Custom Throttle Classes for Authentication (TASK-2.20)
class AuthThrottle(AnonRateThrottle):
    """Throttle for authentication endpoints (login, register)."""
    scope = 'auth'


class AuthBurstThrottle(AnonRateThrottle):
    """Strict burst protection for authentication endpoints."""
    scope = 'auth_burst'


class RegisterView(APIView):
    """
    API endpoint for user registration.

    POST /api/auth/register/
    - Creates a new user account with email/password
    - Sets user as inactive (is_active=False) until email verification
    - Sends verification email automatically
    - Returns 201 with success message (no JWT until verified)
    """
    permission_classes = [AllowAny]
    throttle_classes = [AuthThrottle, AuthBurstThrottle]  # Rate limiting

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        try:
            if serializer.is_valid():
                user = serializer.save()

                return Response(
                    {
                        'message': 'Inscription réussie ! Un email de vérification a été envoyé à votre adresse.',
                        'email': user.email
                    },
                    status=status.HTTP_201_CREATED
                )

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        except IntegrityError:
            return Response(
                {'email': 'Un compte avec cette adresse email existe déjà.'},
                status=status.HTTP_409_CONFLICT
            )


class VerifyEmailView(APIView):
    """
    API endpoint for email verification.

    GET/POST /api/auth/verify-email/<key>/
    - Verifies the email confirmation token
    - Activates the user account (is_active=True)
    - Returns 200 with success message
    - Returns 400 if token is invalid or expired
    """
    permission_classes = [AllowAny]

    def get(self, request, key):
        return self._verify_email(key, request)

    def post(self, request, key):
        return self._verify_email(key, request)

    def _verify_email(self, key, request=None):
        """
        Internal method to verify email with the provided key.
        """
        try:
            # Try to get the confirmation object from database first
            emailconfirmation = EmailConfirmation.objects.filter(
                key=key.lower()
            ).select_related('email_address').first()

            if not emailconfirmation:
                # Try HMAC-based confirmation (newer allauth versions)
                try:
                    emailconfirmation = EmailConfirmationHMAC.from_key(key)
                    if not emailconfirmation:
                        return Response(
                            {
                                'error': 'Token de vérification invalide ou expiré.',
                                'code': 'invalid_token'
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except Exception as e:
                    return Response(
                        {
                            'error': 'Token de vérification invalide ou expiré.',
                            'code': 'invalid_token',
                            'detail': str(e)
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Check if email is already verified
            if emailconfirmation.email_address.verified:
                return Response(
                    {
                        'message': 'Votre adresse email a déjà été vérifiée.',
                        'already_verified': True
                    },
                    status=status.HTTP_200_OK
                )

            # Confirm the email
            email_address = emailconfirmation.confirm(request)

            if email_address:
                # Activate the user account
                user = email_address.user
                user.is_active = True
                user.save()

                return Response(
                    {
                        'message': 'Votre adresse email a été vérifiée avec succès ! Vous pouvez maintenant vous connecter.',
                        'email': user.email,
                        'verified': True
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        'error': 'Une erreur est survenue lors de la vérification.',
                        'code': 'verification_failed'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {
                    'error': 'Token de vérification invalide ou expiré.',
                    'code': 'invalid_token',
                    'detail': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class ResendVerificationEmailView(APIView):
    """
    API endpoint to resend verification email.

    POST /api/auth/resend-verification/
    - Resends verification email to the provided email address
    - Returns 200 with success message
    - Returns 400 if email is already verified or doesn't exist
    """
    permission_classes = [AllowAny]
    throttle_classes = [AuthThrottle]  # Rate limiting (no burst for resend)

    def post(self, request):
        email = request.data.get('email', '').lower()

        if not email:
            return Response(
                {'email': 'L\'adresse email est requise.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email__iexact=email)

            # Check if user is already active
            if user.is_active:
                return Response(
                    {'message': 'Ce compte est déjà vérifié.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get or create EmailAddress object
            from allauth.account.models import EmailAddress
            email_address = EmailAddress.objects.filter(
                user=user,
                email__iexact=email
            ).first()

            if email_address:
                if email_address.verified:
                    return Response(
                        {'message': 'Cette adresse email est déjà vérifiée.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Send new confirmation email
                email_address.send_confirmation(request)

                return Response(
                    {
                        'message': 'Un nouvel email de vérification a été envoyé.',
                        'email': email
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Aucun compte trouvé pour cette adresse email.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except User.DoesNotExist:
            # For security, return success even if user doesn't exist
            # to prevent email enumeration
            return Response(
                {
                    'message': 'Si cette adresse email existe dans notre système, un email de vérification a été envoyé.',
                    'email': email
                },
                status=status.HTTP_200_OK
            )


class LoginView(APIView):
    """
    API endpoint for user login with JWT token generation.

    POST /api/auth/login/
    - Validates email/password credentials
    - Returns JWT access and refresh tokens
    - Returns user data
    - Logs all login attempts for security audit
    """
    permission_classes = [AllowAny]
    throttle_classes = [AuthThrottle, AuthBurstThrottle]  # Rate limiting

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Prepare user data
            user_data = UserSerializer(user).data

            # Log successful login
            logger.info(
                f"Login successful - Email: {user.email}, "
                f"IP: {request.META.get('REMOTE_ADDR', 'unknown')}"
            )

            return Response(
                {
                    'message': 'Connexion réussie.',
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user': user_data
                },
                status=status.HTTP_200_OK
            )

        # Log failed login attempt
        email = request.data.get('email', 'unknown')
        logger.warning(
            f"Login failed - Email: {email}, "
            f"IP: {request.META.get('REMOTE_ADDR', 'unknown')}, "
            f"Errors: {serializer.errors}"
        )

        return Response(
            serializer.errors,
            status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    """
    API endpoint for user logout with token blacklisting.

    POST /api/auth/logout/
    - Requires authentication (valid JWT access token)
    - Blacklists the provided refresh token
    - Returns 204 No Content on success
    - Returns 400 if refresh token is invalid or missing
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh_token')

        if not refresh_token:
            return Response(
                {'refresh_token': 'Le refresh token est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Log successful logout
            logger.info(
                f"Logout successful - User: {request.user.email}, "
                f"IP: {request.META.get('REMOTE_ADDR', 'unknown')}"
            )

            return Response(
                {'message': 'Déconnexion réussie.'},
                status=status.HTTP_204_NO_CONTENT
            )

        except TokenError as e:
            logger.warning(
                f"Logout failed - User: {request.user.email}, "
                f"IP: {request.META.get('REMOTE_ADDR', 'unknown')}, "
                f"Error: {str(e)}"
            )
            return Response(
                {'refresh_token': 'Token invalide ou déjà blacklisté.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserDetailView(APIView):
    """
    API endpoint to retrieve current authenticated user's data.

    GET /api/users/me/
    - Requires authentication (valid JWT access token)
    - Returns current user's profile data
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
