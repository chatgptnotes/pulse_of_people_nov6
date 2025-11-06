from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from api.views import UserViewSet, UserProfileViewSet, TaskViewSet, NotificationViewSet, UploadedFileViewSet, health_check, profile_me
from api.views.transcription_views import TranscriptionViewSet

# Create router for viewsets (legacy routes)
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', UserProfileViewSet, basename='profile')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'files', UploadedFileViewSet, basename='file')
router.register(r'transcriptions', TranscriptionViewSet, basename='transcription')

urlpatterns = [
    # Health check
    path('health/', health_check, name='health-check'),

    # JWT Authentication
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', UserViewSet.as_view({'post': 'create'}), name='register'),

    # Profile endpoint
    path('profile/me/', profile_me, name='profile-me'),

    # Role-based routes
    path('superadmin/', include('api.urls.superadmin_urls')),
    path('admin/', include('api.urls.admin_urls')),
    path('user/', include('api.urls.user_urls')),

    # JioTV API routes
    path('jiotv/', include('api.urls.jiotv_urls')),

    # Router URLs (legacy)
    path('', include(router.urls)),
]
