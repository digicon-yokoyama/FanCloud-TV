from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Video, VideoCategory
from mock_services.streaming_service import mock_streaming_service


def trending(request):
    """Trending videos page."""
    videos = Video.objects.filter(
        status='ready',
        privacy__in=['public', 'unlisted']
    ).order_by('-view_count')
    
    # Filter by category if requested
    category_slug = request.GET.get('category')
    if category_slug and category_slug != 'all':
        try:
            # Try to get category by name
            category = VideoCategory.objects.get(
                name__iexact=category_slug,
                is_active=True
            )
            videos = videos.filter(category=category)
        except VideoCategory.DoesNotExist:
            # If category doesn't exist, ignore the filter
            pass
    
    paginator = Paginator(videos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = VideoCategory.objects.filter(is_active=True)
    
    context = {
        'trending_videos': page_obj,
        'categories': categories,
        'current_category': category_slug,
        'period': request.GET.get('period', 'week'),
    }
    return render(request, 'content/trending.html', context)


@login_required
def subscriptions(request):
    """User subscriptions page."""
    # This would be implemented with a proper follow system
    videos = Video.objects.filter(
        status='ready',
        privacy__in=['public', 'unlisted']
    ).order_by('-published_at')
    
    paginator = Paginator(videos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'videos': page_obj,
    }
    return render(request, 'content/subscriptions.html', context)


def watch_video(request, video_id):
    """Watch VOD video page."""
    video = get_object_or_404(Video, id=video_id, status='ready')
    
    # Check privacy settings
    if video.privacy == 'private' and video.uploader != request.user:
        return render(request, 'errors/403.html', status=403)
    
    if video.privacy == 'premium' and not request.user.is_premium():
        return render(request, 'content/premium_required.html', {'video': video})
    
    # Get related videos
    related_videos = Video.objects.filter(
        status='ready',
        privacy__in=['public', 'unlisted']
    ).exclude(id=video_id)
    
    if video.category:
        related_videos = related_videos.filter(category=video.category)
    
    related_videos = related_videos.order_by('-view_count')[:10]
    
    # Increment view count (simplified)
    video.view_count += 1
    video.save(update_fields=['view_count'])
    
    context = {
        'video': video,
        'related_videos': related_videos,
    }
    return render(request, 'streaming/watch.html', context)