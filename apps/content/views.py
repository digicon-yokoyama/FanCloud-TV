from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.utils.text import slugify
from django.utils import timezone
from django.core.files.storage import default_storage
import uuid
import os
from .models import Video, VideoCategory, VideoTag, Comment, VideoLike
from apps.accounts.permissions import tenant_admin_required


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
    
    # Check if current user is following the uploader
    is_following = False
    user_like_status = None
    if request.user.is_authenticated:
        from apps.accounts.models import Follow
        is_following = Follow.objects.filter(
            follower=request.user,
            following=video.uploader
        ).exists()
        
        # Check user's like status
        try:
            like_obj = VideoLike.objects.get(video=video, user=request.user)
            user_like_status = 'like' if like_obj.is_like else 'dislike'
        except VideoLike.DoesNotExist:
            user_like_status = None
    
    # Get related videos
    related_videos = Video.objects.filter(
        status='ready',
        privacy__in=['public', 'unlisted']
    ).exclude(id=video_id)
    
    if video.category:
        related_videos = related_videos.filter(category=video.category)
    
    related_videos = related_videos.order_by('-view_count')[:10]
    
    # Get comments
    comments = Comment.objects.filter(
        video=video,
        parent=None,
        is_hidden=False
    ).prefetch_related('replies', 'user').order_by('-is_pinned', '-created_at')
    
    # Increment view count (simplified)
    video.view_count += 1
    video.save(update_fields=['view_count'])
    
    context = {
        'video': video,
        'related_videos': related_videos,
        'is_following': is_following,
        'user_like_status': user_like_status,
        'comments': comments,
    }
    return render(request, 'content/watch.html', context)


@login_required
def upload_video(request):
    """Video upload page."""
    if not request.user.can_stream:
        messages.error(request, '動画アップロード権限がありません')
        return redirect('streaming:home')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        privacy = request.POST.get('privacy', 'public')
        category_id = request.POST.get('category')
        tags_input = request.POST.get('tags', '').strip()
        
        if not title:
            messages.error(request, 'タイトルを入力してください')
            return render(request, 'content/upload.html', get_upload_context())
        
        # Skip file upload validation for now
        # Original file upload code is commented out
        """
        if 'video_file' not in request.FILES:
            messages.error(request, '動画ファイルを選択してください')
            return render(request, 'content/upload.html', get_upload_context())
        
        video_file = request.FILES['video_file']
        
        # Basic file validation
        if video_file.size > 500 * 1024 * 1024:  # 500MB limit
            messages.error(request, 'ファイルサイズが大きすぎます (上限: 500MB)')
            return render(request, 'content/upload.html', get_upload_context())
        """
        
        # Create clean video record without file
        try:
            video = Video.objects.create(
                title=title,
                description=description,
                uploader=request.user,
                privacy=privacy,
                status='ready',
                slug=generate_unique_slug(title),
                file_size=0,
                playback_url="",
                thumbnail_url="",
                duration=0,
                published_at=timezone.now()
            )
            
            # Set category if provided
            if category_id:
                try:
                    category = VideoCategory.objects.get(id=category_id, is_active=True)
                    video.category = category
                except VideoCategory.DoesNotExist:
                    pass
            
            # Save the video with thumbnail and category
            video.save()
            
            # Process and save tags
            if tags_input:
                tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
                for tag_name in tag_names:
                    tag, created = VideoTag.objects.get_or_create(name=tag_name)
                    video.tags.add(tag)
            
            # Send notifications to followers
            from apps.notifications.services import NotificationService
            NotificationService.notify_new_video(video)
            
            messages.success(request, '動画エントリが作成されました。')
            return redirect('content:manage_videos')
            
        except Exception as e:
            messages.error(request, f'動画エントリの作成に失敗しました: {str(e)}')
    
    return render(request, 'content/upload.html', get_upload_context())


