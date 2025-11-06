"""
URL configuration for superadmin routes
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views.superadmin.user_management import SuperAdminUserManagementViewSet

router = DefaultRouter()
router.register(r'users', SuperAdminUserManagementViewSet, basename='superadmin-users')

urlpatterns = [
    path('', include(router.urls)),
]
