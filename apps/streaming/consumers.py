"""
WebSocket consumers for streaming features (reactions, live updates, etc.)
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


class StreamReactionConsumer(AsyncWebsocketConsumer):
    """
    YouTubeLive風のリアルタイムリアクション機能
    配信画面上を流れるリアクションエフェクト用
    """
    
    async def connect(self):
        self.stream_id = self.scope['url_route']['kwargs']['stream_id']
        self.room_group_name = f'reactions_{self.stream_id}'
        
        # グループに参加
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # 接続確認メッセージ
        await self.send(text_data=json.dumps({
            'type': 'connection_status',
            'message': 'リアクション機能に接続しました'
        }))

    async def disconnect(self, close_code):
        # グループから退出
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'stream_reaction':
                await self.handle_stream_reaction(data)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error', 
                'message': f'Server error: {str(e)}'
            }))

    async def handle_stream_reaction(self, data):
        """
        配信に対するリアクションを処理
        """
        user = self.scope.get('user')
        if isinstance(user, AnonymousUser):
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'ログインが必要です'
            }))
            return
            
        stamp_id = data.get('stamp_id')
        stamp_name = data.get('stamp_name')
        stamp_image_url = data.get('stamp_image_url')
        stream_id = data.get('stream_id')
        
        if not all([stamp_id, stream_id]):
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Required fields missing'
            }))
            return
        
        # データベースにリアクションを保存（統計用）
        try:
            await self.save_stream_reaction(user.id, stream_id, stamp_id)
        except Exception as e:
            print(f"Failed to save reaction: {e}")
        
        # 全視聴者にリアクションを配信
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'reaction_message',
                'stamp_id': stamp_id,
                'stamp_name': stamp_name,
                'stamp_image_url': stamp_image_url,
                'username': user.username,
                'user_id': user.id,
            }
        )

    async def reaction_message(self, event):
        """
        リアクションメッセージを送信
        """
        await self.send(text_data=json.dumps({
            'type': 'reaction',
            'stamp_id': event['stamp_id'],
            'stamp_name': event['stamp_name'],
            'stamp_image_url': event['stamp_image_url'],
            'username': event['username'],
            'user_id': event['user_id'],
        }))

    @database_sync_to_async
    def save_stream_reaction(self, user_id, stream_id, stamp_id):
        """
        配信リアクションをデータベースに保存（統計・分析用）
        """
        from apps.streaming.models import Stream
        from apps.chat.models import ChatStamp
        from apps.streaming.models import StreamReaction
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
            stream = Stream.objects.get(stream_id=stream_id)
            stamp = ChatStamp.objects.get(id=stamp_id)
            
            # StreamReactionレコードを作成
            reaction = StreamReaction.objects.create(
                stream=stream,
                user=user,
                stamp=stamp
            )
            
            return reaction
            
        except (User.DoesNotExist, Stream.DoesNotExist, ChatStamp.DoesNotExist) as e:
            raise Exception(f"Record not found: {e}")