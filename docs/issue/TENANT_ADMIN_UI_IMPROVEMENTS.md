# テナント管理者UI改善 Issue

## 📋 概要

現在の実装では、テナント管理者向けの専用UIが不足しており、権限に応じた適切な管理インターフェースが提供されていない。権限システムの基盤は完成しているため、主にフロントエンド側のUI実装が必要。

## 🎯 課題

### 現在の問題点

1. **専用ダッシュボードの不在**
   - テナント管理者が利用できる統合的な管理画面がない
   - 各管理機能が分散しており、アクセスしにくい

2. **ナビゲーションの不整合**
   - 権限レベルに応じたメニュー表示の最適化が不十分
   - テナント管理者が利用可能な機能への導線が不明確

3. **権限チェックの不完全性**
   - 一部のテンプレートで権限に応じた表示制御が未実装
   - テナント管理者限定機能の視覚的な区別が不足

4. **管理機能の分散**
   - ユーザー管理、コンテンツ管理、カテゴリ管理が独立
   - 統合的な管理体験の不足

## ✅ 実装済みの基盤

### 権限システム
- **デコレーター**: `@tenant_admin_required` 完備
- **権限チェック関数**: `user.can_manage_users()`, `user.is_tenant_admin()` 動作済み
- **コンテキストプロセッサ**: `perms.is_tenant_admin` テンプレートで利用可能
- **ロールベース制御**: 4階層のユーザーロール完全実装

### 既存の管理機能
- **ユーザー管理**: `/accounts/admin/users/` 実装済み
- **カテゴリ管理**: `/content/admin/categories/` 実装済み
- **権限変更API**: ロール・配信権限の変更機能あり

## 🚀 実装計画

### Phase 1: テナント管理者ダッシュボード作成

#### 1.1 ダッシュボード画面設計
- **URL**: `/tenant/dashboard/`
- **機能**:
  - テナント統計の表示（ユーザー数、動画数、配信数）
  - 最近のアクティビティ
  - クイックアクション（ユーザー管理、カテゴリ管理へのリンク）
  - 重要な通知・アラート

#### 1.2 必要なファイル
```
templates/tenant/
├── dashboard.html          # メインダッシュボード
├── base_admin.html        # 管理者用ベーステンプレート
└── components/
    ├── stats_cards.html   # 統計カード
    ├── recent_activity.html # 最近のアクティビティ
    └── quick_actions.html  # クイックアクション
```

#### 1.3 バックエンド実装
```python
# apps/tenant/views.py
@tenant_admin_required
def dashboard(request):
    # 統計データの取得
    # 最近のアクティビティ
    # ダッシュボード表示
```

### Phase 2: ナビゲーション改善

#### 2.1 メニュー構造の最適化
- **管理者メニュー**の統合
- **権限レベル別表示**の実装
- **アクティブ状態**の管理

#### 2.2 テンプレート修正
```html
<!-- base/base.html での権限チェック強化 -->
{% if perms.is_tenant_admin %}
    <li class="nav-item dropdown">
        <a class="nav-link dropdown-toggle" href="#" id="adminDropdown">
            <i class="bi bi-gear"></i> 管理機能
        </a>
        <ul class="dropdown-menu">
            <li><a href="{% url 'tenant:dashboard' %}">ダッシュボード</a></li>
            <li><a href="{% url 'accounts:admin_users' %}">ユーザー管理</a></li>
            <li><a href="{% url 'content:admin_categories' %}">カテゴリ管理</a></li>
        </ul>
    </li>
{% endif %}
```

### Phase 3: 既存機能の統合・改善

#### 3.1 ユーザー管理機能の強化
- **テナント管理者専用ビュー**の追加
- **権限変更フロー**の改善
- **バルク操作**の実装

#### 3.2 コンテンツ管理機能の追加
- **動画モデレーション**機能
- **コンテンツ統計**表示
- **レポート機能**

#### 3.3 権限チェックの完全化
```html
<!-- 各テンプレートでの権限チェック追加例 -->
{% if perms.is_tenant_admin or video.uploader == user %}
    <a href="{% url 'content:edit_video' video.id %}" class="btn btn-sm btn-outline-primary">
        編集
    </a>
{% endif %}
```

