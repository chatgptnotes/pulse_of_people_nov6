"""
Tenant Detection Middleware for Multi-Tenancy Support

This middleware detects the organization (tenant) from the URL path and attaches it to the request object.

URL Pattern: /api/org/{org_slug}/...
Example: /api/org/acme-corp/users/

The middleware:
1. Extracts org_slug from the URL path
2. Fetches the Organization from the database
3. Attaches it to request.tenant
4. Handles missing/invalid organizations gracefully
"""

import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from api.models import Organization

logger = logging.getLogger(__name__)


class TenantDetectionMiddleware(MiddlewareMixin):
    """
    Middleware to detect and attach organization (tenant) to request

    This middleware extracts the organization slug from the URL path and
    attaches the corresponding Organization object to the request.

    URL Pattern: /api/org/{org_slug}/...

    If the organization is not found or the URL doesn't contain an org_slug,
    request.tenant will be None.
    """

    def process_request(self, request):
        """Process incoming request to detect tenant"""
        request.tenant = None
        request.org_slug = None

        # Skip tenant detection for certain paths
        skip_paths = [
            '/admin/',
            '/api/auth/',
            '/api/health/',
            '/api/docs/',
            '/api/schema/',
            '/static/',
            '/media/',
        ]

        # Check if path should skip tenant detection
        if any(request.path.startswith(path) for path in skip_paths):
            return None

        # Extract org_slug from path: /api/org/{org_slug}/...
        path_parts = request.path.split('/')

        try:
            # Look for 'org' in path and get the next part as org_slug
            if 'org' in path_parts:
                org_index = path_parts.index('org')
                if len(path_parts) > org_index + 1:
                    org_slug = path_parts[org_index + 1]

                    if org_slug:  # Ensure org_slug is not empty
                        request.org_slug = org_slug

                        try:
                            # Fetch organization from database
                            organization = Organization.objects.get(slug=org_slug)
                            request.tenant = organization

                            logger.debug(f"Tenant detected: {organization.name} (slug: {org_slug})")

                        except Organization.DoesNotExist:
                            logger.warning(f"Organization not found: {org_slug}")
                            # Return 404 for invalid organization
                            return JsonResponse(
                                {
                                    'error': 'Organization not found',
                                    'detail': f'Organization with slug "{org_slug}" does not exist',
                                    'org_slug': org_slug
                                },
                                status=404
                            )

        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing org_slug from path: {e}")

        return None


class TenantRequiredMiddleware(MiddlewareMixin):
    """
    Middleware to enforce tenant requirement for specific endpoints

    This middleware ensures that certain API endpoints MUST have a valid tenant
    attached to the request. If no tenant is found, it returns a 400 Bad Request.

    Use this middleware after TenantDetectionMiddleware in MIDDLEWARE settings.
    """

    def process_request(self, request):
        """Enforce tenant requirement"""

        # Paths that require a tenant
        tenant_required_paths = [
            '/api/org/',  # All org-scoped endpoints
        ]

        # Paths that are exempt from tenant requirement
        exempt_paths = [
            '/admin/',
            '/api/auth/',
            '/api/health/',
            '/api/docs/',
            '/api/schema/',
            '/api/organizations/',  # Organization CRUD doesn't require tenant in path
            '/static/',
            '/media/',
        ]

        # Check if path is exempt
        if any(request.path.startswith(path) for path in exempt_paths):
            return None

        # Check if path requires tenant
        requires_tenant = any(request.path.startswith(path) for path in tenant_required_paths)

        if requires_tenant and not request.tenant:
            logger.warning(f"Tenant required but not found for path: {request.path}")
            return JsonResponse(
                {
                    'error': 'Organization required',
                    'detail': 'This endpoint requires a valid organization in the URL path',
                    'expected_format': '/api/org/{org_slug}/...'
                },
                status=400
            )

        return None


class TenantIsolationMiddleware(MiddlewareMixin):
    """
    Middleware to enforce tenant data isolation

    This middleware adds additional security checks to prevent cross-tenant data access.
    It validates that the authenticated user belongs to the tenant organization.
    """

    def process_request(self, request):
        """Enforce tenant isolation"""

        # Skip for unauthenticated requests
        if not request.user.is_authenticated:
            return None

        # Skip for superadmin users (they can access all tenants)
        if hasattr(request.user, 'profile') and request.user.profile.is_superadmin():
            logger.debug(f"Superadmin access: {request.user.username}")
            return None

        # If tenant is set, verify user belongs to that organization
        if request.tenant:
            if hasattr(request.user, 'profile'):
                user_org = request.user.profile.organization

                if user_org != request.tenant:
                    logger.warning(
                        f"Tenant isolation violation: User {request.user.username} "
                        f"(org: {user_org.slug if user_org else 'None'}) "
                        f"attempted to access {request.tenant.slug}"
                    )
                    return JsonResponse(
                        {
                            'error': 'Access denied',
                            'detail': 'You do not have access to this organization',
                        },
                        status=403
                    )

        return None


class OrganizationContextMiddleware(MiddlewareMixin):
    """
    Middleware to provide organization context utilities

    This middleware adds helper methods to the request object for working with tenants.
    """

    def process_request(self, request):
        """Add organization context utilities to request"""

        # Helper method: Check if user has access to tenant
        def has_tenant_access(organization=None):
            """Check if current user has access to the specified organization"""
            if not request.user.is_authenticated:
                return False

            # Superadmins have access to all organizations
            if hasattr(request.user, 'profile') and request.user.profile.is_superadmin():
                return True

            # Check if user's organization matches the specified organization
            target_org = organization or request.tenant
            if target_org and hasattr(request.user, 'profile'):
                return request.user.profile.organization == target_org

            return False

        # Helper method: Get user's organization
        def get_user_organization():
            """Get the organization of the authenticated user"""
            if request.user.is_authenticated and hasattr(request.user, 'profile'):
                return request.user.profile.organization
            return None

        # Helper method: Check if tenant isolation is active
        def is_tenant_isolated():
            """Check if current request is operating in tenant isolation mode"""
            return request.tenant is not None

        # Attach helper methods to request
        request.has_tenant_access = has_tenant_access
        request.get_user_organization = get_user_organization
        request.is_tenant_isolated = is_tenant_isolated

        return None
