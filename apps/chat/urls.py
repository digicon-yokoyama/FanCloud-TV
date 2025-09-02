from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('history/<str:stream_id>/', views.chat_history, name='chat_history'),
    path('toggle/<str:stream_id>/', views.toggle_chat, name='toggle_chat'),
    path('moderate/<int:message_id>/', views.moderate_message, name='moderate_message'),
]
