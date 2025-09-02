from django.db import models
from django.conf import settings


class Notification(models.Model):
    """User notifications."""
    
    NOTIFICATION_TYPES = [
        ('stream_start', 'ライブ配信開始'),
        ('new_video', '新着動画'),
        ('new_follower', '新しいフォロワー'),
        ('comment', 'コメント'),
        ('like', 'いいね'),
        ('mention', 'メンション'),
        ('system', 'システム通知'),
    ]
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Related objects
    stream_id = models.CharField(max_length=100, blank=True)
    video_id = models.CharField(max_length=100, blank=True)
    comment_id = models.IntegerField(null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_sent_email = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} for {self.recipient.username}"


class NotificationSettings(models.Model):
    """User notification preferences."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_settings')
    
    # Email notifications
    email_stream_start = models.BooleanField(default=True)
    email_new_video = models.BooleanField(default=True)
    email_new_follower = models.BooleanField(default=True)
    email_comments = models.BooleanField(default=True)
    email_mentions = models.BooleanField(default=True)
    
    # Push notifications (for future mobile app)
    push_stream_start = models.BooleanField(default=True)
    push_new_video = models.BooleanField(default=True)
    push_new_follower = models.BooleanField(default=False)
    push_comments = models.BooleanField(default=True)
    push_mentions = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification settings for {self.user.username}"


class EmailTemplate(models.Model):
    """Email templates for notifications."""
    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=200)
    body_text = models.TextField()
    body_html = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name