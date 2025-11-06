"""
User Service

This module handles all user-related business logic including:
- User registration
- Profile management
- Role assignment
- Permission management
"""

from typing import Dict, Any, Optional
from django.contrib.auth.models import User
from django.db import transaction
from api.models import UserProfile, Organization, Permission
from .base_service import BaseService, ServiceException
from .audit_service import AuditService


class UserService(BaseService):
    """Service class for user-related operations"""

    @transaction.atomic
    def create_user_with_profile(
        self,
        username: str,
        email: str,
        password: str,
        organization: Organization,
        role: str = 'user',
        **profile_data
    ) -> User:
        """
        Create a new user with profile

        Args:
            username: Username for the new user
            email: Email address
            password: User password
            organization: Organization to assign user to
            role: User role (default: 'user')
            **profile_data: Additional profile fields

        Returns:
            Created User instance

        Raises:
            ServiceException: If user creation fails
        """
        try:
            # Validate organization
            if not organization:
                raise ServiceException(
                    message="Organization is required",
                    code='org_required'
                )

            # Check if username already exists
            if User.objects.filter(username=username).exists():
                raise ServiceException(
                    message=f"Username '{username}' already exists",
                    code='username_exists',
                    status=400
                )

            # Check if email already exists
            if User.objects.filter(email=email).exists():
                raise ServiceException(
                    message=f"Email '{email}' already exists",
                    code='email_exists',
                    status=400
                )

            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            # Create profile
            profile = UserProfile.objects.create(
                user=user,
                organization=organization,
                role=role,
                **profile_data
            )

            self.log_action(
                f"Created user: {username}",
                {'user_id': user.id, 'organization': organization.slug, 'role': role}
            )

            # Create audit log
            AuditService.log_user_action(
                user=self.user if self.user else user,
                action='create',
                target_model='User',
                target_id=str(user.id),
                changes={'username': username, 'email': email, 'role': role}
            )

            return user

        except ServiceException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create user: {str(e)}")
            raise ServiceException(
                message=f"Failed to create user: {str(e)}",
                code='user_creation_failed',
                status=500
            )

    def update_user_profile(
        self,
        user: User,
        **update_data
    ) -> UserProfile:
        """
        Update user profile

        Args:
            user: User to update
            **update_data: Fields to update

        Returns:
            Updated UserProfile instance

        Raises:
            ServiceException: If update fails
        """
        try:
            if not hasattr(user, 'profile'):
                raise ServiceException(
                    message="User profile not found",
                    code='profile_not_found',
                    status=404
                )

            profile = user.profile

            # Track changes for audit log
            changes = {}

            # Update profile fields
            for field, value in update_data.items():
                if hasattr(profile, field):
                    old_value = getattr(profile, field)
                    setattr(profile, field, value)
                    changes[field] = {'old': str(old_value), 'new': str(value)}

            profile.save()

            self.log_action(
                f"Updated profile for user: {user.username}",
                {'changes': changes}
            )

            # Create audit log
            if self.user:
                AuditService.log_user_action(
                    user=self.user,
                    action='update',
                    target_model='UserProfile',
                    target_id=str(profile.id),
                    changes=changes
                )

            return profile

        except ServiceException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update profile: {str(e)}")
            raise ServiceException(
                message=f"Failed to update profile: {str(e)}",
                code='profile_update_failed',
                status=500
            )

    def assign_role(
        self,
        user: User,
        role: str
    ) -> UserProfile:
        """
        Assign a role to a user

        Args:
            user: User to assign role to
            role: Role name

        Returns:
            Updated UserProfile

        Raises:
            ServiceException: If role assignment fails
        """
        # Validate permission
        self.validate_permission('users.manage_roles')

        try:
            if not hasattr(user, 'profile'):
                raise ServiceException(
                    message="User profile not found",
                    code='profile_not_found',
                    status=404
                )

            # Validate role
            valid_roles = [choice[0] for choice in UserProfile.ROLE_CHOICES]
            if role not in valid_roles:
                raise ServiceException(
                    message=f"Invalid role: {role}",
                    code='invalid_role',
                    status=400
                )

            profile = user.profile
            old_role = profile.role
            profile.role = role
            profile.save()

            self.log_action(
                f"Assigned role to user: {user.username}",
                {'old_role': old_role, 'new_role': role}
            )

            # Create audit log
            AuditService.log_user_action(
                user=self.user,
                action='role_change',
                target_model='UserProfile',
                target_id=str(profile.id),
                changes={'role': {'old': old_role, 'new': role}}
            )

            return profile

        except ServiceException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to assign role: {str(e)}")
            raise ServiceException(
                message=f"Failed to assign role: {str(e)}",
                code='role_assignment_failed',
                status=500
            )

    def get_user_permissions(self, user: User) -> list:
        """
        Get all permissions for a user

        Args:
            user: User to get permissions for

        Returns:
            List of permission names

        Raises:
            ServiceException: If operation fails
        """
        try:
            if not hasattr(user, 'profile'):
                raise ServiceException(
                    message="User profile not found",
                    code='profile_not_found',
                    status=404
                )

            permissions = user.profile.get_permissions()

            self.log_action(
                f"Retrieved permissions for user: {user.username}",
                {'permission_count': len(permissions)}
            )

            return permissions

        except ServiceException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get permissions: {str(e)}")
            raise ServiceException(
                message=f"Failed to get permissions: {str(e)}",
                code='permission_retrieval_failed',
                status=500
            )

    def assign_user_to_organization(
        self,
        user: User,
        organization: Organization
    ) -> UserProfile:
        """
        Assign a user to an organization

        Args:
            user: User to assign
            organization: Organization to assign to

        Returns:
            Updated UserProfile

        Raises:
            ServiceException: If assignment fails
        """
        # Validate permission
        self.validate_permission('users.manage_organization')

        try:
            if not hasattr(user, 'profile'):
                raise ServiceException(
                    message="User profile not found",
                    code='profile_not_found',
                    status=404
                )

            profile = user.profile
            old_org = profile.organization
            profile.organization = organization
            profile.save()

            self.log_action(
                f"Assigned user to organization: {user.username}",
                {
                    'old_org': old_org.slug if old_org else None,
                    'new_org': organization.slug
                }
            )

            # Create audit log
            AuditService.log_user_action(
                user=self.user,
                action='update',
                target_model='UserProfile',
                target_id=str(profile.id),
                changes={
                    'organization': {
                        'old': old_org.slug if old_org else None,
                        'new': organization.slug
                    }
                }
            )

            return profile

        except ServiceException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to assign organization: {str(e)}")
            raise ServiceException(
                message=f"Failed to assign organization: {str(e)}",
                code='org_assignment_failed',
                status=500
            )