def get_upload_context():
    """Get context for upload form."""
    return {
        'categories': VideoCategory.objects.filter(is_active=True),
        'max_file_size': 500,  # MB
        'supported_formats': ['mp4', 'mov', 'avi', 'mkv']
    }


def generate_unique_slug(title):
    """Generate unique slug for video."""
    base_slug = slugify(title)
    if not base_slug:
        base_slug = 'video'
    
    slug = base_slug
    counter = 1
    while Video.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug




@login_required
def manage_videos(request):
    """Manage user's uploaded videos."""
    videos = Video.objects.filter(uploader=request.user)
    
    # Search filter
    search_query = request.GET.get('search')
    if search_query:
        videos = videos.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        videos = videos.filter(status=status_filter)
    
    # Filter by category
    category_filter = request.GET.get('category')
    if category_filter and category_filter != 'all':
        try:
            category = VideoCategory.objects.get(id=category_filter, is_active=True)
            videos = videos.filter(category=category)
        except VideoCategory.DoesNotExist:
            pass
    
    # Sort order
    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = ['-created_at', 'created_at', '-view_count', 'title', '-duration']
    if sort_by in valid_sorts:
        videos = videos.order_by(sort_by)
    else:
        videos = videos.order_by('-created_at')
    
    paginator = Paginator(videos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_videos': videos.count(),
        'total_views': sum(v.view_count for v in videos),
        'total_likes': sum(v.like_count for v in videos),
        'processing': videos.filter(status='processing').count(),
    }
    
    context = {
        'videos': page_obj,
        'stats': stats,
        'search_query': search_query,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'sort_by': sort_by,
        'categories': VideoCategory.objects.filter(is_active=True),
    }
    return render(request, 'content/manage.html', context)


@login_required
def edit_video(request, video_id):
    """Edit video information."""
    video = get_object_or_404(Video, id=video_id, uploader=request.user)
    categories = VideoCategory.objects.filter(is_active=True)
    
    if request.method == 'POST':
        # Update video information
        video.title = request.POST.get('title', '').strip()
        video.description = request.POST.get('description', '').strip()
        video.privacy = request.POST.get('privacy', 'public')
        tags_input = request.POST.get('tags', '').strip()
        
        category_id = request.POST.get('category')
        if category_id:
            try:
                video.category = VideoCategory.objects.get(id=category_id, is_active=True)
            except VideoCategory.DoesNotExist:
                pass
        else:
            video.category = None
        
        # Validate title
        if not video.title:
            messages.error(request, 'タイトルは必須です。')
            return render(request, 'content/edit.html', {
                'video': video,
                'categories': categories
            })
        
        video.save()
        
        # Process and update tags
        video.tags.clear()  # Clear existing tags
        if tags_input:
            tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            for tag_name in tag_names:
                tag, created = VideoTag.objects.get_or_create(name=tag_name)
                video.tags.add(tag)
        
        messages.success(request, f'動画「{video.title}」の情報を更新しました。')
        return redirect('content:manage_videos')
    
    return render(request, 'content/edit.html', {
        'video': video,
        'categories': categories
    })


@login_required
@require_http_methods(["POST"])
def delete_video(request, video_id):
    """Delete user's video."""
    video = get_object_or_404(Video, id=video_id, uploader=request.user)
    video.delete()
    messages.success(request, f'「{video.title}」を削除しました')
    return redirect('content:manage_videos')


@require_http_methods(["GET"])
def video_processing_status(request, video_id):
    """API endpoint for video processing status."""
    try:
        video = Video.objects.get(id=video_id)
        return JsonResponse({
            'status': video.status,
            'progress': video.processing_progress,
            'ready': video.status == 'ready'
        })
    except Video.DoesNotExist:
        return JsonResponse({'error': 'Video not found'}, status=404)


