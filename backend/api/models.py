from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Organization(models.Model):
    """Organization model for multi-tenancy support"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    # Subscription
    subscription_status = models.CharField(max_length=20, default='active')
    subscription_tier = models.CharField(max_length=20, default='basic')
    max_users = models.IntegerField(default=10)

    # Settings
    settings = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"


class Permission(models.Model):
    """Granular permissions for RBAC"""
    CATEGORIES = [
        ('users', 'User Management'),
        ('data', 'Data Access'),
        ('analytics', 'Analytics'),
        ('settings', 'Settings'),
        ('system', 'System'),
    ]

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORIES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category}: {self.name}"

    class Meta:
        ordering = ['category', 'name']
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"


class UserProfile(models.Model):
    """Extended user profile with additional fields"""
    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('analyst', 'Analyst'),
        ('user', 'User'),
        ('viewer', 'Viewer'),
        ('volunteer', 'Volunteer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

    # Organization support
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='members',
        null=True,
        blank=True
    )

    # Profile fields
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)  # Supabase storage URL
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    # Custom permissions
    custom_permissions = models.ManyToManyField(
        Permission,
        through='UserPermission',
        related_name='users',
        blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_superadmin(self):
        return self.role == 'superadmin'

    def is_admin(self):
        return self.role == 'admin'

    def is_manager(self):
        return self.role == 'manager'

    def is_user(self):
        return self.role == 'user'

    def is_admin_or_above(self):
        return self.role in ['admin', 'superadmin', 'manager']

    def has_permission(self, permission_name):
        """Check if user has a specific permission"""
        # Superadmin has all permissions
        if self.is_superadmin():
            return True

        # Check role-based permissions
        role_has_perm = RolePermission.objects.filter(
            role=self.role,
            permission__name=permission_name
        ).exists()

        if role_has_perm:
            return True

        # Check user-specific permissions
        user_perm = UserPermission.objects.filter(
            user_profile=self,
            permission__name=permission_name,
            granted=True
        ).exists()

        return user_perm

    def get_permissions(self):
        """Get all permissions for this user"""
        if self.is_superadmin():
            return list(Permission.objects.all().values_list('name', flat=True))

        # Get role permissions
        role_perms = Permission.objects.filter(
            role_permissions__role=self.role
        ).values_list('name', flat=True)

        # Get user-specific permissions
        user_perms = Permission.objects.filter(
            user_permissions__user_profile=self,
            user_permissions__granted=True
        ).values_list('name', flat=True)

        # Combine and remove duplicates
        all_perms = set(list(role_perms) + list(user_perms))
        return list(all_perms)

    def __str__(self):
        return f"{self.user.username}'s profile"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


class RolePermission(models.Model):
    """Maps roles to permissions"""
    role = models.CharField(max_length=20, choices=UserProfile.ROLE_CHOICES)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='role_permissions')

    class Meta:
        unique_together = ['role', 'permission']
        verbose_name = "Role Permission"
        verbose_name_plural = "Role Permissions"

    def __str__(self):
        return f"{self.role} -> {self.permission.name}"


class UserPermission(models.Model):
    """User-specific permission overrides"""
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='user_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='user_permissions')
    granted = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user_profile', 'permission']
        verbose_name = "User Permission"
        verbose_name_plural = "User Permissions"

    def __str__(self):
        status = "Granted" if self.granted else "Revoked"
        return f"{self.user_profile.user.username} - {self.permission.name} ({status})"


class AuditLog(models.Model):
    """Audit log for tracking all user actions"""
    ACTION_TYPES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('permission_change', 'Permission Change'),
        ('role_change', 'Role Change'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    target_model = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=100, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action']),
            models.Index(fields=['target_model', 'target_id']),
        ]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"{user_str} - {self.action} - {self.timestamp}"


class Notification(models.Model):
    """
    Notification model for real-time user notifications
    Syncs with Supabase for real-time delivery
    """
    TYPE_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('task', 'Task'),
        ('user', 'User'),
        ('system', 'System'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Link to related object (optional)
    related_model = models.CharField(max_length=100, blank=True)
    related_id = models.CharField(max_length=100, blank=True)

    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)

    # Supabase sync
    supabase_id = models.UUIDField(null=True, blank=True, unique=True)
    synced_to_supabase = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_read']),
            models.Index(fields=['notification_type']),
        ]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def mark_as_read(self):
        """Mark notification as read"""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save()


class Task(models.Model):
    """Sample Task model for demonstration"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    due_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ['-created_at']


