"""
Base Service Class

This module provides a base class for all service layer implementations.
Services encapsulate business logic and provide a clean interface for views.
"""

import logging
from typing import Optional, Dict, Any
from django.db import transaction
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class ServiceException(Exception):
    """Custom exception for service layer errors"""
    def __init__(self, message: str, code: str = 'error', status: int = 400):
        self.message = message
        self.code = code
        self.status = status
        super().__init__(self.message)


class BaseService:
    """
    Base service class providing common functionality

    All service classes should inherit from this class to get:
    - Consistent error handling
    - Transaction management
    - Logging
    - Common utility methods
    """

    def __init__(self, user: Optional[User] = None, organization=None):
        """
        Initialize service with context

        Args:
            user: The user performing the operation (optional)
            organization: The organization context (optional)
        """
        self.user = user
        self.organization = organization
        self.logger = logging.getLogger(self.__class__.__name__)

    @transaction.atomic
    def execute_in_transaction(self, func, *args, **kwargs):
        """
        Execute a function within a database transaction

        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func execution

        Raises:
            ServiceException: If func raises an exception
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Transaction failed: {str(e)}")
            raise ServiceException(
                message=f"Operation failed: {str(e)}",
                code='transaction_error',
                status=500
            )

    def validate_user_authenticated(self):
        """
        Validate that a user is set and authenticated

        Raises:
            ServiceException: If user is not authenticated
        """
        if not self.user or not self.user.is_authenticated:
            raise ServiceException(
                message="Authentication required",
                code='auth_required',
                status=401
            )

    def validate_organization_set(self):
        """
        Validate that an organization context is set

        Raises:
            ServiceException: If organization is not set
        """
        if not self.organization:
            raise ServiceException(
                message="Organization context required",
                code='org_required',
                status=400
            )

    def validate_permission(self, permission_name: str):
        """
        Validate that the user has a specific permission

        Args:
            permission_name: Name of the permission to check

        Raises:
            ServiceException: If user lacks the permission
        """
        self.validate_user_authenticated()

        if not hasattr(self.user, 'profile'):
            raise ServiceException(
                message="User profile not found",
                code='profile_not_found',
                status=403
            )

        if not self.user.profile.has_permission(permission_name):
            raise ServiceException(
                message=f"Permission denied: {permission_name}",
                code='permission_denied',
                status=403
            )

    def validate_role(self, *allowed_roles):
        """
        Validate that the user has one of the allowed roles

        Args:
            *allowed_roles: Variable number of allowed role names

        Raises:
            ServiceException: If user doesn't have any of the allowed roles
        """
        self.validate_user_authenticated()

        if not hasattr(self.user, 'profile'):
            raise ServiceException(
                message="User profile not found",
                code='profile_not_found',
                status=403
            )

        if self.user.profile.role not in allowed_roles:
            raise ServiceException(
                message=f"Required role: {', '.join(allowed_roles)}",
                code='role_required',
                status=403
            )

    def log_action(self, action: str, details: Dict[str, Any] = None):
        """
        Log a service action

        Args:
            action: Description of the action
            details: Additional details to log (optional)
        """
        log_message = f"{action}"
        if self.user:
            log_message = f"[User: {self.user.username}] {log_message}"
        if self.organization:
            log_message = f"[Org: {self.organization.slug}] {log_message}"

        self.logger.info(log_message)

        if details:
            self.logger.debug(f"Details: {details}")

    def success_response(self, data: Any, message: str = "Success") -> Dict[str, Any]:
        """
        Create a success response dict

        Args:
            data: The response data
            message: Success message

        Returns:
            Dict with success response format
        """
        return {
            'success': True,
            'message': message,
            'data': data
        }

    def error_response(self, message: str, code: str = 'error') -> Dict[str, Any]:
        """
        Create an error response dict

        Args:
            message: Error message
            code: Error code

        Returns:
            Dict with error response format
        """
        return {
            'success': False,
            'error': message,
            'code': code
        }
