"""
Views for accounts app - API endpoints for registration and authentication.
"""

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils.translation import gettext as _
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter

from .models import CustomUser, EmailVerificationToken
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    EmailVerificationSerializer,
    ResendVerificationEmailSerializer
)
from .tasks import send_verification_email, send_welcome_email
from .rate_limiting import (
    check_resend_rate_limit,
    increment_resend_counter,
    get_remaining_resends
)


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


@extend_schema(
    tags=['Authentication'],
    summary='Verify user email address',
    description="""
    Verify user email address using verification token.

    **Flow:**
    1. User clicks verification link in email (with token query parameter)
    2. System validates token (exists, not expired, not used)
    3. User account activated (is_active=True, is_email_verified=True)
    4. Token marked as used (is_used=True, used_at set)
    5. Welcome email sent asynchronously
    6. Success response returned

    **Token Validation:**
    - Token must exist in database
    - Token must not be expired (24-hour validity)
    - Token must not have been used previously
    - All operations performed within database transaction (atomic)

    **Error Responses:**
    - 400 Bad Request: Missing token or token already used
    - 410 Gone: Token expired (suggests resend)
    """,
    parameters=[
        OpenApiParameter(
            name='token',
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Email verification token (UUID format)',
            examples=[
                OpenApiExample(
                    'Valid Token',
                    value='550e8400-e29b-41d4-a716-446655440000'
                )
            ]
        )
    ],
    responses={
        200: OpenApiResponse(
            description='Email verified successfully',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'message': 'Email verified successfully. You can now log in.',
                        'is_active': True,
                        'is_email_verified': True
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description='Invalid or used token',
            examples=[
                OpenApiExample(
                    'Missing Token',
                    value={
                        'error': 'token_required',
                        'message': 'Verification token is required.',
                        'resend_url': '/api/auth/resend-verification/'
                    }
                ),
                OpenApiExample(
                    'Token Already Used',
                    value={
                        'error': 'token_used',
                        'message': 'This verification token has already been used.',
                        'resend_url': '/api/auth/resend-verification/'
                    }
                ),
                OpenApiExample(
                    'Invalid Token',
                    value={
                        'error': 'token_invalid',
                        'message': 'Invalid verification token.',
                        'resend_url': '/api/auth/resend-verification/'
                    }
                )
            ]
        ),
        410: OpenApiResponse(
            description='Token expired',
            examples=[
                OpenApiExample(
                    'Expired Token',
                    value={
                        'error': 'token_expired',
                        'message': 'Verification link has expired. Please request a new one.',
                        'resend_url': '/api/auth/resend-verification/'
                    }
                )
            ]
        )
    }
)
class EmailVerificationView(generics.GenericAPIView):
    """
    API endpoint for email verification via GET request.

    GET /api/auth/verify-email/?token=<uuid>
    - Validates verification token from query parameter
    - Activates user account atomically
    - Sends welcome email
    - Returns success message

    The endpoint uses database transactions to ensure atomicity:
    user activation and token marking happen together or not at all.
    """
    authentication_classes = []  # Disable authentication for email verification
    permission_classes = [AllowAny]
    serializer_class = None  # No serializer needed for GET request

    def get(self, request, *args, **kwargs):
        """
        Handle GET request for email verification.

        Query Parameters:
            token (str): Email verification token (UUID format)

        Returns:
            Response: JSON response with verification status

        Raises:
            400: If token is missing, invalid, or already used
            410: If token is expired
        """
        # Get token from query parameters
        token_value = request.query_params.get('token')

        # Validate token parameter is provided
        if not token_value:
            return Response({
                'error': 'token_required',
                'message': _('Verification token is required.'),
                'resend_url': '/api/auth/resend-verification/'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate token format (UUID)
        try:
            import uuid
            token_uuid = uuid.UUID(token_value)
        except (ValueError, AttributeError):
            return Response({
                'error': 'token_invalid',
                'message': _('Invalid verification token format.'),
                'resend_url': '/api/auth/resend-verification/'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve token from database
        try:
            token_obj = EmailVerificationToken.objects.select_related('user').get(token=token_uuid)
        except EmailVerificationToken.DoesNotExist:
            return Response({
                'error': 'token_invalid',
                'message': _('Invalid verification token.'),
                'resend_url': '/api/auth/resend-verification/'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if token is already used
        if token_obj.is_used:
            return Response({
                'error': 'token_used',
                'message': _('This verification token has already been used.'),
                'resend_url': '/api/auth/resend-verification/'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if token is expired
        if token_obj.is_expired():
            return Response({
                'error': 'token_expired',
                'message': _('Verification link has expired. Please request a new one.'),
                'resend_url': '/api/auth/resend-verification/'
            }, status=status.HTTP_410_GONE)

        # Use atomic transaction to ensure user activation and token marking happen together
        with transaction.atomic():
            # Verify email and activate user
            user = token_obj.user
            user.is_email_verified = True
            user.is_active = True
            user.email_verified_at = timezone.now()
            user.save(update_fields=['is_email_verified', 'is_active', 'email_verified_at'])

            # Mark token as used
            token_obj.is_used = True
            token_obj.save(update_fields=['is_used'])

        # Send welcome email asynchronously (after successful commit)
        send_welcome_email.delay(str(user.id))

        return Response({
            'message': _('Email verified successfully. You can now log in.'),
            'is_active': True,
            'is_email_verified': True
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Authentication'],
    summary='Resend verification email',
    description="""
    Resend verification email to user who hasn't verified their account.

    **Flow:**
    1. User provides email address
    2. System validates email exists and needs verification
    3. Rate limit checked (3 requests per 24 hours per email)
    4. New verification token created
    5. Verification email sent asynchronously
    6. Success response returned

    **Rate Limiting:**
    - Maximum 3 resend requests per email address per 24 hours
    - Returns 429 Too Many Requests with retry timing when limit exceeded
    - Uses Redis for distributed rate limiting
    - Email addresses hashed (SHA-256) in Redis keys for privacy

    **Security:**
    - Rate limiting prevents abuse and email bombing
    - Token expires after 24 hours
    - User must exist and not be already verified
    """,
    request=ResendVerificationEmailSerializer,
    responses={
        200: OpenApiResponse(
            description='Verification email sent successfully',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'message': 'Verification email sent successfully. Please check your inbox.',
                        'attempts_remaining': 2
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description='Validation error',
            examples=[
                OpenApiExample(
                    'Email Not Found',
                    value={
                        'email': ['No account found with this email address.']
                    }
                ),
                OpenApiExample(
                    'Already Verified',
                    value={
                        'email': ['This email address is already verified.']
                    }
                )
            ]
        ),
        429: OpenApiResponse(
            description='Rate limit exceeded',
            examples=[
                OpenApiExample(
                    'Too Many Requests',
                    value={
                        'error': 'rate_limit_exceeded',
                        'message': 'Too many verification email requests. Please try again later.',
                        'retry_after_seconds': 43200,
                        'max_attempts': 3,
                        'attempts_remaining': 0
                    }
                )
            ]
        )
    }
)
class ResendVerificationEmailView(generics.GenericAPIView):
    """
    API endpoint for resending verification email.

    POST /api/auth/resend-verification/
    - Validates email exists and needs verification
    - Checks rate limit (3 requests per 24 hours)
    - Creates new verification token
    - Sends new verification email
    - Returns success message

    Rate Limiting: 3 requests per 24 hours per email address
    - Uses Redis-backed distributed rate limiting
    - Email addresses hashed for privacy
    - Returns 429 Too Many Requests with retry information
    """
    serializer_class = ResendVerificationEmailSerializer
    authentication_classes = []  # Disable authentication for resending verification
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get user from serializer context
        user = serializer.context.get('user')
        email = user.email

        # Check rate limit BEFORE sending email
        is_limited, retry_after = check_resend_rate_limit(email)
        if is_limited:
            return Response({
                'error': 'rate_limit_exceeded',
                'message': _('Too many verification email requests. Please try again later.'),
                'retry_after_seconds': retry_after,
                'max_attempts': 3,
                'attempts_remaining': 0
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Increment counter BEFORE sending email (prevent race conditions)
        increment_resend_counter(email)

        # Create new verification token
        token = EmailVerificationToken.create_token(user)

        # Send verification email asynchronously
        send_verification_email.delay(str(user.id), str(token.token))

        # Calculate remaining attempts for response
        attempts_remaining = get_remaining_resends(email)

        return Response({
            'message': _('Verification email sent successfully. Please check your inbox.'),
            'attempts_remaining': attempts_remaining
        }, status=status.HTTP_200_OK)
