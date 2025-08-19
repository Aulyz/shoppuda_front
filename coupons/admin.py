from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Coupon, UserCoupon, CouponLog


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """쿠폰 관리"""
    list_display = [
        'code', 'name', 'discount_type', 'discount_value_display',
        'issue_type', 'status_display', 'usage_info', 'valid_period'
    ]
    list_filter = [
        'is_active', 'discount_type', 'issue_type',
        'valid_from', 'valid_to', 'created_at'
    ]
    search_fields = ['code', 'name', 'description']
    readonly_fields = [
        'issued_quantity', 'used_count', 'created_at', 
        'updated_at', 'created_by'
    ]
    filter_horizontal = [
        'applicable_categories', 'applicable_products', 'target_users'
    ]
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('code', 'name', 'description', 'issue_type')
        }),
        ('할인 설정', {
            'fields': (
                'discount_type', 'discount_value', 'max_discount_amount',
                'min_order_amount', 'exclude_sale_items'
            )
        }),
        ('적용 대상', {
            'fields': (
                'applicable_categories', 'applicable_products',
                'target_membership_levels', 'target_users'
            )
        }),
        ('발급/사용 제한', {
            'fields': (
                'total_quantity', 'issued_quantity',
                'usage_limit_total', 'usage_limit_per_user', 'used_count'
            )
        }),
        ('유효 기간', {
            'fields': (
                'valid_from', 'valid_to', 'days_valid_after_issue'
            )
        }),
        ('기타 설정', {
            'fields': ('is_active', 'is_stackable')
        }),
        ('메타 정보', {
            'fields': ('created_at', 'created_by', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_coupons', 'deactivate_coupons', 'duplicate_coupon']
    
    def discount_value_display(self, obj):
        """할인 값 표시"""
        if obj.discount_type == 'PERCENTAGE':
            return f"{obj.discount_value}%"
        elif obj.discount_type == 'FIXED':
            return f"₩{obj.discount_value:,.0f}"
        else:
            return "무료배송"
    discount_value_display.short_description = '할인 값'
    
    def status_display(self, obj):
        """상태 표시"""
        if not obj.is_active:
            return format_html('<span style="color: gray;">비활성</span>')
        elif obj.is_valid:
            return format_html('<span style="color: green;">✓ 활성</span>')
        else:
            return format_html('<span style="color: red;">✗ 만료</span>')
    status_display.short_description = '상태'
    
    def usage_info(self, obj):
        """사용 정보"""
        issued = f"{obj.issued_quantity}"
        if obj.total_quantity:
            issued += f"/{obj.total_quantity}"
        
        used = f"{obj.used_count}"
        if obj.usage_limit_total:
            used += f"/{obj.usage_limit_total}"
        
        return f"발급: {issued}, 사용: {used}"
    usage_info.short_description = '발급/사용'
    
    def valid_period(self, obj):
        """유효 기간"""
        return f"{obj.valid_from.strftime('%Y-%m-%d')} ~ {obj.valid_to.strftime('%Y-%m-%d')}"
    valid_period.short_description = '유효 기간'
    
    def activate_coupons(self, request, queryset):
        """쿠폰 활성화"""
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count}개의 쿠폰이 활성화되었습니다.")
    activate_coupons.short_description = "선택한 쿠폰 활성화"
    
    def deactivate_coupons(self, request, queryset):
        """쿠폰 비활성화"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count}개의 쿠폰이 비활성화되었습니다.")
    deactivate_coupons.short_description = "선택한 쿠폰 비활성화"
    
    def duplicate_coupon(self, request, queryset):
        """쿠폰 복제"""
        for coupon in queryset:
            new_coupon = coupon
            new_coupon.pk = None
            new_coupon.code = None  # 새로운 코드 자동 생성
            new_coupon.issued_quantity = 0
            new_coupon.used_count = 0
            new_coupon.save()
            
            # M2M 관계 복사
            new_coupon.applicable_categories.set(coupon.applicable_categories.all())
            new_coupon.applicable_products.set(coupon.applicable_products.all())
            new_coupon.target_users.set(coupon.target_users.all())
        
        self.message_user(request, f"{queryset.count()}개의 쿠폰이 복제되었습니다.")
    duplicate_coupon.short_description = "선택한 쿠폰 복제"
    
    def save_model(self, request, obj, form, change):
        if not change:  # 새로 생성하는 경우
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(UserCoupon)
class UserCouponAdmin(admin.ModelAdmin):
    """사용자 쿠폰 관리"""
    list_display = [
        'user', 'coupon', 'status', 'issued_at', 
        'expires_at', 'used_at', 'discount_amount'
    ]
    list_filter = ['status', 'issued_at', 'expires_at', 'used_at']
    search_fields = [
        'user__username', 'user__email', 
        'coupon__code', 'coupon__name'
    ]
    readonly_fields = ['issued_at', 'used_at', 'discount_amount']
    raw_id_fields = ['user', 'coupon', 'order']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'coupon', 'order')
    
    actions = ['mark_as_expired']
    
    def mark_as_expired(self, request, queryset):
        """만료 처리"""
        count = queryset.filter(status='ISSUED').update(
            status='EXPIRED',
            expires_at=timezone.now()
        )
        self.message_user(request, f"{count}개의 쿠폰이 만료 처리되었습니다.")
    mark_as_expired.short_description = "선택한 쿠폰 만료 처리"


@admin.register(CouponLog)
class CouponLogAdmin(admin.ModelAdmin):
    """쿠폰 로그 관리"""
    list_display = ['coupon', 'user', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['coupon__code', 'coupon__name', 'user__username']
    readonly_fields = ['coupon', 'user', 'action', 'details', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('coupon', 'user')