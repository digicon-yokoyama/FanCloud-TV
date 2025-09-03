from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def readable_time(value):
    """
    読みやすい時間表示フィルター
    - 1時間以内: 分数表示 (例: 5分前)
    - 24時間以内: 時間表示 (例: 3時間前)
    - 7日以内: 日数表示 (例: 2日前)
    - 4週間以内: 週間表示 (例: 1週間前)
    - 1年以内: 月数表示 (例: 3ヶ月前)
    - 1年以上: 年数表示 (例: 1年前)
    """
    if not value:
        return ""
    
    now = timezone.now()
    if value > now:
        return "今"
    
    diff = now - value
    seconds = diff.total_seconds()
    
    # 1分未満
    if seconds < 60:
        return "今"
    
    # 1時間以内（分数表示）
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes}分前"
    
    # 24時間以内（時間表示）
    elif seconds < 86400:  # 24 * 60 * 60
        hours = int(seconds // 3600)
        return f"{hours}時間前"
    
    # 7日以内（日数表示）
    elif seconds < 604800:  # 7 * 24 * 60 * 60
        days = int(seconds // 86400)
        return f"{days}日前"
    
    # 4週間以内（週間表示）
    elif seconds < 2419200:  # 28 * 24 * 60 * 60
        weeks = int(seconds // 604800)
        return f"{weeks}週間前"
    
    # 1年以内（月数表示）
    elif seconds < 31536000:  # 365 * 24 * 60 * 60
        months = int(seconds // 2592000)  # 30 * 24 * 60 * 60
        return f"{months}ヶ月前"
    
    # 1年以上（年数表示）
    else:
        years = int(seconds // 31536000)
        return f"{years}年前"