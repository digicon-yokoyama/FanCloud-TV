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
    path('playlists/public/', views.public_playlists, name='public_playlists'),
    path('playlists/create/', views.create_playlist, name='create_playlist'),
    path('playlists/add/', views.add_to_playlist, name='add_to_playlist'),
    path('playlists/<int:pk>/', views.playlist_detail, name='playlist_detail'),
    path('playlists/<int:pk>/edit/', views.edit_playlist, name='edit_playlist'),
    path('playlists/<int:pk>/delete/', views.delete_playlist, name='delete_playlist'),
    path('playlists/<int:pk>/add-video/', views.add_video_to_playlist, name='add_video_to_playlist'),
    path('playlists/<int:pk>/add-multiple/', views.add_multiple_videos_to_playlist, name='add_multiple_videos_to_playlist'),
    path('playlists/<int:pk>/remove/<int:item_id>/', views.remove_from_playlist, name='remove_from_playlist'),
    
    # Video upload and management
    path('upload/', views.upload_video, name='upload_video'),
    path('manage/', views.manage_videos, name='manage_videos'),
    path('edit/<int:video_id>/', views.edit_video, name='edit_video'),
    path('delete/<int:video_id>/', views.delete_video, name='delete_video'),
    path('api/video/<int:video_id>/status/', views.video_processing_status, name='video_processing_status'),
    
    # Comments and likes
    path('api/video/<int:video_id>/like/', views.like_video, name='like_video'),
    path('api/video/<int:video_id>/comment/', views.add_comment, name='add_comment'),
    path('api/comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    
    # Category Management (Admin only)
    path('admin/categories/', views.manage_categories, name='admin_categories'),
    path('admin/categories/create/', views.create_category, name='create_category'),
    path('admin/categories/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('admin/categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),
]
