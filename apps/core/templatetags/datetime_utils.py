from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def format_datetime(value, format_type='default'):
    """統一された日時フォーマット
    
    Args:
        value: datetime オブジェクト
        format_type: フォーマットタイプ
            - 'default': Y年m月d日 H:i (2024年1月15日 14:30)
            - 'date': Y年m月d日 (2024年1月15日)  
            - 'time': H:i (14:30)
            - 'short': m/d H:i (1/15 14:30)
            - 'full': Y年m月d日 H時i分s秒 (2024年1月15日 14時30分25秒)
            - 'slash_date': Y/m/d (2024/1/15)
            - 'slash_datetime': Y/m/d H:i (2024/1/15 14:30)
    
    Returns:
        str: フォーマット済み日時文字列
    """
    if not value:
        return ''
    
    formats = {
        'default': '%Y年%m月%d日 %H:%M',
        'date': '%Y年%m月%d日',
        'time': '%H:%M',
        'short': '%m/%d %H:%M',
        'full': '%Y年%m月%d日 %H時%M分%S秒',
        'slash_date': '%Y/%m/%d',
        'slash_datetime': '%Y/%m/%d %H:%M'
    }
    
    return value.strftime(formats.get(format_type, formats['default']))

@register.filter
def relative_time(value):
    """相対時間表示（○分前、○時間前、など）
    
    Args:
        value: datetime オブジェクト
    
    Returns:
        str: 相対時間文字列
    """
    if not value:
        return ''
    
    now = timezone.now()
    if value > now:
        return 'たった今'
    
    diff = now - value
    seconds = diff.total_seconds()
    
    # 1分未満
    if seconds < 60:
        return 'たった今'
    
    # 1時間以内（分数表示）
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f'{minutes}分前'
    
    # 24時間以内（時間表示）
    elif seconds < 86400:  # 24 * 60 * 60
        hours = int(seconds // 3600)
        return f'{hours}時間前'
    
    # 7日以内（日数表示）
    elif seconds < 604800:  # 7 * 24 * 60 * 60
        days = int(seconds // 86400)
        return f'{days}日前'
    
    # 4週間以内（週間表示）
    elif seconds < 2419200:  # 28 * 24 * 60 * 60
        weeks = int(seconds // 604800)
        return f'{weeks}週間前'
    
    # 1年以内（月数表示）
    elif seconds < 31536000:  # 365 * 24 * 60 * 60
        months = int(seconds // 2592000)  # 30 * 24 * 60 * 60
        return f'{months}ヶ月前'
    
    # 1年以上（年数表示）
    else:
        years = int(seconds // 31536000)
        return f'{years}年前'

@register.filter  
def smart_datetime(value, show_time=True):
    """スマート日時表示（最近なら相対時間、古いなら絶対時間）
    
    Args:
        value: datetime オブジェクト
        show_time: 時刻も表示するかどうか
    
    Returns:
        str: スマート日時文字列
    """
    if not value:
        return ''
    
    now = timezone.now()
    diff = now - value
    
    # 7日以内なら相対時間
    if diff < timedelta(days=7):
        return relative_time(value)
    
    # 7日以上なら絶対時間
    if show_time:
        return format_datetime(value, 'default')
    else:
        return format_datetime(value, 'date')