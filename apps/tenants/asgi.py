"""
ASGI middleware for django-tenants WebSocket support.

This middleware resolves the tenant from the Host header and sets the
appropriate database schema context for WebSocket connections.
"""

from django.db import connection
from django_tenants.utils import get_tenant_model, get_public_schema_name, schema_context
from channels.db import database_sync_to_async


class TenantResolverMiddleware:
    """
    ASGI middleware that resolves tenant from Host header and sets schema context.
    
    This middleware must be placed BEFORE AuthMiddlewareStack to ensure
    that session and authentication queries use the correct tenant schema.
    """
    
    def __init__(self, app):
        self.app = app
        self.TenantModel = get_tenant_model()

    async def __call__(self, scope, receive, send):
        # Only process websocket connections
        if scope["type"] != "websocket":
            return await self.app(scope, receive, send)
            
        # Extract host from headers
        headers = dict(scope.get("headers") or [])
        host = headers.get(b'host', b'').decode().split(':')[0]
        
        print(f"🏢 TENANT: Resolving tenant for host: {host}")
        
        # Resolve tenant from host (async-safe)
        tenant = await self.get_tenant_for_host(host)

        # Determine schema name
        schema_name = tenant.schema_name if tenant else get_public_schema_name()
        
        # Add tenant info to scope for consumers
        scope["tenant"] = tenant
        scope["schema_name"] = schema_name
        
        print(f"🏢 TENANT: Using schema: {schema_name}")
        print(f"🏢 TENANT: About to call inner app with schema context")
        
        # Set schema in connection for this async context
        # We use sync_to_async to safely set the schema
        await self.set_tenant_schema(schema_name)
        
        print(f"🏢 TENANT: Schema set, calling inner app")
        
        try:
            result = await self.app(scope, receive, send)
            print(f"🏢 TENANT: Inner app completed successfully")
            return result
        except Exception as e:
            print(f"🏢 TENANT: ERROR in inner app: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @database_sync_to_async
    def set_tenant_schema(self, schema_name):
        """Set the database schema for the current connection."""
        connection.set_schema(schema_name)
        print(f"🏢 TENANT: Schema set to: {schema_name}")
    
    @database_sync_to_async
    def get_tenant_for_host(self, host):
        """Safely resolve tenant from host in async context."""
        try:
            # Try to find tenant by domain
            from apps.tenants.models import Domain
            domain = Domain.objects.select_related('tenant').get(domain=host)
            tenant = domain.tenant
            print(f"🏢 TENANT: Found tenant: {tenant.name} (schema: {tenant.schema_name})")
            return tenant
        except Domain.DoesNotExist:
            # Fallback: try localhost for development
            if host in ['localhost', '127.0.0.1', '0.0.0.0']:
                try:
                    tenant = self.TenantModel.objects.first()
                    if tenant:
                        print(f"🏢 TENANT: Using first tenant for localhost: {tenant.name}")
                        return tenant
                except Exception as e:
                    print(f"🏢 TENANT: Error getting first tenant: {e}")
            else:
                print(f"🏢 TENANT: No tenant found for host: {host}")
        except Exception as e:
            print(f"🏢 TENANT: Error resolving tenant: {e}")
        
        return None
