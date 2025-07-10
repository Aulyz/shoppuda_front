# inventory/models.py - 완성된 재고 관리 모델
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone

class StockMovement(models.Model):
    """재고 이동 이력"""
    MOVEMENT_TYPES = [
        ('IN', '입고'),
        ('OUT', '출고'),
        ('ADJUST', '조정'),
        ('TRANSFER', '이동'),
        ('RETURN', '반품'),
        ('DAMAGE', '손상'),
        ('SALE', '판매'),
        ('PURCHASE', '구매'),
        ('CANCEL', '취소'),
        ('CORRECTION', '수정'),
    ]
    
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.CASCADE, 
        related_name='stock_movements', 
        verbose_name='상품'
    )
    movement_type = models.CharField(
        max_length=20, 
        choices=MOVEMENT_TYPES, 
        verbose_name='이동 유형'
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='수량'
    )
    previous_stock = models.IntegerField(
        default=0,
        verbose_name='이전 재고'
    )
    current_stock = models.IntegerField(
        default=0,
        verbose_name='현재 재고'
    )
    reference_number = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name='참조 번호'
    )
    reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='사유'
    )
    notes = models.TextField(
        blank=True, 
        verbose_name='메모'
    )
    
    # 관련 주문이나 기타 참조
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='관련 주문'
    )
    
    # 플랫폼 정보 (플랫폼별 재고 동기화시 사용)
    platform = models.ForeignKey(
        'platforms.Platform',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='플랫폼'
    )
    
    # 창고 정보 (향후 멀티 창고 지원용)
    warehouse = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='창고'
    )
    
    # 비용 정보 (원가 기록)
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='단위 원가'
    )
    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='총 원가'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='생성일시'
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='생성자'
    )
    
    # 시스템 정보
    is_automated = models.BooleanField(
        default=False,
        verbose_name='자동 처리'
    )
    source_system = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='소스 시스템'
    )
    
    class Meta:
        verbose_name = '재고 이동'
        verbose_name_plural = '재고 이동'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', '-created_at']),
            models.Index(fields=['movement_type', '-created_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['reference_number']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return f"{self.product.sku} - {self.get_movement_type_display()} ({self.quantity}개)"
    
    def save(self, *args, **kwargs):
        # 총 원가 자동 계산
        if self.unit_cost and self.quantity:
            self.total_cost = self.unit_cost * self.quantity
        
        super().save(*args, **kwargs)
    
    @property
    def quantity_change(self):
        """재고 변화량 (+ 증가, - 감소)"""
        if self.movement_type in ['IN', 'PURCHASE', 'RETURN', 'CORRECTION']:
            return self.quantity
        elif self.movement_type in ['OUT', 'SALE', 'DAMAGE', 'TRANSFER']:
            return -self.quantity
        else:  # ADJUST
            return self.current_stock - self.previous_stock
    
    @property
    def is_increase(self):
        """재고 증가 여부"""
        return self.quantity_change > 0
    
    @property
    def is_decrease(self):
        """재고 감소 여부"""
        return self.quantity_change < 0

class StockAlert(models.Model):
    """재고 알림"""
    ALERT_TYPES = [
        ('LOW_STOCK', '재고 부족'),
        ('OUT_OF_STOCK', '재고 없음'),
        ('OVERSTOCK', '재고 과다'),
        ('EXPIRY_WARNING', '유통기한 임박'),
        ('SLOW_MOVING', '장기 재고'),
    ]
    
    ALERT_STATUS = [
        ('ACTIVE', '활성'),
        ('RESOLVED', '해결됨'),
        ('DISMISSED', '무시됨'),
    ]
    
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='stock_alerts',
        verbose_name='상품'
    )
    alert_type = models.CharField(
        max_length=20,
        choices=ALERT_TYPES,
        verbose_name='알림 유형'
    )
    status = models.CharField(
        max_length=20,
        choices=ALERT_STATUS,
        default='ACTIVE',
        verbose_name='상태'
    )
    message = models.TextField(verbose_name='알림 메시지')
    threshold_value = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='임계값'
    )
    current_value = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='현재값'
    )
    
    # 알림 설정
    is_email_sent = models.BooleanField(
        default=False,
        verbose_name='이메일 발송됨'
    )
    email_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='이메일 발송일시'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='생성일시'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='수정일시'
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='해결일시'
    )
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts',
        verbose_name='해결자'
    )
    
    class Meta:
        verbose_name = '재고 알림'
        verbose_name_plural = '재고 알림'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'status']),
            models.Index(fields=['alert_type', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]
        unique_together = ['product', 'alert_type', 'status']
    
    def __str__(self):
        return f"{self.product.sku} - {self.get_alert_type_display()}"
    
    def resolve(self, user=None):
        """알림 해결 처리"""
        self.status = 'RESOLVED'
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save(update_fields=['status', 'resolved_at', 'resolved_by', 'updated_at'])
    
    def dismiss(self, user=None):
        """알림 무시 처리"""
        self.status = 'DISMISSED'
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save(update_fields=['status', 'resolved_at', 'resolved_by', 'updated_at'])

class StockLevel(models.Model):
    """상품별 재고 수준 설정"""
    product = models.OneToOneField(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='stock_level',
        verbose_name='상품'
    )
    
    # 재고 수준
    min_stock_level = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='최소 재고'
    )
    max_stock_level = models.IntegerField(
        default=1000,
        validators=[MinValueValidator(1)],
        verbose_name='최대 재고'
    )
    reorder_point = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='재주문 시점'
    )
    reorder_quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='재주문 수량'
    )
    
    # 안전 재고
    safety_stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='안전 재고'
    )
    
    # 창고별 설정 (향후 확장용)
    warehouse = models.CharField(
        max_length=100,
        blank=True,
        default='DEFAULT',
        verbose_name='창고'
    )
    
    # 자동 주문 설정
    auto_reorder_enabled = models.BooleanField(
        default=False,
        verbose_name='자동 재주문 활성화'
    )
    
    # 리드타임 (일 단위)
    lead_time_days = models.IntegerField(
        default=7,
        validators=[MinValueValidator(0)],
        verbose_name='리드타임(일)'
    )
    
    # 계절성 고려
    is_seasonal = models.BooleanField(
        default=False,
        verbose_name='계절성 상품'
    )
    seasonal_factor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
        verbose_name='계절성 계수'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    
    class Meta:
        verbose_name = '재고 수준'
        verbose_name_plural = '재고 수준'
        unique_together = ['product', 'warehouse']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['warehouse']),
            models.Index(fields=['auto_reorder_enabled']),
        ]
    
    def __str__(self):
        return f"{self.product.sku} - 재고수준"
    
    def clean(self):
        """유효성 검사"""
        from django.core.exceptions import ValidationError
        
        if self.min_stock_level >= self.max_stock_level:
            raise ValidationError('최소 재고는 최대 재고보다 작아야 합니다.')
        
        if self.reorder_point > self.max_stock_level:
            raise ValidationError('재주문 시점은 최대 재고보다 작거나 같아야 합니다.')
        
        if self.safety_stock > self.min_stock_level:
            raise ValidationError('안전 재고는 최소 재고보다 작거나 같아야 합니다.')
    
    @property
    def current_stock(self):
        """현재 재고 수량"""
        return self.product.stock_quantity
    
    @property
    def stock_status(self):
        """재고 상태"""
        current = self.current_stock
        
        if current == 0:
            return 'OUT_OF_STOCK'
        elif current <= self.min_stock_level:
            return 'LOW_STOCK'
        elif current >= self.max_stock_level:
            return 'OVERSTOCK'
        else:
            return 'NORMAL'
    
    @property
    def needs_reorder(self):
        """재주문 필요 여부"""
        return self.current_stock <= self.reorder_point
    
    @property
    def days_of_stock(self):
        """재고 소진 예상 일수 (간단 계산)"""
        # 실제로는 판매 이력을 기반으로 더 정확한 계산 필요
        if self.current_stock <= 0:
            return 0
        
        # 기본적으로 30일간 평균 판매량 기준 (실제 구현시 수정 필요)
        avg_daily_sales = 1  # 임시값
        return self.current_stock / avg_daily_sales if avg_daily_sales > 0 else float('inf')

