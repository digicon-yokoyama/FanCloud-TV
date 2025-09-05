from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape

register = template.Library()


@register.simple_tag
def user_avatar(user, size=48, css_classes=""):
    """
    統一されたユーザーアバター表示タグ
    
    使用例:
    {% load avatar_tags %}
    {% user_avatar user 80 "rounded-circle" %}
    """
    try:
        size = int(size)  # サイズを整数に変換
        if hasattr(user, 'avatar') and user.avatar:
            # ユーザーがアバター画像をアップロードしている場合
            return mark_safe(
                f'<img src="{escape(user.avatar.url)}" '
                f'alt="{escape(user.username)}" '
                f'class="{escape(css_classes)}" '
                f'style="width: {size}px; height: {size}px; object-fit: cover;">'
            )
        else:
            # フォールバック: アイコン表示
            icon_size = size // 2
            return mark_safe(
                f'<div class="bg-light d-flex align-items-center justify-content-center {escape(css_classes)}" '
                f'style="width: {size}px; height: {size}px;">'
                f'<i class="bi bi-person-fill text-muted" style="font-size: {icon_size}px;"></i>'
                f'</div>'
            )
    except (ValueError, AttributeError) as e:
        # エラー時のフォールバック
        return mark_safe('<div class="bg-light rounded" style="width: 48px; height: 48px;"></div>')


@register.simple_tag  
def user_avatar_fallback(user, size=48, css_classes=""):
    """
    外部サービスを使用したフォールバックアバター（現在の実装との互換性用）
    将来的に削除予定
    """
    if hasattr(user, 'avatar') and user.avatar:
        return mark_safe(f'''
            <img src="{user.avatar.url}" 
                 alt="{user.username}" 
                 class="{css_classes}"
                 style="width: {size}px; height: {size}px; object-fit: cover;">
        ''')
    else:
        # 現在の外部サービス使用（ui-avatars.com）
        # TODO: プロダクション環境では user_avatar タグを使用すること
        return mark_safe(f'''
            <img src="https://ui-avatars.com/api/?name={user.username|urlencode}&size={size}&rounded=true" 
                 alt="{user.username}" 
                 class="{css_classes}"
                 style="width: {size}px; height: {size}px;">
        ''')


@register.inclusion_tag('partials/user_avatar.html')
def avatar_with_name(user, size=48, show_name=True, link_to_channel=True):
    """
    アバター + ユーザー名の組み合わせ表示
    
    使用例:
    {% load avatar_tags %}
    {% avatar_with_name user 64 True True %}
    """
    return {
        'user': user,
        'size': size,
        'show_name': show_name,
        'link_to_channel': link_to_channel,
    }