"""
Role-based authentication middleware
Attaches user role to request for easy access throughout the application
"""
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)


class RoleAuthMiddleware(MiddlewareMixin):
    """
    Global middleware to attach user role to request
    Makes role checking available throughout the application
    """

    def process_request(self, request):
        """Attach role to request if user is authenticated"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                # Get or create profile for user
                profile = getattr(request.user, 'profile', None)
                if profile:
                    request.user_role = profile.role
                    request.is_superadmin = profile.is_superadmin()
                    request.is_admin = profile.is_admin()
                    request.is_admin_or_above = profile.is_admin_or_above()
                else:
                    # If profile doesn't exist, create it with default role
                    from api.models import UserProfile
                    profile = UserProfile.objects.create(user=request.user)
                    request.user_role = 'user'
                    request.is_superadmin = False
                    request.is_admin = False
                    request.is_admin_or_above = False
            except Exception as e:
                logger.error(f"Error attaching role to request: {str(e)}")
                request.user_role = None
                request.is_superadmin = False
                request.is_admin = False
                request.is_admin_or_above = False
        else:
            request.user_role = None
            request.is_superadmin = False
            request.is_admin = False
            request.is_admin_or_above = False

        return None

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Check role-based access control before view is executed
        Returns 403 if user doesn't have required role
        """
        # Get the view's required role from view attributes
        required_role = getattr(view_func, 'required_role', None)

        if required_role:
            if not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Authentication required',
                    'detail': 'You must be logged in to access this resource'
                }, status=401)

            user_role = getattr(request, 'user_role', None)

            # Check role hierarchy
            role_hierarchy = {
                'superadmin': 3,
                'admin': 2,
                'user': 1,
            }

            required_level = role_hierarchy.get(required_role, 0)
            user_level = role_hierarchy.get(user_role, 0)

            if user_level < required_level:
                return JsonResponse({
                    'error': 'Insufficient permissions',
                    'detail': f'This resource requires {required_role} role. Your role: {user_role}'
                }, status=403)

        return None


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Log all API requests with user and role information
    """

    def process_request(self, request):
        """Log incoming request"""
        if request.path.startswith('/api/'):
            user = 'Anonymous'
            role = 'None'

            if hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user.username
                role = getattr(request, 'user_role', 'Unknown')

            logger.info(f"{request.method} {request.path} - User: {user} - Role: {role}")

        return None

    def process_response(self, request, response):
        """Log response status"""
        if request.path.startswith('/api/'):
            logger.info(f"Response: {response.status_code} - {request.path}")

        return response