class InventoryTransaction(models.Model):
    """재고 트랜잭션 (복수 상품 동시 처리용)"""
    TRANSACTION_TYPES = [
        ('ADJUSTMENT', '재고 조정'),
        ('TRANSFER', '창고 이동'),
        ('STOCKTAKE', '재고 실사'),
        ('BULK_UPDATE', '일괄 업데이트'),
        ('PLATFORM_SYNC', '플랫폼 동기화'),
    ]
    
    TRANSACTION_STATUS = [
        ('PENDING', '대기중'),
        ('PROCESSING', '처리중'),
        ('COMPLETED', '완료'),
        ('FAILED', '실패'),
        ('CANCELLED', '취소'),
    ]
    
    transaction_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='트랜잭션 번호'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        verbose_name='트랜잭션 유형'
    )
    status = models.CharField(
        max_length=20,
        choices=TRANSACTION_STATUS,
        default='PENDING',
        verbose_name='상태'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='설명'
    )
    
    # 처리 정보
    total_items = models.IntegerField(
        default=0,
        verbose_name='총 항목 수'
    )
    processed_items = models.IntegerField(
        default=0,
        verbose_name='처리된 항목 수'
    )
    failed_items = models.IntegerField(
        default=0,
        verbose_name='실패한 항목 수'
    )
    
    # 시간 정보
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='시작일시')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='완료일시')
    
    # 사용자 정보
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='생성자'
    )
    
    # 메타데이터
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='메타데이터'
    )
    
    class Meta:
        verbose_name = '재고 트랜잭션'
        verbose_name_plural = '재고 트랜잭션'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"{self.transaction_number} - {self.get_transaction_type_display()}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_number:
            self.transaction_number = self.generate_transaction_number()
        super().save(*args, **kwargs)
    
    def generate_transaction_number(self):
        """트랜잭션 번호 생성"""
        from django.utils import timezone
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        type_code = {
            'ADJUSTMENT': 'ADJ',
            'TRANSFER': 'TRF',
            'STOCKTAKE': 'STK',
            'BULK_UPDATE': 'BLK',
            'PLATFORM_SYNC': 'SYN',
        }.get(self.transaction_type, 'TXN')
        
        return f"{type_code}-{timestamp}"
    
    def start_processing(self):
        """처리 시작"""
        self.status = 'PROCESSING'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def complete(self):
        """처리 완료"""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
    
    def fail(self, error_message=None):
        """처리 실패"""
        self.status = 'FAILED'
        self.completed_at = timezone.now()
        if error_message:
            self.metadata['error_message'] = error_message
        self.save(update_fields=['status', 'completed_at', 'metadata'])
    
    @property
    def progress_percentage(self):
        """진행률 (%))"""
        if self.total_items == 0:
            return 0
        return round((self.processed_items / self.total_items) * 100, 1)
    
    @property
    def duration(self):
        """처리 시간"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return timezone.now() - self.started_at
        return None