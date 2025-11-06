from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Task, Permission, Notification, UploadedFile, Transcription


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'role', 'bio', 'avatar', 'avatar_url', 'phone', 'date_of_birth', 'permissions', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'permissions']

    def get_permissions(self, obj):
        """Get all permissions for this user"""
        return obj.get_permissions()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    profile = UserProfileSerializer(read_only=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'profile']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        """Create user with profile"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )
        UserProfile.objects.create(user=user)
        return user


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model"""
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'priority', 'owner', 'owner_username', 'due_date', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Auto-assign owner from request user"""
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for updating user roles (superadmin only)"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'role']
        read_only_fields = ['id', 'username', 'email']


class UserManagementSerializer(serializers.ModelSerializer):
    """Serializer for user management (admin/superadmin)"""
    profile = UserProfileSerializer(read_only=True)
    role = serializers.CharField(source='profile.role', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'profile', 'date_joined', 'last_login', 'is_active']
        read_only_fields = ['id', 'date_joined', 'last_login']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'username', 'title', 'message', 'notification_type',
            'is_read', 'read_at', 'related_model', 'related_id', 'metadata',
            'supabase_id', 'synced_to_supabase', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'supabase_id', 'synced_to_supabase', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Auto-assign user from request"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UploadedFileSerializer(serializers.ModelSerializer):
    """Serializer for uploaded files"""
    username = serializers.CharField(source='user.username', read_only=True)
    file_extension = serializers.SerializerMethodField()
    human_readable_size = serializers.SerializerMethodField()
    is_image = serializers.SerializerMethodField()
    is_video = serializers.SerializerMethodField()
    is_audio = serializers.SerializerMethodField()
    is_document = serializers.SerializerMethodField()

    class Meta:
        model = UploadedFile
        fields = [
            'id', 'user', 'username', 'filename', 'original_filename',
            'file_size', 'mime_type', 'storage_path', 'storage_url',
            'bucket_id', 'file_category', 'metadata',
            'file_extension', 'human_readable_size',
            'is_image', 'is_video', 'is_audio', 'is_document',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_file_extension(self, obj):
        return obj.get_file_extension()

    def get_human_readable_size(self, obj):
        return obj.get_human_readable_size()

    def get_is_image(self, obj):
        return obj.is_image()

    def get_is_video(self, obj):
        return obj.is_video()

    def get_is_audio(self, obj):
        return obj.is_audio()

    def get_is_document(self, obj):
        return obj.is_document()


class TranscriptionSerializer(serializers.ModelSerializer):
    """Serializer for speech-to-text transcriptions"""
    username = serializers.CharField(source='user.username', read_only=True)
    language_name = serializers.SerializerMethodField()
    processing_time = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Transcription
        fields = [
            'id', 'user', 'username', 'language_code', 'language_name',
            'transcription_text', 'confidence_score', 'status', 'status_display',
            'error_message', 'audio_metadata', 'audio_duration',
            'model_version', 'sarvam_request_id', 'session_id',
            'started_at', 'completed_at', 'processing_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'error_message', 'confidence_score',
            'sarvam_request_id', 'session_id', 'started_at', 'completed_at',
            'created_at', 'updated_at'
        ]

    def get_language_name(self, obj):
        """Get human-readable language name"""
        language_map = {
            'hi-IN': 'Hindi',
            'en-IN': 'English (India)',
            'ta-IN': 'Tamil',
            'te-IN': 'Telugu',
            'kn-IN': 'Kannada',
            'ml-IN': 'Malayalam',
            'mr-IN': 'Marathi',
            'bn-IN': 'Bengali',
            'gu-IN': 'Gujarati',
            'pa-IN': 'Punjabi',
        }
        return language_map.get(obj.language_code, obj.language_code)

    def get_processing_time(self, obj):
        """Get processing time in seconds"""
        return obj.get_processing_time()


class TranscriptionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing transcriptions"""
    username = serializers.CharField(source='user.username', read_only=True)
    language_name = serializers.SerializerMethodField()
    preview_text = serializers.SerializerMethodField()

    class Meta:
        model = Transcription
        fields = [
            'id', 'username', 'language_code', 'language_name',
            'preview_text', 'status', 'audio_duration',
            'created_at', 'completed_at'
        ]

    def get_language_name(self, obj):
        """Get human-readable language name"""
        language_map = dict(Transcription.LANGUAGE_CHOICES)
        return language_map.get(obj.language_code, obj.language_code)

    def get_preview_text(self, obj):
        """Get preview of transcription text (first 100 chars)"""
        if obj.transcription_text:
            return obj.transcription_text[:100] + "..." if len(obj.transcription_text) > 100 else obj.transcription_text
        return ""
