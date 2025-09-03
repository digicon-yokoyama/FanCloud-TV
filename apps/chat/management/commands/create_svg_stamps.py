"""
Management command to create chat stamps from SVG files
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django_tenants.utils import schema_context
from apps.tenants.models import Tenant
from apps.chat.models import ChatStamp


class Command(BaseCommand):
    help = 'Create chat stamps from SVG files'

    def handle(self, *args, **options):
        # 新しいSVGスタンプファイル情報
        svg_stamps = [
            {'name': ':smile:', 'filename': '01_smile.svg'},
            {'name': ':surprise:', 'filename': '02_surprise.svg'},
            {'name': ':cry:', 'filename': '03_cry.svg'},
            {'name': ':love:', 'filename': '04_love.svg'},
            {'name': ':scream:', 'filename': '05_scream.svg'},
            {'name': ':angry:', 'filename': '06_angry.svg'},
        ]

        # Get first tenant and execute in its schema context
        tenant = Tenant.objects.first()
        if not tenant:
            self.stdout.write(self.style.ERROR('No tenant found. Please create a tenant first.'))
            return
            
        self.stdout.write(f'Using tenant: {tenant.domain_url}')
        
        with schema_context(tenant.schema_name):
            self.stdout.write('Creating SVG stamps...')
            
            # 既存のスタンプを全て削除
            deleted_count = ChatStamp.objects.all().delete()[0]
            if deleted_count > 0:
                self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing stamps'))
            
            # メディアディレクトリのパス確認
            stamps_dir = os.path.join(settings.MEDIA_ROOT, 'stamps')
            if not os.path.exists(stamps_dir):
                self.stdout.write(self.style.ERROR(f'Stamps directory not found: {stamps_dir}'))
                return
            
            created_count = 0
            for stamp_data in svg_stamps:
                # SVGファイルが存在するかチェック
                svg_path = os.path.join(stamps_dir, stamp_data['filename'])
                if not os.path.exists(svg_path):
                    self.stdout.write(
                        self.style.ERROR(f'SVG file not found: {svg_path}')
                    )
                    continue
                
                # ChatStamp オブジェクトを作成
                stamp = ChatStamp.objects.create(
                    name=stamp_data['name'],
                    is_active=True
                )
                
                # image フィールドにSVGファイルのパスを設定
                stamp.image = f"stamps/{stamp_data['filename']}"
                stamp.save()
                
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created SVG stamp: {stamp.name} -> {stamp_data["filename"]}')
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} SVG stamps')
            )