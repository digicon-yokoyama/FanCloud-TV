# 動画評価・お気に入り機能 仕様書

## 概要

動画視聴ページにおける「いいね/バッド評価」機能と「お気に入りブックマーク」機能の実装仕様。
これらは独立した機能として設計され、それぞれ異なる用途で利用される。

## 機能区分

### 1. いいね/バッド機能（動画評価）
- **目的**: 動画コンテンツに対する評価表現
- **用途**: コンテンツの品質や好みを示すレーティング機能
- **データモデル**: `VideoLike`
- **表示**: 評価数の集計表示あり

### 2. お気に入り機能（ブックマーク）
- **目的**: 後で再度視聴したい動画の個人的保存
- **用途**: 個人のブックマーク・コレクション機能
- **データモデル**: `VideoFavorite`
- **表示**: 個人利用のため集計表示なし

## データモデル

### VideoLike（動画評価モデル）

```python
class VideoLike(models.Model):
    """動画のいいね/バッド評価."""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_like = models.BooleanField()  # True=いいね、False=バッド
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('video', 'user')
```

**特徴:**
- 1ユーザーにつき1動画に対して1評価まで
- `is_like`フィールドでいいね/バッドを区別
- 評価の切り替え・削除が可能

### VideoFavorite（お気に入りモデル）

```python
class VideoFavorite(models.Model):
    """動画お気に入り/ブックマーク."""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='favorites')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('video', 'user')
```

**特徴:**
- シンプルなブックマーク機能
- 追加・削除のトグル動作
- 個人的なコレクション管理

## API仕様

### いいね/バッド API

**エンドポイント**: `POST /content/api/video/<video_id>/like/`

**リクエストパラメータ:**
```
action: "like" | "dislike"
```

**レスポンス:**
```json
{
    "status": "added" | "removed" | "changed",
    "action": "like" | "dislike",
    "like_count": 整数,
    "dislike_count": 整数
}
```

**処理ロジック:**
1. 既存評価なし → 新規追加
2. 同じ評価をクリック → 評価削除
3. 異なる評価をクリック → 評価変更

### お気に入り API

**エンドポイント**: `POST /content/api/video/<video_id>/favorite/`

**パラメータ**: なし（トグル動作）

**レスポンス:**
```json
{
    "status": "added" | "removed",
    "favorited": true | false
}
```

**処理ロジック:**
1. お気に入り未登録 → 追加
2. お気に入り登録済み → 削除

## UI仕様

### ボタンデザイン（一貫性重視）

| 機能 | 未選択状態 | 選択済み状態 | アイコン |
|------|------------|--------------|----------|
| **いいね** | `btn-outline-primary` (青枠) | `btn-primary` (青塗りつぶし) | `bi-hand-thumbs-up` |
| **バッド** | `btn-outline-secondary` (グレー枠) | `btn-danger` (赤塗りつぶし) | `bi-hand-thumbs-down` |
| **お気に入り** | `btn-outline-danger` (赤枠) | `btn-danger` (赤塗りつぶし) | `bi-heart` / `bi-heart-fill` |

### レイアウト配置

```
[👍 いいね 123] [👎 456] [💾 保存] [❤️ お気に入り]
```

### 状態表示

**いいね/バッドボタン:**
- 数値表示でコミュニティの評価を可視化
- リアルタイム更新でカウント反映

**お気に入りボタン:**
- ハートアイコンの塗りつぶし有無で状態表示
- 数値表示なし（個人的利用のため）

## JavaScript実装

### お気に入り機能

```javascript
// 独立したAPIエンドポイント使用
fetch(`/content/api/video/${videoId}/favorite/`, {
    method: 'POST',
    headers: {
        'X-CSRFToken': csrfToken,
        'Content-Type': 'application/json',
    },
})
.then(response => response.json())
.then(data => {
    // ボタン状態とアイコンの更新
    if (data.status === 'added') {
        button.className = 'btn btn-danger';
        button.innerHTML = '<i class="bi bi-heart-fill me-1"></i>お気に入り';
    } else if (data.status === 'removed') {
        button.className = 'btn btn-outline-danger';
        button.innerHTML = '<i class="bi bi-heart me-1"></i>お気に入り';
    }
});
```

