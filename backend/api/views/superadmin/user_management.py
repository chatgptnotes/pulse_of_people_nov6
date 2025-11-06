"""
Superadmin views for managing all users, admins, and roles
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Q

from api.models import UserProfile
from api.serializers import UserManagementSerializer, UserRoleSerializer
from api.permissions.role_permissions import IsSuperAdmin, CanChangeRole


class SuperAdminUserManagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for superadmin to manage all users
    - List all users with any role
    - Create new users with any role
    - Update user information
    - Delete users
    - Change user roles
    """
    serializer_class = UserManagementSerializer
    permission_classes = [IsSuperAdmin]
    queryset = User.objects.all().select_related('profile').order_by('-date_joined')

    def get_queryset(self):
        """
        Filter users by role, search query, or status
        """
        queryset = super().get_queryset()

        # Filter by role
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(profile__role=role)

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

    @action(detail=True, methods=['patch'], permission_classes=[CanChangeRole])
    def change_role(self, request, pk=None):
        """
        Change a user's role
        Only superadmins can change roles
        """
        user = self.get_object()
        new_role = request.data.get('role')

        if not new_role:
            return Response(
                {'error': 'Role is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_role not in ['superadmin', 'admin', 'user']:
            return Response(
                {'error': 'Invalid role. Must be superadmin, admin, or user'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the user's role
        profile = user.profile
        old_role = profile.role
        profile.role = new_role
        profile.save()

        return Response({
            'message': f'User role changed from {old_role} to {new_role}',
            'user': UserManagementSerializer(user).data
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get user statistics by role
        """
        total_users = User.objects.count()
        superadmins = User.objects.filter(profile__role='superadmin').count()
        admins = User.objects.filter(profile__role='admin').count()
        users = User.objects.filter(profile__role='user').count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = User.objects.filter(is_active=False).count()

        return Response({
            'total_users': total_users,
            'superadmins': superadmins,
            'admins': admins,
            'users': users,
            'active_users': active_users,
            'inactive_users': inactive_users
        })

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        Toggle user active status
        """
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()

        return Response({
            'message': f'User {"activated" if user.is_active else "deactivated"}',
            'user': UserManagementSerializer(user).data
        })

    @action(detail=False, methods=['get'])
    def admins(self, request):
        """
        Get list of all admins and superadmins
        """
        admins = User.objects.filter(
            Q(profile__role='admin') | Q(profile__role='superadmin')
        ).select_related('profile').order_by('-date_joined')

        serializer = self.get_serializer(admins, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def create_admin(self, request):
        """
        Create a new admin user
        """
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        role = request.data.get('role', 'admin')

        if not all([username, email, password]):
            return Response(
                {'error': 'Username, email, and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if role not in ['admin', 'superadmin']:
            return Response(
                {'error': 'Role must be admin or superadmin'},
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

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', '')
        )

        # Create or update profile with admin role
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        profile.save()

        return Response(
            {
                'message': f'{role.title()} user created successfully',
                'user': UserManagementSerializer(user).data
            },
            status=status.HTTP_201_CREATED
        )
