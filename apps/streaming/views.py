from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse

from apps.accounts.permissions import streaming_permission_required
from .models import Stream, StreamCategory
from .services import StreamingService, validate_stream_settings
from apps.content.models import Video
import json
import uuid


def home(request):
    """Homepage with live streams and recent videos."""
    # Get live streams
    live_streams = Stream.objects.filter(status='live', privacy='public')[:10]
    
    # Get trending videos
    trending_videos = Video.objects.filter(
        status='ready',
        privacy__in=['public', 'unlisted']
    ).order_by('-view_count')[:10]
    
    # Get recent videos
    recent_videos = Video.objects.filter(
        status='ready',
        privacy__in=['public', 'unlisted']
    ).order_by('-published_at')[:10]
    
    # Get subscription videos for authenticated users
    subscription_videos = []
    if request.user.is_authenticated:
        from apps.accounts.models import Follow
        following_users = Follow.objects.filter(follower=request.user).values_list('following', flat=True)
        subscription_videos = Video.objects.filter(
            uploader__in=following_users,
            status='ready',
            privacy__in=['public', 'unlisted']
        ).order_by('-published_at')[:10]
    
    # Get recommended videos based on user preferences
    videos_base = Video.objects.filter(
        status='ready',
        privacy__in=['public', 'unlisted']
    )
    recommended_videos = get_recommended_videos(request.user, videos_base)[:10]
    
    context = {
        'live_streams': live_streams,
        'trending_videos': trending_videos,
        'recent_videos': recent_videos,
        'subscription_videos': subscription_videos,
        'recommended_videos': recommended_videos,
    }
    return render(request, 'streaming/home.html', context)


def get_recommended_videos(user, videos_base):
    """Get recommended videos based on user preferences and viewing history."""
    if not user.is_authenticated:
        # For anonymous users, return popular videos from different categories
        return videos_base.order_by('-view_count', '-like_count')
    
    # For authenticated users, use simple recommendation logic
    recommended = videos_base.exclude(uploader=user)
    
    # Get user's liked video categories
    from apps.content.models import VideoLike
    liked_categories = VideoLike.objects.filter(
        user=user, 
        is_like=True
    ).values_list('video__category', flat=True).distinct()
    
    if liked_categories:
        # Prioritize videos from liked categories
        category_videos = recommended.filter(category__in=liked_categories)
        other_videos = recommended.exclude(category__in=liked_categories)
        
        # Mix category-based and popular videos
        recommended_list = list(category_videos.order_by('-view_count')[:6])
        recommended_list.extend(list(other_videos.order_by('-view_count')[:4]))
        
        return recommended_list
    else:
        # Fallback to popular videos
        return recommended.order_by('-view_count', '-like_count')


def live_streams(request):
    """Live streams page."""
    streams = Stream.objects.filter(status='live', privacy='public').order_by('-started_at')
    
    paginator = Paginator(streams, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'streams': page_obj,
    }
    return render(request, 'streaming/live.html', context)


def watch_stream(request, stream_id):
    """Watch live stream page."""
    # Get stream from database first (authoritative source)
    stream = get_object_or_404(Stream, stream_id=stream_id)
    
    # Create stream data from database
    stream_data = {
        'stream_id': stream.stream_id,
        'title': stream.title,
        'description': stream.description,
        'playback_url': stream.playback_url,
        'thumbnail_url': stream.thumbnail_url,
        'status': stream.status,
        'viewer_count': stream.viewer_count,
        'uploader': stream.streamer,
        'enable_chat': stream.enable_chat,
        'is_live': stream.status == 'live'
    }
    
    # Get related streams
    related_streams = Stream.objects.filter(
        status='live',
        privacy='public'
    ).exclude(stream_id=stream_id)[:10]
    
    context = {
        'video': stream_data,
        'related_videos': related_streams,
        'user': request.user,  # ユーザー認証情報を追加
        'show_chat': True,  # チャット表示フラグを追加
    }
    return render(request, 'streaming/watch.html', context)


