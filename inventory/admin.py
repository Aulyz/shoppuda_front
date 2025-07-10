# inventory/admin.py - 재고 관리 Django 관리자
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.contrib import messages

from .models import StockMovement, StockAlert, StockLevel, InventoryTransaction

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        'reference_number', 'product_link', 'movement_type_badge', 
        'quantity_display', 'stock_change', 'reason', 
        'created_by', 'created_at_formatted'
    ]
    list_filter = [
        'movement_type', 'is_automated', 'source_system',
        'created_at', 'created_by'
    ]
    search_fields = [
        'product__name', 'product__sku', 'reference_number', 
        'reason', 'notes'
    ]
    readonly_fields = [
        'reference_number', 'quantity_change', 'created_at', 
        'total_cost_display'
    ]
    autocomplete_fields = ['product', 'order', 'platform', 'created_by']
    
    fieldsets = (
        ('기본 정보', {
            'fields': (
                'product', 'movement_type', 'quantity', 'reference_number'
            )
        }),
        ('재고 정보', {
            'fields': (
                'previous_stock', 'current_stock', 'quantity_change'
            )
        }),
        ('상세 정보', {
            'fields': (
                'reason', 'notes', 'warehouse'
            )
        }),
        ('비용 정보', {
            'fields': (
                'unit_cost', 'total_cost', 'total_cost_display'
            ),
            'classes': ('collapse',)
        }),
        ('연관 정보', {
            'fields': (
                'order', 'platform'
            ),
            'classes': ('collapse',)
        }),
        ('시스템 정보', {
            'fields': (
                'is_automated', 'source_system', 'created_by', 'created_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def product_link(self, obj):
        if obj.product:
            url = reverse('admin:products_product_change', args=[obj.product.pk])
            return format_html('<a href="{}">{}</a>', url, obj.product.name)
        return '-'
    product_link.short_description = '상품'
    
    def movement_type_badge(self, obj):
        colors = {
            'IN': 'success',
            'OUT': 'danger', 
            'ADJUST': 'warning',
            'TRANSFER': 'info',
            'RETURN': 'secondary',
            'DAMAGE': 'dark',
            'SALE': 'primary',
            'PURCHASE': 'success'
        }
        color = colors.get(obj.movement_type, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_movement_type_display()
        )
    movement_type_badge.short_description = '이동 유형'
    
    def quantity_display(self, obj):
        if obj.is_increase:
            return format_html('<span style="color: green;">+{}</span>', obj.quantity)
        elif obj.is_decrease:
            return format_html('<span style="color: red;">-{}</span>', obj.quantity)
        else:
            return str(obj.quantity)
    quantity_display.short_description = '수량'
    
    def stock_change(self, obj):
        return f'{obj.previous_stock} → {obj.current_stock}'
    stock_change.short_description = '재고 변화'
    
    def created_at_formatted(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_formatted.short_description = '생성일시'
    
    def total_cost_display(self, obj):
        if obj.total_cost:
            return f'₩{obj.total_cost:,.0f}'
        return '-'
    total_cost_display.short_description = '총 비용'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'product', 'product__brand', 'created_by', 'order', 'platform'
        )

@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = [
        'product_link', 'alert_type_badge', 'status_badge',
        'current_vs_threshold', 'created_at_formatted',
        'resolved_by'
    ]
    list_filter = [
        'alert_type', 'status', 'is_email_sent',
        'created_at', 'resolved_at'
    ]
    search_fields = [
        'product__name', 'product__sku', 'message'
    ]
    readonly_fields = [
        'created_at', 'email_sent_at', 'resolved_at'
    ]
    autocomplete_fields = ['product', 'resolved_by']
    actions = ['resolve_alerts', 'dismiss_alerts', 'send_email_alerts']
    
    fieldsets = (
        ('알림 정보', {
            'fields': (
                'product', 'alert_type', 'status', 'message'
            )
        }),
        ('수치 정보', {
            'fields': (
                'threshold_value', 'current_value'
            )
        }),
        ('처리 정보', {
            'fields': (
                'resolved_at', 'resolved_by'
            )
        }),
        ('이메일 정보', {
            'fields': (
                'is_email_sent', 'email_sent_at'
            ),
            'classes': ('collapse',)
        }),
        ('시간 정보', {
            'fields': (
                'created_at',
            ),
            'classes': ('collapse',)
        })
    )
    
    def product_link(self, obj):
        if obj.product:
            url = reverse('admin:products_product_change', args=[obj.product.pk])
            return format_html('<a href="{}">{}</a>', url, obj.product.name)
        return '-'
    product_link.short_description = '상품'
    
    def alert_type_badge(self, obj):
        colors = {
            'LOW_STOCK': 'warning',
            'OUT_OF_STOCK': 'danger',
            'OVERSTOCK': 'info',
            'EXPIRY_WARNING': 'secondary',
            'SLOW_MOVING': 'dark'
        }
        color = colors.get(obj.alert_type, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_alert_type_display()
        )
    alert_type_badge.short_description = '알림 유형'
    
    def status_badge(self, obj):
        colors = {
            'ACTIVE': 'danger',
            'RESOLVED': 'success',
            'DISMISSED': 'secondary'
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = '상태'
    
    def current_vs_threshold(self, obj):
        if obj.current_value is not None and obj.threshold_value is not None:
            if obj.alert_type in ['LOW_STOCK', 'OUT_OF_STOCK']:
                if obj.current_value <= obj.threshold_value:
                    color = 'red'
                else:
                    color = 'green'
            else:  # OVERSTOCK
                if obj.current_value > obj.threshold_value:
                    color = 'red'
                else:
                    color = 'green'
            
            return format_html(
                '<span style="color: {};">{} / {}</span>',
                color, obj.current_value, obj.threshold_value
            )
        return '-'
    current_vs_threshold.short_description = '현재/기준'
    
    def created_at_formatted(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_formatted.short_description = '생성일시'
    
    def resolve_alerts(self, request, queryset):
        updated = queryset.filter(status='ACTIVE').update(
            status='RESOLVED',
            resolved_at=timezone.now(),
            resolved_by=request.user
        )
        messages.success(request, f'{updated}개의 알림이 해결되었습니다.')
    resolve_alerts.short_description = '선택한 알림 해결'
    
    def dismiss_alerts(self, request, queryset):
        updated = queryset.filter(status='ACTIVE').update(
            status='DISMISSED',
            resolved_at=timezone.now(),
            resolved_by=request.user
        )
        messages.success(request, f'{updated}개의 알림이 무시되었습니다.')
    dismiss_alerts.short_description = '선택한 알림 무시'
    
    def send_email_alerts(self, request, queryset):
        from .signals import send_stock_alert_email
        sent_count = 0
        
        for alert in queryset.filter(status='ACTIVE', is_email_sent=False):
            try:
                send_stock_alert_email(alert)
                sent_count += 1
            except Exception as e:
                messages.error(request, f'알림 {alert.id} 이메일 발송 실패: {str(e)}')
        
        if sent_count > 0:
            messages.success(request, f'{sent_count}개의 알림 이메일이 발송되었습니다.')
    send_email_alerts.short_description = '선택한 알림 이메일 발송'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'product', 'product__brand', 'resolved_by'
        )

@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = [
        'product_link', 'current_stock_display', 'min_max_levels',
        'reorder_info', 'stock_status_badge', 'auto_reorder_enabled',
        'updated_at_formatted'
    ]
    list_filter = [
        'auto_reorder_enabled', 'is_seasonal', 'warehouse',
        'updated_at'
    ]
    search_fields = [
        'product__name', 'product__sku', 'warehouse'
    ]
    readonly_fields = [
        'current_stock_display', 'stock_status_display', 
        'needs_reorder_display', 'days_of_stock_display',
        'created_at', 'updated_at'
    ]
    autocomplete_fields = ['product']
    actions = ['enable_auto_reorder', 'disable_auto_reorder', 'reset_to_product_levels']
    
    fieldsets = (
        ('상품 정보', {
            'fields': (
                'product', 'warehouse'
            )
        }),
        ('재고 수준', {
            'fields': (
                'min_stock_level', 'max_stock_level', 'safety_stock'
            )
        }),
        ('재주문 설정', {
            'fields': (
                'reorder_point', 'reorder_quantity', 'auto_reorder_enabled',
                'lead_time_days'
            )
        }),
        ('계절성 설정', {
            'fields': (
                'is_seasonal', 'seasonal_factor'
            ),
            'classes': ('collapse',)
        }),
        ('현재 상태', {
            'fields': (
                'current_stock_display', 'stock_status_display',
                'needs_reorder_display', 'days_of_stock_display'
            ),
            'classes': ('collapse',)
        }),
        ('시간 정보', {
            'fields': (
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def product_link(self, obj):
        if obj.product:
            url = reverse('admin:products_product_change', args=[obj.product.pk])
            return format_html('<a href="{}">{}</a>', url, obj.product.name)
        return '-'
    product_link.short_description = '상품'
    
    def current_stock_display(self, obj):
        current = obj.current_stock
        if current == 0:
            color = 'red'
        elif current <= obj.min_stock_level:
            color = 'orange'
        elif current > obj.max_stock_level:
            color = 'purple'
        else:
            color = 'green'
        
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, current)
    current_stock_display.short_description = '현재 재고'
    
    def min_max_levels(self, obj):
        return f'{obj.min_stock_level} ~ {obj.max_stock_level}'
    min_max_levels.short_description = '최소~최대'
    
    def reorder_info(self, obj):
        return f'{obj.reorder_point} / {obj.reorder_quantity}'
    reorder_info.short_description = '재주문 시점/수량'
    
    def stock_status_badge(self, obj):
        status = obj.stock_status
        colors = {
            'OUT_OF_STOCK': 'danger',
            'LOW_STOCK': 'warning',
            'NORMAL': 'success',
            'OVERSTOCK': 'info'
        }
        labels = {
            'OUT_OF_STOCK': '재고없음',
            'LOW_STOCK': '부족',
            'NORMAL': '정상',
            'OVERSTOCK': '과다'
        }
        
        color = colors.get(status, 'secondary')
        label = labels.get(status, status)
        
        return format_html('<span class="badge badge-{}">{}</span>', color, label)
    stock_status_badge.short_description = '재고 상태'
    
    def updated_at_formatted(self, obj):
        return obj.updated_at.strftime('%Y-%m-%d %H:%M')
    updated_at_formatted.short_description = '수정일시'
    
    def stock_status_display(self, obj):
        return obj.get_stock_status_display() if hasattr(obj, 'get_stock_status_display') else obj.stock_status
    stock_status_display.short_description = '재고 상태'
    
    def needs_reorder_display(self, obj):
        return '예' if obj.needs_reorder else '아니오'
    needs_reorder_display.short_description = '재주문 필요'
    
    def days_of_stock_display(self, obj):
        days = obj.days_of_stock
        if days == float('inf'):
            return '무제한'
        elif days == 0:
            return '소진됨'
        else:
            return f'{days:.0f}일'
    days_of_stock_display.short_description = '재고 소진 예상'
    
    def enable_auto_reorder(self, request, queryset):
        updated = queryset.update(auto_reorder_enabled=True)
        messages.success(request, f'{updated}개 상품의 자동 재주문이 활성화되었습니다.')
    enable_auto_reorder.short_description = '자동 재주문 활성화'
    
    def disable_auto_reorder(self, request, queryset):
        updated = queryset.update(auto_reorder_enabled=False)
        messages.success(request, f'{updated}개 상품의 자동 재주문이 비활성화되었습니다.')
    disable_auto_reorder.short_description = '자동 재주문 비활성화'
    
    def reset_to_product_levels(self, request, queryset):
        updated_count = 0
        for stock_level in queryset:
            product = stock_level.product
            if hasattr(product, 'min_stock_level') and hasattr(product, 'max_stock_level'):
                stock_level.min_stock_level = product.min_stock_level
                stock_level.max_stock_level = product.max_stock_level
                stock_level.reorder_point = product.min_stock_level
                stock_level.save()
                updated_count += 1
        
        messages.success(request, f'{updated_count}개 상품의 재고 수준이 상품 설정값으로 초기화되었습니다.')
    reset_to_product_levels.short_description = '상품 설정값으로 초기화'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'product__brand')

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_number', 'transaction_type_badge', 'status_badge',
        'progress_display', 'duration_display', 'created_by',
        'created_at_formatted'
    ]
    list_filter = [
        'transaction_type', 'status', 'created_at', 'created_by'
    ]
    search_fields = [
        'transaction_number', 'description'
    ]
    readonly_fields = [
        'transaction_number', 'progress_display', 'duration_display',
        'created_at', 'started_at', 'completed_at'
    ]
    autocomplete_fields = ['created_by']
    actions = ['cancel_transactions']
    
    fieldsets = (
        ('기본 정보', {
            'fields': (
                'transaction_number', 'transaction_type', 'status', 'description'
            )
        }),
        ('진행 상황', {
            'fields': (
                'total_items', 'processed_items', 'failed_items', 'progress_display'
            )
        }),
        ('시간 정보', {
            'fields': (
                'created_at', 'started_at', 'completed_at', 'duration_display'
            )
        }),
        ('사용자 정보', {
            'fields': (
                'created_by',
            )
        }),
        ('메타데이터', {
            'fields': (
                'metadata',
            ),
            'classes': ('collapse',)
        })
    )
    
    def transaction_type_badge(self, obj):
        colors = {
            'ADJUSTMENT': 'warning',
            'TRANSFER': 'info',
            'STOCKTAKE': 'primary',
            'BULK_UPDATE': 'secondary',
            'PLATFORM_SYNC': 'success'
        }
        color = colors.get(obj.transaction_type, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_transaction_type_display()
        )
    transaction_type_badge.short_description = '유형'
    
    def status_badge(self, obj):
        colors = {
            'PENDING': 'secondary',
            'PROCESSING': 'warning',
            'COMPLETED': 'success',
            'FAILED': 'danger',
            'CANCELLED': 'dark'
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = '상태'
    
    def progress_display(self, obj):
        percentage = obj.progress_percentage
        if percentage == 0:
            color = 'secondary'
        elif percentage < 50:
            color = 'warning'
        elif percentage < 100:
            color = 'info'
        else:
            color = 'success'
        
        return format_html(
            '<div class="progress" style="width: 100px; height: 20px;">'
            '<div class="progress-bar bg-{}" style="width: {}%">{:.1f}%</div>'
            '</div>',
            color, percentage, percentage
        )
    progress_display.short_description = '진행률'
    
    def duration_display(self, obj):
        duration = obj.duration
        if duration:
            total_seconds = int(duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if hours > 0:
                return f'{hours}h {minutes}m {seconds}s'
            elif minutes > 0:
                return f'{minutes}m {seconds}s'
            else:
                return f'{seconds}s'
        return '-'
    duration_display.short_description = '소요 시간'
    
    def created_at_formatted(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_formatted.short_description = '생성일시'
    
    def cancel_transactions(self, request, queryset):
        updated = queryset.filter(status__in=['PENDING', 'PROCESSING']).update(
            status='CANCELLED',
            completed_at=timezone.now()
        )
        messages.success(request, f'{updated}개의 트랜잭션이 취소되었습니다.')
    cancel_transactions.short_description = '선택한 트랜잭션 취소'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')

# 인라인 관리자 설정
class StockMovementInline(admin.TabularInline):
    model = StockMovement
    extra = 0
    readonly_fields = ['created_at', 'quantity_change']
    fields = [
        'movement_type', 'quantity', 'previous_stock', 'current_stock', 
        'reason', 'created_at'
    ]
    
    def has_add_permission(self, request, obj=None):
        return False  # 재고 이동은 시스템에서만 생성

class StockAlertInline(admin.TabularInline):
    model = StockAlert
    extra = 0
    readonly_fields = ['created_at', 'resolved_at']
    fields = ['alert_type', 'status', 'message', 'created_at']
    
    def has_add_permission(self, request, obj=None):
        return False  # 알림은 시스템에서만 생성

# 관련 모델에 인라인 추가하기 위한 설정
# (실제 Product 모델의 admin에서 사용할 수 있음)
def add_stock_inlines_to_product_admin():
    """Product 관리자에 재고 관련 인라인 추가"""
    try:
        from products.admin import ProductAdmin
        from products.models import Product
        
        # 기존 인라인에 추가
        if hasattr(ProductAdmin, 'inlines'):
            ProductAdmin.inlines = list(ProductAdmin.inlines) + [StockMovementInline, StockAlertInline]
        else:
            ProductAdmin.inlines = [StockMovementInline, StockAlertInline]
        
        # 관리자 재등록
        admin.site.unregister(Product)
        admin.site.register(Product, ProductAdmin)
        
    except Exception:
        # Product 모델이나 관리자가 없는 경우 무시
        pass

# 앱 준비시 호출
# add_stock_inlines_to_product_admin()