### いいね/バッド機能

```javascript
// 既存のlike APIエンドポイント使用
fetch(`/content/api/video/${videoId}/like/`, {
    method: 'POST',
    body: `action=${action}` // "like" or "dislike"
})
.then(response => response.json())
.then(data => {
    // カウント更新とボタン状態変更
    document.getElementById('like-count').textContent = data.like_count;
    document.getElementById('dislike-count').textContent = data.dislike_count;
    // ボタンスタイル更新...
});
```

## 関連ページとの連携

### お気に入りページ (`/content/favorites/`)

**ビュー関数**: `favorites(request)`

```python
def favorites(request):
    """ユーザーのお気に入り動画一覧."""
    favorite_videos = Video.objects.filter(
        favorites__user=request.user,
        status='ready'
    ).order_by('-favorites__created_at')
    
    # ページネーション処理...
```

**表示仕様:**
- お気に入り登録順（新しい順）で表示
- `library_page.html`テンプレート使用
- 12件ごとのページネーション

### ナビゲーション連携

**サイドバーメニュー:**
```html
<a class="nav-link" href="{% url 'content:favorites' %}">
    <i class="bi bi-heart me-2"></i>
    お気に入り
</a>
```

## セキュリティ考慮事項

### 認証・認可
- **ログイン必須**: 全ての評価・お気に入り機能はログインユーザーのみ
- **CSRF保護**: 全APIエンドポイントでCSRFトークン検証
- **ユーザー検証**: 他ユーザーのデータ操作不可

### データ整合性
- **ユニーク制約**: 1ユーザー×1動画の重複登録防止
- **カスケード削除**: 動画削除時の関連データ自動削除
- **トランザクション**: カウント更新の整合性保証

## パフォーマンス考慮事項

### データベース最適化
- **インデックス**: `unique_together`制約によるクエリ最適化
- **N+1問題対策**: `select_related`/`prefetch_related`使用
- **カウント集計**: リアルタイム集計（将来的にキャッシュ検討）

### フロントエンド最適化
- **非同期処理**: Ajax通信でページリロード不要
- **ローディング状態**: ボタン無効化と処理中表示
- **エラーハンドリング**: 通信失敗時の適切な復旧

## 今後の拡張可能性

### 機能拡張案
1. **お気に入りフォルダ機能**: カテゴリ別ブックマーク整理
2. **評価理由コメント**: いいね/バッドの理由記述
3. **評価統計**: 期間別評価トレンド分析
4. **ソーシャル機能**: お気に入りの共有・フォロー

### 技術的拡張
1. **Redis キャッシング**: 評価カウントのキャッシュ化
2. **バッチ処理**: 評価集計の非同期処理
3. **API拡張**: RESTful APIとしての外部公開
4. **リアルタイム更新**: WebSocketによる評価数リアルタイム反映

## マイグレーション履歴

### 0002_videofavorite.py
- **作成日**: 実装完了時
- **内容**: VideoFavoriteモデルの作成
- **実行**: `python manage.py migrate_schemas --tenant`

## テスト仕様

### 単体テスト
- **モデルテスト**: ユニーク制約、カスケード削除
- **ビューテスト**: API レスポンス、認証チェック
- **JavaScriptテスト**: ボタン状態変更、API通信

### 統合テスト
- **ユーザーフロー**: 評価→お気に入り→ページ遷移
- **権限テスト**: 未ログイン、他ユーザーデータアクセス
- **エラーケース**: 存在しない動画、通信エラー

---

*最終更新: 2025年9月5日*
*実装バージョン: Django 5.2*