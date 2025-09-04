# 📁 FanCloud TV - 機能別ファイル構造ガイド

## 概要

このドキュメントは、FanCloud TVプロジェクトの各機能と実装ファイルの対応表です。機能修正や開発時に素早く該当ファイルを見つけられるように設計されています。

## 📋 クイック参照

### 特定の機能を探す場合

| やりたいこと | 参照ファイル |
|-------------|-------------|
| ユーザー認証機能修正 | `apps/accounts/views.py`, `apps/accounts/models.py` |
| ストリーム作成機能 | `apps/streaming/views.py`, `apps/streaming/services.py` |
| 動画アップロード機能 | `apps/content/views.py`, `apps/content/models.py` |
| チャット機能 | `apps/chat/consumers.py`, `apps/chat/views.py` |
| 権限管理 | `apps/accounts/permissions.py` |
| URL設定変更 | `config/urls.py`, 各アプリの`urls.py` |
| テナント機能 | `apps/tenants/models.py`, `config/settings.py` |
| WebSocket設定 | `config/routing.py`, `apps/chat/consumers.py` |
| Docker環境変更 | `docker-compose.yml`, `requirements.txt` |

## 📂 詳細な機能別ファイル一覧

### 🎯 1. ユーザー認証・権限管理 (`apps/accounts/`)

| 機能 | ファイル | 詳細 |
|------|----------|------|
| **ユーザーモデル** | `models.py` | カスタムUserモデル、UserProfile、Follow、ViewHistoryモデル |
| **ビュー関数** | `views.py` | ログイン/ログアウト/登録/プロフィール管理 |
| **管理者ビュー** | `views_admin.py` | ユーザー管理、権限変更機能 |
| **URLルーティング** | `urls.py` | アカウント関連のURLパターン |
| **権限管理** | `permissions.py` | カスタム権限クラス、ロールベース制御 |
| **テンプレートコンテキスト** | `context_processors.py` | ユーザー権限、ロールバッジ、未読通知数のコンテキスト |
| **Admin設定** | `admin.py` | Django Adminのカスタム設定 |

### 📺 2. ライブストリーミング機能 (`apps/streaming/`)

| 機能 | ファイル | 詳細 |
|------|----------|------|
| **ストリームモデル** | `models.py` | Stream、StreamCategory、StreamViewerモデル |
| **ストリーミングサービス** | `services.py` | StreamingServiceクラス、ストリーム制御 |
| **ビュー関数** | `views.py` | ストリーム作成/管理/視聴ページ |
| **URLルーティング** | `urls.py` | ストリーミング関連のURLパターン |
| **Admin設定** | `admin.py` | ストリーム管理画面 |

### 🎬 3. コンテンツ管理機能 (`apps/content/`)

| 機能 | ファイル | 詳細 |
|------|----------|------|
| **動画モデル** | `models.py` | Video、VideoCategory、VideoLike、VideoComment、Playlistモデル |
| **ビュー関数** | `views.py` | 動画アップロード/管理/視聴ページ、お気に入り機能 |
| **URLルーティング** | `urls.py` | コンテンツ関連のURLパターン |
| **管理コマンド** | `management/commands/seed_content.py` | モックコンテンツ生成コマンド |
| **Admin設定** | `admin.py` | コンテンツ管理画面 |

### 💬 4. リアルタイムチャット機能 (`apps/chat/`)

| 機能 | ファイル | 詳細 |
|------|----------|------|
| **チャットモデル** | `models.py` | ChatRoom、ChatMessage、ChatStamp、ChatBan、NGWordモデル |
| **WebSocketコンシューマー** | `consumers.py` | リアルタイムチャット処理、モデレーション機能統合 |
| **ビュー関数** | `views.py` | チャットUI表示、メッセージ管理、モデレーション |
| **ミドルウェア** | `middleware.py` | チャット関連ミドルウェア処理 |
| **URLルーティング** | `urls.py` | チャット関連のURLパターン |
| **管理コマンド** | `management/commands/` | スタンプ作成コマンド（create_default_stamps.py、create_svg_stamps.py） |
| **Admin設定** | `admin.py` | チャット管理画面 |