@streaming_permission_required
def create_stream(request):
    """Create new live stream."""
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        privacy = request.POST.get('privacy', 'public')
        category_id = request.POST.get('category')
        quality = request.POST.get('quality', '720p')
        bitrate = request.POST.get('bitrate', '2500')
        framerate = int(request.POST.get('framerate', '30'))
        
        # Validate settings
        is_valid, error_message = validate_stream_settings(quality, bitrate, framerate)
        if not is_valid:
            messages.error(request, error_message)
            return redirect('streaming:create')
        
        # Get category
        category = None
        if category_id:
            try:
                category = StreamCategory.objects.get(id=category_id)
            except StreamCategory.DoesNotExist:
                pass
        
        # Generate stream ID and key
        stream_id = str(uuid.uuid4())
        stream_key = str(uuid.uuid4())
        
        # Create stream using service
        streaming_service = StreamingService()
        stream_data = streaming_service.create_stream({
            'stream_id': stream_id,
            'title': title,
            'description': description,
            'quality': quality,
            'bitrate': bitrate,
            'framerate': framerate,
        })
        
        # Save to database
        stream = Stream.objects.create(
            title=title,
            description=description,
            streamer=request.user,
            stream_id=stream_id,
            stream_key=stream_key,
            ingest_url=stream_data['ingest_url'],
            playback_url=stream_data['playback_url'],
            privacy=privacy,
            category=category,
            quality=quality,
            bitrate=bitrate,
            framerate=framerate,
            is_recording=request.POST.get('is_recording') == 'on',
            enable_chat=request.POST.get('enable_chat') == 'on',
            subscriber_only_chat=request.POST.get('subscriber_only_chat') == 'on',
            enable_donations=request.POST.get('enable_donations') == 'on',
            mature_content=request.POST.get('mature_content') == 'on',
        )
        
        messages.success(request, '配信が作成されました！配信を開始してください。')
        return redirect('streaming:stream_dashboard', stream_id=stream.stream_id)
    
    # Get available categories
    categories = StreamCategory.objects.filter(is_active=True)
    
    context = {
        'categories': categories,
    }
    return render(request, 'streaming/create.html', context)


def embed_player(request, stream_id):
    """Embedded player for iframe."""
    # Get stream data
    streaming_service = StreamingService()
    stream_data = streaming_service.get_stream_status(stream_id)
    
    if 'error' in stream_data:
        try:
            stream = Stream.objects.get(stream_id=stream_id)
            stream_data = {
                'stream_id': stream.stream_id,
                'title': stream.title,
                'playback_url': stream.playback_url,
                'thumbnail_url': stream.thumbnail_url,
                'uploader': stream.streamer,
                'viewer_count': stream.viewer_count,
                'enable_chat': stream.enable_chat,
                'is_live': stream.status == 'live'
            }
        except Stream.DoesNotExist:
            stream_data = {
                'title': 'Stream not found',
                'playback_url': '',
                'is_live': False
            }
    
    # Check if chat should be shown
    show_chat = request.GET.get('chat', '0') == '1'
    
    context = {
        'video': stream_data,
        'show_chat': show_chat,
        'user': request.user,  # ユーザー認証情報を追加
    }
    return render(request, 'embed/player.html', context)


