# 視聴履歴機能実装 - 課題整理ドキュメント

## 概要

動画視聴履歴機能の実装に向けた技術課題と実装方針の整理。現在は基盤モデルとUIは存在するが、実際のデータ記録・表示処理が未実装の状態。

## 現在の実装状況

### ✅ 実装済み部分

**1. データモデル**
```python
class VideoView(models.Model):
    """視聴履歴追跡モデル（実装済み）"""
    video = models.ForeignKey(Video, related_name='views')
    user = models.ForeignKey(User, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    watch_duration = models.IntegerField(default=0)     # 視聴時間（秒）
    completed = models.BooleanField(default=False)      # 完全視聴フラグ
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('video', 'user', 'ip_address')
```

**2. UI・ルーティング**
- 履歴ページURL: `/content/history/` ✅
- ナビゲーションリンク: サイドバーに実装済み ✅
- ビュー関数: `history(request)` 存在（プレースホルダー） ✅

**3. 動画プレーヤー環境**
- **Video.js 8.6.1**: 統一APIによる進捗取得可能 ✅
- **HLS.js**: HLS配信対応済み ✅
- **HLS/MP4両対応**: 柔軟な配信方式 ✅

### ❌ 未実装部分

**1. 視聴記録の保存処理**
- 現在の`watch_video`関数：`view_count += 1` のみ
- VideoViewレコード作成処理なし
- ユーザー履歴データ蓄積されない

**2. 履歴表示処理**
- 現在の`history`関数：空のリスト返却のみ
- VideoViewからの履歴取得処理なし
- 「視聴履歴はありません」のみ表示

## 実装課題の段階別整理

### フェーズ1: 基本履歴機能（優先度: 高）

**実装難度: 低（30分程度）**

#### 課題1.1: 視聴記録保存の実装
**場所**: `apps/content/views.py` - `watch_video`関数

**必要な実装:**
```python
@login_required
def watch_video(request, video_id):
    # 既存処理...
    
    # 履歴記録を追加
    if request.user.is_authenticated:
        VideoView.objects.update_or_create(
            video=video,
            user=request.user,
            defaults={
                'ip_address': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'watch_duration': 0,  # フェーズ2で詳細実装
                'completed': False,   # フェーズ2で詳細実装
            }
        )
```

**技術的考慮事項:**
- `get_client_ip()` ヘルパー関数の実装が必要
- `update_or_create` で重複視聴の適切な処理
- パフォーマンス影響は軽微（単純なINSERT/UPDATE）

#### 課題1.2: 履歴表示の実装
**場所**: `apps/content/views.py` - `history`関数

**必要な実装:**
```python
@login_required
def history(request):
    """ユーザーの視聴履歴表示."""
    history_videos = Video.objects.filter(
        views__user=request.user,
        status='ready'
    ).select_related('uploader', 'category').prefetch_related('tags').annotate(
        last_viewed=models.Max('views__created_at')
    ).order_by('-last_viewed').distinct()
    
    # ページネーション処理
    paginator = Paginator(history_videos, 12)
    # ...
```

**技術的考慮事項:**
- `distinct()` で重複動画の除外
- `select_related/prefetch_related` でN+1問題回避
- 既存の `library_page.html` テンプレート流用可能

**期待される成果:**
- ユーザーが視聴した動画一覧の表示
- 最新視聴順でのソート
- 既存UIとの一貫性維持

### フェーズ2: 詳細視聴情報記録（優先度: 中）

**実装難度: 中（1-2時間程度）**

#### 課題2.1: 視聴時間の正確な記録

**技術的挑戦:**
- **HLS配信での時間同期**: セグメント境界での微調整
- **アダプティブビットレート**: 品質変更時の位置維持
- **ネットワーク不安定時**: 再接続時の位置復元

**実装アプローチ:**
```javascript
// Video.jsでの統一API利用
const player = videojs('video-player');
let lastSaveTime = 0;

player.on('timeupdate', function() {
    const currentTime = player.currentTime();
    const duration = player.duration();
    
    // 10秒間隔での定期保存
    if (Math.floor(currentTime) - lastSaveTime >= 10) {
        saveWatchProgress(videoId, currentTime, duration);
        lastSaveTime = Math.floor(currentTime);
    }
});

// ページ離脱時の最終保存
window.addEventListener('beforeunload', function() {
    const finalTime = player.currentTime();
    const finalDuration = player.duration();
    const completed = (finalTime / finalDuration) > 0.9; // 90%以上で完了
    
    // 同期リクエストで確実に保存
    navigator.sendBeacon('/content/api/save-progress/', {
        video_id: videoId,
        watch_duration: Math.floor(finalTime),
        completed: completed
    });
});
```

