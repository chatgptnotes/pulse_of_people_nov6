"""
Organization Service

This module handles all organization-related business logic including:
- Organization creation
- Organization settings management
- Member management
- Subscription management
"""

from typing import Dict, Any, Optional
from django.db import transaction
from django.utils.text import slugify
from api.models import Organization, UserProfile
from .base_service import BaseService, ServiceException
from .audit_service import AuditService


class OrganizationService(BaseService):
    """Service class for organization-related operations"""

    @transaction.atomic
    def create_organization(
        self,
        name: str,
        slug: Optional[str] = None,
        subscription_tier: str = 'basic',
        max_users: int = 10,
        **settings_data
    ) -> Organization:
        """
        Create a new organization

        Args:
            name: Organization name
            slug: URL-friendly slug (auto-generated if not provided)
            subscription_tier: Subscription tier (default: 'basic')
            max_users: Maximum number of users allowed (default: 10)
            **settings_data: Additional settings

        Returns:
            Created Organization instance

        Raises:
            ServiceException: If creation fails
        """
        try:
            # Auto-generate slug if not provided
            if not slug:
                slug = slugify(name)

            # Check if slug already exists
            if Organization.objects.filter(slug=slug).exists():
                raise ServiceException(
                    message=f"Organization with slug '{slug}' already exists",
                    code='slug_exists',
                    status=400
                )

            # Create organization
            organization = Organization.objects.create(
                name=name,
                slug=slug,
                subscription_tier=subscription_tier,
                max_users=max_users,
                settings=settings_data
            )

            self.log_action(
                f"Created organization: {name}",
                {'slug': slug, 'tier': subscription_tier}
            )

            # Create audit log
            if self.user:
                AuditService.log_user_action(
                    user=self.user,
                    action='create',
                    target_model='Organization',
                    target_id=str(organization.id),
                    changes={'name': name, 'slug': slug}
                )

            return organization

        except ServiceException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create organization: {str(e)}")
            raise ServiceException(
                message=f"Failed to create organization: {str(e)}",
                code='org_creation_failed',
                status=500
            )

    def update_organization_settings(
        self,
        organization: Organization,
        **settings
    ) -> Organization:
        """
        Update organization settings

        Args:
            organization: Organization to update
            **settings: Settings to update

        Returns:
            Updated Organization instance

        Raises:
            ServiceException: If update fails
        """
        try:
            # Update settings
            organization.settings.update(settings)
            organization.save()

            self.log_action(
                f"Updated settings for organization: {organization.name}",
                {'settings': settings}
            )

            # Create audit log
            if self.user:
                AuditService.log_user_action(
                    user=self.user,
                    action='update',
                    target_model='Organization',
                    target_id=str(organization.id),
                    changes={'settings': settings}
                )

            return organization

        except Exception as e:
            self.logger.error(f"Failed to update organization settings: {str(e)}")
            raise ServiceException(
                message=f"Failed to update settings: {str(e)}",
                code='settings_update_failed',
                status=500
            )

    def get_organization_members(
        self,
        organization: Organization
    ) -> list:
        """
        Get all members of an organization

        Args:
            organization: Organization to get members for

        Returns:
            List of UserProfile instances

        Raises:
            ServiceException: If operation fails
        """
        try:
            members = UserProfile.objects.filter(organization=organization).select_related('user')

            self.log_action(
                f"Retrieved members for organization: {organization.name}",
                {'member_count': members.count()}
            )

            return list(members)

        except Exception as e:
            self.logger.error(f"Failed to get organization members: {str(e)}")
            raise ServiceException(
                message=f"Failed to get members: {str(e)}",
                code='member_retrieval_failed',
                status=500
            )

    def check_member_limit(
        self,
        organization: Organization
    ) -> Dict[str, Any]:
        """
        Check if organization has reached member limit

        Args:
            organization: Organization to check

        Returns:
            Dict with limit info

        Raises:
            ServiceException: If operation fails
        """
        try:
            current_count = UserProfile.objects.filter(organization=organization).count()
            max_users = organization.max_users

            return {
                'current_count': current_count,
                'max_users': max_users,
                'can_add_more': current_count < max_users,
                'available_slots': max(0, max_users - current_count)
            }

        except Exception as e:
            self.logger.error(f"Failed to check member limit: {str(e)}")
            raise ServiceException(
                message=f"Failed to check limit: {str(e)}",
                code='limit_check_failed',
                status=500
            )
