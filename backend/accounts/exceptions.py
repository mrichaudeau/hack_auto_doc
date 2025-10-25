# -*- coding: utf-8 -*-
"""
Custom exception handlers for authentication and JWT errors.
Provides standardized JSON error responses with clear French messages.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError, AuthenticationFailed
from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides standardized JSON responses
    for JWT and authentication errors with French messages.

    Args:
        exc: The exception instance
        context: Dictionary with 'view' and 'request' keys

    Returns:
        Response object with error details
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # If the default handler didn't handle it, check for JWT exceptions
    if response is None:
        # Handle JWT-specific exceptions that might not be caught by default handler
        if isinstance(exc, (InvalidToken, TokenError)):
            response = Response(
                {
                    'error': 'Token invalide ou expiré.',
                    'code': 'invalid_token',
                    'detail': str(exc)
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        elif isinstance(exc, AuthenticationFailed):
            response = Response(
                {
                    'error': 'Authentification échouée.',
                    'code': 'authentication_failed',
                    'detail': str(exc)
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        elif isinstance(exc, PermissionDenied):
            response = Response(
                {
                    'error': 'Permission refusée.',
                    'code': 'permission_denied',
                    'detail': str(exc)
                },
                status=status.HTTP_403_FORBIDDEN
            )

    # If we still don't have a response, let it propagate
    if response is None:
        return None

    # Enhance response with additional context for JWT errors
    if isinstance(exc, InvalidToken):
        # Check if token is expired
        if 'expired' in str(exc).lower():
            response.data['error'] = 'Token expiré.'
            response.data['code'] = 'token_expired'
            response.data['message'] = 'Votre session a expiré. Veuillez vous reconnecter.'
        # Check if token is invalid/malformed
        elif 'invalid' in str(exc).lower() or 'malformed' in str(exc).lower():
            response.data['error'] = 'Token invalide.'
            response.data['code'] = 'token_invalid'
            response.data['message'] = 'Le token fourni est invalide ou mal formé.'
        # Check if token is blacklisted
        elif 'blacklist' in str(exc).lower():
            response.data['error'] = 'Token révoqué.'
            response.data['code'] = 'token_blacklisted'
            response.data['message'] = 'Ce token a été révoqué. Veuillez vous reconnecter.'

    elif isinstance(exc, AuthenticationFailed):
        # Provide clearer message for authentication failures
        if 'no active account' in str(exc).lower():
            response.data['error'] = 'Compte introuvable ou inactif.'
            response.data['code'] = 'no_active_account'
            response.data['message'] = 'Aucun compte actif trouvé avec ces identifiants.'
        elif 'credentials' in str(exc).lower():
            response.data['error'] = 'Identifiants invalides.'
            response.data['code'] = 'invalid_credentials'
            response.data['message'] = 'Les identifiants fournis sont incorrects.'

    # Log authentication errors for security monitoring
    if response.status_code in [401, 403]:
        view = context.get('view', None)
        request = context.get('request', None)

        log_message = f"Authentication error: {exc.__class__.__name__}"
        if request:
            log_message += f" | IP: {request.META.get('REMOTE_ADDR', 'unknown')}"
            log_message += f" | Path: {request.path}"
            if hasattr(request, 'user') and request.user and not request.user.is_anonymous:
                log_message += f" | User: {request.user.email}"

        logger.warning(log_message)

    return response


def jwt_authentication_failed_handler(exc, context):
    """
    Specialized handler for JWT authentication failures.
    Provides more specific error messages based on the failure type.

    Args:
        exc: The exception instance
        context: Dictionary with 'view' and 'request' keys

    Returns:
        Response object with error details
    """
    error_messages = {
        'token_not_valid': {
            'error': 'Token non valide.',
            'code': 'token_not_valid',
            'message': 'Le token fourni n\'est pas valide. Veuillez vous reconnecter.',
            'status': status.HTTP_401_UNAUTHORIZED
        },
        'user_not_found': {
            'error': 'Utilisateur introuvable.',
            'code': 'user_not_found',
            'message': 'L\'utilisateur associé à ce token n\'existe plus.',
            'status': status.HTTP_401_UNAUTHORIZED
        },
        'user_inactive': {
            'error': 'Compte inactif.',
            'code': 'user_inactive',
            'message': 'Votre compte est inactif. Veuillez vérifier votre email.',
            'status': status.HTTP_403_FORBIDDEN
        },
        'no_authorization_header': {
            'error': 'En-tête d\'autorisation manquant.',
            'code': 'no_authorization_header',
            'message': 'Aucun token d\'authentification fourni.',
            'status': status.HTTP_401_UNAUTHORIZED
        },
        'invalid_authorization_header': {
            'error': 'En-tête d\'autorisation invalide.',
            'code': 'invalid_authorization_header',
            'message': 'Le format de l\'en-tête Authorization est invalide.',
            'status': status.HTTP_401_UNAUTHORIZED
        }
    }

    # Try to extract error code from exception
    error_code = getattr(exc, 'code', None) or 'token_not_valid'
    error_info = error_messages.get(error_code, error_messages['token_not_valid'])

    # Log the authentication failure
    request = context.get('request', None)
    if request:
        logger.warning(
            f"JWT authentication failed: {error_code} | "
            f"IP: {request.META.get('REMOTE_ADDR', 'unknown')} | "
            f"Path: {request.path}"
        )

    return Response(
        {
            'error': error_info['error'],
            'code': error_info['code'],
            'message': error_info['message'],
            'detail': str(exc)
        },
        status=error_info['status']
    )
