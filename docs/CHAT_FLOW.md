# 💬 チャットシステム フロー＆データ保存仕様

## 📋 目次

- [概要](#概要)
- [システムアーキテクチャ](#システムアーキテクチャ)
- [データフロー](#データフロー)
- [データ保存仕様](#データ保存仕様)
- [WebSocket通信プロトコル](#websocket通信プロトコル)
- [実装詳細](#実装詳細)
- [セキュリティ](#セキュリティ)

## 📝 概要

FanCloud TVのチャットシステムは、WebSocketを使用したリアルタイムチャット機能を提供します。Django Channelsを基盤とし、Redisをメッセージブローカーとして使用することで、スケーラブルな配信を実現しています。

## 🏗 システムアーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                     チャットシステム全体構成                      │
└─────────────────────────────────────────────────────────────────┘

    [ブラウザ]           [Django/Daphne]          [Redis]         [PostgreSQL]
        │                      │                     │                 │
        │   WebSocket          │                     │                 │
        ├──────────────────────┤                     │                 │
        │                      │                     │                 │
        │                 [ChatConsumer]             │                 │
        │                      │                     │                 │
        │                      ├─────Channel Layer──┤                 │
        │                      │                     │                 │
        │                      ├─────────────────────┼─────DB Access──┤
        │                      │                     │                 │
```

## 📊 データフロー

### 1. 初期接続フロー

```
ユーザー → ブラウザ → WebSocket接続要求 → Django Channels
                                              ↓
                                        ChatConsumer
                                              ↓
                                    ┌─────────┴─────────┐
                                    │                   │
                              認証チェック        ルーム確認
                                    │                   │
                                    └─────────┬─────────┘
                                              ↓
                                      Redisグループ参加
                                              ↓
                                        接続確立
```

### 2. メッセージ送信フロー

```
[送信者]
    │
    ├── 1. メッセージ入力
    │
    ├── 2. WebSocket送信
    │      {
    │        "message": "こんにちは！"
    │      }
    │
    └──→ [ChatConsumer]
            │
            ├── 3. 権限確認
            │      - ユーザー認証
            │      - 送信権限チェック
            │
            ├── 4. データ保存（PostgreSQL）
            │      - chat_chatmessage テーブル
            │      - テナントスキーマ内
            │
            └── 5. ブロードキャスト（Redis）
                    │
                    ├──→ [受信者A]
                    ├──→ [受信者B]
                    └──→ [送信者（エコーバック）]
```

### 3. メッセージ受信フロー

```
[Redis Channel Layer]
    │
    ├── グループメッセージ配信
    │
    └──→ [各接続者のChatConsumer]
            │
            ├── メッセージフォーマット
            │      {
            │        "username": "streamer",
            │        "message": "こんにちは！",
            │        "message_type": "message",
            │        "timestamp": null
            │      }
            │
            └──→ [ブラウザ]
                    │
                    └── DOM更新・表示
```

## 💾 データ保存仕様

### データベース構造

```sql
-- PostgreSQL: localhost スキーマ（テナント固有）

-- チャットルームテーブル
CREATE TABLE chat_chatroom (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    stream_id INTEGER REFERENCES streaming_stream(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- チャットメッセージテーブル
CREATE TABLE chat_chatmessage (
    id SERIAL PRIMARY KEY,
    room_id INTEGER REFERENCES chat_chatroom(id) NOT NULL,
    user_id INTEGER REFERENCES accounts_user(id),
    content TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'message',
    is_deleted BOOLEAN DEFAULT false,
    is_pinned BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX idx_chatmessage_room_created ON chat_chatmessage(room_id, created_at DESC);
CREATE INDEX idx_chatmessage_user ON chat_chatmessage(user_id);
```

### データモデル

#### ChatRoom

| フィールド | 型 | 説明 |
|-----------|-----|------|
| id | Integer | 主キー |
| name | String | ルーム名（stream_{uuid}形式） |
| stream | ForeignKey | 関連するストリーム |
| is_active | Boolean | アクティブ状態 |
| created_at | DateTime | 作成日時 |

#### ChatMessage

| フィールド | 型 | 説明 |
|-----------|-----|------|
| id | Integer | 主キー |
| room | ForeignKey | チャットルーム |
| user | ForeignKey | 送信ユーザー |
| content | Text | メッセージ本文 |
| message_type | String | メッセージ種別 |
| is_deleted | Boolean | 削除フラグ |
| is_pinned | Boolean | ピン留めフラグ |
| created_at | DateTime | 送信日時 |

### メッセージ種別

- `message` - 通常のチャットメッセージ
- `system` - システムメッセージ
- `join` - 入室通知
- `leave` - 退室通知
- `moderation` - モデレーション通知

## 🔌 WebSocket通信プロトコル

### エンドポイント

```
ws://localhost:8000/ws/chat/stream_{stream_id}/
```

### メッセージフォーマット

#### クライアント → サーバー

```javascript
{
    "message": "送信するメッセージ"
}
```

#### サーバー → クライアント

```javascript
{
    "username": "送信者のユーザー名",
    "message": "メッセージ本文",
    "message_type": "message|system|join|leave",
    "timestamp": null  // フロントエンドで追加
}
```

### 接続ライフサイクル

1. **接続確立**
   - WebSocketハンドシェイク
   - 認証確認（Cookieベース）
   - チャットルーム存在確認
   - Redisグループ参加

2. **メッセージ送受信**
   - JSONフォーマットで送受信
   - 自動的にブロードキャスト
   - エラー時は個別通知

3. **接続終了**
   - Redisグループから離脱
   - リソースクリーンアップ
   - 必要に応じて退室通知

## 🔧 実装詳細

### ChatConsumer（apps/chat/consumers.py）

```python
class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for live chat."""
    
    async def connect(self):
        # テナント切り替え
        tenant = Tenant.objects.first()
        with schema_context(tenant.schema_name):
            # ルーム確認・グループ参加
            
    async def receive(self, text_data):
        # メッセージ受信・保存・配信
        
    async def disconnect(self, close_code):
        # クリーンアップ処理
```

### フロントエンド（templates/streaming/watch.html）

```javascript
// WebSocket接続
const chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/stream_' + streamId + '/'
);

// メッセージ送信
chatSocket.send(JSON.stringify({
    'message': message
}));

// メッセージ受信
chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    // DOM更新処理
};
```

## 🔒 セキュリティ

### 認証・認可

1. **WebSocket認証**
   - Cookieベースのセッション認証
   - Django認証システムと連携
   - 未認証ユーザーは接続拒否

2. **権限チェック**
   - メッセージ送信前に権限確認
   - BANユーザーのブロック
   - レート制限（実装予定）

### データ保護

1. **XSS対策**
   - HTMLエスケープ処理
   - サニタイゼーション

2. **SQLインジェクション対策**
   - Django ORMによる自動エスケープ
   - パラメータ化クエリ

3. **CSRF対策**
   - WebSocketはOriginヘッダチェック
   - APIエンドポイントはCSRFトークン必須

## 📈 パフォーマンス最適化

### スケーラビリティ

1. **水平スケーリング**
   - Redis Channel Layerによる分散
   - 複数のDaphneワーカー対応

2. **キャッシング**
   - メッセージ履歴のキャッシュ
   - ユーザー情報のキャッシュ

3. **データベース最適化**
   - インデックスの適切な設定
   - 古いメッセージの定期削除

### モニタリング

- WebSocket接続数の監視
- メッセージ送信レートの監視
- エラー率の追跡
- レスポンスタイムの測定

## 🚀 今後の拡張予定

- [ ] メッセージの編集・削除機能
- [ ] リアクション（絵文字）機能
- [ ] メンション機能
- [ ] メッセージの検索機能
- [ ] モデレーション強化（自動フィルタリング）
- [ ] スーパーチャット（投げ銭）機能
- [ ] チャットリプレイ機能
- [ ] 多言語対応

---

**作成日**: 2025-09-01  
**最終更新**: 2025-09-01  
**バージョン**: 1.0.0