class UploadedFile(models.Model):
    """
    Uploaded File model for tracking files stored in Supabase Storage
    Stores metadata while actual files are in Supabase Storage buckets
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')

    # File information
    filename = models.CharField(max_length=255, help_text="Stored filename")
    original_filename = models.CharField(max_length=255, help_text="Original uploaded filename")
    file_size = models.BigIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100)

    # Storage information
    storage_path = models.CharField(max_length=500, help_text="Path in Supabase Storage")
    storage_url = models.URLField(max_length=500, help_text="Public URL from Supabase")
    bucket_id = models.CharField(max_length=100, default='user-files')

    # File categorization
    file_category = models.CharField(
        max_length=50,
        choices=[
            ('document', 'Document'),
            ('image', 'Image'),
            ('video', 'Video'),
            ('audio', 'Audio'),
            ('archive', 'Archive'),
            ('other', 'Other'),
        ],
        default='document'
    )

    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional file metadata")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['file_category']),
            models.Index(fields=['mime_type']),
        ]
        verbose_name = "Uploaded File"
        verbose_name_plural = "Uploaded Files"

    def __str__(self):
        return f"{self.user.username} - {self.original_filename}"

    def get_file_extension(self):
        """Get file extension from original filename"""
        import os
        return os.path.splitext(self.original_filename)[1].lower()

    def is_image(self):
        """Check if file is an image"""
        return self.mime_type.startswith('image/')

    def is_video(self):
        """Check if file is a video"""
        return self.mime_type.startswith('video/')

    def is_audio(self):
        """Check if file is audio"""
        return self.mime_type.startswith('audio/')

    def is_document(self):
        """Check if file is a document"""
        doc_types = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument']
        return any(self.mime_type.startswith(dtype) for dtype in doc_types)

    def get_human_readable_size(self):
        """Convert file size to human readable format"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"


class Transcription(models.Model):
    """
    Transcription model for storing speech-to-text results
    Supports real-time streaming transcription from SarvamAI
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    LANGUAGE_CHOICES = [
        ('hi-IN', 'Hindi'),
        ('en-IN', 'English (India)'),
        ('ta-IN', 'Tamil'),
        ('te-IN', 'Telugu'),
        ('kn-IN', 'Kannada'),
        ('ml-IN', 'Malayalam'),
        ('mr-IN', 'Marathi'),
        ('bn-IN', 'Bengali'),
        ('gu-IN', 'Gujarati'),
        ('pa-IN', 'Punjabi'),
    ]

    # User who created the transcription
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transcriptions',
        help_text="User who created this transcription"
    )

    # Transcription data
    language_code = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='hi-IN',
        help_text="Language of the audio"
    )
    transcription_text = models.TextField(
        blank=True,
        help_text="Transcribed text from audio"
    )
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Confidence score of transcription (0-1)"
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of transcription"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if transcription failed"
    )

    # Audio metadata
    audio_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadata about the audio file (duration, format, sample_rate, etc.)"
    )
    audio_duration = models.FloatField(
        null=True,
        blank=True,
        help_text="Duration of audio in seconds"
    )

    # SarvamAI specific
    model_version = models.CharField(
        max_length=50,
        default='saarika:v2.5',
        help_text="SarvamAI model version used"
    )
    sarvam_request_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="SarvamAI request ID for tracking"
    )

    # Session tracking
    session_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="WebSocket session ID"
    )

    # Processing time tracking
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When processing started"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When processing completed"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['language_code']),
            models.Index(fields=['session_id']),
        ]
        verbose_name = "Transcription"
        verbose_name_plural = "Transcriptions"

    def __str__(self):
        return f"{self.user.username} - {self.language_code} - {self.status}"

    def get_processing_time(self):
        """Calculate processing time in seconds"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        return None

    def mark_as_processing(self):
        """Mark transcription as processing"""
        from django.utils import timezone
        self.status = 'processing'
        self.started_at = timezone.now()
        self.save()

    def mark_as_completed(self, text, confidence=None):
        """Mark transcription as completed with results"""
        from django.utils import timezone
        self.status = 'completed'
        self.transcription_text = text
        self.confidence_score = confidence
        self.completed_at = timezone.now()
        self.save()

    def mark_as_failed(self, error_message):
        """Mark transcription as failed with error"""
        from django.utils import timezone
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()


