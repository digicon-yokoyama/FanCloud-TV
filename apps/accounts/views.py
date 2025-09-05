from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import User, UserProfile, Follow
from django import forms


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('streaming:home')


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('streaming:home')
    http_method_names = ['get', 'post', 'options']
    
    def get(self, request, *args, **kwargs):
        """Allow GET requests for logout."""
        return self.post(request, *args, **kwargs)


class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label='パスワード', widget=forms.PasswordInput)
    password2 = forms.CharField(label='パスワード確認', widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        labels = {
            'username': 'ユーザー名',
            'email': 'メールアドレス',
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("パスワードが一致しません")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            # Create user profile
            UserProfile.objects.create(user=user)
        return user


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('streaming:home')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance
        user = authenticate(
            username=user.username,
            password=form.cleaned_data['password1']
        )
        login(self.request, user)
        messages.success(self.request, 'アカウントが作成されました！')
        return response


@login_required
def profile(request):
    """User profile page."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Handle profile update from modal form
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.save()
        
        profile.bio = request.POST.get('bio', profile.bio)
        profile.website = request.POST.get('website', profile.website)
        profile.save()
        
        messages.success(request, 'プロフィールが更新されました')
        return redirect('accounts:profile')
    
    # Get user's videos and playlists
    from apps.content.models import Video, Playlist
    user_videos = Video.objects.filter(
        uploader=request.user,
        status='ready'
    ).order_by('-published_at')[:6]  # Latest 6 videos
    
    user_playlists = Playlist.objects.filter(
        owner=request.user
    ).order_by('-updated_at')[:6]  # Latest 6 playlists
    
    context = {
        'profile': profile,
        'user_videos': user_videos,
        'user_playlists': user_playlists,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def settings(request):
    """User settings page."""
    if request.method == 'POST':
        # Handle settings update
        user = request.user
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.save()
        
        profile = user.profile
        profile.bio = request.POST.get('bio', profile.bio)
        profile.website = request.POST.get('website', profile.website)
        profile.twitter = request.POST.get('twitter', profile.twitter)
        profile.youtube = request.POST.get('youtube', profile.youtube)
        profile.save()
        
        messages.success(request, '設定が更新されました')
        return redirect('accounts:settings')
    
    context = {
        'user': request.user,
        'profile': getattr(request.user, 'profile', None),
    }
    return render(request, 'accounts/settings.html', context)


@login_required
@require_POST
def follow_user(request, user_id):
    """Follow/unfollow a user."""
    target_user = get_object_or_404(User, id=user_id)
    
    if target_user == request.user:
        return JsonResponse({'error': '自分をフォローすることはできません'}, status=400)
    
    follow_instance, created = Follow.objects.get_or_create(
        follower=request.user,
        following=target_user
    )
    
    if created:
        # Update follower counts
        request.user.profile.following_count += 1
        request.user.profile.save()
        
        target_user.profile.followers_count += 1
        target_user.profile.save()
        
        # Send notification
        from apps.notifications.services import NotificationService
        NotificationService.notify_new_follower(request.user, target_user)
        
        return JsonResponse({
            'status': 'followed',
            'message': f'{target_user.username}をフォローしました',
            'followers_count': target_user.profile.followers_count
        })
    else:
        # Unfollow
        follow_instance.delete()
        
        # Update follower counts
        request.user.profile.following_count -= 1
        request.user.profile.save()
        
        target_user.profile.followers_count -= 1
        target_user.profile.save()
        
        return JsonResponse({
            'status': 'unfollowed',
            'message': f'{target_user.username}のフォローを解除しました',
            'followers_count': target_user.profile.followers_count
        })


def user_channel(request, username):
    """User channel page."""
    user = get_object_or_404(User, username=username)
    profile = user.profile
    
    # Check if current user is following this channel
    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=user
        ).exists()
    
    # Get user's videos
    from apps.content.models import Video
    from apps.streaming.models import Stream
    
    videos = Video.objects.filter(
        uploader=user,
        status='ready',
        privacy__in=['public', 'unlisted']
    ).order_by('-published_at')
    
    # Get user's streams (if they can stream)
    streams = None
    if user.can_stream:
        streams = Stream.objects.filter(
            streamer=user
        ).order_by('-created_at')[:5]
    
    # Pagination for videos
    paginator = Paginator(videos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'channel_user': user,
        'profile': profile,
        'is_following': is_following,
        'videos': page_obj,
        'recent_streams': streams,
        'stats': {
            'total_videos': videos.count(),
            'followers_count': profile.followers_count,
            'following_count': profile.following_count,
            'total_views': profile.total_views,
        }
    }
    return render(request, 'accounts/channel.html', context)


@login_required
def following_list(request):
    """List of users that current user is following."""
    following = Follow.objects.filter(
        follower=request.user
    ).select_related('following', 'following__profile').order_by('-created_at')
    
    paginator = Paginator(following, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'following': page_obj,
        'title': 'フォロー中'
    }
    return render(request, 'accounts/follow_list.html', context)


@login_required
def followers_list(request):
    """List of users that follow current user."""
    followers = Follow.objects.filter(
        following=request.user
    ).select_related('follower', 'follower__profile').order_by('-created_at')
    
    paginator = Paginator(followers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'followers': page_obj,
        'title': 'フォロワー'
    }
    return render(request, 'accounts/follow_list.html', context)