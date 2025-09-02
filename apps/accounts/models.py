from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extended user model with streaming platform specific fields."""
    
    ROLE_CHOICES = [
        ('system_admin', 'システム管理者'),
        ('tenant_admin', 'テナント管理者'),
        ('tenant_user', 'テナントユーザー'),
        ('subscriber', '登録者'),
    ]
    
    MEMBERSHIP_CHOICES = [
        ('free', '無料会員'),
        ('premium', '有料会員'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='subscriber')
    membership = models.CharField(max_length=10, choices=MEMBERSHIP_CHOICES, default='free')
    
    # Profile fields
    bio = models.TextField(blank=True, max_length=500)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    website = models.URLField(blank=True)
    
    # Streaming specific
    can_stream = models.BooleanField(default=False)
    max_concurrent_streams = models.IntegerField(default=1)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_system_admin(self):
        return self.role == 'system_admin'
    
    def is_tenant_admin(self):
        return self.role == 'tenant_admin'
    
    def is_tenant_user(self):
        return self.role == 'tenant_user'
    
    def is_subscriber(self):
        return self.role == 'subscriber'
    
    def is_premium(self):
        return self.membership == 'premium'
    
    def can_manage_users(self):
        return self.role in ['system_admin', 'tenant_admin']
    
    def can_manage_content(self):
        return self.role in ['system_admin', 'tenant_admin', 'tenant_user']


class UserProfile(models.Model):
    """Additional user profile information."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Social links
    twitter = models.CharField(max_length=100, blank=True)
    youtube = models.CharField(max_length=100, blank=True)
    twitch = models.CharField(max_length=100, blank=True)
    
    # Preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    privacy_level = models.CharField(
        max_length=20,
        choices=[
            ('public', '公開'),
            ('followers', 'フォロワーのみ'),
            ('private', '非公開'),
        ],
        default='public'
    )
    
    # Statistics
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    total_views = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"


class Follow(models.Model):
    """User following relationship."""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"