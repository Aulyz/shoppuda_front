# File: platforms/models.py
from django.db import models

class Platform(models.Model):
    """외부 플랫폼 정보"""
    PLATFORM_TYPES = [
        ('SMARTSTORE', '스마트스토어'),
        ('COUPANG', '쿠팡'),
        ('GMARKET', 'G마켓'),
        ('AUCTION', '옥션'),
        ('11ST', '11번가'),
        ('TMON', '티몬'),
        ('WMP', '위메프'),
        ('SHOPIFY', 'Shopify'),
        ('AMAZON', 'Amazon'),
        ('OTHER', '기타'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='플랫폼명')
    platform_type = models.CharField(max_length=20, choices=PLATFORM_TYPES, verbose_name='플랫폼 유형')
    api_key = models.CharField(max_length=500, blank=True, null=True, verbose_name='API 키')
    api_secret = models.CharField(max_length=500, blank=True, null=True, verbose_name='API 시크릿')
    api_url = models.URLField(blank=True, null=True, verbose_name='API URL')
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    sync_enabled = models.BooleanField(default=False, verbose_name='동기화 활성화')
    sync_interval = models.IntegerField(default=60, verbose_name='동기화 간격(분)')
    last_sync_at = models.DateTimeField(blank=True, null=True, verbose_name='마지막 동기화 시간')
    last_sync_status = models.CharField(
        max_length=20, 
        choices=[
            ('success', '성공'),
            ('error', '오류'),
            ('running', '진행중'),
        ],
        blank=True, 
        null=True, 
        verbose_name='마지막 동기화 상태'
    )
    last_sync_message = models.TextField(blank=True, verbose_name='마지막 동기화 메시지')
    api_endpoint = models.URLField(blank=True, null=True, verbose_name='API 엔드포인트')
    description = models.TextField(blank=True, verbose_name='설명')

    class Meta:
        verbose_name = '플랫폼'
        verbose_name_plural = '플랫폼'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_platform_type_display()})"

class PlatformProduct(models.Model):
    """플랫폼별 상품 정보"""
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='platform_products', verbose_name='상품')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, verbose_name='플랫폼')
    platform_product_id = models.CharField(max_length=100, verbose_name='플랫폼 상품 ID')
    platform_sku = models.CharField(max_length=100, blank=True, verbose_name='플랫폼 SKU')
    
    # 플랫폼별 가격 (다를 수 있음)
    platform_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='플랫폼 판매가')
    platform_stock = models.IntegerField(default=0, verbose_name='플랫폼 재고')
    
    # 플랫폼별 상태
    is_active = models.BooleanField(default=True, verbose_name='플랫폼 활성 상태')
    last_sync_at = models.DateTimeField(blank=True, null=True, verbose_name='마지막 동기화')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    
    class Meta:
        verbose_name = '플랫폼 상품'
        verbose_name_plural = '플랫폼 상품'
        unique_together = ['platform', 'platform_product_id']
        indexes = [
            models.Index(fields=['platform', 'is_active']),
            models.Index(fields=['product', 'platform']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.platform.name}"

class Supplier(models.Model):
    """공급업체"""
    name = models.CharField(max_length=100, verbose_name='업체명')
    code = models.CharField(max_length=50, unique=True, verbose_name='업체 코드')
    contact_person = models.CharField(max_length=100, blank=True, verbose_name='담당자')
    email = models.EmailField(blank=True, verbose_name='이메일')
    phone = models.CharField(max_length=20, blank=True, verbose_name='전화번호')
    address = models.TextField(blank=True, verbose_name='주소')
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    
    class Meta:
        verbose_name = '공급업체'
        verbose_name_plural = '공급업체'
        ordering = ['name']
    
    def __str__(self):
        return self.name