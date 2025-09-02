from django_tenants.models import TenantMixin, DomainMixin
from django.db import models


class Tenant(TenantMixin):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Streaming platform specific fields
    max_concurrent_streams = models.IntegerField(default=5)
    max_storage_gb = models.IntegerField(default=100)
    max_bandwidth_mbps = models.IntegerField(default=1000)
    
    # Feature flags
    enable_chat = models.BooleanField(default=True)
    enable_analytics = models.BooleanField(default=True)
    enable_moderation = models.BooleanField(default=True)
    enable_paid_content = models.BooleanField(default=False)
    
    auto_create_schema = True

    def __str__(self):
        return self.name


class Domain(DomainMixin):
    pass