"""
Context processors for user permissions and roles.
"""
from .permissions import get_user_permissions


def user_permissions(request):
    """
    Add user permissions to template context.
    Usage in templates: {% if perms.can_stream %}...{% endif %}
    """
    if request.user.is_authenticated:
        # Get unread notification count
        try:
            from apps.notifications.services import NotificationService
            unread_count = NotificationService.get_unread_count(request.user)
        except:
            unread_count = 0
        
        return {
            'perms': get_user_permissions(request.user),
            'user_role': request.user.role,
            'user_membership': request.user.membership,
            'unread_notification_count': unread_count,
        }
    return {
        'perms': {},
        'user_role': None,
        'user_membership': None,
        'unread_notification_count': 0,
    }


def role_badges(request):
    """
    Add role badge information for UI display.
    """
    role_badge_map = {
        'system_admin': {
            'class': 'badge bg-danger',
            'icon': 'bi-shield-fill-check',
            'text': 'システム管理者'
        },
        'tenant_admin': {
            'class': 'badge bg-warning',
            'icon': 'bi-person-fill-gear',
            'text': 'テナント管理者'
        },
        'tenant_user': {
            'class': 'badge bg-primary',
            'icon': 'bi-broadcast',
            'text': '配信者'
        },
        'subscriber': {
            'class': 'badge bg-secondary',
            'icon': 'bi-person-fill',
            'text': '登録者'
        }
    }
    
    membership_badge_map = {
        'premium': {
            'class': 'badge bg-gold',
            'icon': 'bi-star-fill',
            'text': 'プレミアム'
        },
        'free': {
            'class': 'badge bg-light text-dark',
            'icon': 'bi-person',
            'text': '無料'
        }
    }
    
    context = {
        'role_badges': role_badge_map,
        'membership_badges': membership_badge_map,
    }
    
    if request.user.is_authenticated:
        context.update({
            'current_role_badge': role_badge_map.get(request.user.role, {}),
            'current_membership_badge': membership_badge_map.get(request.user.membership, {}),
        })
    
    return context