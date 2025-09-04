# テナント別ストリーミングプロバイダー設定

## 概要

FanCloud TVでは、テナント（組織・グループ）毎に異なるストリーミングエンジンや提供機能を設定可能です。これにより、テナントの用途や要件に応じた最適なストリーミング環境を提供できます。

## アーキテクチャ

### 設計原則

- **後方互換性**: 既存機能への影響は最小限
- **段階的導入**: Phase別に安全に導入可能
- **Open-Closed Principle**: 既存コードを変更せず、新機能を追加

### システム構成

```
テナント設定 → StreamingService → プロバイダー選択 → 実際のストリーミングAPI
     ↓              ↓                ↓                    ↓
   Tenant       サービス抽象化      Provider実装      外部サービス
   Model         レイヤー          (THEOlive等)     (Dolby/AWS等)
```

## 対応ストリーミングプロバイダー

### 利用可能なプロバイダー

| プロバイダー | 特徴 | 用途 | 遅延 |
|-------------|------|------|------|
| **THEOlive** | Dolby製、超低遅延 | インタラクティブ配信、ライブイベント | Sub-second |
| **AWS IVS** | AWS製、高可用性 | 企業配信、安定性重視 | 2-5秒 |
| **Bitmovin** | 高品質エンコーディング | 教育、エンタメコンテンツ | 3-8秒 |
| **Mock** | 開発・テスト用 | 開発環境 | N/A |

### 機能セット

| 機能セット | 説明 | 対象テナント例 |
|-----------|------|---------------|
| **live_only** | ライブ配信のみ | 企業内会議、セミナー |
| **vod_only** | VOD（録画動画）のみ | 教育機関、アーカイブサービス |
| **live_and_vod** | ライブ配信 + VOD | 総合配信プラットフォーム |

## データベース設計

### Tenantモデル拡張

```python
# apps/tenants/models.py
class Tenant(TenantMixin):
    # ストリーミングエンジン選択
    STREAMING_PROVIDER_CHOICES = [
        ('mock', 'Mock Provider (Development)'),
        ('theolive', 'THEOlive (Dolby)'),
        ('aws_ivs', 'Amazon IVS'),
        ('bitmovin', 'Bitmovin'),
    ]
    
    streaming_provider = models.CharField(
        max_length=20, 
        choices=STREAMING_PROVIDER_CHOICES,
        default='mock'
    )
    
    # 提供機能制御
    FEATURE_CHOICES = [
        ('live_only', 'ライブ配信のみ'),
        ('vod_only', 'VOD（録画動画）のみ'),
        ('live_and_vod', 'ライブ配信 + VOD'),
    ]
    
    supported_features = models.CharField(
        max_length=20,
        choices=FEATURE_CHOICES,
        default='live_and_vod'
    )
    
    # プロバイダー固有設定
    provider_config = models.JSONField(default=dict, blank=True)
```

### マイグレーション

```bash
# マイグレーションファイル生成
docker compose exec web python manage.py makemigrations tenants

# 共有アプリのマイグレーション実行
docker compose exec web python manage.py migrate_schemas --shared
```

## コード実装

### StreamingService拡張

```python
# apps/streaming/services.py
class StreamingService:
    def __init__(self, tenant=None):
        """
        テナント固有のストリーミングサービス初期化
        
        Args:
            tenant: テナントオブジェクト（Noneの場合は現在のテナントを取得）
        """
        from django_tenants.utils import tenant_context
        
        if tenant is None:
            tenant = tenant_context.tenant
        
        self.tenant = tenant
        self.provider = self._get_tenant_provider()
    
    def _get_tenant_provider(self):
        """テナント設定に基づいてプロバイダー選択"""
        if not self.tenant:
            return MockStreamingProvider()
        
        provider_type = self.tenant.streaming_provider
        provider_config = self.tenant.provider_config
        
        # プロバイダーファクトリーパターン
        if provider_type == 'theolive':
            return TheOliveProvider(provider_config)
        elif provider_type == 'aws_ivs':
            return AWSIVSProvider(provider_config)
        elif provider_type == 'bitmovin':
            return BitmovinProvider(provider_config)
        else:
            return MockStreamingProvider()
    
    def can_create_live_stream(self):
        """ライブ配信作成可能かチェック"""
        if not self.tenant:
            return False
        return self.tenant.supported_features in ['live_only', 'live_and_vod']
    
    def can_upload_vod(self):
        """VOD アップロード可能かチェック"""
        if not self.tenant:
            return False
        return self.tenant.supported_features in ['vod_only', 'live_and_vod']
```

### プロバイダー実装例

