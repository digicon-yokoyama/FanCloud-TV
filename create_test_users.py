#!/usr/bin/env python
"""
Create test users for different permission levels.
Run this script from the Django project root.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User, UserProfile


def create_test_users():
    """Create test users for each permission level."""
    
    test_users = [
        {
            'username': 'sysadmin',
            'email': 'sysadmin@example.com',
            'password': 'test123456',
            'role': 'system_admin',
            'membership': 'premium',
            'can_stream': True,
            'first_name': 'システム',
            'last_name': '管理者',
            'is_staff': True,
            'is_superuser': True,
        },
        {
            'username': 'tenantadmin',
            'email': 'tenantadmin@example.com',
            'password': 'test123456',
            'role': 'tenant_admin',
            'membership': 'premium',
            'can_stream': True,
            'first_name': 'テナント',
            'last_name': '管理者',
            'is_staff': True,
        },
        {
            'username': 'streamer',
            'email': 'streamer@example.com',
            'password': 'test123456',
            'role': 'tenant_user',
            'membership': 'premium',
            'can_stream': True,
            'first_name': '配信',
            'last_name': 'ユーザー',
        },
        {
            'username': 'viewer',
            'email': 'viewer@example.com',
            'password': 'test123456',
            'role': 'subscriber',
            'membership': 'free',
            'can_stream': False,
            'first_name': '視聴',
            'last_name': 'ユーザー',
        },
        {
            'username': 'premium_viewer',
            'email': 'premium@example.com',
            'password': 'test123456',
            'role': 'subscriber',
            'membership': 'premium',
            'can_stream': False,
            'first_name': 'プレミアム',
            'last_name': '視聴者',
        }
    ]
    
    created_users = []
    
    for user_data in test_users:
        username = user_data['username']
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            print(f"❌ User '{username}' already exists. Skipping...")
            continue
        
        try:
            # Create user
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role'],
                membership=user_data['membership'],
                can_stream=user_data['can_stream'],
                is_staff=user_data.get('is_staff', False),
                is_superuser=user_data.get('is_superuser', False),
            )
            
            # Update user bio (it's on User model, not Profile)
            user.bio = f'{user.get_role_display()}のテストアカウントです。'
            user.save()
            
            # Create user profile
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'privacy_level': 'public',
                    'email_notifications': True,
                    'push_notifications': True,
                }
            )
            
            created_users.append(user)
            
            print(f"✅ Created user: {username} ({user.get_role_display()}) - Password: {user_data['password']}")
            
        except Exception as e:
            print(f"❌ Error creating user '{username}': {e}")
    
    return created_users


def display_user_info():
    """Display information about all test users."""
    
    print("\n" + "="*80)
    print("🎯 テストユーザー情報")
    print("="*80)
    
    test_usernames = ['sysadmin', 'tenantadmin', 'streamer', 'viewer', 'premium_viewer']
    
    for username in test_usernames:
        try:
            user = User.objects.get(username=username)
            print(f"""
📋 ユーザー: {user.username}
   🏷️  ロール: {user.get_role_display()} ({user.role})
   💳 メンバーシップ: {user.get_membership_display()} ({user.membership})
   📺 配信権限: {'✅' if user.can_stream else '❌'}
   🔑 パスワード: test123456
   📧 メール: {user.email}
   🔗 ログインURL: http://localhost:8000/accounts/login/
            """)
            
        except User.DoesNotExist:
            print(f"❌ User '{username}' not found")
    
    print("\n" + "="*80)
    print("🚀 管理者機能のテスト方法:")
    print("="*80)
    print("""
1. sysadmin または tenantadmin でログイン
2. 右上のユーザーアイコン → 「ユーザー管理」をクリック
3. ユーザー一覧で権限を確認・変更可能
4. 各ロールでログインして機能をテスト

📍 管理画面URL: http://localhost:8000/accounts/admin/users/
📍 Django Admin: http://localhost:8000/admin/
    """)


if __name__ == "__main__":
    print("🎭 テストユーザー作成スクリプトを開始...")
    
    created_users = create_test_users()
    
    if created_users:
        print(f"\n🎉 {len(created_users)}人のテストユーザーを作成しました！")
    else:
        print("\n⚠️  新しいユーザーは作成されませんでした。")
    
    display_user_info()
    
    print("\n✨ 完了！")