class StreamAPIView(View):
    """API endpoints for stream management."""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """Handle stream actions."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        data = json.loads(request.body)
        action = data.get('action')
        stream_id = data.get('stream_id')
        
        if action == 'start':
            # Start streaming
            streaming_service = StreamingService()
            result = streaming_service.start_stream({'stream_id': stream_id})
            if 'error' not in result:
                Stream.objects.filter(stream_id=stream_id).update(
                    status='live',
                    viewer_count=result.get('viewer_count', 0)
                )
            return JsonResponse(result)
        
        elif action == 'stop':
            # Stop streaming
            from django.utils import timezone
            streaming_service = StreamingService()
            result = streaming_service.end_stream(stream_id)
            if 'error' not in result:
                Stream.objects.filter(stream_id=stream_id).update(
                    status='ended',
                    ended_at=timezone.now()
                )
            return JsonResponse(result)
        
        return JsonResponse({'error': 'Invalid action'}, status=400)


@streaming_permission_required
def stream_dashboard(request, stream_id):
    """Stream management dashboard."""
    stream = get_object_or_404(Stream, stream_id=stream_id, streamer=request.user)
    
    context = {
        'stream': stream,
        'stream_key': stream.stream_key,
        'ingest_url': stream.ingest_url,
        'playback_url': stream.playback_url,
    }
    return render(request, 'streaming/dashboard.html', context)


@streaming_permission_required
@require_http_methods(["POST"])
def start_stream(request, stream_id):
    """Start a live stream."""
    stream = get_object_or_404(Stream, stream_id=stream_id, streamer=request.user)
    
    if not stream.can_start:
        messages.error(request, '配信を開始できません。配信状態を確認してください。')
        return redirect('streaming:stream_dashboard', stream_id=stream_id)
    
    try:
        stream.start_stream()
        messages.success(request, '配信を開始しました！')
    except Exception as e:
        messages.error(request, f'配信開始に失敗しました: {str(e)}')
    
    return redirect('streaming:stream_dashboard', stream_id=stream_id)


@streaming_permission_required
@require_http_methods(["POST"])
def end_stream(request, stream_id):
    """End a live stream."""
    stream = get_object_or_404(Stream, stream_id=stream_id, streamer=request.user)
    
    if not stream.can_end:
        messages.error(request, '配信を終了できません。配信状態を確認してください。')
        return redirect('streaming:stream_dashboard', stream_id=stream_id)
    
    try:
        stream.end_stream()
        messages.success(request, '配信を終了しました。')
        # 配信一覧ページにリダイレクト（終了後はダッシュボードよりも一覧が見やすい）
        return redirect('streaming:my_streams')
    except Exception as e:
        messages.error(request, f'配信終了に失敗しました: {str(e)}')
        return redirect('streaming:stream_dashboard', stream_id=stream_id)


@streaming_permission_required
def my_streams(request):
    """List user's streams."""
    streams = Stream.objects.filter(streamer=request.user).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        streams = streams.filter(status=status_filter)
    
    paginator = Paginator(streams, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_streams': Stream.objects.filter(streamer=request.user).count(),
        'live_streams': Stream.objects.filter(streamer=request.user, status='live').count(),
        'total_views': sum(stream.total_views for stream in Stream.objects.filter(streamer=request.user)),
        'avg_viewers': 0,  # TODO: Calculate average viewers
    }
    
    context = {
        'streams': page_obj,
        'stats': stats,
        'status_filter': status_filter,
    }
    return render(request, 'streaming/my_streams.html', context)


@streaming_permission_required
@require_http_methods(["POST"])
def delete_stream(request, stream_id):
    """Delete a stream."""
    stream = get_object_or_404(Stream, stream_id=stream_id, streamer=request.user)
    
    # Only allow deletion of ended or error streams
    if stream.status not in ['ended', 'error']:
        messages.error(request, 'ライブ中または作成済みの配信は削除できません。')
        return redirect('streaming:my_streams')
    
    stream_title = stream.title
    stream.delete()
    messages.success(request, f'配信「{stream_title}」を削除しました。')
    return redirect('streaming:my_streams')


