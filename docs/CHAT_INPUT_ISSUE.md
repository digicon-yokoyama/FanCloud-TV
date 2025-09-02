# チャット機能不具合 - 総合イシュー報告書

## 問題の概要
ライブ配信視聴ページのチャット機能において、複数の深刻な問題が発生している。

## 主要な問題

### 1. チャット入力欄表示問題 ✅ **解決済み** 
ログイン済みユーザーでもチャット入力欄が表示されない問題
- **解決方法**: 独立したテンプレートファイル `/templates/chat/chat_widget.html` を作成し、モジュール化

### 2. ユーザー名表示不整合問題 ❌ **未解決**
**現在の主要問題**: 同一メッセージに対して、異なるユーザーが異なるユーザー名を見る問題
- streamerが見る名前: "sysadmin" → "premium_viewer" 
- premium_viewerが見る名前: "premium_viewer" → "premium_viewer"

### 3. 認証機能の問題 ❌ **部分解決**
WebSocket認証が不完全で、メッセージ送信時にログインエラーが発生

## 発生状況
- **日時**: 2025-09-02
- **環境**: Docker環境（`http://localhost:8000`）
- **影響ユーザー**: streamer, premium_viewer
- **ストリーム**: live状態、チャット有効

## 実施した調査・対策

### Phase 1: チャット入力欄表示問題の修正 ✅
- デバッグログのクリーンアップ
- チャット入力欄の独立したテンプレート化
- プレースホルダー表示の改善（コメントがない場合のみ表示）

### Phase 2: ユーザー認証システムの修正 🔄
- テストユーザー表示問題の修正
- WebSocket認証システムの緊急修正実装
- セッションベース認証の導入

### Phase 3: データベースクリーンアップ ✅
- チャットメッセージテーブルのクリア
- テスト環境の初期化

### Phase 4: 緊急認証修正の実装 ✅
```python
# consumers.py の主要修正点
@database_sync_to_async
def get_user_id_from_session(self):
    """セッションからユーザーIDを安全に取得"""
    try:
        session = self.scope.get("session")
        if session and hasattr(session, 'get'):
            user_id = session.get("_auth_user_id")
            return user_id
        return None
    except Exception as e:
        print(f"Error getting user ID from session: {e}")
        return None

@database_sync_to_async
def get_user_by_id(self, user_id):
    """ユーザーIDから実際のユーザーオブジェクトを取得"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.get(id=user_id)
    except Exception as e:
        print(f"Error getting user by ID {user_id}: {e}")
        return None
```

## 現在のシステム状態

### ✅ 正常動作
- Django サーバー起動（Docker環境）
- WebSocket接続確立
- チャット入力欄表示
- プレースホルダー表示制御

### ❌ 問題継続中
- **ユーザー名表示不整合**: 異なるユーザーが同一メッセージで異なる名前を見る
- **認証システムの不完全性**: WebSocketでAnonymousUserが検出される

## デバッグログ（Docker環境）
```
web-1  | WebSocket connect attempt - User: AnonymousUser
web-1  | Room name: stream_1a2cea4e-ab66-4a48-b386-7606240ec322
web-1  | Room exists: True
web-1  | Accepting WebSocket connection for room: stream_1a2cea4e-ab66-4a48-b386-7606240ec322
web-1  | Anonymous user connected to chat
web-1  | 🔑 SESSION AUTH: User ID from session: 1
web-1  | 🔑 SESSION AUTH: User found: streamer (ID: 1)
web-1  | 💾 SAVE: Saving message for user: streamer (ID: 1)
```

## 根本原因分析

### 1. WebSocket認証ミドルウェアの問題
django-tenants環境での標準認証ミドルウェアが正しく動作していない

### 2. セッション管理の複雑性
マルチテナント環境でのセッション管理とWebSocket認証の連携問題

### 3. ユーザー名表示の非同期性
WebSocket接続ごとに異なるユーザー情報が取得される問題

## 未解決の技術的課題

### 1. 一貫性の問題
```
期待される動作: 全ユーザーが同一メッセージで同一ユーザー名を見る
現在の動作: ユーザーごとに異なるユーザー名が表示される
```

### 2. 認証流れの問題
```
期待: WebSocket接続時に正しいユーザー情報を取得
現状: AnonymousUser → セッションから手動でユーザー情報を抽出
```

## 次のステップ

### 優先度 1: ユーザー名表示不整合の解決
- WebSocket認証ミドルウェアの設定見直し
- ASGI設定での認証ミドルウェアチェーンの修正
- テナントスコープでのセッション管理改善

### 優先度 2: 重複WebSocket接続調査
- 接続管理の最適化
- 不要な接続の削除処理

### 優先度 3: システムテスト
- 複数ユーザーでの同時テスト
- 認証状態の一貫性確認

## 影響範囲
- **重要度**: 🔴 高（基本機能の不具合）
- **影響**: リアルタイムチャット機能の信頼性問題
- **ユーザー体験**: 混乱を招くユーザー名表示

## 関連ファイル
- `/apps/chat/consumers.py` - WebSocket処理
- `/templates/chat/chat_widget.html` - チャットUI
- `/config/routing.py` - WebSocket routing
- `/config/settings.py` - 認証設定（要確認）

## 技術仕様メモ
```python
# 現在の認証フロー
WebSocket接続 → AnonymousUser検出 → セッションから手動抽出 → 実ユーザー取得

# 理想的な認証フロー
WebSocket接続 → 自動認証 → 正しいユーザー情報取得
```

---
**作成日**: 2025-09-02  
**最終更新**: 2025-09-02 16:30  
**ステータス**: 🔴 継続調査中（ユーザー名不整合問題）  
**担当**: システム全体の認証アーキテクチャ見直し必要