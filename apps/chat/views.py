# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from .models import ChatMessage, ChatRoom, ChatStamp, ChatReaction
from apps.streaming.models import Stream
from apps.moderation.models import BannedWord, ModerationAction
from django.utils import timezone
from datetime import timedelta
import json
import re


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
        
        # Check stream ownership permission
        can_moderate = False
        
        if room.stream and room.stream.streamer == request.user:
            can_moderate = True
        
        # Also allow system/tenant admins to moderate
        if request.user.role in ['system_admin', 'tenant_admin']:
            can_moderate = True
        
        if can_moderate:
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
            # More detailed error message for debugging
            if not room.stream:
                return JsonResponse({'error': 'No stream associated with chat room'}, status=500)
            else:
                return JsonResponse({'error': 'Only the stream owner can moderate messages'}, status=403)
            
    except ChatMessage.DoesNotExist:
        return JsonResponse({'error': 'Message not found'}, status=404)
    except Exception as e:
        import logging
        logging.error(f"Moderation error: {str(e)}")
        return JsonResponse({'error': f'Moderation failed: {str(e)}'}, status=500)


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
        # Check if user is timed out
        timeout = is_user_timed_out(request.user)
        if timeout:
            return JsonResponse({'error': 'チャット機能が配信者によりロックされています。'}, status=403)
        
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


@login_required
@require_http_methods(["GET", "POST"])
def manage_banned_words(request, stream_id):
    """Manage banned words for a stream."""
    try:
        stream = get_object_or_404(Stream, stream_id=stream_id, streamer=request.user)
        
        if request.method == "GET":
            # Get current banned words
            banned_words = BannedWord.objects.filter(is_active=True).order_by('word')
            words_data = [
                {
                    'id': word.id,
                    'word': word.word,
                    'severity': word.severity,
                    'created_at': word.created_at.isoformat(),
                }
                for word in banned_words
            ]
            return JsonResponse({'banned_words': words_data})
        
        elif request.method == "POST":
            # Add or update banned words
            data = json.loads(request.body)
            words_text = data.get('words', '').strip()
            
            if not words_text:
                return JsonResponse({'error': 'No words provided'}, status=400)
            
            # Parse words (comma separated)
            words = [word.strip().lower() for word in words_text.split(',') if word.strip()]
            
            added_count = 0
            for word in words:
                if word and len(word) > 1:  # Skip empty or single character words
                    banned_word, created = BannedWord.objects.get_or_create(
                        word=word,
                        defaults={'severity': 'medium', 'is_active': True}
                    )
                    if created:
                        added_count += 1
            
            return JsonResponse({
                'success': True,
                'message': f'{added_count}個の禁止ワードを追加しました',
                'added_count': added_count
            })
            
    except Stream.DoesNotExist:
        return JsonResponse({'error': 'Stream not found or no permission'}, status=403)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Failed to manage banned words'}, status=500)


@login_required
@require_http_methods(["POST"])
def remove_banned_word(request, word_id):
    """Remove a banned word."""
    try:
        banned_word = get_object_or_404(BannedWord, id=word_id)
        word_text = banned_word.word
        banned_word.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'「{word_text}」を禁止ワードから削除しました'
        })
        
    except BannedWord.DoesNotExist:
        return JsonResponse({'error': 'Banned word not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Failed to remove banned word'}, status=500)


@login_required
@require_http_methods(["POST"])
def timeout_user(request, stream_id):
    """Timeout a user in chat."""
    try:
        stream = get_object_or_404(Stream, stream_id=stream_id, streamer=request.user)
        
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        duration_minutes = int(data.get('duration', 5))
        reason = data.get('reason', 'Chat timeout')
        
        if not username:
            return JsonResponse({'error': 'Username is required'}, status=400)
        
        # Find the user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            target_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'error': f'User "{username}" not found'}, status=404)
        
        # Check if user is already timed out
        existing_timeout = ModerationAction.objects.filter(
            target_user=target_user,
            action_type='timeout',
            is_active=True,
            expires_at__gt=timezone.now()
        ).first()
        
        if existing_timeout:
            return JsonResponse({
                'error': f'User is already timed out until {existing_timeout.expires_at.strftime("%H:%M")}'
            }, status=400)
        
        # Create timeout action
        expires_at = timezone.now() + timedelta(minutes=duration_minutes)
        timeout_action = ModerationAction.objects.create(
            action_type='timeout',
            target_type='user',
            target_id=str(target_user.id),
            target_user=target_user,
            moderator=request.user,
            reason=reason,
            duration=duration_minutes,
            expires_at=expires_at,
            is_active=True
        )
        
        return JsonResponse({
            'success': True,
            'message': f'{username}を{duration_minutes}分間タイムアウトしました',
            'timeout_id': timeout_action.id,
            'expires_at': expires_at.isoformat()
        })
        
    except Stream.DoesNotExist:
        return JsonResponse({'error': 'Stream not found or no permission'}, status=403)
    except ValueError:
        return JsonResponse({'error': 'Invalid duration'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Failed to timeout user'}, status=500)


@login_required
@require_http_methods(["GET"])
def get_active_timeouts(request, stream_id):
    """Get active timeouts for a stream."""
    try:
        stream = get_object_or_404(Stream, stream_id=stream_id, streamer=request.user)
        
        # Get active timeouts
        active_timeouts = ModerationAction.objects.filter(
            action_type='timeout',
            is_active=True,
            expires_at__gt=timezone.now()
        ).select_related('target_user').order_by('-created_at')
        
        timeouts_data = []
        for timeout in active_timeouts:
            timeouts_data.append({
                'id': timeout.id,
                'username': timeout.target_user.username,
                'reason': timeout.reason,
                'duration': timeout.duration,
                'expires_at': timeout.expires_at.isoformat(),
                'created_at': timeout.created_at.isoformat(),
            })
        
        return JsonResponse({'timeouts': timeouts_data})
        
    except Stream.DoesNotExist:
        return JsonResponse({'error': 'Stream not found or no permission'}, status=403)
    except Exception as e:
        return JsonResponse({'error': 'Failed to load timeouts'}, status=500)


@login_required
@require_http_methods(["POST"])
def remove_timeout(request, timeout_id):
    """Remove user timeout early."""
    try:
        timeout_action = get_object_or_404(
            ModerationAction, 
            id=timeout_id,
            action_type='timeout',
            moderator=request.user,
            is_active=True
        )
        
        timeout_action.is_active = False
        timeout_action.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{timeout_action.target_user.username}のタイムアウトを解除しました'
        })
        
    except ModerationAction.DoesNotExist:
        return JsonResponse({'error': 'Timeout not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Failed to remove timeout'}, status=500)


def check_banned_words(message):
    """Check if message contains banned words."""
    banned_words = BannedWord.objects.filter(is_active=True)
    message_lower = message.lower()
    
    for banned_word in banned_words:
        if banned_word.word in message_lower:
            return True, banned_word.word
    
    return False, None


def is_user_timed_out(user):
    """Check if user is currently timed out."""
    active_timeout = ModerationAction.objects.filter(
        target_user=user,
        action_type='timeout',
        is_active=True,
        expires_at__gt=timezone.now()
    ).first()
    
    return active_timeout