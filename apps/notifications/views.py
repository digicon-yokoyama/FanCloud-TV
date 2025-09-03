from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Notification, NotificationSettings
from .services import NotificationService


@login_required
def notification_list(request):
    """List user notifications."""
    notifications = NotificationService.get_user_notifications(request.user, limit=50)
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Mark displayed notifications as read
    notification_ids = [n.id for n in page_obj]
    NotificationService.mark_as_read(request.user, notification_ids)
    
    context = {
        'notifications': page_obj,
        'unread_count': NotificationService.get_unread_count(request.user),
    }
    return render(request, 'notifications/list.html', context)


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark a notification as read."""
    notification = get_object_or_404(
        Notification, 
        id=notification_id, 
        recipient=request.user
    )
    
    notification.is_read = True
    notification.save()
    
    return JsonResponse({
        'status': 'success',
        'unread_count': NotificationService.get_unread_count(request.user)
    })


@login_required
@require_POST
def mark_all_read(request):
    """Mark all notifications as read."""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    
    return JsonResponse({
        'status': 'success',
        'unread_count': 0
    })


@login_required
def notification_settings_view(request):
    """Notification settings page."""
    settings = NotificationService.get_or_create_notification_settings(request.user)
    
    if request.method == 'POST':
        # Update settings
        settings.email_stream_start = request.POST.get('email_stream_start') == 'on'
        settings.email_new_video = request.POST.get('email_new_video') == 'on'
        settings.email_new_follower = request.POST.get('email_new_follower') == 'on'
        settings.email_comments = request.POST.get('email_comments') == 'on'
        settings.email_mentions = request.POST.get('email_mentions') == 'on'
        
        settings.push_stream_start = request.POST.get('push_stream_start') == 'on'
        settings.push_new_video = request.POST.get('push_new_video') == 'on'
        settings.push_new_follower = request.POST.get('push_new_follower') == 'on'
        settings.push_comments = request.POST.get('push_comments') == 'on'
        settings.push_mentions = request.POST.get('push_mentions') == 'on'
        
        settings.save()
        
        return JsonResponse({'status': 'success', 'message': 'Settings saved successfully'})
    
    context = {
        'settings': settings,
    }
    return render(request, 'notifications/settings.html', context)


@login_required
def get_unread_notifications(request):
    """API endpoint to get unread notifications."""
    notifications = NotificationService.get_user_notifications(
        request.user, 
        limit=10, 
        unread_only=True
    )
    
    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'type': notification.notification_type,
            'title': notification.title,
            'message': notification.message,
            'sender': notification.sender.username if notification.sender else None,
            'created_at': notification.created_at.isoformat(),
            'stream_id': notification.stream_id,
            'video_id': notification.video_id,
        })
    
    return JsonResponse({
        'notifications': notifications_data,
        'unread_count': NotificationService.get_unread_count(request.user)
    })