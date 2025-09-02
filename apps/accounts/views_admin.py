"""
Admin views for user and role management.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

from .models import User, UserProfile, Follow
from .permissions import user_management_required, system_admin_required


@user_management_required
def user_management(request):
    """User management dashboard."""
    # Get filter parameters
    role_filter = request.GET.get('role', '')
    membership_filter = request.GET.get('membership', '')
    search_query = request.GET.get('q', '')
    
    # Build queryset
    users = User.objects.select_related('profile').annotate(
        followers_count=Count('followers'),
        following_count=Count('following')
    )
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    if membership_filter:
        users = users.filter(membership=membership_filter)
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_users': User.objects.count(),
        'system_admins': User.objects.filter(role='system_admin').count(),
        'tenant_admins': User.objects.filter(role='tenant_admin').count(),
        'tenant_users': User.objects.filter(role='tenant_user').count(),
        'subscribers': User.objects.filter(role='subscriber').count(),
        'premium_users': User.objects.filter(membership='premium').count(),
        'streamers': User.objects.filter(can_stream=True).count(),
    }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'role_filter': role_filter,
        'membership_filter': membership_filter,
        'search_query': search_query,
        'role_choices': User.ROLE_CHOICES,
        'membership_choices': User.MEMBERSHIP_CHOICES,
    }
    
    return render(request, 'accounts/admin/user_management.html', context)


@user_management_required
def user_detail(request, user_id):
    """User detail view for admins."""
    user = get_object_or_404(User, id=user_id)
    profile = getattr(user, 'profile', None)
    
    # Get user statistics
    followers = user.followers.select_related('follower')[:10]
    following = user.following.select_related('following')[:10]
    
    context = {
        'target_user': user,
        'profile': profile,
        'recent_followers': followers,
        'recent_following': following,
    }
    
    return render(request, 'accounts/admin/user_detail.html', context)


@user_management_required
@require_http_methods(["POST"])
def update_user_role(request):
    """Update user role via AJAX."""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        new_role = data.get('role')
        
        if new_role not in [choice[0] for choice in User.ROLE_CHOICES]:
            return JsonResponse({'success': False, 'error': '無効なロールです'})
        
        user = get_object_or_404(User, id=user_id)
        
        # System admin can only be changed by system admin
        if (user.role == 'system_admin' or new_role == 'system_admin') and not request.user.is_system_admin():
            return JsonResponse({'success': False, 'error': 'システム管理者のロールを変更する権限がありません'})
        
        old_role = user.get_role_display()
        user.role = new_role
        user.save()
        
        messages.success(request, f'{user.username}のロールを{old_role}から{user.get_role_display()}に変更しました。')
        
        return JsonResponse({
            'success': True,
            'message': f'ロールを{user.get_role_display()}に変更しました',
            'new_role': user.get_role_display()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@user_management_required
@require_http_methods(["POST"])
def toggle_streaming_permission(request):
    """Toggle streaming permission for a user."""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        user = get_object_or_404(User, id=user_id)
        user.can_stream = not user.can_stream
        user.save()
        
        action = "付与" if user.can_stream else "取り消し"
        messages.success(request, f'{user.username}のストリーミング権限を{action}しました。')
        
        return JsonResponse({
            'success': True,
            'can_stream': user.can_stream,
            'message': f'ストリーミング権限を{action}しました'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@user_management_required
@require_http_methods(["POST"])
def update_membership(request):
    """Update user membership."""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        new_membership = data.get('membership')
        
        if new_membership not in [choice[0] for choice in User.MEMBERSHIP_CHOICES]:
            return JsonResponse({'success': False, 'error': '無効なメンバーシップです'})
        
        user = get_object_or_404(User, id=user_id)
        old_membership = user.get_membership_display()
        user.membership = new_membership
        user.save()
        
        messages.success(request, f'{user.username}のメンバーシップを{old_membership}から{user.get_membership_display()}に変更しました。')
        
        return JsonResponse({
            'success': True,
            'message': f'メンバーシップを{user.get_membership_display()}に変更しました',
            'new_membership': user.get_membership_display()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@system_admin_required
def system_dashboard(request):
    """System admin dashboard."""
    # Overall statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    
    # Role distribution
    role_stats = {}
    for role_code, role_name in User.ROLE_CHOICES:
        role_stats[role_name] = User.objects.filter(role=role_code).count()
    
    # Membership distribution
    membership_stats = {}
    for membership_code, membership_name in User.MEMBERSHIP_CHOICES:
        membership_stats[membership_name] = User.objects.filter(membership=membership_code).count()
    
    # Recent registrations
    recent_users = User.objects.order_by('-date_joined')[:10]
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'role_stats': role_stats,
        'membership_stats': membership_stats,
        'recent_users': recent_users,
    }
    
    return render(request, 'accounts/admin/system_dashboard.html', context)