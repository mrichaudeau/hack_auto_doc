# -*- coding: utf-8 -*-
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
from allauth.account.utils import perform_login
from django.contrib.auth import get_user_model

from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


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
