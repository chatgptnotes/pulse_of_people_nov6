"""
Permission Checking Decorators

This module provides decorators for enforcing permissions and role-based access control
in Django views and DRF viewsets.

Usage:
    # In views:
    @require_permission('users.create')
    def create_user(request):
        # Only users with 'users.create' permission can access
        pass

    @require_role('admin')
    def admin_dashboard(request):
        # Only admins can access
        pass

    @superadmin_required
    def system_settings(request):
        # Only superadmins can access
        pass
"""

from functools import wraps
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


def require_permission(permission_name):
    """
    Decorator to require a specific permission

    Args:
        permission_name: String name of the required permission (e.g., 'users.create')

    Usage:
        @require_permission('users.create')
        def create_user(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                logger.warning(f"Unauthenticated access attempt to {view_func.__name__}")
                return JsonResponse(
                    {'error': 'Authentication required'},
                    status=401
                )

            # Check if user has profile
            if not hasattr(request.user, 'profile'):
                logger.error(f"User {request.user.username} has no profile")
                return JsonResponse(
                    {'error': 'User profile not found'},
                    status=403
                )

            # Check permission
            if not request.user.profile.has_permission(permission_name):
                logger.warning(
                    f"Permission denied: User {request.user.username} "
                    f"lacks permission '{permission_name}'"
                )
                return JsonResponse(
                    {
                        'error': 'Permission denied',
                        'detail': f'You do not have permission: {permission_name}'
                    },
                    status=403
                )

            logger.debug(f"Permission granted: {request.user.username} - {permission_name}")
            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def require_role(*allowed_roles):
    """
    Decorator to require one of the specified roles

    Args:
        *allowed_roles: Variable number of role names

    Usage:
        @require_role('admin', 'manager')
        def admin_dashboard(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                logger.warning(f"Unauthenticated access attempt to {view_func.__name__}")
                return JsonResponse(
                    {'error': 'Authentication required'},
                    status=401
                )

            # Check if user has profile
            if not hasattr(request.user, 'profile'):
                logger.error(f"User {request.user.username} has no profile")
                return JsonResponse(
                    {'error': 'User profile not found'},
                    status=403
                )

            # Check role
            user_role = request.user.profile.role
            if user_role not in allowed_roles:
                logger.warning(
                    f"Role access denied: User {request.user.username} "
                    f"has role '{user_role}', required: {allowed_roles}"
                )
                return JsonResponse(
                    {
                        'error': 'Access denied',
                        'detail': f'Required role: {", ".join(allowed_roles)}'
                    },
                    status=403
                )

            logger.debug(f"Role access granted: {request.user.username} - {user_role}")
            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def superadmin_required(view_func):
    """
    Decorator to require superadmin role

    Usage:
        @superadmin_required
        def system_settings(request):
            pass
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            logger.warning(f"Unauthenticated access attempt to {view_func.__name__}")
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )

        # Check if user has profile
        if not hasattr(request.user, 'profile'):
            logger.error(f"User {request.user.username} has no profile")
            return JsonResponse(
                {'error': 'User profile not found'},
                status=403
            )

        # Check if superadmin
        if not request.user.profile.is_superadmin():
            logger.warning(
                f"Superadmin access denied: User {request.user.username} "
                f"is not a superadmin"
            )
            return JsonResponse(
                {
                    'error': 'Access denied',
                    'detail': 'Superadmin access required'
                },
                status=403
            )

        logger.debug(f"Superadmin access granted: {request.user.username}")
        return view_func(request, *args, **kwargs)

    return wrapper


def admin_required(view_func):
    """
    Decorator to require admin or superadmin role

    Usage:
        @admin_required
        def manage_users(request):
            pass
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            logger.warning(f"Unauthenticated access attempt to {view_func.__name__}")
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )

        # Check if user has profile
        if not hasattr(request.user, 'profile'):
            logger.error(f"User {request.user.username} has no profile")
            return JsonResponse(
                {'error': 'User profile not found'},
                status=403
            )

        # Check if admin or superadmin
        if not request.user.profile.is_admin_or_above():
            logger.warning(
                f"Admin access denied: User {request.user.username} "
                f"does not have admin privileges"
            )
            return JsonResponse(
                {
                    'error': 'Access denied',
                    'detail': 'Admin access required'
                },
                status=403
            )

        logger.debug(f"Admin access granted: {request.user.username}")
        return view_func(request, *args, **kwargs)

    return wrapper


