from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('history/<str:stream_id>/', views.chat_history, name='chat_history'),
    path('toggle/<str:stream_id>/', views.toggle_chat, name='toggle_chat'),
    path('moderate/<int:message_id>/', views.moderate_message, name='moderate_message'),
    
    # Stamp and reaction endpoints
    path('stamps/', views.get_stamps, name='get_stamps'),
    path('react/', views.toggle_reaction, name='toggle_reaction'),
    path('reactions/<int:message_id>/', views.get_message_reactions, name='get_message_reactions'),
    
    # Moderation endpoints
    path('banned-words/<str:stream_id>/', views.manage_banned_words, name='manage_banned_words'),
    path('banned-words/remove/<int:word_id>/', views.remove_banned_word, name='remove_banned_word'),
    path('timeout/<str:stream_id>/', views.timeout_user, name='timeout_user'),
    path('timeouts/<str:stream_id>/', views.get_active_timeouts, name='get_active_timeouts'),
    path('timeout/remove/<int:timeout_id>/', views.remove_timeout, name='remove_timeout'),
]
