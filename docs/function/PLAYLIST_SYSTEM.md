# プレイリストシステム仕様書

## 概要

FanCloud TVのプレイリスト機能は、ユーザーが動画を整理・管理し、連続再生やコレクション共有を可能にするシステムです。個人利用から公開共有まで、柔軟なプライバシー設定に対応しています。

## 機能仕様

### 1. プレイリスト管理機能

#### 1.1 CRUD操作
- **作成**: タイトル、説明、プライバシー設定を指定してプレイリスト作成
- **編集**: プレイリスト情報の更新（タイトル、説明、プライバシー設定）
- **削除**: プレイリスト削除（所有者のみ）
- **一覧表示**: ユーザーの作成したプレイリスト一覧（ページネーション対応）

#### 1.2 プライバシー設定
- **公開** (`public`): 全ユーザーが閲覧・検索可能
- **限定公開** (`unlisted`): URL直接アクセスのみ可能、検索対象外
- **非公開** (`private`): 所有者のみアクセス可能

### 2. 動画管理機能

#### 2.1 動画追加
- **個別追加**: 1本ずつ動画を選択して追加
- **複数同時追加**: 複数動画を一括選択して追加
- **並び順管理**: `order`フィールドによる並び順制御

#### 2.2 動画操作
- **削除**: プレイリストから特定動画を削除
- **並び替え**: 動画の表示順序変更
- **重複防止**: 同一動画の重複追加を防止

### 3. 再生機能

#### 3.1 プレイリスト再生
- **連続再生**: プレイリスト内の動画を順次再生
- **プレイリストコンテキスト**: URLパラメータ `?playlist=<id>` でプレイリスト情報を保持
- **ナビゲーション**: 視聴ページでのプレイリスト内動画一覧表示

#### 3.2 視覚的フィードバック
- **現在再生中動画**: プレイリスト内でハイライト表示
- **プレイリスト情報**: 視聴ページでプレイリスト名・説明を表示

### 4. 公開・検索機能

#### 4.1 公開プレイリスト閲覧
- **一覧表示**: 全ユーザーの公開プレイリスト表示
- **検索機能**: タイトルベースの検索（部分一致）
- **ページネーション**: 大量データに対応した分割表示

#### 4.2 メタ情報表示
- 作成者名、動画本数、作成日時
- プライバシー設定のバッジ表示
- 説明文の概要表示（100文字制限）

## データベース設計

### Playlistモデル
```python
class Playlist(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    privacy = models.CharField(
        max_length=20,
        choices=[
            ('public', '公開'),
            ('unlisted', '限定公開'),
            ('private', '非公開'),
        ],
        default='private'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### PlaylistItemモデル
```python
class PlaylistItem(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    video = models.ForeignKey('streaming.Video', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['playlist', 'video']
        ordering = ['order', 'created_at']
```

## URL構成

```python
# プレイリスト基本操作
path('playlists/', views.playlists, name='playlists')
path('playlists/create/', views.create_playlist, name='create_playlist')
path('playlists/<int:pk>/', views.playlist_detail, name='playlist_detail')
path('playlists/<int:pk>/edit/', views.edit_playlist, name='edit_playlist')
path('playlists/<int:pk>/delete/', views.delete_playlist, name='delete_playlist')

# 動画管理
path('playlists/<int:pk>/add-video/', views.add_video_to_playlist, name='add_video_to_playlist')
path('playlists/<int:pk>/add-multiple/', views.add_multiple_videos_to_playlist, name='add_multiple_videos_to_playlist')
path('playlists/<int:pk>/remove/<int:item_id>/', views.remove_from_playlist, name='remove_from_playlist')

# 公開機能
path('playlists/public/', views.public_playlists, name='public_playlists')

# 再生機能
path('watch/<int:video_id>/', views.watch_video, name='watch')  # ?playlist=<id> パラメータ対応
```

## テンプレート構成

### 主要テンプレート
- `templates/content/playlists.html`: プレイリスト一覧
- `templates/content/playlist_detail.html`: プレイリスト詳細・管理
- `templates/content/public_playlists.html`: 公開プレイリスト一覧
- `templates/content/watch.html`: 動画視聴（プレイリスト対応）

### UI特徴
- **レスポンシブデザイン**: Bootstrap 5による各画面サイズ対応
- **複数選択UI**: JavaScript Set を使った効率的な複数選択
- **インライン操作**: モーダルを使わない直感的な操作
- **視覚的フィードバック**: 現在の状態を明確に表示

## 権限制御

### アクセス制御
- **プレイリスト作成**: ログインユーザーのみ
- **編集・削除**: プレイリスト所有者のみ
- **閲覧権限**: プライバシー設定に基づく制御
- **動画追加**: プレイリスト所有者のみ

### プライバシーチェック
```python
def can_view_playlist(user, playlist):
    if playlist.privacy == 'public':
        return True
    elif playlist.privacy == 'unlisted':
        return True  # URL直接アクセスは許可
    elif playlist.privacy == 'private':
        return user == playlist.owner
    return False
```

## JavaScript機能

### 複数選択機能
```javascript
const selectedVideos = new Set();

function toggleVideoSelection(videoId, checkbox) {
    if (checkbox.checked) {
        selectedVideos.add(videoId);
    } else {
        selectedVideos.delete(videoId);
    }
    updateAddSelectedButton();
}
```

### AJAX通信
- 複数動画追加のバッチ処理
- 非同期での動画追加・削除
- レスポンシブなUI更新

## パフォーマンス考慮

### データベース最適化
- `select_related()` による関連オブジェクト取得最適化
- `prefetch_related()` による N+1 問題回避
- 適切なインデックス設定

### キャッシュ戦略
- プレイリスト一覧の部分キャッシュ
- 公開プレイリストの検索結果キャッシュ
- 動画メタデータのキャッシュ

## セキュリティ考慮

### 入力検証
- CSRF トークンによる状態変更保護
- HTML エスケープによる XSS 防止
- 権限チェックによる不正アクセス防止

### データ整合性
- トランザクション処理による整合性保証
- 外部キー制約による参照整合性
- ユニーク制約による重複防止

## 今後の拡張予定

### 機能拡張
- プレイリストのインポート・エクスポート機能
- プレイリストの共同編集機能
- おすすめプレイリストの自動生成
- プレイリストの統計・分析機能

### UI/UX改善
- ドラッグ&ドロップによる並び替え
- プレイリスト間の動画移動
- より詳細な検索フィルター
- プレビュー機能の追加

## 関連ドキュメント
- [プロジェクト概要](../README.md)
- [全体開発計画](../ROADMAP.md)
- [権限システム](./PERMISSIONS.md)
- [ファイル構造](../FILE_STRUCTURE.md)