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

        # TODO: Send verification email in TASK-1.8
        # send_verification_email.delay(user.id, token.token)

        # Return success response
        user_serializer = UserSerializer(user)
        return Response({
            **user_serializer.data,
            'message': _('Registration successful. Please check your email to verify your account.')
        }, status=status.HTTP_201_CREATED)
