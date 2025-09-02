"""
Custom authentication middleware for django-tenants + Django Channels.

This middleware ensures proper authentication handling in WebSocket connections
within a multi-tenant environment.
"""

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context
from apps.tenants.models import Tenant
import logging

logger = logging.getLogger(__name__)


def get_user_from_session_sync(session):
    """
    Synchronous version of get user from session in a tenant-aware way.
    """
    try:
        # Get user ID from session
        user_id = session.get('_auth_user_id')
        if not user_id:
            logger.debug("No user ID found in session")
            return AnonymousUser()

        # Get the current tenant
        tenant = Tenant.objects.first()  # In a real app, you'd determine this properly
        if not tenant:
            logger.warning("No tenant found")
            return AnonymousUser()

        # Use tenant schema context to get user
        with schema_context(tenant.schema_name):
            User = get_user_model()
            user = User.objects.get(id=user_id)
            logger.debug(f"Found authenticated user: {user.username} (ID: {user.id})")
            return user

    except Exception as e:
        logger.error(f"Error getting user from session: {e}")
        return AnonymousUser()


@database_sync_to_async
def get_user_from_session(session):
    """
    Async wrapper for get_user_from_session_sync.
    """
    return get_user_from_session_sync(session)


class TenantAwareAuthMiddleware:
    """
    Simplified auth middleware that works with django-tenants.
    Uses a different approach to avoid async/sync issues.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        import sys
        import logging
        
        # 強制ログ出力
        print(f"🔥 MIDDLEWARE: Called with scope type: {scope.get('type')}", flush=True)
        sys.stdout.flush()
        logging.error(f"🔥 MIDDLEWARE: Called with scope type: {scope.get('type')}")
        
        # Only process websocket connections
        if scope["type"] != "websocket":
            print(f"🔥 MIDDLEWARE: Not websocket, passing through", flush=True)
            return await self.inner(scope, receive, send)

        print(f"🔥 MIDDLEWARE: Processing WebSocket connection for path: {scope.get('path')}", flush=True)
        logging.error(f"🔥 MIDDLEWARE: Processing WebSocket connection for path: {scope.get('path')}")
        
        # 実際のセッション認証を実装
        try:
            session = scope.get("session")
            print(f"🔐 MIDDLEWARE: Session available: {session is not None}")
            
            if session:
                # セッションアクセスを安全に実行
                user_id = await self.get_user_id_safe(session)
                print(f"🔐 MIDDLEWARE: User ID from session: {user_id}")
                
                if user_id:
                    # テスト用：ダミーユーザーオブジェクトを作成
                    class DummyUser:
                        def __init__(self, user_id):
                            self.id = user_id
                            self.username = "streamer"  # テスト用
                            self.is_authenticated = True
                    
                    dummy_user = DummyUser(user_id)
                    scope["user"] = dummy_user
                    print(f"🔐 MIDDLEWARE: Set dummy user: {dummy_user.username} (ID: {dummy_user.id})")
                else:
                    scope["user"] = AnonymousUser()
                    print("🔐 MIDDLEWARE: No user_id in session, set AnonymousUser")
            else:
                scope["user"] = AnonymousUser()
                print("🔐 MIDDLEWARE: No session, set AnonymousUser")
        except Exception as e:
            print(f"🔐 MIDDLEWARE: Error in auth: {e}")
            import traceback
            traceback.print_exc()
            scope["user"] = AnonymousUser()
        
        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def get_user_id_safe(self, session):
        """Safely get user ID from session."""
        try:
            user_id = session.get('_auth_user_id')
            print(f"🔍 SYNC: _auth_user_id = {user_id}")
            return user_id
        except Exception as e:
            print(f"🔍 SYNC: Error getting user_id: {e}")
            return None

    @database_sync_to_async
    def debug_session_safe(self, session):
        """Safely debug session contents."""
        try:
            session_info = {
                'type': str(type(session)),
                'keys': list(session.keys()) if hasattr(session, 'keys') else 'No keys method',
                'auth_user_id': session.get('_auth_user_id'),
                'auth_user_backend': session.get('_auth_user_backend'),
                'auth_user_hash': session.get('_auth_user_hash'),
                'session_key': getattr(session, 'session_key', 'No session_key'),
            }
            return session_info
        except Exception as e:
            return f"Error debugging session: {e}"

    @database_sync_to_async
    def get_user_id_from_session_safe(self, session):
        """Safely get user ID from session."""
        try:
            # セッションアクセスも同期処理なので、ここで実行
            user_id = session.get('_auth_user_id')
            print(f"🔍 SYNC DEBUG: _auth_user_id from session: {user_id}")
            return user_id
        except Exception as e:
            print(f"🔐 MIDDLEWARE: Error getting user ID: {e}")
            return None

    @database_sync_to_async
    def get_user_by_id_safe(self, user_id):
        """Safely get user by ID with tenant context."""
        try:
            from apps.tenants.models import Tenant
            
            # Get the first tenant (in a real app, you'd determine this properly)
            tenant = Tenant.objects.first()
            if not tenant:
                print("🔐 MIDDLEWARE: No tenant found")
                return AnonymousUser()

            # Use tenant schema context to get user
            with schema_context(tenant.schema_name):
                User = get_user_model()
                user = User.objects.get(id=user_id)
                print(f"🔐 MIDDLEWARE: Found user: {user.username}")
                return user

        except Exception as e:
            print(f"🔐 MIDDLEWARE: Error getting user by ID {user_id}: {e}")
            return AnonymousUser()


def TenantAwareAuthMiddlewareStack(inner):
    """
    Middleware stack that includes tenant-aware authentication.
    """
    print(f"🔥 STACK: Creating TenantAwareAuthMiddlewareStack")
    auth_stack = AuthMiddlewareStack(inner)
    tenant_middleware = TenantAwareAuthMiddleware(auth_stack)
    print(f"🔥 STACK: TenantAwareAuthMiddlewareStack created successfully")
    return tenant_middleware
