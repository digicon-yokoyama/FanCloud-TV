#!/usr/bin/env python
"""
Content Data Seeder
===================

このスクリプトはVODシステムのモックデータを作成します。
開発・テスト環境でのデータベースセットアップに使用してください。

Usage:
    python scripts/seed_content_data.py

Requirements:
    - Django environment must be properly configured
    - User accounts (especially streamers) must exist
    - Run within tenant context for multi-tenant setup
"""

import os
import sys
import django
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context, get_tenant_model
from apps.content.models import Video, VideoCategory
from apps.accounts.models import User
from django.utils import timezone
import secrets
import random


def create_video_categories():
    """Create video categories if they don't exist."""
    categories_data = [
        {
            'name': 'ゲーム',
            'description': 'ゲーム実況・攻略・レビューなどゲーム関連の動画',
            'color': '#e74c3c'
        },
        {
            'name': 'エンターテイメント',
            'description': 'バラエティ・コメディ・エンタメ系動画',
            'color': '#f39c12'
        },
        {
            'name': '教育',
            'description': '学習・解説・チュートリアル動画',
            'color': '#3498db'
        },
        {
            'name': '音楽',
            'description': '音楽・歌・演奏動画',
            'color': '#9b59b6'
        },
        {
            'name': 'スポーツ',
            'description': 'スポーツ・運動・フィットネス関連動画',
            'color': '#27ae60'
        },
        {
            'name': 'ライフスタイル',
            'description': '日常・料理・旅行・美容などライフスタイル動画',
            'color': '#e67e22'
        }
    ]
    
    created_categories = []
    for cat_data in categories_data:
        category, created = VideoCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'description': cat_data['description'],
                'color': cat_data['color'],
                'is_active': True
            }
        )
        if created:
            print(f'✓ Created category: {cat_data["name"]}')
        else:
            print(f'- Category already exists: {cat_data["name"]}')
        created_categories.append(category)
    
    return created_categories


def create_sample_videos(categories, streamers, count=10):
    """Create sample VOD videos."""
    
    # Sample video data templates
    video_templates = [
        {
            'title': 'プログラミング入門講座 - Python基礎編',
            'description': 'プログラミング初心者向けのPython入門講座です。基本的な文法から実践的な使い方まで丁寧に解説します。',
            'category': '教育',
            'duration': 1800  # 30 minutes
        },
        {
            'title': '【ゲーム実況】最新RPGを初見プレイ！',
            'description': '話題の新作RPGを初見でプレイします！一緒に冒険の旅を楽しみましょう。',
            'category': 'ゲーム',
            'duration': 3600  # 60 minutes
        },
        {
            'title': '簡単美味しい！10分で作れる時短レシピ',
            'description': '忙しい日でも簡単に作れる美味しい時短レシピをご紹介。材料も少なくて済みます！',
            'category': 'ライフスタイル',
            'duration': 600  # 10 minutes
        },
        {
            'title': 'ピアノ演奏 - クラシック名曲集',
            'description': '誰もが知るクラシックの名曲をピアノで演奏しました。リラックスタイムにどうぞ。',
            'category': '音楽',
            'duration': 2400  # 40 minutes
        },
        {
            'title': 'サッカー技術解説 - ドリブルの基本',
            'description': 'サッカーのドリブル技術について基礎から応用まで詳しく解説します。',
            'category': 'スポーツ',
            'duration': 900  # 15 minutes
        },
        {
            'title': 'お笑い動画 - 面白コント集',
            'description': 'オリジナルコントをお届け！日常のあるあるネタで笑ってください。',
            'category': 'エンターテイメント',
            'duration': 1200  # 20 minutes
        }
    ]
    
    # Sample video URLs (free sample videos)
    sample_videos = [
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4"
    ]
    
    created_videos = []
    category_dict = {cat.name: cat for cat in categories}
    
    for i in range(count):
        # Cycle through templates
        template = video_templates[i % len(video_templates)]
        streamer = random.choice(streamers)
        
        # Generate unique title
        if i >= len(video_templates):
            title = f"{template['title']} - Part {i // len(video_templates) + 1}"
        else:
            title = template['title']
        
        video = Video.objects.create(
            title=title,
            description=template['description'],
            uploader=streamer,
            privacy=random.choice(['public', 'public', 'public', 'unlisted']),  # Mostly public
            status='ready',
            slug=f'mock-video-{i+1}-{secrets.token_hex(4)}',
            playback_url=sample_videos[i % len(sample_videos)],
            thumbnail_url=f'https://picsum.photos/320/180?random={i+100}',
            duration=template['duration'] + random.randint(-300, 300),  # Add some variance
            view_count=random.randint(50, 5000),
            like_count=random.randint(5, 500),
            dislike_count=random.randint(0, 50),
            comment_count=random.randint(0, 100),
            published_at=timezone.now() - timezone.timedelta(days=random.randint(0, 30)),
            category=category_dict.get(template['category'])
        )
        
        created_videos.append(video)
        print(f'✓ Created video: {title}')
    
    return created_videos


def seed_content_data(tenant_schema='localhost'):
    """Main seeder function."""
    print(f"🌱 Starting Content Data Seeding for schema: {tenant_schema}")
    print("=" * 50)
    
    # Get tenant and run in context
    Tenant = get_tenant_model()
    try:
        tenant = Tenant.objects.get(schema_name=tenant_schema)
    except Tenant.DoesNotExist:
        print(f"❌ Error: Tenant '{tenant_schema}' not found!")
        return False
    
    with schema_context(tenant_schema):
        # Check if streamers exist
        streamers = User.objects.filter(can_stream=True)
        if not streamers.exists():
            print("❌ Error: No streamers found! Please create streamer accounts first.")
            return False
        
        print(f"📺 Found {streamers.count()} streamer accounts")
        
        # Create categories
        print("\n📁 Creating video categories...")
        categories = create_video_categories()
        
        # Create sample videos
        print(f"\n🎬 Creating sample videos...")
        videos = create_sample_videos(categories, list(streamers), count=12)
        
        print(f"\n✅ Content seeding completed!")
        print(f"   - Categories: {len(categories)}")
        print(f"   - Videos: {len(videos)}")
        print(f"   - Total videos in DB: {Video.objects.count()}")
        
        return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed VOD content data')
    parser.add_argument(
        '--tenant',
        default='localhost',
        help='Tenant schema to seed (default: localhost)'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Delete existing videos before seeding'
    )
    
    args = parser.parse_args()
    
    if args.reset:
        print("🗑️  Clearing existing content data...")
        with schema_context(args.tenant):
            Video.objects.all().delete()
            VideoCategory.objects.all().delete()
        print("✅ Existing data cleared!")
    
    success = seed_content_data(args.tenant)
    if success:
        print(f"\n🎉 Content data seeding completed successfully for '{args.tenant}'!")
        print("\nUsage:")
        print("  - Access videos at: /content/trending/")
        print("  - Upload new videos at: /content/upload/")
        print("  - Manage videos at: /content/manage/")
    else:
        print("\n❌ Content data seeding failed!")
        sys.exit(1)