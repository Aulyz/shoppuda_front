# File: platforms/admin.py
from django.contrib import admin
from .models import Platform, PlatformProduct, Supplier

@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ['name', 'platform_type', 'is_active', 'created_at']
    list_filter = ['platform_type', 'is_active']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'platform_type', 'is_active')
        }),
        ('API 설정', {
            'fields': ('api_key', 'api_secret', 'api_url'),
            'classes': ('collapse',)
        }),
        ('메타 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PlatformProduct)
class PlatformProductAdmin(admin.ModelAdmin):
    list_display = ['product', 'platform', 'platform_product_id', 'platform_price', 'platform_stock', 'is_active', 'last_sync_at']
    list_filter = ['platform', 'is_active']
    search_fields = ['product__sku', 'product__name', 'platform_product_id']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'platform')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'contact_person', 'email', 'phone', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'contact_person', 'email']