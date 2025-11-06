"""
WebSocket JWT Authentication Middleware
Handles JWT token verification for WebSocket connections
"""

import logging
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser, User
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user_from_token(token_string):
    """Get user from JWT token"""
    try:
        # Decode and verify the token
        access_token = AccessToken(token_string)
        user_id = access_token['user_id']

        # Get user from database
        user = User.objects.get(id=user_id)
        return user

    except (TokenError, InvalidToken) as e:
        logger.warning(f"Invalid token: {str(e)}")
        return AnonymousUser()
    except User.DoesNotExist:
        logger.warning(f"User not found for token")
        return AnonymousUser()
    except Exception as e:
        logger.error(f"Error getting user from token: {str(e)}")
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware for JWT authentication in WebSocket connections

    Extracts JWT token from query parameters and authenticates the user
    Usage: ws://localhost:8080/ws/transcribe/?token=YOUR_JWT_TOKEN
    """

    async def __call__(self, scope, receive, send):
        # Get query parameters
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)

        # Extract token from query parameters
        token = query_params.get('token', [None])[0]

        if token:
            # Get user from token
            scope['user'] = await get_user_from_token(token)
        else:
            # No token provided
            scope['user'] = AnonymousUser()

        logger.info(f"WebSocket connection - User: {scope['user']}")

        return await super().__call__(scope, receive, send)