def require_tenant(view_func):
    """
    Decorator to require a valid tenant in the request

    Usage:
        @require_tenant
        def get_organization_data(request):
            # request.tenant is guaranteed to exist
            pass
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if tenant exists in request
        if not hasattr(request, 'tenant') or request.tenant is None:
            logger.warning(f"Tenant required but not found for {view_func.__name__}")
            return JsonResponse(
                {
                    'error': 'Organization required',
                    'detail': 'This endpoint requires a valid organization in the URL',
                    'expected_format': '/api/org/{org_slug}/...'
                },
                status=400
            )

        logger.debug(f"Tenant access: {request.tenant.name}")
        return view_func(request, *args, **kwargs)

    return wrapper


# DRF-specific permission classes
from rest_framework.permissions import BasePermission


class HasPermission(BasePermission):
    """
    DRF permission class to check for specific permission

    Usage:
        class MyViewSet(viewsets.ModelViewSet):
            permission_classes = [HasPermission]
            required_permission = 'users.create'
    """

    def has_permission(self, request, view):
        """Check if user has the required permission"""
        if not request.user or not request.user.is_authenticated:
            return False

        if not hasattr(request.user, 'profile'):
            return False

        # Get required permission from view
        permission_name = getattr(view, 'required_permission', None)
        if not permission_name:
            logger.warning(f"No required_permission set on {view.__class__.__name__}")
            return False

        return request.user.profile.has_permission(permission_name)


class HasRole(BasePermission):
    """
    DRF permission class to check for specific role

    Usage:
        class MyViewSet(viewsets.ModelViewSet):
            permission_classes = [HasRole]
            required_roles = ['admin', 'manager']
    """

    def has_permission(self, request, view):
        """Check if user has one of the required roles"""
        if not request.user or not request.user.is_authenticated:
            return False

        if not hasattr(request.user, 'profile'):
            return False

        # Get required roles from view
        required_roles = getattr(view, 'required_roles', [])
        if not required_roles:
            logger.warning(f"No required_roles set on {view.__class__.__name__}")
            return False

        return request.user.profile.role in required_roles


class IsSuperAdmin(BasePermission):
    """
    DRF permission class to check for superadmin role

    Usage:
        class MyViewSet(viewsets.ModelViewSet):
            permission_classes = [IsSuperAdmin]
    """

    def has_permission(self, request, view):
        """Check if user is superadmin"""
        if not request.user or not request.user.is_authenticated:
            return False

        if not hasattr(request.user, 'profile'):
            return False

        return request.user.profile.is_superadmin()


class IsAdminOrAbove(BasePermission):
    """
    DRF permission class to check for admin or superadmin role

    Usage:
        class MyViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAdminOrAbove]
    """

    def has_permission(self, request, view):
        """Check if user is admin or above"""
        if not request.user or not request.user.is_authenticated:
            return False

        if not hasattr(request.user, 'profile'):
            return False

        return request.user.profile.is_admin_or_above()


class BelongsToTenant(BasePermission):
    """
    DRF permission class to check if user belongs to the request tenant

    Usage:
        class MyViewSet(viewsets.ModelViewSet):
            permission_classes = [BelongsToTenant]
    """

    def has_permission(self, request, view):
        """Check if user belongs to the tenant"""
        if not request.user or not request.user.is_authenticated:
            return False

        if not hasattr(request.user, 'profile'):
            return False

        # Superadmins can access all tenants
        if request.user.profile.is_superadmin():
            return True

        # Check if tenant exists
        if not hasattr(request, 'tenant') or not request.tenant:
            return False

        # Check if user's organization matches tenant
        return request.user.profile.organization == request.tenant