## 🛠️ 技術仕様

### 必要な新規ファイル
```
apps/tenant/
├── __init__.py
├── apps.py
├── views.py              # ダッシュボード、管理機能
├── urls.py               # テナント管理者用URL
├── services.py           # 統計データ取得サービス
└── admin.py

templates/tenant/
├── dashboard.html
├── base_admin.html
└── components/
    ├── stats_cards.html
    ├── recent_activity.html
    └── quick_actions.html

static/css/
└── admin.css            # 管理者UI専用スタイル
```

### URL設計
```python
# config/urls.py
urlpatterns = [
    # ...
    path('tenant/', include('apps.tenant.urls')),
]

# apps/tenant/urls.py
urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('stats/', views.stats_api, name='stats_api'),
    path('activity/', views.recent_activity, name='activity'),
]
```

### データベース変更
- **追加のマイグレーションは不要**
- 既存モデルから統計データを計算

## 📊 工数見積もり

| Phase | 作業内容 | 難易度 | 予想工数 |
|-------|---------|--------|----------|
| **Phase 1** | ダッシュボード作成 | 🟡 Medium | 4-6時間 |
| **Phase 2** | ナビゲーション改善 | 🟢 Easy | 2-3時間 |
| **Phase 3** | 既存機能統合 | 🟡 Medium | 3-4時間 |
| **テスト・調整** | 動作確認・UI調整 | 🟢 Easy | 2-3時間 |

**総工数**: 11-16時間

## 🧪 テスト計画

### 機能テスト
1. **各ロールでのログイン**テスト
   - `tenant_admin` でのダッシュボードアクセス
   - `tenant_user`, `subscriber` でのアクセス拒否確認

2. **権限チェック**テスト
   - 管理機能への適切なアクセス制御
   - UI要素の表示/非表示

3. **統計データ**テスト
   - ダッシュボードでの数値の正確性
   - リアルタイム更新の動作

### UIテスト
- **レスポンシブ**デザインの確認
- **アクセシビリティ**のチェック
- **ナビゲーション**の使いやすさ

## 📝 チェックリスト

### Phase 1: ダッシュボード
- [ ] `apps/tenant/` アプリケーション作成
- [ ] テナント統計サービスの実装
- [ ] ダッシュボードビューの作成
- [ ] テンプレートの作成
- [ ] CSS スタイリング

### Phase 2: ナビゲーション
- [ ] `base.html` のメニュー権限チェック追加
- [ ] 管理者用ドロップダウンメニュー実装
- [ ] アクティブ状態の管理
- [ ] モバイル対応

### Phase 3: 統合・改善
- [ ] ユーザー管理画面の改善
- [ ] コンテンツ管理機能追加
- [ ] 権限チェックの完全化
- [ ] エラーハンドリングの改善

### テスト
- [ ] 全ロールでの動作テスト
- [ ] 権限チェックテスト
- [ ] UIレスポンシブテスト
- [ ] パフォーマンステスト

## 📋 完了条件

1. **テナント管理者がダッシュボードにアクセス**できる
2. **統計情報が正確に表示**される
3. **権限に応じたUI要素の制御**が完璧
4. **他のロールからのアクセスが適切に制限**される
5. **既存機能との統合**が完了している
6. **レスポンシブデザイン**が実装されている

## 🚨 注意事項

### セキュリティ
- **全ての新規ビュー**に適切な権限デコレーター適用
- **CSRF トークン**の適切な使用
- **XSS 対策**の実装

### パフォーマンス
- **N+1クエリ**の回避
- **適切なページネーション**の実装
- **キャッシング**の活用

### 互換性
- **既存の権限システム**との完全互換
- **マルチテナント**アーキテクチャとの整合性
- **今後の機能拡張**への対応

---

**作成日**: 2025-09-04  
**ステータス**: 🔴 未着手  
**担当者**: TBD  
**優先度**: 🟡 Medium