#### 課題2.2: 進捗保存API実装

**新規エンドポイント**: `POST /content/api/video/<video_id>/progress/`

**実装内容:**
```python
@login_required
@require_POST
def save_watch_progress(request, video_id):
    """視聴進捗の保存."""
    video = get_object_or_404(Video, id=video_id)
    watch_duration = int(request.POST.get('watch_duration', 0))
    completed = request.POST.get('completed', 'false').lower() == 'true'
    
    VideoView.objects.update_or_create(
        video=video,
        user=request.user,
        defaults={
            'watch_duration': watch_duration,
            'completed': completed,
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
    )
    
    return JsonResponse({'status': 'success'})
```

### フェーズ3: 高度な履歴機能（優先度: 低）

**実装難度: 中〜高（2-4時間程度）**

#### 課題3.1: 続きから視聴機能

**技術的要件:**
- 履歴ページから動画クリック時の位置復元
- URLパラメータでの開始時間指定
- プレーヤーの自動シーク機能

**実装例:**
```javascript
// 履歴から開始位置を取得
const resumeTime = {{ last_watch_position|default:0 }};

player.ready(function() {
    if (resumeTime > 0) {
        player.currentTime(resumeTime);
        showResumeNotification(resumeTime);
    }
});
```

#### 課題3.2: 履歴フィルタリング・検索

**機能要件:**
- 日付範囲での絞り込み
- 完了/未完了でのフィルタ
- 動画タイトル・投稿者での検索
- 視聴時間でのソート

#### 課題3.3: 履歴統計表示

**データ可視化:**
- 総視聴時間の計算
- 最も見たカテゴリ
- 視聴傾向のグラフ化

## 技術的制約と考慮事項

### パフォーマンス課題

**データベース負荷:**
- VideoViewテーブルの急速な成長
- 履歴クエリの最適化（インデックス設計）
- 古い履歴データの アーカイブ戦略

**解決策:**
```python
# 効率的な履歴取得クエリ
class VideoViewManager(models.Manager):
    def recent_for_user(self, user, days=30):
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(
            user=user,
            created_at__gte=cutoff
        ).select_related('video__uploader')
```

### セキュリティ課題

**プライバシー保護:**
- 履歴データの適切な権限制御
- 他ユーザーの履歴へのアクセス防止
- 履歴削除機能の提供

**実装例:**
```python
# 履歴削除API
@login_required
@require_POST
def clear_history(request):
    VideoView.objects.filter(user=request.user).delete()
    return JsonResponse({'status': 'cleared'})
```

### HLS配信特有の課題

**時間同期の精度:**
- セグメント境界（通常6-10秒単位）での丸め誤差
- GOP（Group of Pictures）単位での精度限界
- クライアント・サーバー間の時間差

**対応方針:**
- ±5秒程度の誤差は許容範囲として設計
- ユーザー体験を損なわない範囲での精度確保
- 完了判定は90%閾値で実用的に運用

## 実装優先度と工数見積

### フェーズ1: 基本履歴（推奨実装）
- **工数**: 0.5人日
- **リスク**: 低
- **ユーザー価値**: 高
- **技術負債**: なし

### フェーズ2: 詳細記録
- **工数**: 1-2人日  
- **リスク**: 中（HLS同期）
- **ユーザー価値**: 中
- **技術負債**: JavaScript複雑化

### フェーズ3: 高度機能
- **工数**: 3-5人日
- **リスク**: 中〜高
- **ユーザー価値**: 低〜中
- **技術負債**: 高（保守コスト増）

## 推奨実装ロードマップ

### ステップ1: 基本履歴の実装
1. `watch_video` 関数への視聴記録追加（15分）
2. `history` 関数の履歴表示実装（15分）
3. テスト・動作確認（15分）

### ステップ2: 評価・判断
- ユーザーフィードバックの収集
- 基本機能の使用状況確認
- フェーズ2移行の必要性判断

### ステップ3: 段階的拡張（必要に応じて）
- ユーザー要望に基づく機能追加
- パフォーマンス問題があれば最適化
- 高度な機能は慎重に検討

## 関連する既存機能との整合性

### お気に入り機能との連携
- 履歴からお気に入り追加の導線
- お気に入り動画の視聴履歴表示

### プレイリスト機能との連携  
- 履歴からプレイリスト追加
- 「最近見た動画」自動プレイリスト

### 検索機能との連携
- 履歴に基づく検索候補
- 視聴傾向を反映したレコメンド

---

**作成日**: 2025年9月5日  
**最終更新**: 2025年9月5日  
**ステータス**: 実装待機中  
**担当予定**: 未定