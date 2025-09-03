# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from .models import ChatMessage, ChatRoom, ChatStamp, ChatReaction
from apps.streaming.models import Stream
import json


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
            ).select_related('user').prefetch_related('reactions__stamp').order_by('-timestamp')[:50]
            
            messages_data = []
            for message in reversed(messages):
                username = message.user.username if message.user else 'システム'
                
                # Get reactions for this message
                reactions = {}
                for reaction in message.reactions.all():
                    stamp_id = str(reaction.stamp.id)
                    if stamp_id not in reactions:
                        reactions[stamp_id] = {
                            'stamp': {
                                'id': reaction.stamp.id,
                                'name': reaction.stamp.name,
                                'image_url': reaction.stamp.image.url if reaction.stamp.image else None,
                            },
                            'count': 0,
                            'user_reacted': False
                        }
                    reactions[stamp_id]['count'] += 1
                    if reaction.user == request.user:
                        reactions[stamp_id]['user_reacted'] = True
                
                messages_data.append({
                    'id': message.id,
                    'username': username,
                    'message': message.content,
                    'content': message.content,
                    'message_type': message.message_type,
                    'timestamp': message.timestamp.isoformat(),
                    'is_pinned': message.is_pinned,
                    'reactions': list(reactions.values()),
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


@login_required
@require_http_methods(["GET"])
def get_stamps(request):
    """Get list of available chat stamps."""
    try:
        stamps = ChatStamp.objects.filter(is_active=True).order_by('name')
        stamps_data = []
        
        for stamp in stamps:
            stamps_data.append({
                'id': stamp.id,
                'name': stamp.name,
                'image_url': stamp.image.url if stamp.image else None,
            })
        
        return JsonResponse({'stamps': stamps_data})
        
    except Exception as e:
        return JsonResponse({'error': 'Failed to load stamps'}, status=500)


@login_required
@require_http_methods(["POST"])
def toggle_reaction(request):
    """Add or remove a reaction to a chat message."""
    try:
        data = json.loads(request.body)
        message_id = data.get('message_id')
        stamp_id = data.get('stamp_id')
        
        if not message_id or not stamp_id:
            return JsonResponse({'error': 'Missing message_id or stamp_id'}, status=400)
        
        message = get_object_or_404(ChatMessage, id=message_id)
        stamp = get_object_or_404(ChatStamp, id=stamp_id, is_active=True)
        
        # Check if reaction already exists
        reaction, created = ChatReaction.objects.get_or_create(
            message=message,
            user=request.user,
            stamp=stamp
        )
        
        if created:
            action = 'added'
        else:
            reaction.delete()
            action = 'removed'
        
        # Get updated reaction count for this stamp on this message
        reaction_count = ChatReaction.objects.filter(message=message, stamp=stamp).count()
        
        return JsonResponse({
            'success': True,
            'action': action,
            'stamp_id': stamp_id,
            'message_id': message_id,
            'count': reaction_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except ChatMessage.DoesNotExist:
        return JsonResponse({'error': 'Message not found'}, status=404)
    except ChatStamp.DoesNotExist:
        return JsonResponse({'error': 'Stamp not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Failed to toggle reaction'}, status=500)


@login_required
@require_http_methods(["GET"])
def get_message_reactions(request, message_id):
    """Get all reactions for a specific message."""
    try:
        message = get_object_or_404(ChatMessage, id=message_id)
        
        # Get reactions grouped by stamp
        reactions = ChatReaction.objects.filter(message=message).select_related('stamp', 'user')
        
        reactions_data = {}
        for reaction in reactions:
            stamp_id = str(reaction.stamp.id)
            if stamp_id not in reactions_data:
                reactions_data[stamp_id] = {
                    'stamp': {
                        'id': reaction.stamp.id,
                        'name': reaction.stamp.name,
                        'image_url': reaction.stamp.image.url if reaction.stamp.image else None,
                    },
                    'count': 0,
                    'users': [],
                    'user_reacted': False
                }
            
            reactions_data[stamp_id]['count'] += 1
            reactions_data[stamp_id]['users'].append(reaction.user.username)
            
            if reaction.user == request.user:
                reactions_data[stamp_id]['user_reacted'] = True
        
        return JsonResponse({'reactions': list(reactions_data.values())})
        
    except ChatMessage.DoesNotExist:
        return JsonResponse({'error': 'Message not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Failed to load reactions'}, status=500)