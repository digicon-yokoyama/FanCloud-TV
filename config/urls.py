"""
URL configuration for video streaming platform.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # API endpoints
    # path('api/auth/', include('apps.accounts.urls', namespace='api_accounts')),
    path('api/streaming/', include('apps.streaming.urls', namespace='api_streaming')),
    path('api/content/', include('apps.content.urls', namespace='api_content')),
    path('api/chat/', include('apps.chat.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    
    # Main application views
    path('', include('apps.streaming.urls')),
    path('content/', include('apps.content.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('legal/', include('apps.legal.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
