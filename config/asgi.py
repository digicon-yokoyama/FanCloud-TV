"""
ASGI config for video streaming platform.
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Import tenant resolver middleware
from apps.tenants.asgi import TenantResolverMiddleware

django_asgi_app = get_asgi_application()

from config.routing import websocket_urlpatterns

# Django Channels setup with tenant-aware authentication
# CRITICAL: Middleware order is important!
# 1. TenantResolverMiddleware - determines tenant and sets schema
# 2. AuthMiddlewareStack - handles session/authentication within correct schema
# 3. URLRouter - routes to appropriate consumer
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": TenantResolverMiddleware(      # 1. Tenant resolution first
        AuthMiddlewareStack(                    # 2. Authentication second
            URLRouter(websocket_urlpatterns)    # 3. Routing last
        )
    ),
})

# Previous configurations (kept for reference)
# Standard auth only (didn't work with django-tenants):
# "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
#
# Custom middleware attempt (too complex):
# "websocket": SessionMiddlewareStack(TenantAwareAuthMiddlewareStack(URLRouter(...)))
