"""
WebSocket routing for video streaming platform.
"""

from django.urls import path
from apps.chat import consumers

websocket_urlpatterns = [
    path('ws/chat/<str:room_name>/', consumers.ChatConsumer.as_asgi()),
    path('ws/viewers/<str:stream_id>/', consumers.ViewerCountConsumer.as_asgi()),
]