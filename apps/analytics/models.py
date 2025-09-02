from django.db import models
from django.conf import settings


class StreamAnalytics(models.Model):
    """Analytics data for live streams."""
    stream_id = models.CharField(max_length=100, db_index=True)
    
    # Time-based metrics
    timestamp = models.DateTimeField(auto_now_add=True)
    concurrent_viewers = models.IntegerField(default=0)
    
    # Cumulative metrics
    total_views = models.IntegerField(default=0)
    unique_viewers = models.IntegerField(default=0)
    chat_messages = models.IntegerField(default=0)
    reactions = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['stream_id', '-timestamp']),
        ]


class VideoAnalytics(models.Model):
    """Analytics data for VOD videos."""
    video_id = models.CharField(max_length=100, db_index=True)
    
    # Daily aggregated data
    date = models.DateField()
    views = models.IntegerField(default=0)
    unique_viewers = models.IntegerField(default=0)
    total_watch_time = models.IntegerField(default=0)  # seconds
    average_watch_time = models.FloatField(default=0)  # seconds
    
    # Engagement
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('video_id', 'date')
        ordering = ['-date']


class UserAnalytics(models.Model):
    """Analytics data for users."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='analytics')
    
    # Daily aggregated data
    date = models.DateField()
    
    # Content creation
    streams_created = models.IntegerField(default=0)
    videos_uploaded = models.IntegerField(default=0)
    total_streaming_time = models.IntegerField(default=0)  # minutes
    
    # Engagement as viewer
    videos_watched = models.IntegerField(default=0)
    total_watch_time = models.IntegerField(default=0)  # minutes
    streams_joined = models.IntegerField(default=0)
    chat_messages_sent = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']


class TenantAnalytics(models.Model):
    """Analytics data per tenant."""
    tenant_name = models.CharField(max_length=100)
    
    # Daily aggregated data
    date = models.DateField()
    
    # Users
    total_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)  # users who did something today
    new_users = models.IntegerField(default=0)
    
    # Content
    total_streams = models.IntegerField(default=0)
    live_streams = models.IntegerField(default=0)
    total_videos = models.IntegerField(default=0)
    new_videos = models.IntegerField(default=0)
    
    # Engagement
    total_views = models.IntegerField(default=0)
    total_watch_time = models.IntegerField(default=0)  # minutes
    chat_messages = models.IntegerField(default=0)
    
    # Storage
    storage_used = models.BigIntegerField(default=0)  # bytes
    bandwidth_used = models.BigIntegerField(default=0)  # bytes
    
    class Meta:
        unique_together = ('tenant_name', 'date')
        ordering = ['-date']


class PopularContent(models.Model):
    """Track popular content for recommendations."""
    
    CONTENT_TYPES = [
        ('stream', 'ライブ配信'),
        ('video', 'VOD'),
    ]
    
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    content_id = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    
    # Popularity metrics
    score = models.FloatField(default=0)  # Calculated popularity score
    views_24h = models.IntegerField(default=0)
    views_7d = models.IntegerField(default=0)
    engagement_rate = models.FloatField(default=0)
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('content_type', 'content_id')
        ordering = ['-score']


class RealtimeMetrics(models.Model):
    """Real-time metrics for dashboard."""
    
    # Current metrics (updated frequently)
    current_live_streams = models.IntegerField(default=0)
    current_viewers = models.IntegerField(default=0)
    current_chat_messages_per_minute = models.IntegerField(default=0)
    
    # Server metrics
    cpu_usage = models.FloatField(default=0)
    memory_usage = models.FloatField(default=0)
    disk_usage = models.FloatField(default=0)
    
    timestamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-timestamp']