from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.models import User
from api.models import UserProfile, Task, Notification, UploadedFile
from api.serializers import UserSerializer, UserProfileSerializer, TaskSerializer, NotificationSerializer, UploadedFileSerializer
import os
import uuid
from supabase import create_client, Client


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user management"""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """Allow anyone to create a user (register), but require auth for other actions"""
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for user profile management"""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Users can only see their own profile"""
        return UserProfile.objects.filter(user=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet for task management"""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Users can only see their own tasks"""
        return Task.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """Auto-assign owner when creating task"""
        serializer.save(owner=self.request.user)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'healthy',
        'message': 'API is running'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_me(request):
    """Get current user profile"""
    try:
        profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        profile = UserProfile.objects.create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for notification management"""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Users can only see their own notifications"""
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Auto-assign user when creating notification"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a single notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all user notifications as read"""
        from django.utils import timezone
        updated = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return Response({
            'message': f'{updated} notifications marked as read',
            'updated_count': updated
        })

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return Response({'unread_count': count})


class UploadedFileViewSet(viewsets.ModelViewSet):
    """ViewSet for file upload management with Supabase Storage"""
    queryset = UploadedFile.objects.all()
    serializer_class = UploadedFileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """Users can only see their own files"""
        return UploadedFile.objects.filter(user=self.request.user)

    def get_supabase_client(self):
        """Initialize Supabase client"""
        from django.conf import settings
        return create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )

    def determine_file_category(self, mime_type):
        """Determine file category from MIME type"""
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type in ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            return 'document'
        elif mime_type in ['application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed']:
            return 'archive'
        else:
            return 'other'

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Upload file to Supabase Storage

        Expected fields:
        - file: File object (required)
        - bucket_id: Storage bucket (default: 'user-files')
        - metadata: JSON metadata (optional)
        """
        try:
            # Validate file
            if 'file' not in request.FILES:
                return Response(
                    {'error': 'No file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            uploaded_file = request.FILES['file']

            # File size limit (50MB)
            MAX_FILE_SIZE = 50 * 1024 * 1024
            if uploaded_file.size > MAX_FILE_SIZE:
                return Response(
                    {'error': f'File size exceeds maximum limit of 50MB'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate unique filename
            file_ext = os.path.splitext(uploaded_file.name)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"

            # Get bucket_id from request or use default
            bucket_id = request.data.get('bucket_id', 'user-files')

            # Build storage path: user_id/unique_filename
            user_folder = str(request.user.id)
            storage_path = f"{user_folder}/{unique_filename}"

            # Upload to Supabase Storage
            supabase = self.get_supabase_client()

            # Read file content
            file_content = uploaded_file.read()

            # Upload to Supabase
            upload_response = supabase.storage.from_(bucket_id).upload(
                path=storage_path,
                file=file_content,
                file_options={
                    "content-type": uploaded_file.content_type,
                    "x-upsert": "false"
                }
            )

            # Get public URL
            public_url = supabase.storage.from_(bucket_id).get_public_url(storage_path)

            # Create database record
            file_category = self.determine_file_category(uploaded_file.content_type)

            file_metadata = request.data.get('metadata', {})
            if isinstance(file_metadata, str):
                import json
                file_metadata = json.loads(file_metadata)

            uploaded_file_obj = UploadedFile.objects.create(
                user=request.user,
                filename=unique_filename,
                original_filename=uploaded_file.name,
                file_size=uploaded_file.size,
                mime_type=uploaded_file.content_type,
                storage_path=storage_path,
                storage_url=public_url,
                bucket_id=bucket_id,
                file_category=file_category,
                metadata=file_metadata
            )

            serializer = self.get_serializer(uploaded_file_obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Upload failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['delete'])
    def delete_file(self, request, pk=None):
        """Delete file from Supabase Storage and database"""
        try:
            file_obj = self.get_object()

            # Delete from Supabase Storage
            supabase = self.get_supabase_client()
            supabase.storage.from_(file_obj.bucket_id).remove([file_obj.storage_path])

            # Delete from database
            file_obj.delete()

            return Response(
                {'message': 'File deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {'error': f'Delete failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def download_url(self, request, pk=None):
        """Get temporary download URL for file"""
        try:
            file_obj = self.get_object()

            # Get signed URL (valid for 1 hour)
            supabase = self.get_supabase_client()
            signed_url = supabase.storage.from_(file_obj.bucket_id).create_signed_url(
                file_obj.storage_path,
                expires_in=3600
            )

            return Response({
                'download_url': signed_url['signedURL'],
                'expires_in': 3600
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to generate download URL: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get files filtered by category"""
        category = request.query_params.get('category')
        if not category:
            return Response(
                {'error': 'Category parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        files = self.get_queryset().filter(file_category=category)
        serializer = self.get_serializer(files, many=True)
        return Response(serializer.data)
