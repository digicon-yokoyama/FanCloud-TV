# Issue: セッション管理の設定とRedisの使用に関する不整合

## 概要

現在のシステムでは、Redisをキャッシュとして使用しているにも関わらず、セッション管理はデフォルトのデータベースベース（django_session テーブル）を使用している。この設定の不整合により、マイグレーション時に予期しないログアウトが発生する可能性がある。

## 発生した問題

1. **予期しないログアウト**: マイグレーション実行時（特に `migrate moderation zero` 実行後）にユーザーが強制的にログアウトされる
2. **設定の不整合**: Redisが利用可能であるにも関わらず、セッション管理はデータベースを使用

## 現在の設定状況

### Redis設定（config/settings.py）
```python
# Redis & Channels
REDIS_URL = config('REDIS_URL', default='redis://redis:6379/0')

# Caches
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### セッション設定
- `SESSION_ENGINE` の設定なし（デフォルトのデータベースセッションを使用）
- セッション関連設定：
  - `SESSION_COOKIE_AGE = 86400`  # 24時間
  - `SESSION_SAVE_EVERY_REQUEST = True`
  - `SESSION_EXPIRE_AT_BROWSER_CLOSE = False`

## 調査結果

1. **Redis接続**: 正常に動作中
2. **Redis使用状況**: Django Channels（WebSocket）のみ使用
3. **セッション保存場所**: PostgreSQLの `django_session` テーブル
4. **マイグレーション影響**: データベーススキーマ変更時にセッションテーブルが影響を受ける可能性

## 検討すべき対応案

### 案1: Redisベースセッションへの移行
**メリット**:
- パフォーマンス向上
- マイグレーションの影響を受けない
- Redis既存設定の活用

**設定例**:
```python
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

**検討事項**:
- セッションの永続化（Redisが停止した場合の影響）
- メモリ使用量の増加
- 既存セッションの移行

### 案2: 現状維持（データベースセッション）
**メリット**:
- セッションの永続性
- 既存設定との互換性

**必要な対策**:
- マイグレーション時のセッション保護機能
- セッション管理の改善

### 案3: ハイブリッド設定
**内容**:
- キャッシュバックエンドとしてのRedis
- フォールバックとしてのデータベース

**設定例**:
```python
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'
```

## 優先度と推奨

**優先度**: 中
**推奨案**: 案3（ハイブリッド設定）

**理由**:
1. パフォーマンス向上とデータ永続性の両立
2. Redis停止時の自動フォールバック
3. マルチテナント環境での安定性

## 実装時の注意点

1. **テナント分離**: マルチテナント環境でのセッション分離の確認
2. **WebSocket互換性**: Django Channelsとの連携確認
3. **セッションキーの重複**: テナント間でのセッションキー重複回避
4. **マイグレーション手順**: 既存セッションの移行計画

## 関連ファイル

- `config/settings.py`: セッション・キャッシュ設定
- `docker-compose.yml`: Redis設定
- `config/asgi.py`: Django Channels設定

## 対応予定

後日、パフォーマンステストと設定変更の影響を検証した上で実装予定。