### 🔔 5. 通知機能 (`apps/notifications/`)

| 機能 | ファイル | 詳細 |
|------|----------|------|
| **通知モデル** | `models.py` | Notification、NotificationSettingモデル定義 |
| **通知サービス** | `services.py` | NotificationServiceクラス、統一通知管理 |
| **ビュー関数** | `views.py` | 通知表示/管理/設定機能 |
| **URLルーティング** | `urls.py` | 通知関連のURLパターン |
| **Admin設定** | `admin.py` | 通知管理画面 |

### 📊 6. 分析機能 (`apps/analytics/`)

| 機能 | ファイル | 詳細 |
|------|----------|------|
| **分析モデル** | `models.py` | 分析データモデル定義 |
| **ビュー関数** | `views.py` | 分析ダッシュボード表示 |
| **URLルーティング** | `urls.py` | 分析関連のURLパターン |
| **Admin設定** | `admin.py` | 分析データ管理画面 |

### ⚖️ 7. モデレーション機能 (`apps/moderation/`)

| 機能 | ファイル | 詳細 |
|------|----------|------|
| **モデレーションモデル** | `models.py` | モデレーションデータモデル |
| **ビュー関数** | `views.py` | モデレーションツール表示 |
| **Admin設定** | `admin.py` | モデレーション管理画面 |

### 🏢 8. マルチテナント機能 (`apps/tenants/`)

| 機能 | ファイル | 詳細 |
|------|----------|------|
| **テナントモデル** | `models.py` | Tenant、Domainモデル（django-tenants拡張） |
| **ビュー関数** | `views.py` | テナント管理機能 |
| **管理コマンド** | `management/commands/create_tenant.py` | テナント作成コマンド |
| **Admin設定** | `admin.py` | テナント管理画面 |

### 📜 9. 法的ページ機能 (`apps/legal/`)

| 機能 | ファイル | 詳細 |
|------|----------|------|
| **ビュー関数** | `views.py` | 利用規約/プライバシーポリシー表示 |
| **URLルーティング** | `urls.py` | 法的ページのURLパターン |

## ⚙️ システム設定・共通機能

| 機能 | ファイル | 詳細 |
|------|----------|------|
| **Django設定** | `config/settings.py` | 全体設定（DB、Redis、テナントなど） |
| **URLルーティング** | `config/urls.py` | メインURL設定 |
| **WSGI/ASGI** | `config/wsgi.py` / `config/asgi.py` | サーバー設定 |
| **ルーティング** | `config/routing.py` | WebSocketルーティング |
| **依存関係** | `requirements.txt` | Pythonパッケージ一覧 |
| **Docker設定** | `docker-compose.yml` / `Dockerfile` | コンテナ構成 |
| **テストユーザー作成** | `create_test_users.py` | テストデータ生成スクリプト |

## 🎨 フロントエンド・テンプレート

| 機能 | ファイル/ディレクトリ | 詳細 |
|------|---------------------|------|
| **ベーステンプレート** | `templates/base/base.html` | 共通レイアウト |
| **アカウント関連** | `templates/accounts/` | ログイン/登録/プロフィール画面 |
| **ストリーミング** | `templates/streaming/` | 配信ページ（作成/視聴/管理） |
| **コンテンツ** | `templates/content/` | 動画ページ、プレイリスト |
| **チャット** | `templates/chat/` | チャットウィジェット、モデレーション画面 |
| **通知** | `templates/notifications/` | 通知センター、設定ページ |
| **OBS連携** | `templates/obs/` | OBSオーバーレイテンプレート |
| **埋め込みプレイヤー** | `templates/embed/` | iframe用プレイヤー |
| **法的ページ** | `templates/legal/` | 利用規約/プライバシーポリシー |
| **静的ファイル** | `static/` | CSS/JS/画像ファイル |

## 📝 ファイル命名規則

各Djangoアプリの標準的なファイル構成:

- **`models.py`**: データモデル定義
- **`views.py`**: ビュー関数・APIエンドポイント
- **`urls.py`**: URLパターンマッピング
- **`admin.py`**: Django Adminカスタマイズ
- **`services.py`**: ビジネスロジック・外部API連携
- **`consumers.py`**: WebSocket処理（リアルタイム機能）
- **`permissions.py`**: カスタム権限ロジック
- **`context_processors.py`**: テンプレートコンテキスト処理
- **`middleware.py`**: カスタムミドルウェア
- **`management/commands/`**: Django管理コマンド
- **`apps.py`**: Djangoアプリ設定

## 🔧 開発時のTips

### 新機能開発時のファイル作成順序
1. **`models.py`** でデータモデル定義
2. **`admin.py`** で管理画面設定（必要に応じて）
3. **`services.py`** でビジネスロジック・外部連携実装（必要に応じて）
4. **`views.py`** でビュー関数・APIエンドポイント実装
5. **`urls.py`** でURLパターン設定
6. **`templates/`** でUI実装
7. **`static/`** でCSS/JS実装（必要に応じて）
8. **`management/commands/`** で管理コマンド実装（必要に応じて）

### 機能修正時の確認ポイント
- **モデル変更**: migrationファイルの作成を忘れずに
- **URL変更**: `config/urls.py`のメイン設定も確認
- **権限関連**: `permissions.py`と`context_processors.py`の確認
- **リアルタイム機能**: `consumers.py`と`routing.py`の確認

## 📚 関連ドキュメント

- **[README.md](../README.md)** - プロジェクト全体概要
- **[function/PERMISSIONS.md](function/PERMISSIONS.md)** - 権限管理システム詳細
- **[ROADMAP.md](ROADMAP.md)** - 開発ロードマップ
- **[function/CHAT_FLOW.md](function/CHAT_FLOW.md)** - チャット機能仕様
- **[function/OBS_OVERLAY.md](function/OBS_OVERLAY.md)** - OBS連携機能詳細
- **[function/TEMPLATE_FILTERS.md](function/TEMPLATE_FILTERS.md)** - カスタムテンプレートフィルター

---

**最終更新**: 2025-09-04  
**ドキュメント作成者**: AI Assistant

## 🆕 最新実装状況 (2025-09-04)

### ✅ 完全実装済み機能

#### チャットシステム
- **WebSocketベースリアルタイムチャット**: 即座更新、接続管理
- **スタンプ機能**: デフォルトスタンプ、SVGアイコン対応
- **モデレーション機能**: NGワード自動フィルタ、ユーザーBAR・タイムアウト
- **チャット履歴**: 全メッセージ保存・表示

#### 通知システム
- **統一通知サービス**: NotificationServiceクラスによる一元管理
- **リアルタイム通知**: ヘッダーベルアイコン、バッジ表示、60秒間隔ポーリング
- **通知設定**: ユーザー別メール・プッシュ通知ON/OFF
- **多様な通知タイプ**: フォロー、コメント、いいね、新動画投稿通知

#### 配信システム
- **YouTube Studio風ダッシュボード**: 配信管理UI完全実装
- **配信状態管理**: 作成・ライブ・終了・エラー状態の完全制御
- **ストリーム設定**: 品質設定、遅延設定、バックアップストリーム
- **レスポンシブ対応**: モバイル・タブレット・デスクトップ最適化

#### ユーザー体験機能
- **お気に入り機能**: VideoLikeモデル連携、完全実装
- **視聴履歴**: ViewHistoryモデル、履歴ページ実装
- **プレイリスト**: 基本UIテンプレート作成（機能は今後実装予定）
- **フォロー機能**: ユーザー間フォロー・アンフォロー機能

#### UI/UX改善
- **動画カード表示**: サムネイル、アバター生成、時間表示フィルター
- **サイドバーナビゲーション**: 完全な動線整備
- **レスポンシブデザイン**: 全画面サイズ対応
- **ライトテーマ統一**: Bootstrap 5ベースの一貫したデザイン

### 🚧 進行中・次期実装予定
- **VODシステム**: 動画アップロード・エンコーディング機能
- **高度チャット管理**: Django Admin統合、詳細分析
- **埋め込み機能**: iframeプレイヤー実装
- **コンテンツモデレーション**: 不適切コンテンツ検出・報告システム
