# FanCloud TV(仮) - 動画配信プラットフォーム

## 📋 プロジェクト概要

YouTube風のマルチテナント対応動画配信プラットフォーム。リアルタイム配信、VOD、チャット機能を備えた総合的な動画配信サービスです。

## 🛠️ 技術スタック

- **Backend**: Django 5.2, PostgreSQL, Redis
- **Frontend**: Django Templates, Bootstrap 5, JavaScript
- **Streaming**: Mock Services (将来的にHLS/WebRTC対応予定)
- **Containerization**: Docker, Docker Compose
- **Architecture**: Multi-tenant (django-tenants)

## 🚀 クイックスタート

### 1. 環境構築

```bash
# リポジトリをクローン
git clone <repository-url>
cd you-clone

# コンテナを起動
docker-compose up -d

# データベースマイグレーション
docker-compose exec web python manage.py migrate

# 管理者アカウント作成
docker-compose exec web python manage.py createsuperuser
```

### 2. テストユーザー作成

```bash
# テストユーザーを自動作成
docker-compose exec web python create_test_users.py
```

### 3. アプリケーション起動

- **Webアプリ**: http://localhost:8000/
- **Django Admin**: http://localhost:8000/admin/

## 📖 ドキュメント

- **[権限管理システム](PERMISSIONS.md)** - ユーザーロール・権限の詳細
- **[開発ロードマップ](../ROADMAP.md)** - 機能実装計画
- **API仕様**: 準備中
- **デプロイガイド**: 準備中

## 🎯 主な機能

### ✅ 実装済み
- ✅ **4階層ユーザーロール制御**
- ✅ **認証システム** (ログイン/登録/プロフィール)
- ✅ **管理者機能** (ユーザー管理・権限変更)
- ✅ **基本UI** (YouTube風レスポンシブデザイン)
- ✅ **権限ベースナビゲーション**
- ✅ **エラーページ** (404/500)
- ✅ **リーガルページ** (利用規約/プライバシーポリシー)

### 🚧 開発中
- 🚧 **ライブ配信機能の拡張**
- 🚧 **リアルタイムチャットシステム**
- 🚧 **VODアップロード・管理**

### 📋 予定
- 📋 **HLS/WebRTC対応**
- 📋 **分析ダッシュボード**
- 📋 **モバイルアプリ対応**

## 👥 ユーザーロール

| ロール | 説明 | 主な機能 |
|--------|------|----------|
| 🔴 **System Admin** | システム管理者 | 全権限、システム設定 |
| 🟡 **Tenant Admin** | テナント管理者 | ユーザー管理、コンテンツ管理 |
| 🔵 **Tenant User** | 配信者 | 配信開始、コンテンツ作成 |
| ⚫ **Subscriber** | 登録者 | 視聴、チャット参加 |

詳細は **[権限管理システムドキュメント](PERMISSIONS.md)** を参照してください。

## 🧪 テスト環境

### テストユーザー

| ユーザー名 | ロール | パスワード | 用途 |
|-----------|--------|-----------|------|
| `sysadmin` | System Admin | test123456 | システム管理テスト |
| `tenantadmin` | Tenant Admin | test123456 | テナント管理テスト |
| `streamer` | Tenant User | test123456 | 配信機能テスト |
| `viewer` | Subscriber | test123456 | 視聴機能テスト |
| `premium_viewer` | Premium Subscriber | test123456 | プレミアム機能テスト |

### テスト手順

1. 各ユーザーでログインして権限を確認
2. 管理者で **[ユーザー管理](http://localhost:8000/accounts/admin/users/)** にアクセス
3. 権限変更・配信権限付与をテスト

## 🏗️ アーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│                 │    │                 │    │                 │
│ - Bootstrap 5   │    │ - Django 5.2    │    │ - PostgreSQL    │
│ - JavaScript    │◄──►│ - REST APIs     │◄──►│ - Redis Cache   │
│ - Templates     │    │ - WebSocket     │    │ - File Storage  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### マルチテナント構成

```
┌─────────────────────────────────────┐
│           Shared Schema             │
│  - Users, Tenants, Auth, Admin      │
└─────────────────────────────────────┘
┌─────────────────┐ ┌─────────────────┐
│   Tenant A      │ │   Tenant B      │
│ - Streams       │ │ - Streams       │
│ - Content       │ │ - Content       │
│ - Chat          │ │ - Chat          │
└─────────────────┘ └─────────────────┘
```

## 📂 プロジェクト構造

```
you-clone/
├── apps/
│   ├── accounts/       # ユーザー認証・権限管理
│   ├── streaming/      # ライブ配信機能
│   ├── content/        # コンテンツ管理
│   ├── chat/          # チャット機能
│   ├── analytics/     # 分析・統計
│   └── tenants/       # マルチテナント
├── templates/         # HTMLテンプレート
├── static/           # 静的ファイル
├── config/           # Django設定
├── docs/             # ドキュメント
└── docker-compose.yml
```

## 🌐 環境設定

### 環境変数

```bash
# 基本設定
DEBUG=True
SECRET_KEY=your-secret-key

# データベース
DATABASE_URL=postgresql://user:pass@db:5432/dbname

# Redis
REDIS_URL=redis://redis:6379/0

# 配信設定
VIDEO_SETTINGS__MOCK_MODE=True
```

### Docker構成

- **web**: Django アプリケーション
- **db**: PostgreSQL データベース  
- **redis**: Redis キャッシュ・セッションストア

## 🔧 開発

### ローカル開発環境

```bash
# コンテナ起動
docker-compose up -d

# ログ確認
docker-compose logs -f web

# コンテナ内でコマンド実行
docker-compose exec web python manage.py shell
```

### コード規約

- **Python**: PEP 8準拠
- **HTML**: Bootstrap 5クラス使用
- **JavaScript**: ES6+ 記法推奨
- **CSS**: 既存変数・クラス活用

### テスト実行

```bash
# Django テスト
docker-compose exec web python manage.py test

# 個別アプリテスト
docker-compose exec web python manage.py test apps.accounts
```

## 🤝 コントリビューション

1. Feature ブランチを作成
2. 変更を実装
3. テストを追加・実行
4. プルリクエストを作成

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

---

**プロジェクト開始**: 2025-08-29  
**最終更新**: 2025-09-01  
**現在のフェーズ**: Phase 2 (コア機能実装)