@login_required
@require_POST
def like_video(request, video_id):
    """Like/dislike a video."""
    video = get_object_or_404(Video, id=video_id)
    action = request.POST.get('action')  # 'like' or 'dislike'
    
    if action not in ['like', 'dislike']:
        return JsonResponse({'error': 'Invalid action'}, status=400)
    
    is_like = action == 'like'
    
    try:
        # Check if user already liked/disliked
        existing_like = VideoLike.objects.get(video=video, user=request.user)
        
        if existing_like.is_like == is_like:
            # Remove the like/dislike
            existing_like.delete()
            if is_like:
                video.like_count = max(0, video.like_count - 1)
            else:
                video.dislike_count = max(0, video.dislike_count - 1)
            video.save()
            return JsonResponse({
                'status': 'removed',
                'like_count': video.like_count,
                'dislike_count': video.dislike_count
            })
        else:
            # Change like to dislike or vice versa
            if existing_like.is_like:
                video.like_count = max(0, video.like_count - 1)
                video.dislike_count += 1
            else:
                video.dislike_count = max(0, video.dislike_count - 1)
                video.like_count += 1
            
            existing_like.is_like = is_like
            existing_like.save()
            video.save()
            
            return JsonResponse({
                'status': 'changed',
                'action': action,
                'like_count': video.like_count,
                'dislike_count': video.dislike_count
            })
            
    except VideoLike.DoesNotExist:
        # Create new like/dislike
        video_like = VideoLike.objects.create(video=video, user=request.user, is_like=is_like)
        
        if is_like:
            video.like_count += 1
        else:
            video.dislike_count += 1
        video.save()
        
        # Send notification for likes
        if is_like:
            from apps.notifications.services import NotificationService
            NotificationService.notify_video_like(video_like)
        
        return JsonResponse({
            'status': 'added',
            'action': action,
            'like_count': video.like_count,
            'dislike_count': video.dislike_count
        })


@login_required
@require_POST
def add_comment(request, video_id):
    """Add a comment to a video."""
    video = get_object_or_404(Video, id=video_id)
    
    if not video.enable_comments:
        return JsonResponse({'error': 'Comments are disabled for this video'}, status=403)
    
    content = request.POST.get('content', '').strip()
    parent_id = request.POST.get('parent_id')
    
    if not content or len(content) > 1000:
        return JsonResponse({'error': 'Invalid comment content'}, status=400)
    
    parent = None
    if parent_id:
        try:
            parent = Comment.objects.get(id=parent_id, video=video)
        except Comment.DoesNotExist:
            return JsonResponse({'error': 'Parent comment not found'}, status=404)
    
    comment = Comment.objects.create(
        video=video,
        user=request.user,
        parent=parent,
        content=content
    )
    
    # Update comment count
    video.comment_count = video.comments.filter(is_hidden=False).count()
    video.save(update_fields=['comment_count'])
    
    # Send notifications
    from apps.notifications.services import NotificationService
    if parent:
        NotificationService.notify_comment_reply(comment)
    else:
        NotificationService.notify_new_comment(comment)
    
    return JsonResponse({
        'status': 'success',
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'user': comment.user.username,
            'created_at': comment.created_at.isoformat(),
            'is_reply': comment.is_reply
        },
        'comment_count': video.comment_count
    })


@login_required
@require_POST
def delete_comment(request, comment_id):
    """Delete a comment."""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Only allow comment owner or video owner to delete
    if request.user != comment.user and request.user != comment.video.uploader:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    video = comment.video
    comment.delete()
    
    # Update comment count
    video.comment_count = video.comments.filter(is_hidden=False).count()
    video.save(update_fields=['comment_count'])
    
    return JsonResponse({
        'status': 'success',
        'comment_count': video.comment_count
    })


