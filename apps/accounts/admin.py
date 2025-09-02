from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, Follow


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom user admin with role and streaming fields."""
    
    list_display = ('username', 'email', 'role', 'membership', 'can_stream', 'is_active', 'date_joined')
    list_filter = ('role', 'membership', 'can_stream', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Permissions', {
            'fields': ('role', 'membership', 'can_stream', 'max_concurrent_streams')
        }),
        ('Profile', {
            'fields': ('bio', 'avatar', 'website')
        }),
        ('Activity', {
            'fields': ('last_activity',),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'membership', 'can_stream')
        }),
    )
    
    actions = ['grant_streaming_permission', 'revoke_streaming_permission', 'upgrade_to_premium']
    
    def grant_streaming_permission(self, request, queryset):
        """Grant streaming permission to selected users."""
        updated = queryset.update(can_stream=True)
        self.message_user(request, f'Granted streaming permission to {updated} users.')
    grant_streaming_permission.short_description = 'Grant streaming permission'
    
    def revoke_streaming_permission(self, request, queryset):
        """Revoke streaming permission from selected users."""
        updated = queryset.update(can_stream=False)
        self.message_user(request, f'Revoked streaming permission from {updated} users.')
    revoke_streaming_permission.short_description = 'Revoke streaming permission'
    
    def upgrade_to_premium(self, request, queryset):
        """Upgrade selected users to premium membership."""
        updated = queryset.update(membership='premium')
        self.message_user(request, f'Upgraded {updated} users to premium membership.')
    upgrade_to_premium.short_description = 'Upgrade to premium'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """User profile admin."""
    
    list_display = ('user', 'followers_count', 'following_count', 'total_views', 'privacy_level')
    list_filter = ('privacy_level', 'email_notifications', 'push_notifications')
    search_fields = ('user__username', 'user__email')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user',)
        }),
        ('Social Links', {
            'fields': ('twitter', 'youtube', 'twitch')
        }),
        ('Settings', {
            'fields': ('email_notifications', 'push_notifications', 'privacy_level')
        }),
        ('Statistics', {
            'fields': ('followers_count', 'following_count', 'total_views'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('followers_count', 'following_count', 'total_views')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Follow relationship admin."""
    
    list_display = ('follower', 'following', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('follower__username', 'following__username')
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        """Disable adding follows through admin."""
        return False