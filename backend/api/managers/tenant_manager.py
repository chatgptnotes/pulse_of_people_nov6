"""
Tenant-Scoped Database Query Manager

This module provides custom QuerySet and Manager classes for automatic tenant filtering.
Models using this manager will automatically filter queries based on the current tenant.

Usage:
    class MyModel(models.Model):
        organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
        # ... other fields ...

        objects = TenantManager()

    # In views/viewsets with tenant in request:
    MyModel.objects.for_tenant(request.tenant).all()
"""

from django.db import models
from django.db.models import Q


class TenantQuerySet(models.QuerySet):
    """
    Custom QuerySet for tenant-scoped queries

    This QuerySet provides methods for filtering data based on the current tenant (organization).
    """

    def for_tenant(self, organization):
        """
        Filter queryset for a specific organization (tenant)

        Args:
            organization: Organization instance to filter by

        Returns:
            QuerySet filtered by organization

        Example:
            Task.objects.for_tenant(request.tenant).all()
        """
        if organization is None:
            # If no organization, return empty queryset
            return self.none()

        return self.filter(organization=organization)

    def for_user(self, user):
        """
        Filter queryset for a specific user's organization

        Args:
            user: User instance to get organization from

        Returns:
            QuerySet filtered by user's organization

        Example:
            Task.objects.for_user(request.user).all()
        """
        if not user.is_authenticated:
            return self.none()

        if hasattr(user, 'profile') and user.profile.organization:
            return self.for_tenant(user.profile.organization)

        return self.none()

    def for_request(self, request):
        """
        Filter queryset based on request tenant or user

        Args:
            request: Django request object with tenant attribute

        Returns:
            QuerySet filtered by request.tenant or request.user's organization

        Example:
            Task.objects.for_request(request).all()
        """
        # First, try to use request.tenant
        if hasattr(request, 'tenant') and request.tenant:
            return self.for_tenant(request.tenant)

        # Fallback to user's organization
        if hasattr(request, 'user'):
            return self.for_user(request.user)

        return self.none()

    def accessible_by(self, user):
        """
        Get all records accessible by a user

        Superadmins can access all records.
        Other users can only access records from their organization.

        Args:
            user: User instance to check access for

        Returns:
            QuerySet of accessible records

        Example:
            Task.objects.accessible_by(request.user).all()
        """
        if not user.is_authenticated:
            return self.none()

        # Superadmins can access all records
        if hasattr(user, 'profile') and user.profile.is_superadmin():
            return self.all()

        # Other users can only access their organization's records
        return self.for_user(user)


class TenantManager(models.Manager):
    """
    Custom Manager for tenant-scoped queries

    This manager uses TenantQuerySet to provide tenant-aware database queries.
    """

    def get_queryset(self):
        """Return TenantQuerySet instead of regular QuerySet"""
        return TenantQuerySet(self.model, using=self._db)

    def for_tenant(self, organization):
        """Filter for a specific organization"""
        return self.get_queryset().for_tenant(organization)

    def for_user(self, user):
        """Filter for a specific user's organization"""
        return self.get_queryset().for_user(user)

    def for_request(self, request):
        """Filter based on request tenant or user"""
        return self.get_queryset().for_request(request)

    def accessible_by(self, user):
        """Get all records accessible by a user"""
        return self.get_queryset().accessible_by(user)


class TenantAwareMixin:
    """
    Mixin to add tenant-aware functionality to models

    Usage:
        class MyModel(TenantAwareMixin, models.Model):
            organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
            # ... other fields ...

    This mixin:
    - Adds TenantManager as the default manager
    - Provides helper methods for tenant operations
    """

    objects = TenantManager()

    class Meta:
        abstract = True

    def is_accessible_by(self, user):
        """
        Check if this instance is accessible by a user

        Args:
            user: User instance to check access for

        Returns:
            bool: True if user can access this instance

        Example:
            if task.is_accessible_by(request.user):
                # User can access this task
        """
        if not user.is_authenticated:
            return False

        # Superadmins can access all records
        if hasattr(user, 'profile') and user.profile.is_superadmin():
            return True

        # Check if user's organization matches this record's organization
        if hasattr(user, 'profile') and hasattr(self, 'organization'):
            return self.organization == user.profile.organization

        return False

    def get_tenant(self):
        """
        Get the organization (tenant) this instance belongs to

        Returns:
            Organization instance or None
        """
        if hasattr(self, 'organization'):
            return self.organization
        return None

    def set_tenant(self, organization):
        """
        Set the organization (tenant) for this instance

        Args:
            organization: Organization instance to set

        Example:
            task.set_tenant(request.tenant)
            task.save()
        """
        if hasattr(self, 'organization'):
            self.organization = organization


# Example usage:
"""
# In models.py:
from api.managers import TenantManager, TenantAwareMixin

class Task(TenantAwareMixin, models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    # ... other fields ...

# In views.py:
from rest_framework import viewsets

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    def get_queryset(self):
        # Automatically filter by tenant
        return Task.objects.for_request(self.request)

    def perform_create(self, serializer):
        # Automatically set tenant on create
        serializer.save(organization=self.request.tenant)

# Or in a view:
def get_user_tasks(request):
    # Get all tasks accessible by the current user
    tasks = Task.objects.accessible_by(request.user)
    return JsonResponse({'tasks': list(tasks.values())})
"""
