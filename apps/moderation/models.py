from django.db import models
from django.conf import settings


class ModerationRule(models.Model):
    """Moderation rules for content filtering."""
    
    RULE_TYPES = [
        ('keyword', 'キーワード'),
        ('spam', 'スパム'),
        ('harassment', 'ハラスメント'),
        ('inappropriate', '不適切なコンテンツ'),
        ('copyright', '著作権'),
    ]
    
    ACTION_TYPES = [
        ('warn', '警告'),
        ('timeout', 'タイムアウト'),
        ('ban', 'バン'),
        ('delete', '削除'),
        ('flag', 'フラグ'),
    ]
    
    name = models.CharField(max_length=100)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    pattern = models.TextField()  # Regex pattern or keywords
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    duration = models.IntegerField(null=True, blank=True)  # Duration in minutes for timeout
    
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"


class ModerationAction(models.Model):
    """Moderation actions taken."""
    
    ACTION_TYPES = [
        ('warn', '警告'),
        ('timeout', 'タイムアウト'),
        ('ban', 'バン'),
        ('delete_message', 'メッセージ削除'),
        ('delete_video', '動画削除'),
        ('hide_video', '動画非表示'),
    ]
    
    TARGET_TYPES = [
        ('user', 'ユーザー'),
        ('message', 'チャットメッセージ'),
        ('video', '動画'),
        ('comment', 'コメント'),
    ]
    
    # Action details
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    target_type = models.CharField(max_length=20, choices=TARGET_TYPES)
    target_id = models.CharField(max_length=100)  # ID of the target object
    
    # Users involved
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='moderation_actions_received')
    moderator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='moderation_actions_taken')
    
    # Details
    reason = models.TextField()
    duration = models.IntegerField(null=True, blank=True)  # Duration in minutes
    rule = models.ForeignKey(ModerationRule, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_action_type_display()} on {self.target_user.username} by {self.moderator.username}"


class Report(models.Model):
    """User reports for content."""
    
    REPORT_TYPES = [
        ('spam', 'スパム'),
        ('harassment', 'ハラスメント'),
        ('inappropriate', '不適切なコンテンツ'),
        ('copyright', '著作権侵害'),
        ('fake', '偽情報'),
        ('other', 'その他'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '保留中'),
        ('investigating', '調査中'),
        ('resolved', '解決済み'),
        ('dismissed', '却下'),
    ]
    
    # Reporter
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_made')
    
    # Target
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_received', null=True, blank=True)
    target_type = models.CharField(max_length=20, choices=[
        ('user', 'ユーザー'),
        ('video', '動画'),
        ('comment', 'コメント'),
        ('message', 'チャットメッセージ'),
    ])
    target_id = models.CharField(max_length=100)
    
    # Report details
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_reports')
    resolution_note = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_report_type_display()} report by {self.reporter.username}"


class BannedWord(models.Model):
    """Banned words for chat and comments."""
    word = models.CharField(max_length=100, unique=True)
    severity = models.CharField(max_length=10, choices=[
        ('low', '軽度'),
        ('medium', '中程度'),
        ('high', '重度'),
    ], default='medium')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.word


class UserWarning(models.Model):
    """User warnings."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='warnings')
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='warnings_issued')
    
    reason = models.TextField()
    severity = models.CharField(max_length=10, choices=[
        ('low', '軽度'),
        ('medium', '中程度'),
        ('high', '重度'),
    ], default='medium')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Warning for {self.user.username}: {self.reason[:50]}..."