# 権限管理システム ドキュメント

## 📋 概要

FanCloud TV(仮)では、4階層のユーザーロールベースアクセス制御（RBAC）システムを採用しています。各ユーザーは特定のロールとメンバーシップを持ち、それに応じた権限と機能にアクセスできます。

## 🏷️ ユーザーロール

### 1. System Admin（システム管理者）
- **権限レベル**: 最高
- **説明**: システム全体を管理する権限を持つ
- **バッジ**: 🔴 赤色
- **機能**:
  - 全ユーザーの管理
  - システム設定の変更
  - Django Admin へのフルアクセス
  - 配信権限の付与/取り消し
  - ユーザーロールの変更
  - システム統計ダッシュボード

### 2. Tenant Admin（テナント管理者）
- **権限レベル**: 高
- **説明**: テナント内のユーザーとコンテンツを管理
- **バッジ**: 🟡 黄色
- **機能**:
  - テナント内ユーザーの管理
  - コンテンツの管理・モデレーション
  - 配信権限の付与/取り消し
  - ユーザーロール変更（System Admin除く）
  - 配信機能の利用

### 3. Tenant User（配信者）
- **権限レベル**: 中
- **説明**: 配信とコンテンツ作成を行うユーザー
- **バッジ**: 🔵 青色
- **機能**:
  - ライブ配信の開始/終了
  - 動画コンテンツのアップロード
  - 配信設定の管理
  - チャットモデレーション
  - 配信統計の確認

### 4. Subscriber（登録者）
- **権限レベル**: 基本
- **説明**: 動画視聴とチャット参加を行う一般ユーザー
- **バッジ**: ⚫ グレー
- **機能**:
  - 動画視聴
  - ライブ配信視聴
  - チャット参加
  - チャンネル登録/フォロー
  - プロフィール管理

## 💳 メンバーシップ

### Premium（プレミアム会員）
- **バッジ**: ⭐ 金色
- **特典**:
  - 高画質配信視聴
  - 広告なし視聴
  - 特別なチャット機能
  - 優先サポート

### Free（無料会員）
- **バッジ**: 🆓 ライト
- **制限**:
  - 標準画質での視聴
  - 広告表示
  - 基本チャット機能のみ

## 🔧 権限チェック機能

### デコレータベースの権限制御

```python
# ロール指定
@role_required(['system_admin', 'tenant_admin'])
def admin_view(request):
    pass

# 特定ロール限定
@system_admin_required
def system_view(request):
    pass

# 配信権限必須
@streaming_permission_required  
def stream_view(request):
    pass

# プレミアム会員限定
@premium_required
def premium_view(request):
    pass
```

### クラスベースビュー用ミックスイン

```python
class AdminView(PermissionMixin, View):
    required_roles = ['system_admin', 'tenant_admin']
    require_streaming = False
    require_premium = False
```

### テンプレートでの権限チェック

```html
<!-- ロール確認 -->
{% if perms.is_system_admin %}
    <a href="{% url 'accounts:admin_system' %}">システム管理</a>
{% endif %}

<!-- 配信権限確認 -->
{% if perms.can_stream %}
    <a href="{% url 'streaming:create' %}">配信開始</a>
{% endif %}

<!-- ユーザー管理権限確認 -->
{% if perms.can_manage_users %}
    <a href="{% url 'accounts:admin_users' %}">ユーザー管理</a>
{% endif %}
```

## 🧪 テストユーザー

開発・テスト環境で利用可能なテストユーザー一覧：

| ユーザー名 | ロール | メンバーシップ | 配信権限 | パスワード | メールアドレス |
|-----------|--------|---------------|----------|-----------|------------|
| **sysadmin** | System Admin | Premium | ✅ | test123456 | sysadmin@example.com |
| **tenantadmin** | Tenant Admin | Premium | ✅ | test123456 | tenantadmin@example.com |
| **streamer** | Tenant User | Premium | ✅ | test123456 | streamer@example.com |
| **viewer** | Subscriber | Free | ❌ | test123456 | viewer@example.com |
| **premium_viewer** | Subscriber | Premium | ❌ | test123456 | premium@example.com |