```python
# THEOliveプロバイダー実装
class TheOliveProvider:
    def __init__(self, config=None):
        self.config = config or {}
        self.api_key = self.config.get('api_key', '')
        self.region = self.config.get('region', 'us-east-1')
        self.api_base = f"https://api.theolive.com/{self.region}/v1"
    
    def create_stream(self, stream_data):
        """THEOlive チャンネル作成"""
        # 実装詳細...
```

### ビューレベル制御

```python
# apps/streaming/views.py
@streaming_permission_required
def create_stream(request):
    """新規ライブ配信作成"""
    
    # テナント機能チェック
    from django_tenants.utils import tenant_context
    tenant = tenant_context.tenant
    
    streaming_service = StreamingService(tenant)
    if not streaming_service.can_create_live_stream():
        messages.error(request, 'このテナントではライブ配信機能は利用できません。')
        return redirect('streaming:home')
    
    # 既存の実装継続...
```

## 管理・運用

### Django Admin設定

```python
# apps/tenants/admin.py
@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'streaming_provider', 'supported_features', 'is_active']
    list_filter = ['streaming_provider', 'supported_features']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('ストリーミング設定', {
            'fields': ('streaming_provider', 'supported_features', 'provider_config'),
            'description': 'テナント固有のストリーミング設定を行います。'
        }),
        ('制限設定', {
            'fields': ('max_concurrent_streams', 'max_storage_gb', 'max_bandwidth_mbps')
        }),
    )
```

### プロバイダー設定例

**THEOlive設定:**
```json
{
  "api_key": "theo_live_api_key_here",
  "region": "ap-northeast-1",
  "quality_preset": "ultra_low_latency",
  "recording_enabled": true
}
```

**AWS IVS設定:**
```json
{
  "aws_access_key": "AKIAIOSFODNN7EXAMPLE",
  "aws_secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
  "region": "us-west-2",
  "channel_type": "STANDARD"
}
```

## 導入手順

### Phase 1: 基盤準備

1. **Tenantモデル拡張**
   ```bash
   # マイグレーションファイル作成・実行
   docker compose exec web python manage.py makemigrations tenants
   docker compose exec web python manage.py migrate_schemas --shared
   ```

2. **StreamingService拡張**
   - `apps/streaming/services.py`にテナント対応コード追加
   - 既存の`StreamingService()`呼び出しは無変更で動作

### Phase 2: プロバイダー実装

3. **THEOliveプロバイダー追加**
   - `TheOliveProvider`クラス実装
   - API統合とエラーハンドリング

4. **管理画面設定**
   - Django Adminでテナント設定画面構築

### Phase 3: 機能制御

5. **ビューレベル制御**
   - 特定ビューで機能制限チェック追加

6. **テンプレート制御**
   - UIで機能の表示・非表示制御

## テスト例

### シナリオベーステスト

**テナントA（企業向け）:**
- Provider: THEOlive
- Features: live_only
- 期待結果: ライブ配信のみ利用可能、VODアップロード不可

**テナントB（教育機関）:**
- Provider: AWS IVS
- Features: live_and_vod
- 期待結果: 全機能利用可能、高い安定性

### テストコード例

```python
# tests/test_tenant_streaming.py
class TenantStreamingTest(TestCase):
    def test_live_only_tenant_cannot_upload_vod(self):
        """ライブ専用テナントでVODアップロード不可テスト"""
        tenant = Tenant.objects.create(
            name="LiveOnlyTenant",
            streaming_provider="theolive",
            supported_features="live_only"
        )
        
        service = StreamingService(tenant)
        self.assertTrue(service.can_create_live_stream())
        self.assertFalse(service.can_upload_vod())
```

## トラブルシューティング

### よくある問題

**Q: 既存のストリームが動作しなくなった**
A: `streaming_provider`がデフォルト値（`mock`）になっているか確認してください。

**Q: プロバイダー設定が反映されない**
A: `provider_config`のJSON形式が正しいか確認してください。

**Q: テナント設定変更後に配信できない**
A: テナントの`supported_features`設定を確認してください。

### ログ確認

```bash
# Django ログ確認
docker compose logs -f web

# 特定テナントのストリーミングログ
docker compose exec web python manage.py shell
>>> from apps.streaming.services import StreamingService
>>> service = StreamingService()
>>> service.get_stream_status('stream_id_here')
```

## まとめ

この実装により、以下が実現されます：

- **柔軟性**: テナント毎に最適なストリーミング環境
- **拡張性**: 新しいプロバイダーの追加が容易
- **安全性**: 既存機能への影響なし
- **運用性**: 管理画面での簡単設定

テナント固有の要件に応じて、最適なストリーミング体験を提供できる強力な仕組みです。