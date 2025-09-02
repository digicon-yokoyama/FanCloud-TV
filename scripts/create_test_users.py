#!/usr/bin/env python3
"""
テストユーザー作成スクリプト
docs/PERMISSIONS.md に記載されているテストユーザーを作成します
"""

import os
import sys
import django

# Djangoプロジェクトのパスを追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from apps.tenants.models import Tenant
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile

User = get_user_model()

# テストユーザーのデータ（docs/PERMISSIONS.mdより）
TEST_USERS = [
    {
        'username': 'sysadmin',
        'email': 'sysadmin@example.com',
        'role': 'system_admin',
        'membership': 'premium',
        'can_stream': True,
        'password': 'test123456',
        'is_staff': True
    },
    {
        'username': 'tenantadmin',
        'email': 'tenantadmin@example.com', 
        'role': 'tenant_admin',
        'membership': 'premium',
        'can_stream': True,
        'password': 'test123456',
        'is_staff': True
    },
    {
        'username': 'streamer',
        'email': 'streamer@example.com',
        'role': 'tenant_user',
        'membership': 'premium', 
        'can_stream': True,
        'password': 'test123456',
        'is_staff': False
    },
    {
        'username': 'viewer',
        'email': 'viewer@example.com',
        'role': 'subscriber',
        'membership': 'free',
        'can_stream': False,
        'password': 'test123456',
        'is_staff': False
    },
    {
        'username': 'premium_viewer',
        'email': 'premium@example.com',
        'role': 'subscriber', 
        'membership': 'premium',
        'can_stream': False,
        'password': 'test123456',
        'is_staff': False
    }
]

def create_test_users():
    """テストユーザーを作成"""
    tenant = Tenant.objects.first()
    
    if not tenant:
        print("❌ テナントが見つかりません。先にテナントを作成してください。")
        return
    
    print(f"📍 テナント: {tenant.name} (schema: {tenant.schema_name})")
    
    with schema_context(tenant.schema_name):
        print("\n🔧 テストユーザーを作成中...")
        
        for user_data in TEST_USERS:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'role': user_data['role'],
                    'membership': user_data['membership'],
                    'can_stream': user_data['can_stream'],
                    'is_active': True,
                    'is_staff': user_data['is_staff']
                }
            )
            
            if created:
                user.set_password(user_data['password'])
                user.save()
                
                # UserProfileを作成
                UserProfile.objects.get_or_create(user=user)
                
                print(f"✅ 作成: {user.username} ({user.get_role_display()}) - {user.get_membership_display()}")
            else:
                # 既存ユーザーの情報を更新
                user.email = user_data['email']
                user.role = user_data['role']
                user.membership = user_data['membership']
                user.can_stream = user_data['can_stream']
                user.is_staff = user_data['is_staff']
                user.set_password(user_data['password'])
                user.save()
                
                print(f"♻️  更新: {user.username} ({user.get_role_display()}) - {user.get_membership_display()}")
        
        print(f"\n✨ 完了！ユーザー総数: {User.objects.count()}")
        print("\n📋 テストユーザー一覧:")
        print("┌─────────────────┬──────────────┬───────────────┬──────────┐")
        print("│ ユーザー名      │ ロール       │ メンバーシップ │ 配信権限 │")
        print("├─────────────────┼──────────────┼───────────────┼──────────┤")
        
        for user_data in TEST_USERS:
            user = User.objects.get(username=user_data['username'])
            stream_icon = "✅" if user.can_stream else "❌"
            print(f"│ {user.username:15} │ {user.get_role_display():12} │ {user.get_membership_display():13} │ {stream_icon:8} │")
        
        print("└─────────────────┴──────────────┴───────────────┴──────────┘")
        print("\n🔑 全員のパスワード: test123456")

if __name__ == '__main__':
    create_test_users()