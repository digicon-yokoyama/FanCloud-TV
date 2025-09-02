from django.urls import path, include
from . import views, views_admin

app_name = 'accounts'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    
    # Admin URLs
    path('admin/', include([
        path('users/', views_admin.user_management, name='admin_users'),
        path('users/<int:user_id>/', views_admin.user_detail, name='admin_user_detail'),
        path('system/', views_admin.system_dashboard, name='admin_system'),
        path('api/update-role/', views_admin.update_user_role, name='api_update_role'),
        path('api/toggle-streaming/', views_admin.toggle_streaming_permission, name='api_toggle_streaming'),
        path('api/update-membership/', views_admin.update_membership, name='api_update_membership'),
    ])),
]