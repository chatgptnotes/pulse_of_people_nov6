"""
Supabase JWT Authentication for Django REST Framework
Validates Supabase JWT tokens and syncs with Django User model
"""

import jwt
import requests
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework import authentication, exceptions
from .models import UserProfile

User = get_user_model()


class SupabaseJWTAuthentication(authentication.BaseAuthentication):
    """
    Authenticate requests using Supabase JWT tokens
    """

    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token)
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        try:
            # Decode and verify the Supabase JWT token
            payload = self.verify_supabase_token(token)

            # Get or create Django user from Supabase user data
            user = self.get_or_create_user(payload)

            return (user, token)

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Authentication failed: {str(e)}')

    def verify_supabase_token(self, token):
        """
        Verify the Supabase JWT token using the JWT secret
        """
        supabase_jwt_secret = getattr(settings, 'SUPABASE_JWT_SECRET', None)

        if not supabase_jwt_secret:
            raise exceptions.AuthenticationFailed('Supabase JWT secret not configured')

        try:
            # Decode the JWT token
            payload = jwt.decode(
                token,
                supabase_jwt_secret,
                algorithms=['HS256'],
                audience='authenticated'
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise
        except jwt.InvalidTokenError:
            raise
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Token verification failed: {str(e)}')

    def get_or_create_user(self, payload):
        """
        Get or create Django user from Supabase JWT payload
        """
        supabase_user_id = payload.get('sub')
        email = payload.get('email')

        if not supabase_user_id or not email:
            raise exceptions.AuthenticationFailed('Invalid token payload')

        # Get user metadata from payload
        user_metadata = payload.get('user_metadata', {})
        app_metadata = payload.get('app_metadata', {})

        # Try to find existing user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create new user if doesn't exist
            username = user_metadata.get('username') or email.split('@')[0]

            # Ensure username is unique
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user = User.objects.create(
                username=username,
                email=email,
                first_name=user_metadata.get('first_name', ''),
                last_name=user_metadata.get('last_name', ''),
            )

            # Create user profile with role from Supabase
            role = app_metadata.get('role') or user_metadata.get('role') or 'user'
            UserProfile.objects.create(
                user=user,
                role=role,
                bio=user_metadata.get('bio', ''),
                phone=user_metadata.get('phone', ''),
            )

        # Update user profile if exists
        try:
            profile = user.profile
            # Update role from Supabase if changed
            role = app_metadata.get('role') or user_metadata.get('role')
            if role and profile.role != role:
                profile.role = role
                profile.save()
        except UserProfile.DoesNotExist:
            # Create profile if missing
            role = app_metadata.get('role') or user_metadata.get('role') or 'user'
            UserProfile.objects.create(
                user=user,
                role=role,
            )

        return user

    def authenticate_header(self, request):
        """
        Return WWW-Authenticate header for 401 responses
        """
        return 'Bearer realm="api"'


class HybridAuthentication:
    """
    Try Supabase authentication first, fall back to Django JWT if needed
    This allows both auth methods to work during migration period
    """

    def __init__(self):
        self.supabase_auth = SupabaseJWTAuthentication()

    def authenticate(self, request):
        """
        Try Supabase auth first, then fall back to Django JWT
        """
        # Try Supabase authentication
        try:
            result = self.supabase_auth.authenticate(request)
            if result is not None:
                return result
        except (exceptions.AuthenticationFailed, Exception):
            # If Supabase auth fails, try Django JWT
            pass

        # Fall back to Django JWT
        from rest_framework_simplejwt.authentication import JWTAuthentication
        django_jwt_auth = JWTAuthentication()

        try:
            return django_jwt_auth.authenticate(request)
        except Exception:
            return None

    def authenticate_header(self, request):
        return 'Bearer realm="api"'
