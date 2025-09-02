# 🎥 FanCloud TV - YouTubeクローン配信プラットフォーム

ライブストリーミングと動画共有のためのマルチテナント対応プラットフォーム

## 📋 目次

- [概要](#概要)
- [主な機能](#主な機能)
- [技術スタック](#技術スタック)
- [セットアップ手順](#セットアップ手順)
- [テストアカウント](#テストアカウント)
- [開発](#開発)
- [ドキュメント](#ドキュメント)

## 📝 概要

FanCloud TVは、YouTubeライクなインターフェースを持つライブストリーミング・動画共有プラットフォームです。マルチテナント対応により、複数の独立したストリーミングサービスを単一のアプリケーションで提供できます。

## ✨ 主な機能

- 🎬 **ライブストリーミング** - リアルタイム配信機能
- 💬 **リアルタイムチャット** - WebSocketを使用したライブチャット
- 👥 **ユーザー管理** - 階層型ロールベースアクセス制御（RBAC）
- 🏢 **マルチテナント** - django-tenantsによる完全分離型マルチテナント
- 📊 **配信ダッシュボード** - YouTube Studio風の配信管理画面
- 🎨 **レスポンシブUI** - Bootstrap 5によるモバイル対応デザイン

## 🛠 技術スタック

### バックエンド
- **Django 5.2** - Webフレームワーク
- **Django Channels** - WebSocket対応
- **django-tenants** - マルチテナント機能
- **PostgreSQL** - データベース
- **Redis** - キャッシュ・Channel Layer
- **Daphne** - ASGIサーバー

### フロントエンド
- **Bootstrap 5** - UIフレームワーク
- **Vanilla JavaScript** - インタラクティブ機能
- **WebSocket API** - リアルタイム通信

## 🚀 セットアップ手順

### 前提条件

- Docker & Docker Compose
- Python 3.13+
- Git

### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/you-clone.git
cd you-clone
```

### 2. 環境変数の設定

```bash
cp .env.example .env
# .envファイルを編集して必要な設定を行う
```

### 3. Dockerコンテナの起動

```bash
# コンテナのビルドと起動
docker-compose up -d --build

# ログの確認
docker-compose logs -f
```

### 4. データベースの初期設定

```bash
# 1. マイグレーション実行（共有アプリ）
docker-compose exec web python manage.py migrate_schemas --shared

# 2. テナントの作成
cat << 'EOF' | docker-compose exec -T web python manage.py shell
from apps.tenants.models import Tenant, Domain

# localhostテナントの作成
if not Tenant.objects.filter(schema_name='localhost').exists():
    tenant = Tenant(
        schema_name='localhost',
        name='Localhost Tenant'
    )
    tenant.save()
    
    domain = Domain()
    domain.domain = 'localhost'
    domain.tenant = tenant
    domain.is_primary = True
    domain.save()
    
    print("✅ Tenant created: localhost")
else:
    print("ℹ️  Tenant already exists: localhost")
EOF

# 3. テストユーザーの作成
docker-compose exec web python scripts/create_test_users.py
```

### 5. アクセス確認

ブラウザで http://localhost:8000 にアクセス

## 👤 テストアカウント

セットアップ完了後、以下のテストアカウントが利用可能です：

| ユーザー名 | パスワード | ロール | 権限 |
|-----------|-----------|--------|------|
| **sysadmin** | test123456 | システム管理者 | 全権限（Django Admin含む） |
| **tenantadmin** | test123456 | テナント管理者 | ユーザー管理・配信管理 |
| **streamer** | test123456 | 配信者 | ライブ配信・コンテンツ管理 |
| **viewer** | test123456 | 視聴者（無料） | 視聴のみ |
| **premium_viewer** | test123456 | 視聴者（プレミアム） | 視聴・特典機能 |

## 🔧 開発

### 開発サーバーの起動

```bash
# 開発環境の起動
docker-compose up

# コンテナに入る
docker-compose exec web bash

# Django shellの起動
docker-compose exec web python manage.py shell

# ログの確認
docker-compose logs -f web
```

### マイグレーション

```bash
# マイグレーションファイルの作成
docker-compose exec web python manage.py makemigrations

# マイグレーションの実行（共有アプリ）
docker-compose exec web python manage.py migrate_schemas --shared

# マイグレーションの実行（テナント）
docker-compose exec web python manage.py migrate_schemas --tenant
```

### テストの実行

```bash
# 全テストの実行
docker-compose exec web python manage.py test

# 特定アプリのテスト
docker-compose exec web python manage.py test apps.chat
```

## 📚 ドキュメント

- [権限管理システム](docs/PERMISSIONS.md) - ロールベースアクセス制御の詳細
- [チャットシステムフロー](docs/CHAT_FLOW.md) - リアルタイムチャットの仕組み
- [API仕様書](docs/API.md) - REST APIエンドポイント
- [配信設定ガイド](docs/STREAMING.md) - ライブ配信の設定方法

## 🏗 プロジェクト構造

```
you-clone/
├── apps/                 # Djangoアプリケーション
│   ├── accounts/        # ユーザー管理
│   ├── chat/           # チャットシステム
│   ├── streaming/      # 配信機能
│   ├── tenants/        # マルチテナント
│   └── ...
├── config/              # Django設定
├── templates/           # HTMLテンプレート
├── static/             # 静的ファイル
├── media/              # アップロードファイル
├── scripts/            # ユーティリティスクリプト
├── docs/               # ドキュメント
├── docker-compose.yml  # Docker設定
└── requirements.txt    # Python依存関係
```

## 🐛 トラブルシューティング

### WebSocket接続エラー

```bash
# Redisの確認
docker-compose exec redis redis-cli ping

# Daphneの再起動
docker-compose restart web
```

### マイグレーションエラー

```bash
# データベースのリセット（開発環境のみ）
docker-compose down -v
docker-compose up -d
# セットアップ手順を最初から実行
```

### ログイン不可

```bash
# テストユーザーの再作成
docker-compose exec web python scripts/create_test_users.py
```

## 📄 ライセンス

このプロジェクトは教育目的で作成されています。

## 🤝 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## 📧 お問い合わせ

- プロジェクトリンク: [https://github.com/yourusername/you-clone](https://github.com/yourusername/you-clone)

---

**作成日**: 2025-09-01  
**最終更新**: 2025-09-01  
**バージョン**: 1.0.0