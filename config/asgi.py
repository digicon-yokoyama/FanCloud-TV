"""
ASGI config for video streaming platform.
"""

import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack
from django.core.asgi import get_asgi_application
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

from config.routing import websocket_urlpatterns

User = get_user_model()

class CustomAuthMiddleware(BaseMiddleware):
    """Custom authentication middleware for django-tenants compatibility."""
    
    def __init__(self, inner):
        super().__init__(inner)
    
    async def __call__(self, scope, receive, send):
        print(f"🔐 AUTH DEBUG: CustomAuthMiddleware called")
        print(f"🔐 AUTH DEBUG: Scope type: {scope.get('type')}")
        print(f"🔐 AUTH DEBUG: Headers: {dict(scope.get('headers', []))}")
        
        if scope["type"] == "websocket":
            try:
                # Debug session data
                session = scope.get("session")
                print(f"🔐 AUTH DEBUG: Session object: {session}")
                print(f"🔐 AUTH DEBUG: Session keys: {list(session.keys()) if session else 'No session'}")
                if session:
                    print(f"🔐 AUTH DEBUG: Session content: {dict(session)}")
                
                # Get user ID from session asynchronously
                user_id = await self.get_user_id_from_session(scope)
                print(f"🔐 AUTH DEBUG: User ID from session: {user_id}")
                
                if user_id:
                    try:
                        user = await self.get_user(user_id)
                        print(f"🔐 AUTH DEBUG: User loaded: {user}")
                        print(f"🔐 AUTH DEBUG: User type: {type(user)}")
                        print(f"🔐 AUTH DEBUG: User ID: {user.id if hasattr(user, 'id') else 'No ID'}")
                        print(f"🔐 AUTH DEBUG: User is_authenticated: {getattr(user, 'is_authenticated', 'No method')}")
                        scope["user"] = user
                    except Exception as e:
                        print(f"🔐 AUTH DEBUG: Error loading user: {e}")
                        import traceback
                        traceback.print_exc()
                        scope["user"] = AnonymousUser()
                else:
                    print("🔐 AUTH DEBUG: No user ID in session")
                    scope["user"] = AnonymousUser()
                    
            except Exception as e:
                print(f"🔐 AUTH DEBUG: Error accessing session: {e}")
                import traceback
                traceback.print_exc()
                scope["user"] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)
    
    @database_sync_to_async
    def get_user_id_from_session(self, scope):
        """Safely get user ID from session."""
        try:
            session = scope.get("session")
            if session:
                return session.get("_auth_user_id")
            return None
        except Exception as e:
            print(f"🔐 AUTH DEBUG: Session access error: {e}")
            return None
    
    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()

# Custom middleware stack for multi-tenant WebSocket authentication
def get_websocket_application():
    return SessionMiddlewareStack(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    )

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": get_websocket_application(),
})
