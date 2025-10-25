# -*- coding: utf-8 -*-
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import IntegrityError

from .serializers import RegisterSerializer, UserSerializer


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
