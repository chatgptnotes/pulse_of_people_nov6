"""
User views for managing their own profile
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User

from api.models import UserProfile
from api.serializers import UserProfileSerializer, UserSerializer


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for regular users to manage their own profile
    - View own profile
    - Update own profile information
    - Cannot change role
    - Cannot see other users
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Users can only see their own profile
        """
        return UserProfile.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get current user's profile
        """
        try:
            profile = request.user.profile
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist
            profile = UserProfile.objects.create(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        """
        Update current user's profile
        Users cannot change their own role
        """
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)

        # Prevent role changes
        if 'role' in request.data:
            return Response(
                {'error': 'You cannot change your own role'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Update allowed fields
        profile.bio = request.data.get('bio', profile.bio)
        profile.phone = request.data.get('phone', profile.phone)
        profile.date_of_birth = request.data.get('date_of_birth', profile.date_of_birth)

        # Handle avatar upload
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']

        profile.save()

        # Also update user fields if provided
        user = request.user
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.email = request.data.get('email', user.email)
        user.save()

        serializer = self.get_serializer(profile)
        return Response({
            'message': 'Profile updated successfully',
            'profile': serializer.data
        })

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """
        Change user's own password
        """
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not all([old_password, new_password, confirm_password]):
            return Response(
                {'error': 'All password fields are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_password != confirm_password:
            return Response(
                {'error': 'New passwords do not match'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify old password
        user = request.user
        if not user.check_password(old_password):
            return Response(
                {'error': 'Old password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        user.set_password(new_password)
        user.save()

        return Response({
            'message': 'Password changed successfully'
        })

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """
        Get dashboard statistics for the user
        """
        user = request.user

        # Get user's task statistics if Task model is being used
        from api.models import Task
        total_tasks = Task.objects.filter(owner=user).count()
        pending_tasks = Task.objects.filter(owner=user, status='pending').count()
        completed_tasks = Task.objects.filter(owner=user, status='completed').count()
        in_progress_tasks = Task.objects.filter(owner=user, status='in_progress').count()

        return Response({
            'username': user.username,
            'email': user.email,
            'role': user.profile.role if hasattr(user, 'profile') else 'user',
            'tasks': {
                'total': total_tasks,
                'pending': pending_tasks,
                'in_progress': in_progress_tasks,
                'completed': completed_tasks
            },
            'account': {
                'date_joined': user.date_joined,
                'last_login': user.last_login,
                'is_active': user.is_active
            }
        })
