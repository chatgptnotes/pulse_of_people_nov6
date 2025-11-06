"""
Notification Service

This module handles all notification-related business logic including:
- Notification creation
- Notification delivery
- Bulk notification sending
- Notification management
"""

from typing import Dict, Any, Optional, List
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from api.models import Notification, Organization
from .base_service import BaseService, ServiceException


class NotificationService(BaseService):
    """Service class for notification-related operations"""

    @transaction.atomic
    def create_notification(
        self,
        user: User,
        title: str,
        message: str,
        notification_type: str = 'info',
        **metadata
    ) -> Notification:
        """
        Create a notification for a user

        Args:
            user: User to send notification to
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, success, warning, error, task, user, system)
            **metadata: Additional metadata

        Returns:
            Created Notification instance

        Raises:
            ServiceException: If creation fails
        """
        try:
            # Validate notification type
            valid_types = [choice[0] for choice in Notification.TYPE_CHOICES]
            if notification_type not in valid_types:
                raise ServiceException(
                    message=f"Invalid notification type: {notification_type}",
                    code='invalid_type',
                    status=400
                )

            # Create notification
            notification = Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                metadata=metadata
            )

            self.log_action(
                f"Created notification for user: {user.username}",
                {'title': title, 'type': notification_type}
            )

            return notification

        except ServiceException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create notification: {str(e)}")
            raise ServiceException(
                message=f"Failed to create notification: {str(e)}",
                code='notification_creation_failed',
                status=500
            )

    @transaction.atomic
    def create_bulk_notifications(
        self,
        users: List[User],
        title: str,
        message: str,
        notification_type: str = 'info',
        **metadata
    ) -> List[Notification]:
        """
        Create notifications for multiple users

        Args:
            users: List of users to send notification to
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            **metadata: Additional metadata

        Returns:
            List of created Notification instances

        Raises:
            ServiceException: If creation fails
        """
        try:
            notifications = []

            for user in users:
                notification = Notification.objects.create(
                    user=user,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    metadata=metadata
                )
                notifications.append(notification)

            self.log_action(
                f"Created bulk notifications",
                {'user_count': len(users), 'title': title}
            )

            return notifications

        except Exception as e:
            self.logger.error(f"Failed to create bulk notifications: {str(e)}")
            raise ServiceException(
                message=f"Failed to create bulk notifications: {str(e)}",
                code='bulk_notification_failed',
                status=500
            )

    def mark_as_read(
        self,
        notification: Notification
    ) -> Notification:
        """
        Mark a notification as read

        Args:
            notification: Notification to mark as read

        Returns:
            Updated Notification instance

        Raises:
            ServiceException: If operation fails
        """
        try:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()

            self.log_action(
                f"Marked notification as read",
                {'notification_id': notification.id}
            )

            return notification

        except Exception as e:
            self.logger.error(f"Failed to mark notification as read: {str(e)}")
            raise ServiceException(
                message=f"Failed to mark as read: {str(e)}",
                code='mark_read_failed',
                status=500
            )

    @transaction.atomic
    def mark_all_as_read(
        self,
        user: User
    ) -> int:
        """
        Mark all unread notifications as read for a user

        Args:
            user: User to mark notifications for

        Returns:
            Number of notifications marked as read

        Raises:
            ServiceException: If operation fails
        """
        try:
            count = Notification.objects.filter(
                user=user,
                is_read=False
            ).update(
                is_read=True,
                read_at=timezone.now()
            )

            self.log_action(
                f"Marked all notifications as read for user: {user.username}",
                {'count': count}
            )

            return count

        except Exception as e:
            self.logger.error(f"Failed to mark all as read: {str(e)}")
            raise ServiceException(
                message=f"Failed to mark all as read: {str(e)}",
                code='mark_all_read_failed',
                status=500
            )

    def get_unread_count(
        self,
        user: User
    ) -> int:
        """
        Get count of unread notifications for a user

        Args:
            user: User to get count for

        Returns:
            Number of unread notifications

        Raises:
            ServiceException: If operation fails
        """
        try:
            count = Notification.objects.filter(
                user=user,
                is_read=False
            ).count()

            return count

        except Exception as e:
            self.logger.error(f"Failed to get unread count: {str(e)}")
            raise ServiceException(
                message=f"Failed to get unread count: {str(e)}",
                code='count_failed',
                status=500
            )
