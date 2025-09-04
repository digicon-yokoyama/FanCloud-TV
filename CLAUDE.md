# CLAUDE.md

このファイルは、このリポジトリでコードを扱う際のClaude Code (claude.ai/code)向けガイダンスです。

## プロジェクト概要

FanCloud TVは、Django 5.2で構築されたマルチテナント対応のYouTube風ライブストリーミング・動画共有プラットフォームです。リアルタイムチャット、ロールベースアクセス制御、django-tenantsによる完全なテナント分離機能を備えています。

## 開発コマンド

### Docker環境

```bash
# 全サービスのビルドと起動
docker compose up -d --build

# ログの確認
docker compose logs -f

# Djangoコンテナへのアクセス
docker compose exec web bash

# Django shell
docker compose exec web python manage.py shell

# サービス停止
docker compose down

# データベースリセット（開発環境のみ）
docker compose down -v && docker compose up -d
```

### データベース管理

```bash
# 共有アプリのマイグレーション実行
docker compose exec web python manage.py migrate_schemas --shared

# テナントアプリのマイグレーション実行
docker compose exec web python manage.py migrate_schemas --tenant

# マイグレーションファイル作成
docker compose exec web python manage.py makemigrations

# テストユーザー作成（初期セットアップ後に実行）
docker compose exec web python scripts/create_test_users.py

# VODコンテンツのモックデータ作成
docker compose exec web python manage.py seed_content --reset --count 10
```

### テスト実行

```bash
# 全テスト実行
docker compose exec web python manage.py test

# 特定アプリのテスト実行
docker compose exec web python manage.py test apps.chat
docker compose exec web python manage.py test apps.streaming
```

### データシーディング

```bash
# VODコンテンツのモックデータ作成
docker compose exec web python manage.py seed_content

# オプション:
# --reset: 既存データを削除してから作成
# --count N: 作成する動画数（デフォルト: 12）
# --tenant SCHEMA: 対象テナント（デフォルト: localhost）

# 使用例
docker compose exec web python manage.py seed_content --reset --count 15
```

## アーキテクチャ概要

### マルチテナントアーキテクチャ

- **django-tenants**: テナント毎の完全なデータベーススキーマ分離を提供
- **共有アプリ**: `tenants`, `accounts` - 全テナント間で共有
- **テナントアプリ**: `streaming`, `content`, `chat`, `notifications`など - テナント毎に分離
- **データベース**: PostgreSQL with テナント毎の独立スキーマ
- **ミドルウェア**: `TenantMainMiddleware`がドメインベースのテナントルーティングを処理

### 主要Djangoアプリ

- **accounts**: ロールベース権限システム付きカスタムUserモデル（システム管理者、テナント管理者、テナントユーザー、登録者）
- **tenants**: マルチテナントドメイン・スキーマ管理
- **streaming**: ライブストリーミング機能と動画管理
- **chat**: Django ChannelsによるWebSocketベースリアルタイムチャットシステム
- **content**: 動画コンテンツ管理とレコメンデーション
- **notifications**: プッシュ通知とメール通知
- **analytics**: 使用統計とメトリクス追跡
- **moderation**: コンテンツモデレーションとユーザー管理

### 技術スタック

- **バックエンド**: Django 5.2, Django Channels (WebSocket), PostgreSQL, Redis
- **フロントエンド**: Bootstrap 5, Vanilla JavaScript
- **デプロイ**: Docker, Docker Compose
- **キュー/キャッシュ**: Redisによるチャンネルとキャッシング
- **ASGIサーバー**: DaphneによるWebSocketサポート

### ユーザーロールと権限

システムは階層型ロールベースアクセス制御を実装しています：

1. **システム管理者** (`system_admin`): 全システムアクセス、Django admin権限
2. **テナント管理者** (`tenant_admin`): テナントユーザー管理、コンテンツモデレーション
3. **テナントユーザー** (`tenant_user`): コンテンツ配信、自コンテンツ管理
4. **登録者** (`subscriber`): コンテンツ視聴、チャット参加

メンバーシップタイプ: Free（無料）とPremium（有料）で異なる機能アクセスレベル

### WebSocketアーキテクチャ

- **チャットシステム**: Django Channelsによるリアルタイムチャット
- **視聴者数**: ライブ視聴者数のリアルタイム更新
- **チャンネルレイヤー**: WebSocket通信用Redis連携チャンネルレイヤー
- **ルーティング**: WebSocket URLは`config/routing.py`で定義

## 開発ガイドライン

### カスタムUserモデル

このプロジェクトはAbstractUserを拡張したカスタムUserモデル（`accounts.User`）を使用し、ストリーミング固有のフィールドを持ちます：
- ロールベース権限
- ストリーミング機能
- プロフィール情報
- メンバーシップレベル

### マルチテナント考慮事項

- テナント固有アプリを扱う際は常にテナントコンテキストを意識する
- テナント対応モデルとクエリを使用する
- 異なるテナントスキーマ間で機能をテストする
- 共有アプリはテナントアプリを直接参照してはならない

### テスト環境

異なるロールのテストユーザーが自動作成されます：
- `sysadmin` / `tenantadmin` / `streamer` / `viewer` / `premium_viewer`
- 全テストアカウントのパスワード: `test123456`

### Dockerサービス

- **web**: Djangoアプリケーション (ポート8000)
- **db**: PostgreSQLデータベース (ポート5432)
- **redis**: チャンネル/キャッシュ用Redis (ポート6379)

### 設定

- 設定ファイル: `config/settings.py`
- 環境変数: `.env` (`.env.example`からコピー)
- WebSocketルーティング: `config/routing.py`
- ASGIアプリケーション: `config/asgi.py`

## 一般的な開発タスク

