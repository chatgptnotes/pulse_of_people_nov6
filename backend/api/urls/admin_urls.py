"""
URL configuration for admin routes
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views.admin.user_management import AdminUserManagementViewSet

router = DefaultRouter()
router.register(r'users', AdminUserManagementViewSet, basename='admin-users')

urlpatterns = [
    path('', include(router.urls)),
]
