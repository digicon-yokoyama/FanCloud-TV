import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django_tenants.utils import schema_context
from django_tenants.models import TenantMixin
from .models import ChatRoom, ChatMessage, ChatModerator
from apps.streaming.models import Stream


class TestConsumer(AsyncWebsocketConsumer):
    """Simple test consumer to verify WebSocket routing."""

    async def connect(self):
        print("🧪 TEST: ===== TestConsumer.connect() STARTED =====")
        print(f"🧪 TEST: Scope type: {self.scope.get('type')}")
        print(f"🧪 TEST: Scope path: {self.scope.get('path')}")
        print(f"🧪 TEST: Channel layer: {self.channel_layer}")
        await self.accept()
        await self.send(text_data=json.dumps({
            'message': 'Test WebSocket connection successful!',
            'type': 'test'
        }))
        print("🧪 TEST: ===== TestConsumer.connect() COMPLETED =====")

    async def disconnect(self, close_code):
        print("🧪 TEST: TestConsumer disconnected")


class SimpleChatConsumer(AsyncWebsocketConsumer):
    """Simplified ChatConsumer for testing."""

    async def connect(self):
        import sys
        import logging
        
        # 複数の方法でログ出力
        print("🚀 SIMPLE: ===== SimpleChatConsumer.connect() CALLED =====", flush=True)
        sys.stdout.flush()
        logging.error("🚀 SIMPLE: SimpleChatConsumer.connect() CALLED")
        
        print(f"🔌 WS SIMPLE: Scope type: {self.scope.get('type')}")
        print(f"🔌 WS SIMPLE: Scope path: {self.scope.get('path')}")
        print(f"🔌 WS SIMPLE: URL route: {self.scope.get('url_route')}")
        print(f"🔌 WS SIMPLE: Channel layer: {self.channel_layer}")
        await self.accept()
        await self.send(text_data=json.dumps({
            'message': 'Simple Chat Consumer connected!',
            'type': 'simple_chat'
        }))
        print("🔌 WS SIMPLE: ===== SimpleChatConsumer.connect() COMPLETED =====", flush=True)

    async def receive(self, text_data):
        import sys
        import logging
        
        # 複数の方法でログ出力
        print("🚀 SIMPLE: ===== SimpleChatConsumer.receive() CALLED =====", flush=True)
        sys.stdout.flush()
        logging.error("🚀 SIMPLE: SimpleChatConsumer.receive() CALLED")
        
        print(f"🚀 SIMPLE: Received: {text_data}")
        
        # Echo the message back
        await self.send(text_data=json.dumps({
            'message': f'Echo: {text_data}',
            'type': 'echo'
        }))

    async def disconnect(self, close_code):
        print("🔌 WS SIMPLE: SimpleChatConsumer disconnected")


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for live chat."""

    async def connect(self):
        print("🚀 CONSUMER: ===== ChatConsumer.connect() CALLED =====")
        print("🚀 CONSUMER: This message should appear in logs if Consumer is called")
        
        try:
            # まず確実にログを出力（例外発生前に）
            print("🔌 WS CONNECT: ===== ChatConsumer.connect() STARTED =====")
            print(f"🔌 WS CONNECT: Scope keys: {list(self.scope.keys())}")
            print(f"🔌 WS CONNECT: URL route: {self.scope.get('url_route')}")

            # 即座に例外が発生する可能性がある処理をログ出力
            print(f"🔌 WS CONNECT: Channel layer: {self.channel_layer}")
            print(f"🔌 WS CONNECT: Channel name: {self.channel_name}")
        except Exception as e:
            print(f"🔌 WS CONNECT: CRITICAL ERROR at start: {e}")
            import traceback
            traceback.print_exc()
            return

        try:
            self.room_name = self.scope['url_route']['kwargs']['room_name']
            self.room_group_name = f'chat_{self.room_name}'

            print(f"🔌 WS CONNECT: Room: {self.room_name}")
            print(f"🔌 WS CONNECT: Group name: {self.room_group_name}")

            # 詳細なデバッグログ
            scope_user = self.scope.get('user')
            print(f"🔌 WS CONNECT: Scope user: {scope_user}")
            print(f"🔌 WS CONNECT: Scope user type: {type(scope_user)}")

            # UserLazyObjectの詳細情報
            if hasattr(scope_user, '_wrapped'):
                print(f"🔌 WS CONNECT: UserLazyObject detected")
                try:
                    print(f"🔌 WS CONNECT: Lazy user is_authenticated: {scope_user.is_authenticated}")
                    print(f"🔌 WS CONNECT: Lazy user username: {scope_user.username}")
                    print(f"🔌 WS CONNECT: Lazy user id: {scope_user.id}")
                except Exception as e:
                    print(f"🔌 WS CONNECT: Error accessing lazy user: {e}")

            if hasattr(scope_user, 'is_authenticated') and not hasattr(scope_user, '_wrapped'):
                print(f"🔌 WS CONNECT: Direct user is_authenticated: {scope_user.is_authenticated}")
                if hasattr(scope_user, 'username'):
                    print(f"🔌 WS CONNECT: Direct user username: {scope_user.username}")
                if hasattr(scope_user, 'id'):
                    print(f"🔌 WS CONNECT: Direct user id: {scope_user.id}")

            session = self.scope.get('session')
            print(f"🔌 WS CONNECT: Session object: {session}")
            print(f"🔌 WS CONNECT: Session keys: {list(session.keys()) if session else 'No session'}")
            if session:
                print(f"🔌 WS CONNECT: Auth user ID: {session.get('_auth_user_id')}")

            # デバッグ: scope の詳細情報を確認
            print(f"🔍 DEBUG: Scope keys: {list(self.scope.keys())}")
            print(f"🔍 DEBUG: User in scope: {self.scope.get('user')}")
            print(f"🔍 DEBUG: Session in scope: {self.scope.get('session') is not None}")
            
            # 接続時に認証済みユーザー情報を取得・保存
            self.authenticated_user = await self.get_authenticated_user()
            print(f"🔌 WS CONNECT: Authenticated user: {self.authenticated_user}")
            print(f"🔌 WS CONNECT: Is authenticated: {not isinstance(self.authenticated_user, AnonymousUser)}")

            # self.userも設定（receiveメソッドで使用）
            self.user = self.authenticated_user
            self.authenticated_username = getattr(self.authenticated_user, 'username', 'ゲスト')
            self.authenticated_user_id = getattr(self.authenticated_user, 'id', None)

            print(f"🔌 WS CONNECT: Final user info - username: {self.authenticated_username}, id: {self.authenticated_user_id}")
            print("🔌 WS CONNECT: ===== ChatConsumer.connect() COMPLETED =====")

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

        except Exception as e:
            print(f"WebSocket connect error: {e}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

        except Exception as e:
            print(f"Error during disconnect: {e}")
    
    async def receive(self, text_data):
        print("🚀 CONSUMER: ===== ChatConsumer.receive() CALLED =====")
        print(f"🚀 CONSUMER: Received data: {text_data}")
        
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json['message'].strip()

            print(f"📨 WS RECEIVE: Message: {message[:50]}...")
            print(f"📨 WS RECEIVE: Auth user: {self.authenticated_user}")
            print(f"📨 WS RECEIVE: Is authenticated: {not isinstance(self.authenticated_user, AnonymousUser)}")
            print(f"📨 WS RECEIVE: Username: {self.authenticated_username}")

            # 認証チェック（簡素化）
            if not self.user or not getattr(self.user, 'is_authenticated', False):
                print("❌ WS RECEIVE: Authentication failed - user not authenticated")
                await self.send(text_data=json.dumps({
                    'error': 'チャットに参加するにはログインが必要です',
                    'message_type': 'auth_error'
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

            # Send message to room group（接続時に確定したユーザー情報を使用）
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': filtered_message,
                    'username': self.authenticated_username,
                    'user_id': self.authenticated_user_id,
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
            # TenantResolverMiddlewareが既にスキーマを設定済み
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
            # TenantResolverMiddlewareが既にスキーマを設定済み
            room = ChatRoom.objects.get(name=self.room_name)

            # 接続時に確定したユーザー情報を使用
            ChatMessage.objects.create(
                room=room,
                user=self.authenticated_user if self.authenticated_user and not isinstance(self.authenticated_user, AnonymousUser) else None,
                content=message,
                message_type='message'
            )

            print(f"💾 SAVE: Message saved for user: {self.authenticated_username} (ID: {self.authenticated_user_id})")

        except ChatRoom.DoesNotExist:
            print(f"💾 SAVE ERROR: Chat room not found: {self.room_name}")
        except Exception as e:
            print(f"💾 SAVE ERROR: {e}")
    
    @database_sync_to_async
    def check_user_permissions(self):
        """Check if user can send messages."""
        try:
            # TenantResolverMiddlewareが既にスキーマを設定済み
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
    
    def get_user_id_from_session(self):
        """セッションからユーザーIDを安全に取得（同期版）"""
        try:
            session = self.scope.get("session")
            if session and hasattr(session, 'get'):
                user_id = session.get("_auth_user_id")
                return user_id
            return None
        except Exception as e:
            print(f"Error getting user ID from session: {e}")
            return None
    
    async def get_authenticated_user(self):
        """公式ドキュメント通りの標準的な認証確認"""
        try:
            user = self.scope.get("user")
            print(f"🔐 AUTH: User from scope: {user}")
            print(f"🔐 AUTH: User type: {type(user)}")
            print(f"🔐 AUTH: Is authenticated: {getattr(user, 'is_authenticated', False)}")
            
            # 公式ドキュメント通りの認証確認
            if user and getattr(user, 'is_authenticated', False):
                print(f"🔐 AUTH: Authenticated user: {user.username} (ID: {user.id})")
                return user
            
            print("🔐 AUTH: User not authenticated")
            return AnonymousUser()
            
        except Exception as e:
            print(f"🔐 AUTH: Error getting authenticated user: {e}")
            import traceback
            traceback.print_exc()
            return AnonymousUser()

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
            # TenantResolverMiddlewareが既にスキーマを設定済み
            stream = Stream.objects.get(stream_id=self.stream_id)
            return stream.viewer_count
        except Stream.DoesNotExist:
            return 0
        except Exception:
            return 0