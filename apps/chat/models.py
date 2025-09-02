from django.db import models
from django.conf import settings


class ChatRoom(models.Model):
    """Chat room for live streams."""
    name = models.CharField(max_length=100, unique=True)
    stream = models.OneToOneField('streaming.Stream', on_delete=models.CASCADE, related_name='chat_room', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Chat room: {self.name}"


class ChatMessage(models.Model):
    """Chat messages in stream chat rooms."""
    
    MESSAGE_TYPES = [
        ('message', 'メッセージ'),
        ('join', '参加'),
        ('leave', '退出'),
        ('system', 'システム'),
    ]
    
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='message')
    content = models.TextField(max_length=500)
    
    # Moderation
    is_deleted = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        if self.user:
            return f"{self.user.username}: {self.content[:50]}..."
        return f"System: {self.content[:50]}..."


class ChatStamp(models.Model):
    """Chat stamps/emotes."""
    name = models.CharField(max_length=50, unique=True)
    image = models.ImageField(upload_to='stamps/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class ChatReaction(models.Model):
    """Reactions to chat messages."""
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stamp = models.ForeignKey(ChatStamp, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('message', 'user', 'stamp')
    
    def __str__(self):
        return f"{self.user.username} reacted with {self.stamp.name}"


class ChatModerator(models.Model):
    """Chat moderators for rooms."""
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='moderators')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_moderators')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('room', 'user')
    
    def __str__(self):
        return f"{self.user.username} moderates {self.room.name}"