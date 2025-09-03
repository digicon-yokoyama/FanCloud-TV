from django.urls import path
from . import views

app_name = 'streaming'

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('live/', views.live_streams, name='live'),
    path('watch/<str:stream_id>/', views.watch_stream, name='watch'),
    path('create/', views.create_stream, name='create'),
    
    # Stream management
    path('dashboard/<str:stream_id>/', views.stream_dashboard, name='stream_dashboard'),
    path('start/<str:stream_id>/', views.start_stream, name='start_stream'),
    path('end/<str:stream_id>/', views.end_stream, name='end_stream'),
    path('my-streams/', views.my_streams, name='my_streams'),
    path('update-settings/<str:stream_id>/', views.update_stream_settings, name='update_stream_settings'),
    path('delete/<str:stream_id>/', views.delete_stream, name='delete_stream'),
    
    # Embed
    path('embed/<str:stream_id>/', views.embed_player, name='embed'),
    
    # API
    path('api/stream/', views.StreamAPIView.as_view(), name='stream_api'),
    path('api/stream/<str:stream_id>/status/', views.stream_status_api, name='stream_status_api'),
    path('debug/auth/', views.debug_user_auth, name='debug_auth'),
    
    # OBS Overlay
    path('obs/overlay/<str:stream_id>/<str:token>/', views.obs_overlay, name='obs_overlay'),
    path('api/obs/<str:stream_id>/token/', views.generate_obs_token, name='generate_obs_token'),
]
