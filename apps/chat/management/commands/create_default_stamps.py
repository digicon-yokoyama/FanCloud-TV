"""
Management command to create default chat stamps
"""
import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
from django_tenants.utils import schema_context
from apps.tenants.models import Tenant
from apps.chat.models import ChatStamp
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


class Command(BaseCommand):
    help = 'Create default chat stamps'

    def handle(self, *args, **options):
        default_stamps = [
            {'name': ':smile:', 'emoji': '😊', 'color': '#FFD700'},
            {'name': ':heart:', 'emoji': '❤️', 'color': '#FF69B4'},
            {'name': ':thumbsup:', 'emoji': '👍', 'color': '#32CD32'},
            {'name': ':laugh:', 'emoji': '😂', 'color': '#FF6347'},
            {'name': ':fire:', 'emoji': '🔥', 'color': '#FF4500'},
            {'name': ':clap:', 'emoji': '👏', 'color': '#4169E1'},
            {'name': ':wow:', 'emoji': '😮', 'color': '#9370DB'},
            {'name': ':sad:', 'emoji': '😢', 'color': '#4682B4'},
        ]

        # Get first tenant and execute in its schema context
        tenant = Tenant.objects.first()
        if not tenant:
            self.stdout.write(self.style.ERROR('No tenant found. Please create a tenant first.'))
            return
            
        self.stdout.write(f'Using tenant: {tenant.domain_url}')
        
        with schema_context(tenant.schema_name):
            self.stdout.write('Creating default stamps...')
            
            for stamp_data in default_stamps:
                # Check if stamp already exists
                if ChatStamp.objects.filter(name=stamp_data['name']).exists():
                    self.stdout.write(f"Stamp {stamp_data['name']} already exists, skipping...")
                    continue
                
                # Create simple emoji image
                img = Image.new('RGBA', (64, 64), (255, 255, 255, 0))
                
                try:
                    # Try to use a system font for emoji
                    font_size = 48
                    try:
                        font = ImageFont.truetype("/System/Library/Fonts/Arial Unicode.ttf", font_size)
                    except:
                        try:
                            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                        except:
                            font = ImageFont.load_default()
                
                    draw = ImageDraw.Draw(img)
                    
                    # Calculate text position to center it
                    bbox = draw.textbbox((0, 0), stamp_data['emoji'], font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (64 - text_width) // 2
                    y = (64 - text_height) // 2
                    
                    draw.text((x, y), stamp_data['emoji'], font=font, fill=stamp_data['color'])
                
                except Exception as e:
                    # Fallback: create a colored circle with text
                    draw = ImageDraw.Draw(img)
                    draw.ellipse([8, 8, 56, 56], fill=stamp_data['color'])
                    
                    # Add simple text
                    font = ImageFont.load_default()
                    text = stamp_data['name'][1:-1]  # Remove : from :smile:
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (64 - text_width) // 2
                    y = (64 - text_height) // 2
                    draw.text((x, y), text, font=font, fill='white')
                
                # Save image to BytesIO
                img_io = BytesIO()
                img.save(img_io, format='PNG')
                img_io.seek(0)
                
                # Create ChatStamp object
                stamp = ChatStamp.objects.create(
                    name=stamp_data['name'],
                    is_active=True
                )
                
                # Save image file
                filename = f"{stamp_data['name'].replace(':', '')}.png"
                stamp.image.save(
                    filename,
                    ContentFile(img_io.getvalue()),
                    save=True
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Created stamp: {stamp.name}')
                )
            
            total_stamps = ChatStamp.objects.count()
            self.stdout.write(
                self.style.SUCCESS(f'Completed! Total stamps: {total_stamps}')
            )