def search_videos(request):
    """Search videos with advanced filters and tags."""
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    sort_by = request.GET.get('sort', 'relevance')
    duration_filter = request.GET.get('duration', 'any')
    upload_date = request.GET.get('upload_date', 'any')
    tags_query = request.GET.get('tags', '').strip()
    
    # Base queryset
    videos = Video.objects.filter(
        status='ready',
        privacy__in=['public', 'unlisted']
    ).select_related('uploader', 'category').prefetch_related('tags')
    
    # Search by title, description, and uploader
    if query:
        videos = videos.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(uploader__username__icontains=query)
        )
    
    # Search by tags
    if tags_query:
        tag_names = [tag.strip() for tag in tags_query.split(',') if tag.strip()]
        if tag_names:
            # Search for videos that have any of the specified tags
            videos = videos.filter(tags__name__in=tag_names).distinct()
    
    # Filter by category
    if category_id and category_id != 'all':
        try:
            category = VideoCategory.objects.get(id=category_id, is_active=True)
            videos = videos.filter(category=category)
        except VideoCategory.DoesNotExist:
            pass
    
    # Filter by duration
    if duration_filter == 'short':  # Under 4 minutes
        videos = videos.filter(duration__lt=240)
    elif duration_filter == 'medium':  # 4-20 minutes
        videos = videos.filter(duration__gte=240, duration__lte=1200)
    elif duration_filter == 'long':  # Over 20 minutes
        videos = videos.filter(duration__gt=1200)
    
    # Filter by upload date
    if upload_date != 'any':
        from datetime import datetime, timedelta
        now = timezone.now()
        
        if upload_date == 'hour':
            date_cutoff = now - timedelta(hours=1)
        elif upload_date == 'today':
            date_cutoff = now - timedelta(days=1)
        elif upload_date == 'week':
            date_cutoff = now - timedelta(weeks=1)
        elif upload_date == 'month':
            date_cutoff = now - timedelta(days=30)
        elif upload_date == 'year':
            date_cutoff = now - timedelta(days=365)
        else:
            date_cutoff = None
        
        if date_cutoff:
            videos = videos.filter(published_at__gte=date_cutoff)
    
    # Sort results
    if sort_by == 'date':
        videos = videos.order_by('-published_at')
    elif sort_by == 'views':
        videos = videos.order_by('-view_count')
    elif sort_by == 'rating':
        videos = videos.order_by('-like_count')
    elif sort_by == 'duration':
        videos = videos.order_by('-duration')
    else:  # relevance (default)
        if query or tags_query:
            # Enhanced relevance scoring
            videos = videos.extra(
                select={
                    'title_match': "CASE WHEN title ILIKE %s THEN 2 ELSE 0 END",
                    'desc_match': "CASE WHEN description ILIKE %s THEN 1 ELSE 0 END",
                    'tag_match': "CASE WHEN EXISTS(SELECT 1 FROM content_videotag vt JOIN content_video_tags vvt ON vt.id = vvt.videotag_id WHERE vvt.video_id = content_video.id AND vt.name ILIKE %s) THEN 3 ELSE 0 END"
                },
                select_params=[
                    f'%{query}%' if query else '', 
                    f'%{query}%' if query else '',
                    f'%{tags_query}%' if tags_query else ''
                ],
                order_by=['-tag_match', '-title_match', '-desc_match', '-view_count']
            )
        else:
            videos = videos.order_by('-view_count')
    
    # Pagination
    paginator = Paginator(videos, 20)  # Increased page size for better search results
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter
    categories = VideoCategory.objects.filter(is_active=True)
    
    # Get popular tags for suggestions
    popular_tags = VideoTag.objects.annotate(
        video_count=Count('videos')
    ).filter(video_count__gt=0).order_by('-video_count')[:20]
    
    context = {
        'videos': page_obj,
        'categories': categories,
        'popular_tags': popular_tags,
        'search_query': query,
        'tags_query': tags_query,
        'current_category': category_id,
        'current_sort': sort_by,
        'current_duration': duration_filter,
        'current_upload_date': upload_date,
        'total_results': paginator.count,
    }
    
    return render(request, 'content/search.html', context)


@login_required
def history(request):
    """User's viewing history."""
    # Placeholder for viewing history - would need to implement WatchHistory model
    context = {
        'videos': [],
        'title': '視聴履歴',
        'empty_message': '視聴履歴はありません'
    }
    return render(request, 'content/library_page.html', context)


