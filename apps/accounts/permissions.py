"""
Permission decorators and utilities for role-based access control.
"""
from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(allowed_roles):
    """
    Decorator to check if user has one of the allowed roles.
    Usage: @role_required(['system_admin', 'tenant_admin'])
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if not request.user.role in allowed_roles:
                messages.error(request, 'この操作を実行する権限がありません。')
                return HttpResponseForbidden("権限がありません")
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def system_admin_required(view_func):
    """Decorator for system admin only views."""
    return role_required(['system_admin'])(view_func)


def tenant_admin_required(view_func):
    """Decorator for tenant admin and above views."""
    return role_required(['system_admin', 'tenant_admin'])(view_func)


def tenant_user_required(view_func):
    """Decorator for tenant user and above views."""
    return role_required(['system_admin', 'tenant_admin', 'tenant_user'])(view_func)


def streaming_permission_required(view_func):
    """Decorator to check streaming permissions."""
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not request.user.can_stream:
            messages.error(request, 'ストリーミング権限がありません。')
            return redirect('streaming:home')
        return view_func(request, *args, **kwargs)
    return wrapped_view


def premium_required(view_func):
    """Decorator for premium members only."""
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_premium():
            messages.error(request, 'プレミアム会員限定の機能です。')
            return redirect('accounts:profile')
        return view_func(request, *args, **kwargs)
    return wrapped_view


def content_management_required(view_func):
    """Decorator for content management permissions."""
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not request.user.can_manage_content():
            messages.error(request, 'コンテンツ管理権限がありません。')
            return HttpResponseForbidden("権限がありません")
        return view_func(request, *args, **kwargs)
    return wrapped_view


def user_management_required(view_func):
    """Decorator for user management permissions."""
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not request.user.can_manage_users():
            messages.error(request, 'ユーザー管理権限がありません。')
            return HttpResponseForbidden("権限がありません")
        return view_func(request, *args, **kwargs)
    return wrapped_view


class PermissionMixin:
    """
    Mixin for class-based views to check permissions.
    """
    required_roles = None
    require_streaming = False
    require_premium = False
    require_content_management = False
    require_user_management = False
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'ログインが必要です。')
            return redirect('accounts:login')
        
        # Role check
        if self.required_roles and request.user.role not in self.required_roles:
            messages.error(request, 'この操作を実行する権限がありません。')
            return HttpResponseForbidden("権限がありません")
        
        # Streaming permission check
        if self.require_streaming and not request.user.can_stream:
            messages.error(request, 'ストリーミング権限がありません。')
            return redirect('streaming:home')
        
        # Premium check
        if self.require_premium and not request.user.is_premium():
            messages.error(request, 'プレミアム会員限定の機能です。')
            return redirect('accounts:profile')
        
        # Content management check
        if self.require_content_management and not request.user.can_manage_content():
            messages.error(request, 'コンテンツ管理権限がありません。')
            return HttpResponseForbidden("権限がありません")
        
        # User management check
        if self.require_user_management and not request.user.can_manage_users():
            messages.error(request, 'ユーザー管理権限がありません。')
            return HttpResponseForbidden("権限がありません")
        
        return super().dispatch(request, *args, **kwargs)


def has_permission(user, permission_type, **kwargs):
    """
    General permission checker function.
    
    Args:
        user: User instance
        permission_type: Type of permission to check
        **kwargs: Additional parameters for specific permission checks
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    if not user.is_authenticated:
        return False
    
    permission_map = {
        'system_admin': user.is_system_admin(),
        'tenant_admin': user.is_tenant_admin() or user.is_system_admin(),
        'tenant_user': user.is_tenant_user() or user.is_tenant_admin() or user.is_system_admin(),
        'streaming': user.can_stream,
        'premium': user.is_premium(),
        'content_management': user.can_manage_content(),
        'user_management': user.can_manage_users(),
    }
    
    return permission_map.get(permission_type, False)


def get_user_permissions(user):
    """
    Get all permissions for a user.
    
    Args:
        user: User instance
    
    Returns:
        dict: Dictionary of permissions
    """
    if not user.is_authenticated:
        return {}
    
    return {
        'is_system_admin': user.is_system_admin(),
        'is_tenant_admin': user.is_tenant_admin(),
        'is_tenant_user': user.is_tenant_user(),
        'is_subscriber': user.is_subscriber(),
        'can_stream': user.can_stream,
        'is_premium': user.is_premium(),
        'can_manage_content': user.can_manage_content(),
        'can_manage_users': user.can_manage_users(),
        'role': user.role,
        'membership': user.membership,
    }