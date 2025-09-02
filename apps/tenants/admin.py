from django.contrib import admin
from .models import Tenant, Domain


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'schema_name', 'is_active', 'created_on']
    list_filter = ['is_active', 'created_on']
    search_fields = ['name', 'schema_name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'schema_name', 'description', 'is_active')
        }),
        ('Limits', {
            'fields': ('max_concurrent_streams', 'max_storage_gb', 'max_bandwidth_mbps')
        }),
        ('Features', {
            'fields': ('enable_chat', 'enable_analytics', 'enable_moderation', 'enable_paid_content')
        }),
    )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary']
    list_filter = ['is_primary']