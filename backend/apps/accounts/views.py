"""
Views for accounts app - API endpoints for registration and authentication.
"""

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils.translation import gettext as _

from .models import CustomUser, EmailVerificationToken
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    EmailVerificationSerializer,
    ResendVerificationEmailSerializer
)
from .tasks import send_verification_email, send_welcome_email


class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for user registration.

    POST /api/auth/register/
    - Creates new user account
    - Sends verification email
    - Returns user data with success message
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create user (inactive until email verification)
        user = serializer.save()

        # Create verification token
        token = EmailVerificationToken.create_token(user)

        # Send verification email asynchronously via Celery
        send_verification_email.delay(str(user.id), str(token.token))

        # Return success response
        user_serializer = UserSerializer(user)
        return Response({
            **user_serializer.data,
            'message': _('Registration successful. Please check your email to verify your account.')
        }, status=status.HTTP_201_CREATED)


class EmailVerificationView(generics.GenericAPIView):
    """
    API endpoint for email verification.

    POST /api/auth/verify-email/
    - Validates verification token
    - Activates user account
    - Sends welcome email
    - Returns success message
    """
    serializer_class = EmailVerificationSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get token object from serializer context
        token_obj = serializer.context.get('token_obj')

        # Verify email and activate user
        user = token_obj.user
        user.verify_email()

        # Mark token as used
        token_obj.is_used = True
        token_obj.save(update_fields=['is_used'])

        # Send welcome email asynchronously
        send_welcome_email.delay(str(user.id))

        return Response({
            'message': _('Email verified successfully. You can now log in.')
        }, status=status.HTTP_200_OK)


class ResendVerificationEmailView(generics.GenericAPIView):
    """
    API endpoint for resending verification email.

    POST /api/auth/resend-verification/
    - Validates email exists and needs verification
    - Creates new verification token
    - Sends new verification email
    - Returns success message
    """
    serializer_class = ResendVerificationEmailSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get user from serializer context
        user = serializer.context.get('user')

        # Create new verification token
        token = EmailVerificationToken.create_token(user)

        # Send verification email asynchronously
        send_verification_email.delay(str(user.id), str(token.token))

        return Response({
            'message': _('Verification email sent successfully. Please check your inbox.')
        }, status=status.HTTP_200_OK)
