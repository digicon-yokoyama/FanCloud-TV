from django.db import models
from django.conf import settings


class Video(models.Model):
    """VOD video model."""
    
    STATUS_CHOICES = [
        ('uploading', 'アップロード中'),
        ('processing', '処理中'),
        ('ready', '公開可能'),
        ('failed', '失敗'),
        ('archived', 'アーカイブ済み'),
    ]
    
    PRIVACY_CHOICES = [
        ('public', '公開'),
        ('unlisted', '限定公開'),
        ('private', '非公開'),
        ('premium', 'プレミアム限定'),
    ]
    
    # Basic info
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='videos')
    
    # Video files
    recording_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    playback_url = models.URLField()
    thumbnail_url = models.URLField(blank=True)
    duration = models.IntegerField(default=0)  # seconds
    file_size = models.BigIntegerField(default=0)  # bytes
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploading')
    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')
    processing_progress = models.IntegerField(default=0)  # 0-100%
    
    # Settings
    enable_comments = models.BooleanField(default=True)
    enable_likes = models.BooleanField(default=True)
    is_premium_content = models.BooleanField(default=False)
    
    # Statistics
    view_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    dislike_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    
    # SEO
    slug = models.SlugField(unique=True, blank=True)
    tags = models.ManyToManyField('VideoTag', blank=True, related_name='videos')
    category = models.ForeignKey('VideoCategory', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} by {self.uploader.username}"
    
    @property
    def is_published(self):
        return self.status == 'ready' and self.privacy in ['public', 'unlisted']
    
    @property
    def duration_formatted(self):
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"


class VideoCategory(models.Model):
    """Video category/genre."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'categories'
    
    def __str__(self):
        return self.name


class VideoTag(models.Model):
    """Video tags."""
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name


class Playlist(models.Model):
    """User playlists."""
    
    PRIVACY_CHOICES = [
        ('public', '公開'),
        ('unlisted', '限定公開'),
        ('private', '非公開'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='playlists')
    videos = models.ManyToManyField(Video, through='PlaylistItem', related_name='playlists')
    
    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')
    thumbnail_url = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.title} by {self.owner.username}"
    
    @property
    def video_count(self):
        return self.videos.count()


class PlaylistItem(models.Model):
    """Playlist video items with ordering."""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('playlist', 'video')
        ordering = ['order']


class VideoView(models.Model):
    """Track video views."""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    watch_duration = models.IntegerField(default=0)  # seconds watched
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('video', 'user', 'ip_address')
    
    def __str__(self):
        user_info = self.user.username if self.user else self.ip_address
        return f"{user_info} viewed {self.video.title}"


class VideoLike(models.Model):
    """Video likes/dislikes."""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_like = models.BooleanField()  # True for like, False for dislike
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('video', 'user')
    
    def __str__(self):
        reaction = "liked" if self.is_like else "disliked"
        return f"{self.user.username} {reaction} {self.video.title}"


class Comment(models.Model):
    """Video comments."""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    content = models.TextField(max_length=1000)
    is_pinned = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    
    like_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.video.title}"
    
    @property
    def is_reply(self):
        return self.parent is not None