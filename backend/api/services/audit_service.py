"""
Audit Service

This module handles all audit logging operations including:
- User action logging
- System event logging
- Audit trail queries
"""

from typing import Dict, Any, Optional
from django.contrib.auth.models import User
from api.models import AuditLog
from .base_service import BaseService, ServiceException


class AuditService(BaseService):
    """Service class for audit logging operations"""

    @staticmethod
    def log_user_action(
        user: User,
        action: str,
        target_model: str = '',
        target_id: str = '',
        changes: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> AuditLog:
        """
        Log a user action

        Args:
            user: User performing the action
            action: Action type (create, read, update, delete, login, logout, etc.)
            target_model: Model name being acted upon
            target_id: ID of the target object
            changes: Dict of changes made
            ip_address: IP address of the user
            user_agent: User agent string

        Returns:
            Created AuditLog instance
        """
        try:
            audit_log = AuditLog.objects.create(
                user=user,
                action=action,
                target_model=target_model,
                target_id=target_id,
                changes=changes or {},
                ip_address=ip_address,
                user_agent=user_agent
            )

            return audit_log

        except Exception as e:
            # Don't raise exception for audit logging failures
            # Just log the error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log: {str(e)}")
            return None

    @staticmethod
    def get_user_activity(
        user: User,
        limit: int = 100
    ) -> list:
        """
        Get recent activity for a user

        Args:
            user: User to get activity for
            limit: Maximum number of records to return

        Returns:
            List of AuditLog instances
        """
        try:
            logs = AuditLog.objects.filter(user=user)[:limit]
            return list(logs)

        except Exception as e:
            raise ServiceException(
                message=f"Failed to get user activity: {str(e)}",
                code='activity_retrieval_failed',
                status=500
            )

    @staticmethod
    def get_model_history(
        model_name: str,
        object_id: str,
        limit: int = 100
    ) -> list:
        """
        Get audit history for a specific object

        Args:
            model_name: Name of the model
            object_id: ID of the object
            limit: Maximum number of records to return

        Returns:
            List of AuditLog instances
        """
        try:
            logs = AuditLog.objects.filter(
                target_model=model_name,
                target_id=object_id
            )[:limit]

            return list(logs)

        except Exception as e:
            raise ServiceException(
                message=f"Failed to get model history: {str(e)}",
                code='history_retrieval_failed',
                status=500
            )
