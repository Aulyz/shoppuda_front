# File: products/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Brand, Product, ProductImage
from django.db.models import Count, Q

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'sort_order']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'brand', 'category', 'selling_price', 'stock_quantity', 'status', 'stock_status']
    list_filter = ['status', 'brand', 'category', 'is_featured']
    search_fields = ['sku', 'name', 'barcode']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProductImageInline]
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('sku', 'name', 'brand', 'category', 'description', 'short_description')
        }),
        ('가격 정보', {
            'fields': ('cost_price', 'selling_price', 'discount_price')
        }),
        ('재고 정보', {
            'fields': ('stock_quantity', 'min_stock_level', 'max_stock_level')
        }),
        ('상품 정보', {
            'fields': ('weight', 'dimensions_length', 'dimensions_width', 'dimensions_height')
        }),
        ('상태', {
            'fields': ('status', 'is_featured')
        }),
        ('메타 정보', {
            'fields': ('tags', 'barcode', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def stock_status(self, obj):
        if obj.is_low_stock:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ 재고 부족</span>'
            )
        return format_html(
            '<span style="color: green;">✅ 정상</span>'
        )
    stock_status.short_description = '재고 상태'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'parent', 'product_count_display', 
        'icon_display', 'is_active', 'sort_order', 'created_at'
    ]
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'code', 'description']
    list_editable = ['is_active', 'sort_order']
    readonly_fields = ['code', 'created_at', 'updated_at', 'product_count_display', 'full_path']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'code', 'description', 'icon')
        }),
        ('분류', {
            'fields': ('parent', 'sort_order', 'full_path')
        }),
        ('상태', {
            'fields': ('is_active',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at', 'product_count_display'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            active_product_count=Count('products', filter=Q(products__status='ACTIVE'))
        ).select_related('parent')
    
    def product_count_display(self, obj):
        """상품 수 표시"""
        try:
            # annotate된 값이 있으면 사용
            if hasattr(obj, 'active_product_count'):
                count = obj.active_product_count
            else:
                # 없으면 실시간 계산
                count = obj.get_product_count()
                
            if count > 0:
                # 관리자에서 해당 카테고리의 상품 목록으로 링크
                url = f"/admin/products/product/?category__id__exact={obj.id}"
                return format_html('<a href="{}" style="color: #007cba;">{} 개</a>', url, count)
            return '0 개'
        except:
            return '0 개'
    product_count_display.short_description = '상품 수'
    product_count_display.admin_order_field = 'active_product_count'
    
    def icon_display(self, obj):
        """아이콘 표시"""
        if obj.icon:
            return format_html('<i class="{}" style="font-size: 16px;"></i>', obj.icon)
        return '-'
    icon_display.short_description = '아이콘'
    
    def full_path(self, obj):
        """전체 경로 표시"""
        return obj.full_path
    full_path.short_description = '전체 경로'
    
    def get_form(self, request, obj=None, **kwargs):
        """폼 커스터마이징"""
        form = super().get_form(request, obj, **kwargs)
        
        # 자기 자신과 하위 카테고리를 부모 선택에서 제외
        if obj:
            descendants = [obj.pk] + [cat.pk for cat in obj.get_descendants()]
            form.base_fields['parent'].queryset = Category.objects.exclude(pk__in=descendants)
        
        return form
    
    def save_model(self, request, obj, form, change):
        """모델 저장 시 추가 처리"""
        super().save_model(request, obj, form, change)
        
        # 필요시 추가 처리 (예: 캐시 무효화, 로그 기록 등)
        if change:
            # 수정 시 로그
            pass
        else:
            # 생성 시 로그
            pass
    
    actions = ['make_active', 'make_inactive', 'reset_sort_order']
    
    def make_active(self, request, queryset):
        """선택된 카테고리들을 활성화"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated}개 카테고리가 활성화되었습니다.')
    make_active.short_description = '선택된 카테고리 활성화'
    
    def make_inactive(self, request, queryset):
        """선택된 카테고리들을 비활성화"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated}개 카테고리가 비활성화되었습니다.')
    make_inactive.short_description = '선택된 카테고리 비활성화'
    
    def reset_sort_order(self, request, queryset):
        """정렬 순서 초기화"""
        for i, category in enumerate(queryset.order_by('name')):
            category.sort_order = i * 10
            category.save()
        self.message_user(request, f'{queryset.count()}개 카테고리의 정렬 순서가 초기화되었습니다.')
    reset_sort_order.short_description = '정렬 순서 초기화'

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']