"""
WebSocket routing for video streaming platform.
"""

from django.urls import path
from apps.chat import consumers
from apps.streaming import consumers as streaming_consumers
import traceback

print("🔧 ROUTING: Loading WebSocket consumers...")

try:
    test_consumer = consumers.TestConsumer.as_asgi()
    simple_chat_consumer = consumers.SimpleChatConsumer.as_asgi()
    chat_consumer = consumers.ChatConsumer.as_asgi()
    viewer_consumer = consumers.ViewerCountConsumer.as_asgi()
    reaction_consumer = streaming_consumers.StreamReactionConsumer.as_asgi()

    print("🔧 ROUTING: All consumers loaded successfully")
    print(f"🔧 ROUTING: TestConsumer: {test_consumer}")
    print(f"🔧 ROUTING: SimpleChatConsumer: {simple_chat_consumer}")
    print(f"🔧 ROUTING: ChatConsumer: {chat_consumer}")
    print(f"🔧 ROUTING: ViewerCountConsumer: {viewer_consumer}")
    print(f"🔧 ROUTING: StreamReactionConsumer: {reaction_consumer}")

except Exception as e:
    print(f"🔧 ROUTING: ERROR loading consumers: {e}")
    traceback.print_exc()

websocket_urlpatterns = [
    path('ws/test/', test_consumer),
    path('ws/simple_chat/<str:room_name>/', simple_chat_consumer),
    path('ws/chat/<str:room_name>/', chat_consumer),
    path('ws/viewers/<str:stream_id>/', viewer_consumer),
    path('ws/reactions/<str:stream_id>/', reaction_consumer),
]

print("🔧 ROUTING: WebSocket URL patterns created")
print(f"🔧 ROUTING: Patterns: {websocket_urlpatterns}")