## 🌐 関連URL

### 認証・アカウント管理
- **ログイン**: http://localhost:8000/accounts/login/
- **ログアウト**: http://localhost:8000/accounts/logout/
- **新規登録**: http://localhost:8000/accounts/register/
- **プロフィール**: http://localhost:8000/accounts/profile/
- **設定**: http://localhost:8000/accounts/settings/

### 管理機能（管理者権限必須）
- **ユーザー管理**: http://localhost:8000/accounts/admin/users/
- **システム管理**: http://localhost:8000/accounts/admin/system/
- **Django Admin**: http://localhost:8000/admin/

### API エンドポイント（管理者権限必須）
- **ロール更新**: `POST /accounts/admin/api/update-role/`
- **配信権限切替**: `POST /accounts/admin/api/toggle-streaming/`
- **メンバーシップ更新**: `POST /accounts/admin/api/update-membership/`

### コンテンツ・配信
- **ホーム**: http://localhost:8000/
- **ライブ配信一覧**: http://localhost:8000/live/
- **トレンド**: http://localhost:8000/content/trending/
- **登録チャンネル**: http://localhost:8000/content/subscriptions/
- **配信開始**: http://localhost:8000/create/ （配信権限必須）

## 🔍 権限テスト手順

### 1. 管理者機能のテスト

1. `sysadmin` または `tenantadmin` でログイン
2. 右上のユーザーアイコンをクリック
3. 「ユーザー管理」メニューが表示されることを確認
4. ユーザー管理画面で以下を確認：
   - ユーザー一覧表示
   - ロールバッジの色分け
   - 統計情報の表示
   - 検索・フィルタ機能

### 2. 権限変更のテスト

1. 管理者でユーザー管理画面にアクセス
2. 任意のユーザーの「操作」列のドロップダウンをクリック
3. ロール変更を選択し、変更を実行
4. 配信権限の付与/取り消しを実行
5. 変更がリアルタイムで反映されることを確認

### 3. 各ロールでの機能確認

各テストユーザーでログインし、以下を確認：

- **System Admin**: 全機能へのアクセス
- **Tenant Admin**: ユーザー管理機能へのアクセス
- **Tenant User**: 配信開始ボタンの表示
- **Subscriber**: 管理機能へのアクセス不可
- **Premium Member**: プレミアム限定機能へのアクセス

### 4. 権限エラーのテスト

1. 権限のないユーザーで管理画面URLに直接アクセス
2. 「権限がありません」エラーが表示されることを確認
3. 適切なリダイレクトが行われることを確認

## 🛠️ 権限カスタマイズ

新しい権限を追加する場合：

### 1. モデルに権限フィールドを追加

```python
class User(AbstractUser):
    can_moderate = models.BooleanField(default=False)
    
    def can_moderate_content(self):
        return self.can_moderate and self.can_manage_content()
```

### 2. 権限チェック関数を作成

```python
def moderation_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not request.user.can_moderate_content():
            return HttpResponseForbidden("モデレーション権限がありません")
        return view_func(request, *args, **kwargs)
    return wrapped_view
```

### 3. コンテキストプロセッサを更新

```python
def get_user_permissions(user):
    return {
        # 既存の権限...
        'can_moderate_content': user.can_moderate_content(),
    }
```

## 📚 関連ファイル

- **モデル**: `apps/accounts/models.py`
- **権限デコレータ**: `apps/accounts/permissions.py`
- **管理ビュー**: `apps/accounts/views_admin.py`
- **コンテキストプロセッサ**: `apps/accounts/context_processors.py`
- **管理テンプレート**: `templates/accounts/admin/`
- **Django Admin設定**: `apps/accounts/admin.py`

---

**作成日**: 2025-09-01  
**最終更新**: 2025-09-01  
**バージョン**: 1.0