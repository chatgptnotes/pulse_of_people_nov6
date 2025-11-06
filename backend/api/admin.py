from django.contrib import admin
from .models import UserProfile, Task, Organization, Permission, RolePermission, UserPermission, AuditLog, Notification


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'subscription_status', 'subscription_tier', 'max_users', 'created_at']
    list_filter = ['subscription_status', 'subscription_tier', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'description', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'description']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'organization', 'phone', 'created_at']
    list_filter = ['role', 'organization', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    raw_id_fields = ['user', 'organization']


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'permission']
    list_filter = ['role']
    search_fields = ['permission__name']


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'permission', 'granted', 'created_at']
    list_filter = ['granted', 'created_at']
    search_fields = ['user_profile__user__username', 'permission__name']
    raw_id_fields = ['user_profile', 'permission']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'target_model', 'target_id', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__username', 'target_model', 'target_id']
    readonly_fields = ['user', 'action', 'target_model', 'target_id', 'changes', 'ip_address', 'user_agent', 'timestamp']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'synced_to_supabase', 'created_at']
    list_filter = ['notification_type', 'is_read', 'synced_to_supabase', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['supabase_id', 'created_at', 'updated_at']
    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = "Mark selected notifications as read"

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = "Mark selected notifications as unread"


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'priority', 'owner', 'due_date', 'created_at']
    search_fields = ['title', 'description', 'owner__username']
    list_filter = ['status', 'priority', 'created_at']
    date_hierarchy = 'created_at'
