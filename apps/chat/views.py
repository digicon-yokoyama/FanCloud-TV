# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from .models import ChatMessage, ChatRoom
from apps.streaming.models import Stream


@login_required
@require_http_methods(["GET"])
def chat_history(request, stream_id):
    """Get chat history for a stream."""
    try:
        # テナント対応のためのimport
        from apps.tenants.models import Tenant
        from django_tenants.utils import schema_context
        
        tenant = Tenant.objects.first()
        
        with schema_context(tenant.schema_name):
            stream = get_object_or_404(Stream, stream_id=stream_id)
            
            # Check if chat room exists by room name (matching Consumer logic)
            try:
                room = ChatRoom.objects.get(name=stream_id)
            except ChatRoom.DoesNotExist:
                return JsonResponse({'messages': []})
            
            # Get recent messages (last 50)
            messages = ChatMessage.objects.filter(
                room=room,
                is_deleted=False
            ).select_related('user').order_by('-timestamp')[:50]
            
            messages_data = []
            for message in reversed(messages):
                username = message.user.username if message.user else 'システム'
                
                messages_data.append({
                    'id': message.id,
                    'username': username,
                    'message': message.content,
                    'content': message.content,
                    'message_type': message.message_type,
                    'timestamp': message.timestamp.isoformat(),
                    'is_pinned': message.is_pinned,
                })
            
            return JsonResponse({'messages': messages_data})
        
    except Exception as e:
        return JsonResponse({'error': 'Failed to load chat history'}, status=500)


@login_required  
@require_http_methods(["POST"])
def toggle_chat(request, stream_id):
    """Toggle chat enabled/disabled for stream owner."""
    try:
        stream = get_object_or_404(Stream, stream_id=stream_id, streamer=request.user)
        stream.enable_chat = not stream.enable_chat
        stream.save()
        
        return JsonResponse({
            'success': True,
            'chat_enabled': stream.enable_chat
        })
        
    except Stream.DoesNotExist:
        return JsonResponse({'error': 'Stream not found or no permission'}, status=403)
    except Exception as e:
        return JsonResponse({'error': 'Failed to update chat setting'}, status=500)


@login_required
@require_http_methods(["POST"])
def moderate_message(request, message_id):
    """Moderate (delete/pin) a chat message."""
    try:
        message = get_object_or_404(ChatMessage, id=message_id)
        
        # Check if user can moderate (stream owner or moderator)
        room = message.room
        if (hasattr(room, 'stream') and 
            room.stream.streamer == request.user) or \
           room.moderators.filter(user=request.user).exists():
            
            action = request.POST.get('action')
            
            if action == 'delete':
                message.is_deleted = True
                message.save()
                return JsonResponse({'success': True, 'action': 'deleted'})
            elif action == 'pin':
                message.is_pinned = not message.is_pinned
                message.save()
                return JsonResponse({
                    'success': True, 
                    'action': 'pinned' if message.is_pinned else 'unpinned'
                })
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
        else:
            return JsonResponse({'error': 'No permission'}, status=403)
            
    except ChatMessage.DoesNotExist:
        return JsonResponse({'error': 'Message not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Moderation failed'}, status=500)