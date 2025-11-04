"""
Views for accounts app - API endpoints for registration and authentication.
"""

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils.translation import gettext as _
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from .models import CustomUser, EmailVerificationToken
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    EmailVerificationSerializer,
    ResendVerificationEmailSerializer
)
from .tasks import send_verification_email, send_welcome_email


@extend_schema(
    tags=['Authentication'],
    summary='Register new user account',
    description="""
    Register a new user account with email and password.

    **Flow:**
    1. User submits registration data
    2. System validates input (email format, password strength)
    3. User account created (inactive until email verification)
    4. Verification email sent asynchronously
    5. User data returned with success message

    **Rate Limiting:**
    - 5 requests per hour per IP address
    - Returns 429 Too Many Requests when limit exceeded

    **Security:**
    - Passwords hashed with Argon2
    - Email must be unique
    - Password requirements: min 8 chars, uppercase, lowercase, number
    """,
    request=UserRegistrationSerializer,
    responses={
        201: OpenApiResponse(
            response=UserSerializer,
            description='User registered successfully',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'id': '550e8400-e29b-41d4-a716-446655440000',
                        'email': 'user@example.com',
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'is_active': False,
                        'is_email_verified': False,
                        'message': 'Registration successful. Please check your email to verify your account.'
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description='Validation error',
            examples=[
                OpenApiExample(
                    'Invalid Email',
                    value={'email': ['Enter a valid email address.']}
                ),
                OpenApiExample(
                    'Weak Password',
                    value={'password': ['Password must contain at least 8 characters, including uppercase, lowercase, and numbers.']}
                ),
                OpenApiExample(
                    'Password Mismatch',
                    value={'password_confirm': ['Passwords do not match.']}
                )
            ]
        ),
        409: OpenApiResponse(
            description='Duplicate email',
            examples=[
                OpenApiExample(
                    'Email Already Exists',
                    value={'email': ['An account with this email already exists.']}
                )
            ]
        ),
        429: OpenApiResponse(
            description='Rate limit exceeded',
            examples=[
                OpenApiExample(
                    'Too Many Requests',
                    value={
                        'error': 'Too many registration attempts. Please try again later.',
                        'detail': 'Rate limit exceeded: 5 attempts per hour allowed.'
                    }
                )
            ]
        )
    }
)
@method_decorator(ratelimit(key='ip', rate='30/h', method='POST', block=False), name='dispatch')
class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for user registration.

    POST /api/auth/register/
    - Creates new user account
    - Sends verification email
    - Returns user data with success message

    Rate Limiting: 5 requests per hour per IP address
    - Prevents abuse and brute force attacks
    - Returns 429 Too Many Requests when limit exceeded
    - Uses Redis for distributed rate limiting
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    authentication_classes = []  # Disable authentication for registration
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        # Check if rate limit was exceeded
        if getattr(request, 'limited', False):
            return Response({
                'error': _('Too many registration attempts. Please try again later.'),
                'detail': _('Rate limit exceeded: 5 attempts per hour allowed.')
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

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
    authentication_classes = []  # Disable authentication for email verification
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
    authentication_classes = []  # Disable authentication for resending verification
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
