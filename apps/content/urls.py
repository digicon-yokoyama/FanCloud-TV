from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('trending/', views.trending, name='trending'),
    path('subscriptions/', views.subscriptions, name='subscriptions'),
    path('watch/<int:video_id>/', views.watch_video, name='watch'),
]
