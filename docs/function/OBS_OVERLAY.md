# 🎥 OBS チャットオーバーレイ機能

## 📋 目次

- [概要](#概要)
- [機能特徴](#機能特徴)
- [技術仕様](#技術仕様)
- [セットアップ手順](#セットアップ手順)
- [使用方法](#使用方法)
- [カスタマイズ](#カスタマイズ)
- [トラブルシューティング](#トラブルシューティング)
- [今後の改善予定](#今後の改善予定)

## 📝 概要

FanCloud TVのOBSチャットオーバーレイ機能は、配信者がOBS Studio等の配信ソフトウェアで、ニコニコ動画風のチャットやリアクションを配信画面に重ねて表示できる機能です。視聴者のコメントやリアクションがリアルタイムで画面を横切ることで、より一体感のある配信体験を提供します。

## ✨ 機能特徴

### 1. **ニコニコ動画風表示**
- チャットメッセージが右から左へ流れる
- 重複回避アルゴリズムで読みやすい配置
- 10秒間のスムーズなアニメーション

### 2. **2つの表示モード**

#### 🧑 通常モード
- ユーザー名付きメッセージ表示
- 例: `viewer: こんにちは！`
- 誰が発言したかわかりやすい

#### 🥸 匿名モード（ニコニコ風）
- ユーザー名を非表示
- 例: `こんにちは！`
- よりニコニコ動画らしい雰囲気

### 3. **リアクション対応**
- YouTubeLive風のスタンプ/リアクション表示
- 6種類のSVGスタンプ対応
  - 😊 smile
  - 😲 surprise
  - 😢 cry
  - ❤️ love
  - 😱 scream
  - 😠 angry

### 4. **セキュリティ**
- トークンベース認証
- 配信者のみアクセス可能
- 推測不可能な64文字のセキュアトークン

## 🔧 技術仕様

### アーキテクチャ

```
[OBS Studio]
    │
    ├── ブラウザソース
    │   └── オーバーレイHTML (1920x1080)
    │       ├── グリーンバック (#00FF00)
    │       └── WebSocket接続
    │
    └── クロマキーフィルタ
        └── 緑色を透明化

[Django Backend]
    │
    ├── WebSocket (Django Channels)
    │   └── ChatConsumer
    │
    ├── Redis (メッセージブローカー)
    │
    └── PostgreSQL
        └── StreamReaction (履歴保存)
```

### データベース構造

OBSオーバーレイの情報は`streaming_stream`テーブルで管理されています：

```sql
-- PostgreSQL テーブル構造
CREATE TABLE streaming_stream (
    id SERIAL PRIMARY KEY,
    stream_id VARCHAR(100) UNIQUE,
    title VARCHAR(200),
    streamer_id INTEGER,
    
    -- OBS Overlay 関連フィールド
    obs_overlay_token VARCHAR(64),      -- セキュアアクセストークン (64文字)
    obs_overlay_anonymous BOOLEAN,      -- 匿名モードフラグ (TRUE/FALSE)
    
    -- その他のフィールド...
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

```python
# apps/streaming/models.py - Django モデル定義
class Stream(models.Model):
    # OBS Overlay settings
    obs_overlay_token = models.CharField(max_length=64, blank=True, 
                                       help_text='OBS用オーバーレイアクセストークン')
    obs_overlay_anonymous = models.BooleanField(default=False, 
                                              help_text='ユーザー名を非表示にする（ニコニコ風匿名モード）')
    
    def generate_obs_overlay_token(self):
        """セキュアなトークン生成"""
        self.obs_overlay_token = secrets.token_urlsafe(32)  # 64文字の安全な文字列
        self.save(update_fields=['obs_overlay_token'])
        return self.obs_overlay_token
    
    def get_obs_overlay_url(self, request=None, anonymous=None):
        """モード別URL生成"""
        # トークンが未生成の場合は自動生成
        if not self.obs_overlay_token:
            self.generate_obs_overlay_token()
        
        url = f"{base_url}/obs/overlay/{self.stream_id}/{self.obs_overlay_token}/"
        
        # 匿名モードパラメータの追加
        if anonymous is True or (anonymous is None and self.obs_overlay_anonymous):
            url += "?anonymous=true"
        elif anonymous is False:
            url += "?anonymous=false"
            
        return url
```

### データ管理の詳細

#### 📊 情報の管理場所

| 項目 | 管理場所 | データ型 | 説明 |
|------|----------|----------|------|
| **HTMLテンプレート** | `templates/obs/overlay.html` | ファイルシステム | 静的なHTML構造・CSS・JavaScript |
| **セキュリティトークン** | `streaming_stream.obs_overlay_token` | VARCHAR(64) | セキュアな認証用64文字文字列 |
| **匿名モード設定** | `streaming_stream.obs_overlay_anonymous` | BOOLEAN | ユーザー名表示/非表示の制御 |
| **ストリーム基本情報** | `streaming_stream.*` | 各種型 | stream_id, title, streamer等 |
| **WebSocket URL** | 動的生成 | - | stream_idから `/ws/chat/{stream_id}/` |

#### 🔄 データの流れ

```
1. 配信者がURL生成ボタンをクリック
   ↓
2. generate_obs_overlay_token() 実行
   ↓  
3. secrets.token_urlsafe(32) で64文字トークン生成
   ↓
4. streaming_stream.obs_overlay_token に保存
   ↓
5. get_obs_overlay_url() でURLを構築
   ↓
6. ダッシュボードに2つのURL表示
   - /obs/overlay/{stream_id}/{token}/?anonymous=false
   - /obs/overlay/{stream_id}/{token}/?anonymous=true
   ↓
7. OBS Studio でブラウザソース追加
   ↓
8. obs_overlay() ビューでトークン認証
   ↓
9. HTMLテンプレートに stream オブジェクト渡し
   ↓
10. JavaScript で WebSocket 接続開始
    ↓ 
11. リアルタイムチャット表示
```

#### 🛡️ セキュリティ管理

- **トークン**: `secrets.token_urlsafe(32)` による暗号学的安全な生成
- **認証**: URLアクセス時にstream_id + tokenの組み合わせで認証
- **再生成**: 必要に応じて新しいトークンで既存URLを無効化
- **テナント分離**: django-tenants により完全なデータベース分離

### WebSocket通信

```javascript
// リアルタイムメッセージ受信
chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    displayFloatingMessage(data);
};

// メッセージ表示処理
function displayFloatingMessage(data) {
    // Y座標の重複回避
    const yPosition = getAvailableYPosition();
    // アニメーション表示
    // 10秒後に自動削除
}
```

## 📋 セットアップ手順

### 1. 配信者側の設定

#### ステップ1: URL生成
1. 配信ダッシュボード → **OBS連携**タブを開く
2. **🔗 URL生成**ボタンをクリック
3. 2つのURLが生成される
   - 通常モード用URL（ユーザー名表示）
   - 匿名モード用URL（ニコニコ動画風）

#### ステップ2: URLコピー
- 使いたいモードのURLをコピー
- 各URLの横にある📋ボタンでコピー可能

### 2. OBS Studio側の設定

#### ステップ1: ブラウザソース追加
1. OBS Studio → ソース → **+** → **ブラウザ**
2. 新規作成で名前を設定（例: "チャットオーバーレイ"）

#### ステップ2: プロパティ設定
```
URL: [コピーしたオーバーレイURL]
幅: 1920
高さ: 1080
FPS: 30
カスタムCSS: （空欄でOK）
```

#### ステップ3: クロマキー設定
1. 追加したブラウザソース → **フィルタ** → **+**
2. **クロマキー**を選択
3. 設定:
   - 色キータイプ: 緑
   - 類似性: 400
   - 滑らかさ: 80
   - キーカラー流出削減: 100

## 💻 使用方法

### 配信開始前

1. **トークン生成**: 初回は必ずURL生成が必要
2. **モード選択**: 配信スタイルに合わせて選択
   - 交流重視 → 通常モード
   - 匿名性重視 → 匿名モード
3. **プレビュー**: 👁ボタンでブラウザで確認
4. **OBSでの表示制御**: ソース一覧の👁ボタンで表示/非表示を切り替え

### 配信中

- チャットとリアクションが自動的に表示
- 視聴者のメッセージがリアルタイムで流れる
- WebSocket接続が自動再接続
- **表示/非表示の制御**: OBS Studio側で即座に切り替え可能

### URLパラメータ

```
# 匿名モードを強制
?anonymous=true

# 通常モードを強制
?anonymous=false

# デバッグ情報表示
?debug=true

# 組み合わせ
?anonymous=true&debug=true
```

## 🎛️ OBSでの制御

### 表示/非表示の切り替え

オーバーレイの表示制御は**OBS Studio側で行います**：

1. **ソース一覧**でブラウザソース（チャットオーバーレイ）を確認
2. **👁ボタン**をクリックして表示/非表示を切り替え
3. **即座に反映**され、配信画面に変更が適用されます

### 利用シーン

- **教育配信**: 重要な説明時にチャットを一時非表示
- **ゲーム配信**: 集中が必要な場面でコメントを隠す
- **企業配信**: プレゼンテーション時の画面整理
- **音楽配信**: 楽曲演奏中のクリーンな画面

### その他のOBS制御

- **位置調整**: ソースを選択してドラッグで移動
- **サイズ調整**: 角をドラッグでリサイズ
- **透明度調整**: フィルタ → 色補正で不透明度を変更
- **レイヤー順序**: ソース一覧で上下に移動

## 🎨 カスタマイズ

### CSS変更可能な要素

```css
/* チャットメッセージスタイル */
.floating-chat-message.normal {
    font-size: 24px;
    color: #FFFFFF;
    background: rgba(0, 0, 0, 0.6);
    padding: 6px 12px;
    border-radius: 20px;
}

/* リアクションスタイル */
.floating-chat-message.reaction {
    font-size: 28px;
    color: #FFD700;
    background: rgba(255, 215, 0, 0.2);
    border: 2px solid #FFD700;
}

/* アニメーション速度 */
@keyframes slideRightToLeft {
    /* 10秒 → 変更可能 */
}
```

### 今後の拡張可能な設定

- フォントサイズ調整
- 背景色/透明度設定
- アニメーション速度調整
- 表示位置（上部/中部/下部）選択
- ユーザー名の色カスタマイズ

## 🔍 トラブルシューティング

### Q: URLが生成できない
**A**: 
- 配信の所有者であることを確認
- ログイン状態を確認
- ブラウザのCookieが有効か確認

### Q: チャットが表示されない
**A**:
- WebSocket接続を確認（F12 → Console）
- OBSでブラウザソースが表示状態になっているか確認（👁ボタン）
- クロマキーの色設定を確認（#00FF00）

### Q: 匿名モードが反映されない
**A**:
- URLに`?anonymous=true`が含まれているか確認
- OBSでURLを再読み込み（更新ボタン）
- ブラウザソースのキャッシュをクリア

### Q: 文字が見えにくい
**A**:
- クロマキーの類似性を調整
- 現在は背景色固定（今後カスタマイズ機能追加予定）

## 🚀 今後の改善予定

### 短期的改善
- [ ] テキスト背景色のカスタマイズ機能
- [ ] フォントサイズの調整機能
- [ ] アニメーション速度の調整
- [ ] 表示エリアの選択（上/中/下）

### 中長期的改善
- [ ] スーパーチャット風の強調表示
- [ ] モデレーター専用表示
- [ ] 配信者コメントの特別表示
- [ ] NGワードフィルタリング
- [ ] 表示数の制限設定
- [ ] カスタムCSS適用機能

### ✅ 完了済み改善
- [x] ~~オーバーレイの有効/無効トグル機能~~ → **OBSでの制御に統一** (v1.1.0)

## 📚 関連ドキュメント

- [CHAT_FLOW.md](./CHAT_FLOW.md) - チャットシステムの詳細
- [PERMISSIONS.md](./PERMISSIONS.md) - 権限システム
- [README.md](../README.md) - プロジェクト概要

## 🗂️ 関連ファイル一覧

### コードファイル
```
apps/streaming/
├── models.py                    # Stream モデル定義
├── views.py                     # obs_overlay, generate_obs_token ビュー
├── urls.py                      # OBS関連URLパターン
└── migrations/
    ├── 0004_stream_obs_overlay_enabled_stream_obs_overlay_token.py
    ├── 0005_stream_obs_overlay_anonymous.py
    └── 0006_remove_stream_obs_overlay_enabled.py

templates/
├── obs/
│   └── overlay.html            # OBSオーバーレイHTMLテンプレート
└── streaming/
    └── dashboard.html          # 配信者ダッシュボード（OBS連携タブ）

docs/
└── OBS_OVERLAY.md             # 本ドキュメント
```

### データベース関連
```sql
-- 主要テーブル
streaming_stream                # ストリーム情報・OBS設定
streaming_streamreaction        # リアクション履歴（統計用）

-- チャット関連テーブル  
chat_chatmessage               # チャットメッセージ
chat_chatstamp                 # スタンプ定義
```

### API エンドポイント
```
GET  /obs/overlay/<stream_id>/<token>/     # オーバーレイHTML表示
POST /api/obs/<stream_id>/token/           # トークン生成
GET  /ws/chat/<stream_id>/                 # WebSocket接続
```

## 🛠 技術サポート

問題が発生した場合は、以下の情報を含めて報告してください：

1. ブラウザとバージョン
2. OBS Studioのバージョン
3. エラーメッセージ（F12 → Console）
4. 使用しているモード（通常/匿名）
5. 配信の状態（ライブ中/待機中）

---

**作成日**: 2025-09-03  
**最終更新**: 2025-09-03  
**バージョン**: 1.1.0 - 不要なトグル機能削除、OBS制御に統一