@login_required 
def favorites(request):
    """User's favorite videos."""
    # Get liked videos as favorites
    liked_videos = Video.objects.filter(
        likes__user=request.user,
        likes__is_like=True,
        status='ready'
    ).order_by('-likes__created_at')
    
    paginator = Paginator(liked_videos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'videos': page_obj,
        'title': 'お気に入り',
        'empty_message': 'お気に入りの動画はありません'
    }
    return render(request, 'content/library_page.html', context)


@login_required
def playlists(request):
    """User's playlists."""
    # Placeholder for playlists - would need to implement Playlist model
    context = {
        'playlists': [],
        'title': 'プレイリスト',
        'empty_message': 'プレイリストはありません'
    }
    return render(request, 'content/playlists.html', context)


# Category Management Views (Admin only)

@tenant_admin_required
def manage_categories(request):
    """Manage video categories (Admin only)."""
    categories = VideoCategory.objects.all().order_by('name')
    
    # Statistics
    stats = {
        'total_categories': categories.count(),
        'active_categories': categories.filter(is_active=True).count(),
        'inactive_categories': categories.filter(is_active=False).count(),
    }
    
    context = {
        'categories': categories,
        'stats': stats,
    }
    return render(request, 'content/admin/categories.html', context)


@tenant_admin_required
def create_category(request):
    """Create new video category (Admin only)."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        color = request.POST.get('color', '#6c757d')
        is_active = request.POST.get('is_active') == 'on'
        
        # Validate name
        if not name:
            messages.error(request, 'カテゴリ名は必須です。')
            return render(request, 'content/admin/category_form.html', {
                'form_data': request.POST,
            })
        
        # Check if category name already exists
        if VideoCategory.objects.filter(name=name).exists():
            messages.error(request, 'このカテゴリ名は既に存在します。')
            return render(request, 'content/admin/category_form.html', {
                'form_data': request.POST,
            })
        
        # Create category
        VideoCategory.objects.create(
            name=name,
            description=description,
            color=color,
            is_active=is_active
        )
        
        messages.success(request, f'カテゴリ「{name}」を作成しました。')
        return redirect('content:admin_categories')
    
    return render(request, 'content/admin/category_form.html', {
        'action': '作成',
    })


@tenant_admin_required
def edit_category(request, category_id):
    """Edit video category (Admin only)."""
    category = get_object_or_404(VideoCategory, id=category_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        color = request.POST.get('color', '#6c757d')
        is_active = request.POST.get('is_active') == 'on'
        
        # Validate name
        if not name:
            messages.error(request, 'カテゴリ名は必須です。')
            return render(request, 'content/admin/category_form.html', {
                'category': category,
                'form_data': request.POST,
            })
        
        # Check if category name already exists (excluding current category)
        if VideoCategory.objects.filter(name=name).exclude(id=category_id).exists():
            messages.error(request, 'このカテゴリ名は既に存在します。')
            return render(request, 'content/admin/category_form.html', {
                'category': category,
                'form_data': request.POST,
            })
        
        # Update category
        category.name = name
        category.description = description
        category.color = color
        category.is_active = is_active
        category.save()
        
        messages.success(request, f'カテゴリ「{name}」を更新しました。')
        return redirect('content:admin_categories')
    
    return render(request, 'content/admin/category_form.html', {
        'category': category,
        'action': '編集',
    })


@tenant_admin_required
@require_http_methods(["POST"])
def delete_category(request, category_id):
    """Delete video category (Admin only)."""
    category = get_object_or_404(VideoCategory, id=category_id)
    
    # Check if category is being used by any videos
    videos_count = Video.objects.filter(category=category).count()
    if videos_count > 0:
        messages.error(request, f'このカテゴリは{videos_count}個の動画で使用されているため削除できません。')
        return redirect('content:admin_categories')
    
    category_name = category.name
    category.delete()
    messages.success(request, f'カテゴリ「{category_name}」を削除しました。')
    return redirect('content:admin_categories')