"""
Views package
Exports legacy views and role-based views
"""
from .legacy import UserViewSet, UserProfileViewSet, TaskViewSet, NotificationViewSet, UploadedFileViewSet, health_check, profile_me

__all__ = [
    "UserViewSet",
    "UserProfileViewSet",
    "TaskViewSet",
    "NotificationViewSet",
    "UploadedFileViewSet",
    "health_check",
    "profile_me",
]
