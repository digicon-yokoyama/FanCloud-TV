from django.utils import timezone
from .models import Notification, NotificationSettings


class NotificationService:
    """Service for handling notifications."""
    
    @staticmethod
    def create_notification(
        recipient,
        notification_type,
        title,
        message,
        sender=None,
        stream_id='',
        video_id='',
        comment_id=None
    ):
        """Create a new notification."""
        notification = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            title=title,
            message=message,
            stream_id=stream_id,
            video_id=video_id,
            comment_id=comment_id
        )
        return notification
    
    @staticmethod
    def notify_new_follower(follower, following):
        """Notify user about new follower."""
        title = f"{follower.username}があなたをフォローしました"
        message = f"{follower.username}があなたをフォローしました。"
        
        NotificationService.create_notification(
            recipient=following,
            sender=follower,
            notification_type='new_follower',
            title=title,
            message=message
        )
    
    @staticmethod
    def notify_new_video(video):
        """Notify followers about new video."""
        from apps.accounts.models import Follow
        
        followers = Follow.objects.filter(following=video.uploader).select_related('follower')
        
        title = f"{video.uploader.username}が新しい動画をアップロードしました"
        message = f"{video.uploader.username}が「{video.title}」をアップロードしました。"
        
        for follow in followers:
            NotificationService.create_notification(
                recipient=follow.follower,
                sender=video.uploader,
                notification_type='new_video',
                title=title,
                message=message,
                video_id=str(video.id)
            )
    
    @staticmethod
    def notify_stream_start(stream):
        """Notify followers about stream start."""
        from apps.accounts.models import Follow
        
        followers = Follow.objects.filter(following=stream.creator).select_related('follower')
        
        title = f"{stream.creator.username}がライブ配信を開始しました"
        message = f"{stream.creator.username}が「{stream.title}」の配信を開始しました。"
        
        for follow in followers:
            NotificationService.create_notification(
                recipient=follow.follower,
                sender=stream.creator,
                notification_type='stream_start',
                title=title,
                message=message,
                stream_id=stream.stream_id
            )
    
    @staticmethod
    def notify_new_comment(comment):
        """Notify video uploader about new comment."""
        if comment.user == comment.video.uploader:
            # Don't notify if commenting on own video
            return
        
        title = f"{comment.user.username}があなたの動画にコメントしました"
        message = f"{comment.user.username}が「{comment.video.title}」にコメントしました: {comment.content[:50]}..."
        
        NotificationService.create_notification(
            recipient=comment.video.uploader,
            sender=comment.user,
            notification_type='comment',
            title=title,
            message=message,
            video_id=str(comment.video.id),
            comment_id=comment.id
        )
    
    @staticmethod
    def notify_comment_reply(reply):
        """Notify parent comment author about reply."""
        if not reply.parent or reply.user == reply.parent.user:
            # Don't notify if no parent or replying to own comment
            return
        
        title = f"{reply.user.username}があなたのコメントに返信しました"
        message = f"{reply.user.username}が返信しました: {reply.content[:50]}..."
        
        NotificationService.create_notification(
            recipient=reply.parent.user,
            sender=reply.user,
            notification_type='comment',
            title=title,
            message=message,
            video_id=str(reply.video.id),
            comment_id=reply.id
        )
    
    @staticmethod
    def notify_video_like(video_like):
        """Notify video uploader about like."""
        if video_like.user == video_like.video.uploader or not video_like.is_like:
            # Don't notify if liking own video or if it's a dislike
            return
        
        title = f"{video_like.user.username}があなたの動画にいいねしました"
        message = f"{video_like.user.username}が「{video_like.video.title}」にいいねしました。"
        
        NotificationService.create_notification(
            recipient=video_like.video.uploader,
            sender=video_like.user,
            notification_type='like',
            title=title,
            message=message,
            video_id=str(video_like.video.id)
        )
    
    @staticmethod
    def get_user_notifications(user, limit=20, unread_only=False):
        """Get user notifications."""
        notifications = user.notifications.all()
        
        if unread_only:
            notifications = notifications.filter(is_read=False)
        
        return notifications[:limit]
    
    @staticmethod
    def mark_as_read(user, notification_ids):
        """Mark notifications as read."""
        user.notifications.filter(
            id__in=notification_ids,
            is_read=False
        ).update(is_read=True)
    
    @staticmethod
    def get_unread_count(user):
        """Get count of unread notifications."""
        return user.notifications.filter(is_read=False).count()
    
    @staticmethod
    def get_or_create_notification_settings(user):
        """Get or create notification settings for user."""
        settings, created = NotificationSettings.objects.get_or_create(
            user=user,
            defaults={
                'email_stream_start': True,
                'email_new_video': True,
                'email_new_follower': True,
                'email_comments': True,
                'email_mentions': True,
                'push_stream_start': True,
                'push_new_video': True,
                'push_new_follower': False,
                'push_comments': True,
                'push_mentions': True,
            }
        )
        return settings