"""
URL configuration for user routes
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views.user.profile import UserProfileViewSet

router = DefaultRouter()
router.register(r'profile', UserProfileViewSet, basename='user-profile')

urlpatterns = [
    path('', include(router.urls)),
]