# JioTV Models
class TVChannel(models.Model):
    """Model for storing JioTV channel information"""
    LANGUAGE_CHOICES = [
        ('tamil', 'Tamil'),
        ('hindi', 'Hindi'),
        ('english', 'English'),
        ('telugu', 'Telugu'),
        ('malayalam', 'Malayalam'),
        ('kannada', 'Kannada'),
        ('marathi', 'Marathi'),
        ('bengali', 'Bengali'),
        ('other', 'Other'),
    ]

    CATEGORY_CHOICES = [
        ('news', 'News'),
        ('entertainment', 'Entertainment'),
        ('sports', 'Sports'),
        ('movies', 'Movies'),
        ('music', 'Music'),
        ('kids', 'Kids'),
        ('devotional', 'Devotional'),
        ('documentary', 'Documentary'),
        ('other', 'Other'),
    ]

    # Channel Information
    channel_id = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    logo_url = models.URLField(max_length=500, blank=True)

    # Classification
    language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES, default='other')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')

    # Channel Features
    is_hd = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)

    # Stream URLs (cached)
    stream_url_low = models.URLField(max_length=500, blank=True)
    stream_url_medium = models.URLField(max_length=500, blank=True)
    stream_url_high = models.URLField(max_length=500, blank=True)
    stream_url_auto = models.URLField(max_length=500, blank=True)

    # Metadata
    description = models.TextField(blank=True)
    genre = models.CharField(max_length=100, blank=True)

    # Analytics
    view_count = models.IntegerField(default=0)
    last_viewed_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['language', 'category']),
            models.Index(fields=['is_active', 'language']),
            models.Index(fields=['channel_id']),
        ]
        verbose_name = "TV Channel"
        verbose_name_plural = "TV Channels"

    def __str__(self):
        return f"{self.name} ({self.channel_id})"

    def increment_view_count(self):
        """Increment view count and update last viewed timestamp"""
        self.view_count += 1
        self.last_viewed_at = timezone.now()
        self.save(update_fields=['view_count', 'last_viewed_at'])

    def is_tamil_news(self):
        """Check if channel is Tamil news"""
        return self.language == 'tamil' and self.category == 'news'


class StreamSession(models.Model):
    """Model for tracking user streaming sessions"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('ended', 'Ended'),
        ('error', 'Error'),
    ]

    # Session Information
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stream_sessions')
    channel = models.ForeignKey(TVChannel, on_delete=models.CASCADE, related_name='sessions')

    # Session Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    quality = models.CharField(max_length=20, default='auto')

    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)

    # Technical Details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    device_type = models.CharField(max_length=50, blank=True)

    # Error Tracking
    error_message = models.TextField(blank=True)
    error_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'started_at']),
            models.Index(fields=['channel', 'started_at']),
            models.Index(fields=['status']),
        ]
        verbose_name = "Stream Session"
        verbose_name_plural = "Stream Sessions"

    def __str__(self):
        return f"{self.user.username} - {self.channel.name} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"

    def end_session(self):
        """End the streaming session and calculate duration"""
        if not self.ended_at:
            self.ended_at = timezone.now()
            self.duration_seconds = int((self.ended_at - self.started_at).total_seconds())
            self.status = 'ended'
            self.save()

    def record_error(self, error_message: str):
        """Record an error during streaming"""
        self.error_count += 1
        self.error_message = error_message
        self.status = 'error'
        self.save()

    def calculate_duration(self):
        """Calculate session duration in seconds"""
        if self.ended_at:
            return int((self.ended_at - self.started_at).total_seconds())
        else:
            return int((timezone.now() - self.started_at).total_seconds())


class JioTVAuthentication(models.Model):
    """Model for storing JioTV authentication tokens"""
    # User Information
    mobile_number = models.CharField(max_length=15, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='jiotv_auth')

    # Authentication
    auth_token = models.TextField()
    is_active = models.BooleanField(default=True)

    # Timestamps
    token_created_at = models.DateTimeField(auto_now_add=True)
    token_expires_at = models.DateTimeField()
    last_used_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    login_method = models.CharField(max_length=20, default='otp')  # 'otp' or 'password'
    device_info = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-token_created_at']
        verbose_name = "JioTV Authentication"
        verbose_name_plural = "JioTV Authentications"

    def __str__(self):
        return f"{self.mobile_number} - {'Active' if self.is_active else 'Inactive'}"

    def is_token_expired(self):
        """Check if token is expired"""
        return timezone.now() > self.token_expires_at

    def refresh_last_used(self):
        """Update last used timestamp"""
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at'])

    def deactivate(self):
        """Deactivate the authentication token"""
        self.is_active = False
        self.save()