@streaming_permission_required
@require_http_methods(["POST"])
def update_stream_settings(request, stream_id):
    """Update stream settings."""
    stream = get_object_or_404(Stream, stream_id=stream_id, streamer=request.user)
    
    if stream.status == 'live':
        messages.error(request, 'ライブ配信中は設定を変更できません。')
        return redirect('streaming:stream_dashboard', stream_id=stream_id)
    
    # Update settings
    stream.title = request.POST.get('title', stream.title)
    stream.description = request.POST.get('description', stream.description)
    stream.privacy = request.POST.get('privacy', stream.privacy)
    
    # Quality settings
    quality = request.POST.get('quality', stream.quality)
    bitrate = request.POST.get('bitrate', stream.bitrate)
    framerate = int(request.POST.get('framerate', stream.framerate))
    
    # Validate settings
    is_valid, error_message = validate_stream_settings(quality, bitrate, framerate)
    if not is_valid:
        messages.error(request, error_message)
        return redirect('streaming:stream_dashboard', stream_id=stream_id)
    
    stream.quality = quality
    stream.bitrate = bitrate
    stream.framerate = framerate
    
    # Other settings
    stream.is_recording = request.POST.get('is_recording') == 'on'
    stream.enable_chat = request.POST.get('enable_chat') == 'on'
    stream.subscriber_only_chat = request.POST.get('subscriber_only_chat') == 'on'
    stream.enable_donations = request.POST.get('enable_donations') == 'on'
    stream.mature_content = request.POST.get('mature_content') == 'on'
    
    stream.save()
    messages.success(request, '配信設定を更新しました。')
    return redirect('streaming:stream_dashboard', stream_id=stream_id)


@require_http_methods(["GET"])
def stream_status_api(request, stream_id):
    """API endpoint to get stream status."""
    try:
        stream = Stream.objects.get(stream_id=stream_id)
        
        # Get real-time data from streaming service
        streaming_service = StreamingService()
        service_status = streaming_service.get_stream_status(stream_id)
        viewer_count_data = streaming_service.get_viewer_count(stream_id)
        
        # Update viewer count
        if 'current_viewers' in viewer_count_data:
            stream.update_viewer_count(viewer_count_data['current_viewers'])
        
        return JsonResponse({
            'stream_id': stream.stream_id,
            'status': stream.status,
            'title': stream.title,
            'viewer_count': stream.viewer_count,
            'peak_viewers': stream.peak_viewers,
            'total_views': stream.total_views,
            'uptime': service_status.get('uptime', 0),
            'health': service_status.get('health', 'unknown'),
            'is_live': stream.is_live,
            'started_at': stream.started_at.isoformat() if stream.started_at else None,
        })
        
    except Stream.DoesNotExist:
        return JsonResponse({'error': 'Stream not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def debug_user_auth(request):
    """Debug endpoint for user authentication status."""
    return JsonResponse({
        'is_authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else None,
        'user_id': request.user.id if request.user.is_authenticated else None,
        'session_key': request.session.session_key,
        'user_agent': request.META.get('HTTP_USER_AGENT'),
        'has_session': bool(request.session.items()),
    })


def obs_overlay(request, stream_id, token):
    """OBS用チャットオーバーレイ画面"""
    # ストリームとトークンの認証
    try:
        stream = Stream.objects.get(stream_id=stream_id, obs_overlay_token=token)
        
        # ライブ中でない場合は警告（ただし表示は継続）
        if not stream.is_live:
            pass  # 配信準備中でも表示可能にする
            
    except Stream.DoesNotExist:
        return JsonResponse({'error': '無効なストリームまたはトークンです'}, status=404)
    
    context = {
        'stream': stream,
    }
    return render(request, 'obs/overlay.html', context)


@streaming_permission_required
def generate_obs_token(request, stream_id):
    """OBS用オーバーレイトークンを生成/再生成"""
    stream = get_object_or_404(Stream, stream_id=stream_id, streamer=request.user)
    
    if request.method == 'POST':
        # トークン生成/再生成
        new_token = stream.generate_obs_overlay_token()
        obs_url = stream.get_obs_overlay_url(request)
        
        return JsonResponse({
            'success': True,
            'token': new_token,
            'obs_url': obs_url,
            'message': 'OBS用URLを生成しました'
        })
    
    # GET: 現在のトークン情報を取得
    obs_url = stream.get_obs_overlay_url(request) if stream.obs_overlay_token else None
    
    return JsonResponse({
        'has_token': bool(stream.obs_overlay_token),
        'obs_url': obs_url
    })