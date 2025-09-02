from django.db import models
from django.conf import settings


class Stream(models.Model):
    """Live stream model."""
    
    STATUS_CHOICES = [
        ('created', '作成済み'),
        ('live', 'ライブ中'),
        ('ended', '終了'),
        ('error', 'エラー'),
    ]
    
    PRIVACY_CHOICES = [
        ('public', '公開'),
        ('unlisted', '限定公開'),
        ('private', '非公開'),
    ]
    
    QUALITY_CHOICES = [
        ('360p', '360p (低画質)'),
        ('480p', '480p (標準)'),
        ('720p', '720p (HD)'),
        ('1080p', '1080p (フルHD)'),
        ('1440p', '1440p (2K)'),
        ('2160p', '2160p (4K)'),
    ]
    
    BITRATE_CHOICES = [
        ('500', '500 kbps'),
        ('1000', '1 Mbps'),
        ('2500', '2.5 Mbps'),
        ('5000', '5 Mbps'),
        ('8000', '8 Mbps'),
        ('12000', '12 Mbps'),
    ]
    
    # Basic info
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    streamer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='streams')
    
    # Streaming settings
    stream_id = models.CharField(max_length=100, unique=True)
    stream_key = models.CharField(max_length=200)
    ingest_url = models.URLField()
    playback_url = models.URLField()
    thumbnail_url = models.URLField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')
    
    # Quality settings
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, default='720p')
    bitrate = models.CharField(max_length=10, choices=BITRATE_CHOICES, default='2500')
    framerate = models.IntegerField(default=30, help_text='FPS')
    
    # Stream settings
    category = models.ForeignKey('StreamCategory', on_delete=models.SET_NULL, null=True, blank=True)
    is_recording = models.BooleanField(default=True)
    enable_chat = models.BooleanField(default=True)
    subscriber_only_chat = models.BooleanField(default=False)
    enable_donations = models.BooleanField(default=False)
    mature_content = models.BooleanField(default=False)
    
    # Statistics
    viewer_count = models.IntegerField(default=0)
    peak_viewers = models.IntegerField(default=0)
    total_views = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} by {self.streamer.username}"
    
    @property
    def is_live(self):
        return self.status == 'live'
    
    @property
    def duration(self):
        if self.started_at and self.ended_at:
            return self.ended_at - self.started_at
        return None
    
    @property
    def can_start(self):
        """Check if stream can be started."""
        return self.status == 'created' and self.streamer.can_stream
    
    @property
    def can_end(self):
        """Check if stream can be ended."""
        return self.status == 'live'
    
    def start_stream(self):
        """Start the live stream."""
        from django.utils import timezone
        from .services import StreamingService
        
        if not self.can_start:
            raise ValueError("Cannot start stream in current state")
        
        try:
            # Initialize streaming service
            streaming_service = StreamingService()
            
            # Start stream on service
            stream_data = streaming_service.start_stream({
                'stream_id': self.stream_id,
                'title': self.title,
                'quality': self.quality,
                'bitrate': self.bitrate,
                'framerate': self.framerate,
            })
            
            # Update stream data
            self.status = 'live'
            self.started_at = timezone.now()
            self.ingest_url = stream_data.get('ingest_url', self.ingest_url)
            self.playback_url = stream_data.get('playback_url', self.playback_url)
            self.save()
            
            return True
            
        except Exception as e:
            self.status = 'error'
            self.save()
            raise e
    
    def end_stream(self):
        """End the live stream."""
        from django.utils import timezone
        from .services import StreamingService
        
        if not self.can_end:
            raise ValueError("Cannot end stream in current state")
        
        try:
            # End stream on service
            streaming_service = StreamingService()
            streaming_service.end_stream(self.stream_id)
            
            # Update stream data
            self.status = 'ended'
            self.ended_at = timezone.now()
            self.save()
            
            return True
            
        except Exception as e:
            self.status = 'error'
            self.save()
            raise e
    
    def update_viewer_count(self, count):
        """Update viewer count and peak viewers."""
        self.viewer_count = count
        if count > self.peak_viewers:
            self.peak_viewers = count
        self.save(update_fields=['viewer_count', 'peak_viewers', 'updated_at'])


class StreamCategory(models.Model):
    """Stream category/genre."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'categories'
    
    def __str__(self):
        return self.name


class StreamTag(models.Model):
    """Stream tags for categorization."""
    name = models.CharField(max_length=50, unique=True)
    streams = models.ManyToManyField(Stream, related_name='tags', blank=True)
    
    def __str__(self):
        return self.name


class StreamViewer(models.Model):
    """Track stream viewers."""
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='viewers')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('stream', 'user', 'ip_address')
    
    def __str__(self):
        user_info = self.user.username if self.user else self.ip_address
        return f"{user_info} viewing {self.stream.title}"