### 新機能追加

1. 共有アプリとテナントアプリ両方に適切なマイグレーション作成
2. マルチテナントへの影響を考慮
3. 適切なロールベースアクセス制御の実装
4. リアルタイム機能が必要な場合はWebSocket機能追加
5. 異なるユーザーロールとテナントコンテキスト間でテスト

### WebSocket問題のデバッグ

1. Redis接続確認: `docker compose exec redis redis-cli ping`
2. 設定内のチャンネルレイヤー設定確認
3. ブラウザ開発者ツールでWebSocket接続監視
4. Django Channelsルーティング設定確認

### データベーススキーマ変更

1. 変更が共有アプリかテナントアプリかを識別
2. アプリタイプに基づく適切なマイグレーションコマンド実行
3. 共有・テナントスキーマ両方でマイグレーションテスト
4. 複雑な変更にはデータマイグレーションスクリプトを検討

### 権限システムの使用

- `apps.accounts.permissions`の権限デコレータを使用
- 権限チェック用テンプレートコンテキストプロセッサの活用
- テストアカウントで異なるユーザーロールをテスト
- 詳細な権限システムドキュメントは`docs/function/PERMISSIONS.md`を参照

## 禁止事項

### 絵文字の使用禁止
- **NEVER use emojis (絵文字) in any code, templates, or fallback content**
- 絵文字は日本語環境でのフォント表示問題やアクセシビリティの問題を引き起こすため、一切使用しない
- フォールバックが必要な場合は適切なアイコンフォント（Bootstrap Icons）またはテキストベースの代替手段を使用する

### 特定企業・サービス名の使用禁止
- **NEVER include specific company or service names (YouTube, Google, etc.) in code, function names, class names, or comments**
- コード内で特定企業・サービス名を参照することは法的問題やブランド問題を引き起こす可能性がある
- 機能を説明する汎用的で中立的な命名を使用する
- 例: `youtube_time` → `readable_time`, `google_auth` → `oauth_auth`
- コメントや説明で「○○風の」という表現も避け、機能自体を説明する

### UIデザインガイドライン
- **NEVER use overly colorful designs that impair readability**
- 管理画面やダッシュボードUIでは落ち着いた配色を使用する
- カードヘッダーには原色ではなく`bg-light`（淡いグレー）を使用する
- ボタンはカラフルな色ではなく`btn-outline-secondary`（グレー系）を基本とする
- バッジやラベルも`bg-secondary`（グレー）を基本とし、重要度に応じて控えめに色を使用する
- 全体的な視認性とプロフェッショナル感を重視し、目に優しいデザインを心がける
- 色による機能区別が必要な場合は、アイコンやテキストでの補完も併用する

## ドキュメント構成

このプロジェクトのドキュメントは以下の構成で整理されています：

### `docs/` ディレクトリ構成

```
docs/
├── README.md              # プロジェクト概要とクイックスタート
├── ROADMAP.md            # 全体開発計画とフェーズ管理
├── FILE_STRUCTURE.md     # コードベース構造とアーキテクチャ
├── function/             # 機能仕様・設計ドキュメント
│   ├── CHAT_FLOW.md      # チャットシステムのフローと仕様
│   ├── OBS_OVERLAY.md    # OBS連携機能の詳細設計
│   ├── PERMISSIONS.md    # 権限システムの詳細仕様
│   └── TEMPLATE_FILTERS.md # テンプレートフィルターの仕様
└── issue/                # 問題・修正事項の管理
    ├── Fix_CHAT_INPUT_ISSUE.md   # チャット入力問題の修正記録
    └── Fix_template_ISSUES.md    # テンプレート関連問題の修正記録
```

### ドキュメント参照ガイドライン

- **機能実装時**: `docs/function/` 配下の該当ファイルを参照
- **問題修正時**: `docs/issue/` 配下の関連ファイルを確認
- **全体把握**: `docs/README.md` と `docs/ROADMAP.md` を参照
- **アーキテクチャ理解**: `docs/FILE_STRUCTURE.md` を参照

## 作業実行の重要原則

### ユーザー指示の厳格な遵守
- **NEVER exceed the scope of explicit user instructions**
- ユーザーが明確に依頼したタスクのみを実行する
- 追加の改善や関連機能は、ユーザーから明示的な許可がない限り実装しない
- ROADMAPやドキュメントに記載されていても、ユーザーが依頼していないタスクは実行しない

### 作業範囲の確認原則
- **作業開始前**: 何を実装するか具体的に確認する
- **作業中**: スコープを拡大する前に必ずユーザーに確認する
- **作業後**: 依頼された内容が完了しているかを正確に判断する
- **不明な場合**: 推測で進めず、ユーザーに質問して明確化する

### データ操作の慎重原則
- **NEVER delete or modify existing user data without explicit permission**
- データベースの削除・変更操作は最高度の注意を払う
- 「モックデータの削除」指示でも、何が削除対象かを事前に特定・確認する
- ロールバック時は「自分が追加したもの」と「既存のもの」を明確に区別する
- データベース操作前に、削除対象の詳細をユーザーに確認する

### 効率性とリソース管理
- **無駄なトークン消費を避ける**
- 依頼されていない機能の実装でリソースを浪費しない
- 作業完了の判断を正確に行い、不必要な追加実装を避ける
- ユーザーの時間とコストを最大限尊重する

### エラー対応と責任
- **ミスの早期認識と即座の停止**
- ユーザーから指摘を受けた場合は即座に作業を停止し状況を確認する
- 問題の根本原因を正確に把握し改善策を実行する
- 同じ問題を繰り返さないための仕組みを構築する

これらの原則に違反した場合は、即座に作業を停止し、ユーザーに状況を報告して指示を仰ぐこと。