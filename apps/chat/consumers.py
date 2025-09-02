import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django_tenants.utils import schema_context
from django_tenants.models import TenantMixin
from .models import ChatRoom, ChatMessage, ChatModerator
from apps.streaming.models import Stream


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for live chat."""
    
    async def connect(self):
        try:
            self.room_name = self.scope['url_route']['kwargs']['room_name']
            self.room_group_name = f'chat_{self.room_name}'
            
            # Check if room exists and is active
            room_exists = await self.get_or_create_room()
            if not room_exists:
                await self.close()
                return
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Send join message if user is authenticated
            if not isinstance(self.scope["user"], AnonymousUser):
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': f'{self.scope["user"].username} がチャットに参加しました',
                        'username': 'システム',
                        'message_type': 'join'
                    }
                )
                
        except Exception as e:
            print(f"WebSocket connect error: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        try:
            # Send leave message if user is authenticated
            if not isinstance(self.scope["user"], AnonymousUser):
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': f'{self.scope["user"].username} がチャットから退出しました',
                        'username': 'システム',
                        'message_type': 'leave'
                    }
                )
            
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
        except Exception as e:
            print(f"Error during disconnect: {e}")
    
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json['message'].strip()
            
            # セッションベース認証: WebSocket認証の代替実装
            user = self.scope.get("user")
            
            # セッションからユーザーIDを取得
            user_id = await self.get_user_id_from_session()
            print(f"🔑 SESSION AUTH: User ID from session: {user_id}")
            
            if user_id:
                # セッションのユーザーIDから実際のユーザー情報を取得
                actual_user = await self.get_user_by_id(user_id)
                if actual_user:
                    print(f"🔑 SESSION AUTH: User found: {actual_user.username} (ID: {actual_user.id})")
                    user_authenticated = True
                    self.temp_user = {
                        'id': actual_user.id,
                        'username': actual_user.username
                    }
                else:
                    print(f"🔑 SESSION AUTH: User not found for ID: {user_id}")
                    user_authenticated = False
            else:
                print("🔑 SESSION AUTH: No user ID in session")
                user_authenticated = False
            
            if not user_authenticated:
                await self.send(text_data=json.dumps({
                    'error': 'チャットに参加するにはログインが必要です'
                }))
                return
            
            # Validate message
            if not message or len(message) > 500:
                await self.send(text_data=json.dumps({
                    'error': 'メッセージは1-500文字で入力してください'
                }))
                return
            
            # Check if user is banned or timed out
            user_can_chat = await self.check_user_permissions()
            if not user_can_chat:
                await self.send(text_data=json.dumps({
                    'error': 'チャットする権限がありません'
                }))
                return
            
            # Filter message content
            filtered_message = await self.filter_message(message)
            if not filtered_message:
                await self.send(text_data=json.dumps({
                    'error': 'メッセージが制限されています'
                }))
                return
            
            # Save message to database
            await self.save_message(filtered_message)
            
            # Send message to room group
            username = self.temp_user['username']
            user_id = self.temp_user['id']
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': filtered_message,
                    'username': username,
                    'user_id': user_id,
                    'message_type': 'message'
                }
            )
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': '無効なメッセージ形式です'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': 'メッセージの送信に失敗しました'
            }))
    
    async def chat_message(self, event):
        """Send message to WebSocket."""
        message = event['message']
        username = event['username']
        message_type = event.get('message_type', 'message')
        user_id = event.get('user_id')
        
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'user_id': user_id,
            'message_type': message_type,
            'timestamp': None  # Will be added by frontend
        }))
    
    @database_sync_to_async
    def get_or_create_room(self):
        """Get or create chat room."""
        try:
            # Get tenant from headers or use first available
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.first()  # In production, get from domain
            
            with schema_context(tenant.schema_name):
                # Check if it's a stream room
                if self.room_name.startswith('stream_'):
                    stream_id = self.room_name.replace('stream_', '')
                    try:
                        stream = Stream.objects.get(stream_id=stream_id)
                        room, created = ChatRoom.objects.get_or_create(
                            name=self.room_name,
                            defaults={'stream': stream}
                        )
                        return room.is_active
                    except Stream.DoesNotExist:
                        return False
                else:
                    # Generic room
                    room, created = ChatRoom.objects.get_or_create(
                        name=self.room_name
                    )
                    return room.is_active
        except Exception as e:
            print(f"Error in get_or_create_room: {e}")
            return False
    
    @database_sync_to_async
    def save_message(self, message):
        """Save message to database."""
        try:
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.first()
            
            with schema_context(tenant.schema_name):
                room = ChatRoom.objects.get(name=self.room_name)
                
                # 実際のユーザーオブジェクトを取得
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                try:
                    actual_user = User.objects.get(id=self.temp_user['id'])
                    print(f"💾 SAVE: Saving message for user: {actual_user.username} (ID: {actual_user.id})")
                except User.DoesNotExist:
                    print(f"💾 SAVE ERROR: User not found for ID: {self.temp_user['id']}")
                    actual_user = None
                
                ChatMessage.objects.create(
                    room=room,
                    user=actual_user,
                    content=message,
                    message_type='message'
                )
                
        except ChatRoom.DoesNotExist:
            pass
        except Exception as e:
            print(f"Error saving message: {e}")
    
    @database_sync_to_async
    def check_user_permissions(self):
        """Check if user can send messages."""
        try:
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.first()
            
            with schema_context(tenant.schema_name):
                # For now, all authenticated users can chat
                # This can be extended with ban/timeout checks
                return True
        except Exception:
            return False
    
    @database_sync_to_async
    def filter_message(self, message):
        """Filter message content for spam/inappropriate content."""
        # Basic filtering - can be extended with proper moderation
        if len(message.strip()) == 0:
            return None
        
        # Remove excessive whitespace
        filtered = ' '.join(message.split())
        
        # Basic spam detection (repeated characters)
        if len(set(filtered.lower())) < 3 and len(filtered) > 10:
            return None
        
        return filtered
    
    @database_sync_to_async
    def get_user_id_from_session(self):
        """セッションからユーザーIDを安全に取得"""
        try:
            session = self.scope.get("session")
            if session and hasattr(session, 'get'):
                user_id = session.get("_auth_user_id")
                return user_id
            return None
        except Exception as e:
            print(f"Error getting user ID from session: {e}")
            return None
    
    @database_sync_to_async
    def get_user_by_id(self, user_id):
        """ユーザーIDから実際のユーザーオブジェクトを取得"""
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            return User.objects.get(id=user_id)
        except Exception as e:
            print(f"Error getting user by ID {user_id}: {e}")
            return None


class ViewerCountConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time viewer count updates."""
    
    async def connect(self):
        self.stream_id = self.scope['url_route']['kwargs']['stream_id']
        self.room_group_name = f'viewers_{self.stream_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current viewer count
        viewer_count = await self.get_viewer_count()
        await self.send(text_data=json.dumps({
            'type': 'viewer_count',
            'count': viewer_count
        }))
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def viewer_update(self, event):
        """Send viewer count update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'viewer_count',
            'count': event['count']
        }))
    
    @database_sync_to_async
    def get_viewer_count(self):
        """Get current viewer count."""
        try:
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.first()
            
            with schema_context(tenant.schema_name):
                stream = Stream.objects.get(stream_id=self.stream_id)
                return stream.viewer_count
        except Stream.DoesNotExist:
            return 0
        except Exception:
            return 0