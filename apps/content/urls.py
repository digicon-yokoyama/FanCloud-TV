from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('trending/', views.trending, name='trending'),
    path('subscriptions/', views.subscriptions, name='subscriptions'),
    path('search/', views.search_videos, name='search'),
    path('watch/<int:video_id>/', views.watch_video, name='watch'),
    
    # User library
    path('history/', views.history, name='history'),
    path('favorites/', views.favorites, name='favorites'),
    path('playlists/', views.playlists, name='playlists'),
    
    # Video upload and management
    path('upload/', views.upload_video, name='upload_video'),
    path('manage/', views.manage_videos, name='manage_videos'),
    path('delete/<int:video_id>/', views.delete_video, name='delete_video'),
    path('api/video/<int:video_id>/status/', views.video_processing_status, name='video_processing_status'),
    
    # Comments and likes
    path('api/video/<int:video_id>/like/', views.like_video, name='like_video'),
    path('api/video/<int:video_id>/comment/', views.add_comment, name='add_comment'),
    path('api/comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
]
