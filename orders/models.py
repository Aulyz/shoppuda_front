# File: orders/models.py
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Order(models.Model):
    """주문"""
    STATUS_CHOICES = [
        ('PENDING', '대기중'),
        ('CONFIRMED', '확인됨'),
        ('PROCESSING', '처리중'),
        ('SHIPPED', '배송중'),
        ('DELIVERED', '배송완료'),
        ('CANCELLED', '취소됨'),
        ('REFUNDED', '환불됨'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True, verbose_name='주문번호')
    platform = models.ForeignKey('platforms.Platform', on_delete=models.SET_NULL, null=True, verbose_name='플랫폼')
    platform_order_id = models.CharField(max_length=100, blank=True, verbose_name='플랫폼 주문 ID')
    
    # 고객 정보
    customer_name = models.CharField(max_length=100, verbose_name='고객명')
    customer_email = models.EmailField(blank=True, verbose_name='고객 이메일')
    customer_phone = models.CharField(max_length=20, blank=True, verbose_name='고객 전화번호')
    
    # 배송 정보
    shipping_address = models.TextField(verbose_name='배송 주소')
    shipping_zipcode = models.CharField(max_length=10, verbose_name='우편번호')
    shipping_method = models.CharField(max_length=100, blank=True, verbose_name='배송방법')
    tracking_number = models.CharField(max_length=100, blank=True, verbose_name='송장번호')
    
    # 주문 정보
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name='상태')
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='총 금액')
    shipping_fee = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name='배송비')
    discount_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name='할인 금액')
    
    # 일시
    order_date = models.DateTimeField(verbose_name='주문일시')
    shipped_date = models.DateTimeField(blank=True, null=True, verbose_name='배송일시')
    delivered_date = models.DateTimeField(blank=True, null=True, verbose_name='배송완료일시')
    cancelled_date = models.DateTimeField(blank=True, null=True, verbose_name='취소일시')
    refunded_date = models.DateTimeField(blank=True, null=True, verbose_name='환불일시')
    
    # 메모
    notes = models.TextField(blank=True, verbose_name='메모')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    
    class Meta:
        verbose_name = '주문'
        verbose_name_plural = '주문'
        ordering = ['-order_date']
        indexes = [
            models.Index(fields=['platform', 'status']),
            models.Index(fields=['order_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.order_number} - {self.customer_name}"

class OrderItem(models.Model):
    """주문 상품"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='주문')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, verbose_name='상품')
    quantity = models.IntegerField(validators=[MinValueValidator(1)], verbose_name='수량')
    unit_price = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='단가')
    total_price = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='총 금액')

    class Meta:
        verbose_name = '주문 상품'
        verbose_name_plural = '주문 상품'
    
    def __str__(self):
        return f"{self.order.order_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)