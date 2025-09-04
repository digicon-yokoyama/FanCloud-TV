# 現在確認されている問題一覧

## 🔴 高優先度の問題

### 1. テンプレート欠落エラー
**問題**: 特定のページでテンプレートが存在せず500エラーが発生

**影響範囲**:
- `/live/` ページ → `TemplateDoesNotExist: streaming/live.html`
- `/content/trending/` ページ → `TemplateDoesNotExist: content/trending.html`

**エラーログ**:
```
django.template.exceptions.TemplateDoesNotExist: streaming/live.html
django.template.exceptions.TemplateDoesNotExist: content/trending.html
```

**対処法**: 欠落しているテンプレートファイルの作成が必要

### 2. 認証システムの無効化
**問題**: accounts アプリが無効化されているため認証機能が利用不可

**影響範囲**:
- ログイン機能が使用不可
- ユーザー登録機能が使用不可
- `/accounts/login/` で404エラー
- 認証が必要なページでリダイレクトエラー

**エラーログ**:
```
Not Found: /accounts/login/
WARNING 2025-08-29 20:32:55,513 log 7 281473389228416 Not Found: /accounts/login/
```

**現在の状態**: 
- `config/settings.py` で `'apps.accounts'` がコメントアウト
- テンプレート内の認証関連URLが `href="#"` で仮設定

## 🟡 中優先度の問題

### 3. ナビゲーションリンクの仮設定
**問題**: ユーザー認証関連のリンクが一時的に無効化

**影響範囲**:
- ログインボタン
- 登録ボタン  
- ログアウトリンク

**現在の状態**: `href="#"` で仮設定中

### 4. 配信カテゴリ関連機能
**問題**: Stream にカテゴリが紐付けされていない

**影響範囲**:
- カテゴリ別の配信フィルタリング機能が未実装
- `StreamCategory` モデルは存在するが活用されていない

## 🟢 低優先度の問題

### 5. Docker Compose 警告
**問題**: 非推奨の設定による警告（既に修正済み）

**状態**: ✅ 修正完了
- `version: '3.8'` の削除済み

### 6. 開発時のセキュリティ設定
**問題**: 本番環境に向けた設定の見直しが必要

**要確認項目**:
- `DEBUG = True` (開発時のみ)
- `SECRET_KEY` のデフォルト値
- `ALLOWED_HOSTS` の設定

## ✅ 正常に動作している機能

### インフラ層
- ✅ PostgreSQL データベース接続
- ✅ Redis 接続
- ✅ Docker コンテナ環境
- ✅ django-tenants マルチテナント機能

### アプリケーション層
- ✅ メインページ (`/`)
- ✅ 動画視聴ページ (`/watch/<stream_id>/`)
- ✅ 管理画面 (`/admin/`)
- ✅ 埋め込みプレイヤー機能
- ✅ Mock 配信サービス
- ✅ WebSocket (Django Channels) 設定

### データベース
- ✅ 全マイグレーション適用済み
- ✅ テナント「Demo Tenant」作成済み
- ✅ 管理者アカウント設定済み (admin/admin123)

## 📋 修正予定

### 即座に対応が必要
1. `streaming/live.html` テンプレート作成
2. `content/trending.html` テンプレート作成

### 短期的に対応が必要  
3. accounts アプリの再有効化
4. 認証システムの復旧
5. URL パターンの修正

### 中長期的に対応が必要
6. カテゴリ機能の実装
7. 本番環境向けセキュリティ設定
8. ユーザーロール・権限システムの実装

---

**最終更新**: 2025-08-29
**システム状態**: 基本機能は動作中、認証系とページテンプレートに課題あり