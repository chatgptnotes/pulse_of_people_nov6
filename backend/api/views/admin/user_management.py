"""
Admin views for managing regular users only
Admins cannot manage other admins or superadmins
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Q

from api.models import UserProfile
from api.serializers import UserManagementSerializer
from api.permissions.role_permissions import IsAdminOrAbove, CanManageUsers


class AdminUserManagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for admins to manage regular users only
    - List all regular users (role='user')
    - Create new regular users
    - Update regular user information
    - Delete regular users
    - Cannot change roles
    - Cannot manage admins or superadmins
    """
    serializer_class = UserManagementSerializer
    permission_classes = [IsAdminOrAbove, CanManageUsers]

    def get_queryset(self):
        """
        Admins can only see regular users, not other admins or superadmins
        """
        queryset = User.objects.filter(profile__role='user').select_related('profile').order_by('-date_joined')

        # Search by username, email, or name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create a new regular user
        Admins can only create users with 'user' role
        """
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if not all([username, email, password]):
            return Response(
                {'error': 'Username, email, and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'Email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create user with 'user' role only
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', '')
        )

        # Create or update profile with user role
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.role = 'user'  # Force user role
        profile.save()

        return Response(
            {
                'message': 'User created successfully',
                'user': UserManagementSerializer(user).data
            },
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """
        Update user information
        Admins cannot change user roles
        """
        user = self.get_object()

        # Prevent role changes
        if 'role' in request.data:
            return Response(
                {'error': 'Admins cannot change user roles'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Update allowed fields
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.email = request.data.get('email', user.email)
        user.save()

        return Response({
            'message': 'User updated successfully',
            'user': UserManagementSerializer(user).data
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get statistics for regular users only
        """
        total_users = User.objects.filter(profile__role='user').count()
        active_users = User.objects.filter(profile__role='user', is_active=True).count()
        inactive_users = User.objects.filter(profile__role='user', is_active=False).count()

        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users
        })

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        Toggle user active status
        """
        user = self.get_object()

        # Additional check to ensure user is regular user
        if hasattr(user, 'profile') and user.profile.role != 'user':
            return Response(
                {'error': 'You can only manage regular users'},
                status=status.HTTP_403_FORBIDDEN
            )

        user.is_active = not user.is_active
        user.save()

        return Response({
            'message': f'User {"activated" if user.is_active else "deactivated"}',
            'user': UserManagementSerializer(user).data
        })

    def destroy(self, request, *args, **kwargs):
        """
        Delete a user
        Admins can only delete regular users
        """
        user = self.get_object()

        # Additional check to ensure user is regular user
        if hasattr(user, 'profile') and user.profile.role != 'user':
            return Response(
                {'error': 'You can only delete regular users'},
                status=status.HTTP_403_FORBIDDEN
            )

        username = user.username
        user.delete()

        return Response({
            'message': f'User {username} deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
