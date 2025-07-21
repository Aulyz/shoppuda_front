from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils import timezone
from django import forms
from .models import User, ShippingAddress, PointHistory, UserPermission


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """커스텀 유저 관리자"""
    list_display = ['username', 'email', 'first_name', 'user_type', 'admin_level_display',
                    'membership_level', 'points', 'total_purchase_amount', 'is_active', 'created_at']
    list_filter = ['user_type', 'admin_level', 'membership_level', 'is_active', 'is_staff', 
                   'marketing_agreed', 'gender', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('추가 정보', {'fields': (
            'user_type', 'admin_level', 'phone_number', 'birth_date', 'gender',
            'postal_code', 'address', 'detail_address',
            'profile_image', 'memo'
        )}),
        ('쇼핑몰 정보', {'fields': (
            'total_purchase_amount', 'purchase_count', 'last_purchase_date',
            'points', 'membership_level'
        )}),
        ('동의 정보', {'fields': (
            'is_email_verified', 'is_phone_verified',
            'terms_agreed', 'privacy_agreed', 'marketing_agreed'
        )}),
        ('탈퇴 정보', {'fields': (
            'withdrawal_date', 'withdrawal_reason'
        )}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('추가 정보', {'fields': (
            'email', 'first_name', 'last_name', 'phone_number',
            'user_type', 'admin_level', 'terms_agreed', 'privacy_agreed'
        )}),
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related()
    
    @admin.display(description='총 구매액')
    def display_purchase_amount(self, obj):
        return f"₩{obj.total_purchase_amount:,.0f}"
    
    @admin.display(description='포인트')
    def display_points(self, obj):
        return f"{obj.points:,}P"
    
    actions = ['grant_points', 'upgrade_membership']
    
    def grant_points(self, request, queryset):
        """선택한 회원에게 포인트 지급"""
        for user in queryset:
            user.add_points(1000)
            PointHistory.objects.create(
                user=user,
                point_type='EARN',
                amount=1000,
                balance=user.points,
                description='관리자 지급'
            )
        self.message_user(request, f'{queryset.count()}명에게 1000 포인트를 지급했습니다.')
    grant_points.short_description = '1000 포인트 지급'
    
    def upgrade_membership(self, request, queryset):
        """선택한 회원의 등급 업그레이드"""
        upgraded = 0
        for user in queryset:
            old_level = user.membership_level
            user.update_membership_level()
            if old_level != user.membership_level:
                upgraded += 1
                user.save()
        self.message_user(request, f'{upgraded}명의 회원 등급이 업그레이드되었습니다.')
    upgrade_membership.short_description = '회원 등급 재산정'
    
    @admin.display(description='관리자 레벨')
    def admin_level_display(self, obj):
        if obj.user_type == 'ADMIN':
            level_colors = {
                0: '#6b7280',  # gray
                1: '#10b981',  # green
                2: '#3b82f6',  # blue
                3: '#8b5cf6',  # purple
                4: '#f59e0b',  # amber
                5: '#ef4444',  # red
            }
            color = level_colors.get(obj.admin_level, '#6b7280')
            return format_html(
                '<span style="color: {}; font-weight: bold;">레벨 {} - {}</span>',
                color,
                obj.admin_level,
                obj.get_admin_level_display()
            )
        return '-'


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    """배송지 관리자"""
    list_display = ['user', 'nickname', 'recipient_name', 'phone_number', 
                    'get_full_address', 'is_default', 'created_at']
    list_filter = ['is_default', 'created_at']
    search_fields = ['user__username', 'user__email', 'recipient_name', 
                     'phone_number', 'address']
    ordering = ['-created_at']
    
    def get_full_address(self, obj):
        return f"{obj.address} {obj.detail_address}"
    get_full_address.short_description = '주소'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(PointHistory)
class PointHistoryAdmin(admin.ModelAdmin):
    """포인트 내역 관리자"""
    list_display = ['user', 'point_type', 'display_amount', 'balance', 
                    'description', 'order_id', 'created_at']
    list_filter = ['point_type', 'created_at']
    search_fields = ['user__username', 'user__email', 'description', 'order_id']
    ordering = ['-created_at']
    readonly_fields = ['user', 'point_type', 'amount', 'balance', 'order_id', 'created_at']
    
    def display_amount(self, obj):
        if obj.point_type in ['EARN', 'CANCEL']:
            return format_html('<span style="color: green;">+{}</span>', obj.amount)
        else:
            return format_html('<span style="color: red;">-{}</span>', obj.amount)
    display_amount.short_description = '포인트'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def has_add_permission(self, request):
        # 포인트 내역은 시스템에서만 생성
        return False
    
    def has_delete_permission(self, request, obj=None):
        # 포인트 내역은 삭제 불가
        return False


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    """사용자 권한 관리자"""
    list_display = ['user', 'permission_display', 'granted_by', 'granted_at', 'expires_at', 'is_active', 'is_expired']
    list_filter = ['permission', 'is_active', 'granted_at', 'expires_at']
    search_fields = ['user__username', 'user__email', 'permission']
    readonly_fields = ['granted_by', 'granted_at']
    autocomplete_fields = ['user']
    
    fieldsets = (
        ('권한 정보', {
            'fields': ('user', 'permission', 'is_active')
        }),
        ('부여 정보', {
            'fields': ('granted_by', 'granted_at', 'expires_at')
        }),
    )
    
    def permission_display(self, obj):
        return obj.get_permission_display()
    permission_display.short_description = '권한'
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = '만료됨'
    
    def save_model(self, request, obj, form, change):
        if not change:  # 새로운 권한 생성시
            obj.granted_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'granted_by')
    
    actions = ['activate_permissions', 'deactivate_permissions', 'extend_permissions']
    
    def activate_permissions(self, request, queryset):
        """선택한 권한 활성화"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count}개의 권한이 활성화되었습니다.')
    activate_permissions.short_description = '선택한 권한 활성화'
    
    def deactivate_permissions(self, request, queryset):
        """선택한 권한 비활성화"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count}개의 권한이 비활성화되었습니다.')
    deactivate_permissions.short_description = '선택한 권한 비활성화'
    
    def extend_permissions(self, request, queryset):
        """선택한 권한 기한 연장 (30일)"""
        from datetime import timedelta
        for perm in queryset:
            if perm.expires_at:
                perm.expires_at += timedelta(days=30)
            else:
                perm.expires_at = timezone.now() + timedelta(days=30)
            perm.save()
        self.message_user(request, f'{queryset.count()}개의 권한이 30일 연장되었습니다.')
    extend_permissions.short_description = '선택한 권한 30일 연장'


