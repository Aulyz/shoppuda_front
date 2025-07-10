# File: orders/admin.py
from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'platform', 'customer_name', 'status', 'total_amount', 'order_date']
    list_filter = ['status', 'platform', 'order_date']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'platform_order_id']
    date_hierarchy = 'order_date'
    inlines = [OrderItemInline]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('주문 정보', {
            'fields': ('order_number', 'platform', 'platform_order_id', 'status')
        }),
        ('고객 정보', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('배송 정보', {
            'fields': ('shipping_address', 'shipping_zipcode', 'shipping_method', 'tracking_number')
        }),
        ('금액 정보', {
            'fields': ('total_amount', 'shipping_fee', 'discount_amount')
        }),
        ('일시 정보', {
            'fields': ('order_date', 'shipped_date', 'delivered_date', 'cancelled_date', 'refunded_date')
        }),
        ('메타 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )