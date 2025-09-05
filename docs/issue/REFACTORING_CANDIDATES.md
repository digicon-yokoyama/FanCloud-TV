# リファクタリング候補リスト

このドキュメントは、FanCloud TVプロジェクト全体で共通化・リファクタリング可能な部分を詳細にまとめたものです。

## 📈 実装進捗
- **完了項目**: 1/12項目 （8.3%）
- **最終更新**: 2025年09月05日
- **実装完了**:
  - ✅ 日時フォーマットの統一（低優先度項目）

## 目次
1. [高優先度項目](#高優先度項目)
2. [中優先度項目](#中優先度項目)
3. [低優先度項目](#低優先度項目)
4. [実装推奨順序](#実装推奨順序)

---

## 高優先度項目

### 1. 動画カード表示の重複 🎬

#### 現状の問題点
動画カードの表示が複数のテンプレートで異なる実装になっており、保守性が低下している。

#### 影響範囲
- `templates/partials/video_card.html`
- `templates/content/trending.html` (行 45-72)
- `templates/content/subscriptions.html` (行 33-58)
- `templates/streaming/home.html` (行 89-115)
- `templates/content/search.html` (行 40-65)

#### 現在のコード例
```django
<!-- trending.html での実装 -->
<div class="card h-100">
    <img src="{{ video.thumbnail.url }}" class="card-img-top">
    <div class="card-body">
        <h5 class="card-title">{{ video.title|truncatechars:50 }}</h5>
        <p class="text-muted">{{ video.views }} 回視聴</p>
    </div>
</div>

<!-- home.html での実装（微妙に異なる） -->
<div class="video-card">
    <img src="{{ video.thumbnail.url }}" alt="{{ video.title }}">
    <div class="video-info">
        <h6>{{ video.title|truncatechars:40 }}</h6>
        <span>{{ video.views|intcomma }} views</span>
    </div>
</div>
```

#### 改善案
```django
<!-- 統一された video_card.html -->
{% load humanize %}
<div class="video-card h-100">
    <div class="video-thumbnail position-relative">
        <img src="{{ video.thumbnail.url|default:'/static/img/default-thumbnail.jpg' }}" 
             class="w-100" 
             alt="{{ video.title }}"
             onerror="this.src='/static/img/default-thumbnail.jpg';">
        {% if video.duration %}
        <span class="duration-badge">{{ video.duration|readable_time }}</span>
        {% endif %}
    </div>
    <div class="video-info p-2">
        <h6 class="video-title mb-1">
            <a href="{% url 'content:watch' video.id %}" class="text-decoration-none text-dark">
                {{ video.title|truncatechars:50 }}
            </a>
        </h6>
        {% if show_channel|default:True %}
        <p class="channel-name mb-1">
            <a href="{% url 'accounts:channel' video.uploader.username %}">
                {{ video.uploader.username }}
            </a>
        </p>
        {% endif %}
        <div class="video-stats text-muted small">
            <span>{{ video.views|intcomma }} 回視聴</span>
            <span>・{{ video.created_at|timesince }}前</span>
        </div>
    </div>
</div>

<!-- 使用例 -->
{% include 'partials/video_card.html' with video=video show_channel=True %}
```

#### 期待される効果
- コードの重複を削減（約200行削減）
- 一貫性のあるUI表示
- 保守性の向上（変更箇所が1つに）

---

### 2. チャットメッセージ表示の重複 💬

#### 現状の問題点
チャットメッセージのHTML生成が3箇所で異なる実装になっている。

#### 影響範囲
- `templates/chat/room.html` (サーバーサイドレンダリング)
- `templates/streaming/watch_live.html` (JavaScript動的生成)
- `static/js/chat.js` (WebSocket受信時の生成)

#### 現在のコード例
```javascript
// watch_live.html のJavaScript
function addMessage(message) {
    const messageHtml = `
        <div class="chat-message">
            <strong>${message.username}:</strong>
            <span>${message.message}</span>
            <small>${message.timestamp}</small>
        </div>
    `;
    chatContainer.innerHTML += messageHtml;
}

// chat.js の実装（また異なる）
socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message';
    msgDiv.innerHTML = `<b>${data.user}</b>: ${data.message}`;
    // ...
}
```

#### 改善案
```django
<!-- templates/partials/chat_message.html -->
<div class="chat-message d-flex align-items-start mb-2" data-message-id="{{ message.id }}">
    <div class="message-avatar me-2">
        {% if message.user.avatar %}
        <img src="{{ message.user.avatar.url }}" class="rounded-circle" width="32" height="32">
        {% else %}
        <div class="avatar-placeholder rounded-circle">{{ message.user.username|first|upper }}</div>
        {% endif %}
    </div>
    <div class="message-content flex-grow-1">
        <div class="message-header">
            <strong class="username">{{ message.user.username }}</strong>
            {% if message.user.is_moderator %}
            <span class="badge bg-primary ms-1">MOD</span>
            {% endif %}
            <small class="timestamp text-muted ms-2">{{ message.timestamp|time:"H:i" }}</small>
        </div>
        <div class="message-text">{{ message.content|escape|urlize }}</div>
    </div>
</div>
```

```javascript
// static/js/chat-message-renderer.js
class ChatMessageRenderer {
    static render(messageData) {
        const template = document.getElementById('chat-message-template').content.cloneNode(true);
        template.querySelector('.username').textContent = messageData.username;
        template.querySelector('.message-text').textContent = messageData.message;
        template.querySelector('.timestamp').textContent = this.formatTime(messageData.timestamp);
        return template;
    }
    
    static formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString('ja-JP', {hour: '2-digit', minute: '2-digit'});
    }
}
```

#### 期待される効果
- 一貫性のあるチャット表示
- XSS脆弱性の防止
- メッセージ表示ロジックの一元管理

---

### 3. ページネーションの重複 📄

#### 現状の問題点
Bootstrapページネーションが12箇所以上で同じコードがコピペされている。

#### 影響範囲
- `templates/content/favorites.html` (行 98-120)
- `templates/content/history.html` (行 85-107)
- `templates/content/manage.html` (行 110-132)
- `templates/content/playlists.html` (行 75-97)
- `templates/content/public_playlists.html` (行 73-101)
- `templates/accounts/channel.html` (行 169-200)
- その他6箇所以上

#### 現在のコード例（全て同じ）
```django
{% if videos.has_other_pages %}
<nav aria-label="ページネーション">
    <ul class="pagination justify-content-center">
        {% if videos.has_previous %}
        <li class="page-item">
            <a class="page-link" href="?page={{ videos.previous_page_number }}">前へ</a>
        </li>
        {% endif %}
        
        {% for num in videos.paginator.page_range %}
            {% if videos.number == num %}
            <li class="page-item active">
                <span class="page-link">{{ num }}</span>
            </li>
            {% elif num > videos.number|add:'-3' and num < videos.number|add:'3' %}
            <li class="page-item">
                <a class="page-link" href="?page={{ num }}">{{ num }}</a>
            </li>
            {% endif %}
        {% endfor %}
        
        {% if videos.has_next %}
        <li class="page-item">
            <a class="page-link" href="?page={{ videos.next_page_number }}">次へ</a>
        </li>
        {% endif %}
    </ul>
</nav>
{% endif %}
```

#### 改善案
```django
<!-- templates/partials/pagination.html -->
{% load query_utils %}
{% if page_obj.has_other_pages %}
<nav aria-label="{{ aria_label|default:'ページネーション' }}">
    <ul class="pagination {{ class|default:'justify-content-center' }}">
        <!-- First Page -->
        {% if page_obj.number > 2 %}
        <li class="page-item">
            <a class="page-link" href="?{% update_query page=1 %}" aria-label="最初のページ">
                <i class="bi bi-chevron-double-left"></i>
            </a>
        </li>
        {% endif %}
        
        <!-- Previous Page -->
        {% if page_obj.has_previous %}
        <li class="page-item">
            <a class="page-link" href="?{% update_query page=page_obj.previous_page_number %}">
                <i class="bi bi-chevron-left"></i> 前へ
            </a>
        </li>
        {% endif %}
        
        <!-- Page Numbers -->
        {% for num in page_obj.paginator.page_range %}
            {% if page_obj.number == num %}
            <li class="page-item active">
                <span class="page-link">{{ num }}</span>
            </li>
            {% elif num > page_obj.number|add:'-3' and num < page_obj.number|add:'3' %}
            <li class="page-item">
                <a class="page-link" href="?{% update_query page=num %}">{{ num }}</a>
            </li>
            {% elif num == 1 or num == page_obj.paginator.num_pages %}
            <li class="page-item">
                <a class="page-link" href="?{% update_query page=num %}">{{ num }}</a>
            </li>
            {% elif num == page_obj.number|add:'-3' or num == page_obj.number|add:'3' %}
            <li class="page-item disabled">
                <span class="page-link">...</span>
            </li>
            {% endif %}
        {% endfor %}
        
        <!-- Next Page -->
        {% if page_obj.has_next %}
        <li class="page-item">
            <a class="page-link" href="?{% update_query page=page_obj.next_page_number %}">
                次へ <i class="bi bi-chevron-right"></i>
            </a>
        </li>
        {% endif %}
        
        <!-- Last Page -->
        {% if page_obj.number < page_obj.paginator.num_pages|add:'-1' %}
        <li class="page-item">
            <a class="page-link" href="?{% update_query page=page_obj.paginator.num_pages %}" aria-label="最後のページ">
                <i class="bi bi-chevron-double-right"></i>
            </a>
        </li>
        {% endif %}
    </ul>
</nav>
{% endif %}

<!-- 使用例 -->
{% include 'partials/pagination.html' with page_obj=videos %}
{% include 'partials/pagination.html' with page_obj=playlists class="pagination-sm" %}
```

#### 期待される効果
- 約300行のコード削減
- 検索パラメータの保持機能
- 一貫性のあるページネーション表示

---

### 4. AJAX リクエストパターンの重複 🔄

#### 現状の問題点
同じAJAXパターンが20箇所以上で重複している。CSRFトークン取得も各所でバラバラ。

#### 影響範囲
- 全テンプレートファイルのJavaScript部分
- いいね、お気に入り、フォロー、コメント投稿などの非同期処理

#### 現在のコード例
```javascript
// watch.html
fetch(`/content/api/video/${videoId}/like/`, {
    method: 'POST',
    headers: {
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({action: 'like'})
})
.then(response => response.json())
.then(data => {
    // 処理
})
.catch(error => console.error('Error:', error));

// channel.html （同じパターン）
fetch(`/accounts/follow/${userId}/`, {
    method: 'POST',
    headers: {
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        'Content-Type': 'application/json',
    },
})
// ...
```

#### 改善案
```javascript
// static/js/api-client.js
class ApiClient {
    static getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.content || '';
    }
    
    static async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'X-CSRFToken': this.getCsrfToken(),
                'Content-Type': 'application/json',
                ...options.headers
            },
            credentials: 'same-origin'
        };
        
        try {
            const response = await fetch(url, {...defaultOptions, ...options});
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return await response.text();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }
    
    static get(url, options = {}) {
        return this.request(url, {...options, method: 'GET'});
    }
    
    static post(url, data = null, options = {}) {
        const requestOptions = {...options, method: 'POST'};
        if (data) {
            requestOptions.body = JSON.stringify(data);
        }
        return this.request(url, requestOptions);
    }
    
    static put(url, data = null, options = {}) {
        const requestOptions = {...options, method: 'PUT'};
        if (data) {
            requestOptions.body = JSON.stringify(data);
        }
        return this.request(url, requestOptions);
    }
    
    static delete(url, options = {}) {
        return this.request(url, {...options, method: 'DELETE'});
    }
}

// 使用例
ApiClient.post(`/content/api/video/${videoId}/like/`, {action: 'like'})
    .then(data => {
        updateLikeButton(data);
    })
    .catch(error => {
        showNotification('エラーが発生しました', 'error');
    });
```

#### 期待される効果
- エラーハンドリングの統一
- CSRFトークン取得の一元化
- 約200行のコード削減
- リトライ機能やローディング表示の追加が容易

---

### 5. 重複クエリパターン 🗄️

#### 現状の問題点
同じような複雑なクエリが複数のビューで重複している。

#### 影響範囲
- `apps/content/views.py` (5箇所)
- `apps/streaming/views.py` (3箇所)
- `apps/accounts/views.py` (2箇所)

#### 現在のコード例
```python
# content/views.py
def trending(request):
    videos = Video.objects.filter(
        status='published',
        privacy='public'
    ).select_related('uploader').prefetch_related('categories').order_by('-views')[:50]
    
def search_videos(request):
    videos = Video.objects.filter(
        status='published',
        privacy='public'
    ).select_related('uploader').prefetch_related('categories')
    # さらにフィルタリング

# streaming/views.py（同じパターン）
def home(request):
    videos = Video.objects.filter(
        status='published',
        privacy='public'
    ).select_related('uploader').prefetch_related('categories')
```

#### 改善案
```python
# apps/content/managers.py
class VideoQuerySet(models.QuerySet):
    def published(self):
        """公開済みの動画のみ"""
        return self.filter(status='published')
    
    def public(self):
        """公開設定の動画のみ"""
        return self.filter(privacy='public')
    
    def visible_to(self, user=None):
        """ユーザーが視聴可能な動画"""
        queryset = self.published()
        
        if user and user.is_authenticated:
            # ログインユーザーは限定公開も視聴可能
            return queryset.filter(
                models.Q(privacy='public') |
                models.Q(privacy='unlisted') |
                models.Q(uploader=user)
            )
        return queryset.public()
    
    def with_details(self):
        """関連データを効率的に取得"""
        return self.select_related(
            'uploader',
            'uploader__profile'
        ).prefetch_related(
            'categories',
            'tags',
            Prefetch('videlike_set', 
                    queryset=VideoLike.objects.select_related('user'))
        )
    
    def trending(self, days=7):
        """トレンド動画を取得"""
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.visible_to().filter(
            created_at__gte=cutoff_date
        ).with_details().annotate(
            score=models.F('views') + models.F('likes') * 10
        ).order_by('-score')

class VideoManager(models.Manager):
    def get_queryset(self):
        return VideoQuerySet(self.model, using=self._db)
    
    def published(self):
        return self.get_queryset().published()
    
    def visible_to(self, user=None):
        return self.get_queryset().visible_to(user)
    
    def trending(self, days=7):
        return self.get_queryset().trending(days)

# models.py
class Video(models.Model):
    # ...
    objects = VideoManager()

# 使用例
def trending(request):
    videos = Video.objects.trending(days=7)[:50]
    
def search_videos(request, query):
    videos = Video.objects.visible_to(request.user).with_details().filter(
        models.Q(title__icontains=query) |
        models.Q(description__icontains=query)
    )
```

#### 期待される効果
- クエリロジックの一元管理
- N+1問題の防止
- テスタビリティの向上
- 約150行のコード削減

---

## 中優先度項目

### 6. 通知ドロップダウンの重複 🔔

#### 現状の問題点
通知表示のHTMLとロジックが複数箇所で重複。

#### 改善案
```django
<!-- templates/partials/notification_item.html -->
{% load humanize %}
<div class="notification-item {% if not notification.is_read %}unread{% endif %}" 
     data-notification-id="{{ notification.id }}">
    <div class="d-flex align-items-start">
        <div class="notification-icon me-2">
            {% if notification.type == 'like' %}
            <i class="bi bi-heart-fill text-danger"></i>
            {% elif notification.type == 'comment' %}
            <i class="bi bi-chat-dots-fill text-primary"></i>
            {% elif notification.type == 'follow' %}
            <i class="bi bi-person-plus-fill text-success"></i>
            {% endif %}
        </div>
        <div class="flex-grow-1">
            <p class="mb-1">{{ notification.message }}</p>
            <small class="text-muted">{{ notification.created_at|timesince }}前</small>
        </div>
        {% if show_actions|default:False %}
        <div class="notification-actions">
            <button class="btn btn-sm btn-outline-secondary mark-as-read" 
                    data-id="{{ notification.id }}">
                <i class="bi bi-check"></i>
            </button>
        </div>
        {% endif %}
    </div>
</div>
```

---

### 7. 動画プレーヤー初期化の重複 🎥

#### 現状の問題点
Video.jsとHLS.jsの初期化が複数テンプレートで重複。

#### 改善案
```javascript
// static/js/video-player.js
class VideoPlayerManager {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.player = null;
        this.options = {
            controls: true,
            autoplay: false,
            preload: 'auto',
            fluid: true,
            ...options
        };
    }
    
    initializePlayer(videoUrl, type = 'video') {
        if (type === 'live' && Hls.isSupported()) {
            return this.initializeHlsPlayer(videoUrl);
        }
        return this.initializeVideoJs(videoUrl);
    }
    
    initializeHlsPlayer(streamUrl) {
        const video = this.container.querySelector('video');
        const hls = new Hls();
        hls.loadSource(streamUrl);
        hls.attachMedia(video);
        
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
            video.play();
        });
        
        return hls;
    }
    
    initializeVideoJs(videoUrl) {
        this.player = videojs(this.container.querySelector('video'), this.options);
        this.player.src({
            src: videoUrl,
            type: 'video/mp4'
        });
        
        return this.player;
    }
    
    destroy() {
        if (this.player) {
            this.player.dispose();
        }
    }
}
```

---

### 8. 権限チェックデコレーター 🔐

#### 現状の問題点
権限チェックロジックが各ビューで重複。

#### 改善案
```python
# apps/core/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def require_streaming_permission(func):
    """配信権限を要求するデコレーター"""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'ログインが必要です')
            return redirect('accounts:login')
        
        if not request.user.can_stream:
            messages.error(request, '配信権限がありません')
            return redirect('streaming:home')
        
        return func(request, *args, **kwargs)
    return wrapper

def require_role(*roles):
    """特定のロールを要求するデコレーター"""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            
            if request.user.role not in roles:
                messages.error(request, 'アクセス権限がありません')
                return redirect('streaming:home')
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

# 使用例
@require_streaming_permission
def create_stream(request):
    # ...

@require_role('moderator', 'admin')
def moderate_content(request):
    # ...
```

---

### 9. モーダルダイアログの共通化 🎨

#### 改善案
```django
<!-- templates/partials/confirm_modal.html -->
<div class="modal fade" id="{{ modal_id|default:'confirmModal' }}" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">{{ title|default:'確認' }}</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p>{{ message|default:'この操作を実行してもよろしいですか？' }}</p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                    キャンセル
                </button>
                <button type="button" class="btn {{ btn_class|default:'btn-danger' }}" 
                        id="{{ confirm_btn_id|default:'confirmBtn' }}">
                    {{ confirm_text|default:'削除' }}
                </button>
            </div>
        </div>
    </div>
</div>
```

---

### 10. マジックナンバーの定数化 🔢

#### 改善案
```python
# apps/core/constants.py
class PaginationSettings:
    DEFAULT_PAGE_SIZE = 12
    MAX_PAGE_SIZE = 100
    VIDEO_LIST_SIZE = 12
    COMMENT_LIST_SIZE = 20
    NOTIFICATION_LIST_SIZE = 10

class VideoSettings:
    TITLE_MAX_LENGTH = 100
    DESCRIPTION_MAX_LENGTH = 5000
    THUMBNAIL_MAX_SIZE = 5 * 1024 * 1024  # 5MB
    VIDEO_MAX_SIZE = 500 * 1024 * 1024  # 500MB
    SUPPORTED_FORMATS = ['mp4', 'webm', 'ogg']

class UISettings:
    DEFAULT_AVATAR_SIZE = 48
    THUMBNAIL_WIDTH = 320
    THUMBNAIL_HEIGHT = 180
    TRUNCATE_TITLE_LENGTH = 50
    TRUNCATE_DESCRIPTION_LENGTH = 150

# settings.py
from apps.core.constants import PaginationSettings, VideoSettings, UISettings

PAGINATION_SETTINGS = PaginationSettings
VIDEO_SETTINGS = VideoSettings
UI_SETTINGS = UISettings

# 使用例
from django.conf import settings

paginator = Paginator(videos, settings.PAGINATION_SETTINGS.VIDEO_LIST_SIZE)
```

---

## 低優先度項目

### 11. フォームエラー表示の統一 📝

#### 改善案
```django
<!-- templates/partials/form_errors.html -->
{% if form.errors %}
<div class="alert alert-danger alert-dismissible fade show" role="alert">
    <h6 class="alert-heading">エラーが発生しました</h6>
    {% if form.non_field_errors %}
    <ul class="mb-0">
        {% for error in form.non_field_errors %}
        <li>{{ error }}</li>
        {% endfor %}
    </ul>
    {% endif %}
    
    {% for field in form %}
        {% if field.errors %}
        <p class="mb-1"><strong>{{ field.label }}:</strong></p>
        <ul class="mb-2">
            {% for error in field.errors %}
            <li>{{ error }}</li>
            {% endfor %}
        </ul>
        {% endif %}
    {% endfor %}
    
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
</div>
{% endif %}

<!-- 使用例 -->
{% include 'partials/form_errors.html' with form=form %}
```

---

### 12. 日時フォーマットの統一 📅 ✅ **実装完了**

#### 実装状況
- **実装日**: 2025年09月05日
- **実装者**: Claude Code
- **テスト**: 全15テスト成功

#### 実装したファイル
- `apps/core/templatetags/datetime_utils.py` - 統一日時フィルター（新規作成）
- `apps/core/tests/test_datetime_utils.py` - テストファイル（新規作成）
- `templates/content/watch.html` - 日時表示を統一フィルターに変更
- `templates/partials/comment.html` - 相対時間表示を統一フィルターに変更
- `templates/partials/video_card.html` - 相対時間表示を統一フィルターに変更

#### 提供機能
```django
{% load datetime_utils %}

{{ date|format_datetime:'date' }}      <!-- 2024年01月15日 -->
{{ date|format_datetime:'default' }}   <!-- 2024年01月15日 14:30 -->
{{ date|format_datetime:'short' }}     <!-- 01/15 14:30 -->
{{ date|format_datetime:'slash_date' }}<!-- 2024/01/15 -->
{{ date|relative_time }}               <!-- 30分前 -->
{{ date|smart_datetime }}              <!-- 最近なら相対時間、古いなら絶対時間 -->
```

#### 実装した改善案（参考）
```python
# apps/core/templatetags/datetime_utils.py
from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def format_datetime(value, format_type='default'):
    """統一された日時フォーマット"""
    if not value:
        return ''
    
    formats = {
        'default': '%Y年%m月%d日 %H:%M',
        'date': '%Y年%m月%d日',
        'time': '%H:%M',
        'short': '%m/%d %H:%M',
        'full': '%Y年%m月%d日 %H時%M分%S秒'
    }
    
    return value.strftime(formats.get(format_type, formats['default']))

@register.filter
def relative_time(value):
    """相対時間表示（3時間前、昨日、など）"""
    if not value:
        return ''
    
    now = timezone.now()
    diff = now - value
    
    if diff < timedelta(minutes=1):
        return 'たった今'
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f'{minutes}分前'
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f'{hours}時間前'
    elif diff < timedelta(days=7):
        days = diff.days
        return f'{days}日前' if days > 1 else '昨日'
    else:
        return value.strftime('%Y年%m月%d日')

# 使用例
{{ video.created_at|format_datetime:'short' }}
{{ comment.created_at|relative_time }}
```

---

## 実装推奨順序

### フェーズ1（即座に実装可能）
1. **ページネーションの共通化** - 最も簡単で効果的
2. **AJAX リクエストの共通化** - セキュリティ向上も期待
3. **マジックナンバーの定数化** - 設定ファイルに移動するだけ

### フェーズ2（少し時間が必要）
4. **動画カード表示の統一** - UI改善効果大
5. **チャットメッセージ表示の統一** - リアルタイム機能の改善
6. **フォームエラー表示** - UX向上

### フェーズ3（慎重な実装が必要）
7. **重複クエリパターン** - パフォーマンス改善
8. **権限チェックデコレーター** - セキュリティ強化
9. **動画プレーヤー初期化** - 動画再生の安定化

### フェーズ4（時間があるとき）
10. **通知ドロップダウン**
11. **モーダルダイアログ**
12. ~~**日時フォーマット統一**~~ ✅ **実装完了**

---

## 期待される全体的な効果

### 定量的効果
- **コード削減**: 約1,000行以上
- **ファイル数削減**: 重複テンプレートの統合で約20ファイル
- **パフォーマンス向上**: クエリ最適化で30-40%の改善

### 定性的効果
- **保守性向上**: 変更箇所の一元化
- **バグ削減**: 一貫性のある実装
- **開発速度向上**: 再利用可能なコンポーネント
- **チーム開発効率化**: 標準化されたパターン

---

## 注意事項

1. **段階的な実装**: 一度に全てを変更せず、段階的に実装
2. **テストの追加**: 共通化したコンポーネントには必ずテストを追加
3. **ドキュメント化**: 新しいコンポーネントの使用方法を文書化
4. **後方互換性**: 既存機能を壊さないよう注意
5. **パフォーマンス測定**: 変更前後でパフォーマンスを測定

---

## まとめ

このリファクタリングを実施することで、コードベースの品質が大幅に向上し、今後の機能追加や保守が容易になります。特に高優先度の5項目は、比較的少ない工数で大きな効果が期待できるため、早期の実装を推奨します。

### 実装済み項目の効果
- **日時フォーマット統一**: テンプレートの保守性向上、一貫性のある日時表示、15個のテストによる品質保証を実現