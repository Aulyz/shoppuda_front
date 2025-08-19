from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.conf import settings
import string
import random


class Coupon(models.Model):
    """쿠폰 정보"""
    
    DISCOUNT_TYPE_CHOICES = [
        ('FIXED', '정액 할인'),
        ('PERCENTAGE', '정률 할인'),
        ('FREE_SHIPPING', '무료 배송'),
    ]
    
    ISSUE_TYPE_CHOICES = [
        ('PUBLIC', '공개 쿠폰'),
        ('PRIVATE', '개인 쿠폰'),
        ('WELCOME', '회원가입 쿠폰'),
        ('BIRTHDAY', '생일 쿠폰'),
        ('COMEBACK', '휴면 복귀 쿠폰'),
        ('VIP', 'VIP 전용 쿠폰'),
        ('EVENT', '이벤트 쿠폰'),
    ]
    
    # 기본 정보
    code = models.CharField(
        '쿠폰 코드', 
        max_length=50, 
        unique=True, 
        db_index=True,
        help_text='쿠폰 코드 (자동 생성 가능)'
    )
    name = models.CharField('쿠폰명', max_length=200)
    description = models.TextField('설명', blank=True)
    
    # 할인 정보
    discount_type = models.CharField(
        '할인 타입', 
        max_length=20, 
        choices=DISCOUNT_TYPE_CHOICES,
        default='FIXED'
    )
    discount_value = models.DecimalField(
        '할인 값', 
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='정액 할인: 원 단위, 정률 할인: % 단위'
    )
    max_discount_amount = models.DecimalField(
        '최대 할인 금액', 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='정률 할인 시 최대 할인 금액 제한'
    )
    
    # 사용 조건
    min_order_amount = models.DecimalField(
        '최소 주문 금액', 
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    applicable_categories = models.ManyToManyField(
        'products.Category', 
        blank=True, 
        verbose_name='적용 카테고리',
        help_text='비어있으면 모든 카테고리 적용'
    )
    applicable_products = models.ManyToManyField(
        'products.Product', 
        blank=True, 
        verbose_name='적용 상품',
        help_text='비어있으면 모든 상품 적용'
    )
    exclude_sale_items = models.BooleanField('세일 상품 제외', default=False)
    
    # 발급 정보
    issue_type = models.CharField(
        '발급 타입', 
        max_length=20, 
        choices=ISSUE_TYPE_CHOICES,
        default='PUBLIC'
    )
    total_quantity = models.IntegerField(
        '총 발급 수량', 
        null=True, 
        blank=True,
        validators=[MinValueValidator(1)],
        help_text='비어있으면 무제한'
    )
    issued_quantity = models.IntegerField('발급된 수량', default=0)
    
    # 사용 제한
    usage_limit_total = models.IntegerField(
        '전체 사용 제한', 
        null=True, 
        blank=True,
        validators=[MinValueValidator(1)],
        help_text='비어있으면 무제한'
    )
    usage_limit_per_user = models.IntegerField(
        '사용자별 사용 제한', 
        default=1,
        validators=[MinValueValidator(1)]
    )
    used_count = models.IntegerField('사용된 횟수', default=0)
    
    # 유효 기간
    valid_from = models.DateTimeField('유효 시작일')
    valid_to = models.DateTimeField('유효 종료일')
    days_valid_after_issue = models.IntegerField(
        '발급 후 유효 일수', 
        null=True, 
        blank=True,
        validators=[MinValueValidator(1)],
        help_text='개인 쿠폰 발급 시 사용'
    )
    
    # 대상 설정
    target_membership_levels = models.JSONField(
        '대상 회원 등급', 
        default=list, 
        blank=True,
        help_text='["BRONZE", "SILVER", "GOLD", "PLATINUM", "DIAMOND"]'
    )
    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        blank=True, 
        verbose_name='대상 사용자',
        related_name='targeted_coupons'
    )
    
    # 상태
    is_active = models.BooleanField('활성 상태', default=True)
    is_stackable = models.BooleanField('다른 쿠폰과 중복 사용', default=False)
    
    # 메타 정보
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='created_coupons',
        verbose_name='생성자'
    )
    updated_at = models.DateTimeField('수정일', auto_now=True)
    
    class Meta:
        verbose_name = '쿠폰'
        verbose_name_plural = '쿠폰'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['valid_from', 'valid_to']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)
    
    def generate_code(self, length=10):
        """쿠폰 코드 자동 생성"""
        while True:
            code = ''.join(random.choices(
                string.ascii_uppercase + string.digits, 
                k=length
            ))
            if not Coupon.objects.filter(code=code).exists():
                return code
    
    @property
    def is_valid(self):
        """쿠폰 유효성 확인"""
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_to and
            (self.total_quantity is None or self.issued_quantity < self.total_quantity) and
            (self.usage_limit_total is None or self.used_count < self.usage_limit_total)
        )
    
    @property
    def remaining_quantity(self):
        """남은 발급 수량"""
        if self.total_quantity is None:
            return None
        return max(0, self.total_quantity - self.issued_quantity)
    
    @property
    def remaining_usage(self):
        """남은 사용 가능 횟수"""
        if self.usage_limit_total is None:
            return None
        return max(0, self.usage_limit_total - self.used_count)
    
    def can_issue_to_user(self, user):
        """특정 사용자에게 발급 가능한지 확인"""
        if not self.is_valid:
            return False, "유효하지 않은 쿠폰입니다."
        
        # 회원 등급 확인
        if self.target_membership_levels:
            if user.membership_level not in self.target_membership_levels:
                return False, "회원 등급이 맞지 않습니다."
        
        # 대상 사용자 확인
        if self.target_users.exists():
            if user not in self.target_users.all():
                return False, "대상 사용자가 아닙니다."
        
        # 이미 발급받았는지 확인
        existing = UserCoupon.objects.filter(
            user=user,
            coupon=self
        ).count()
        if existing >= self.usage_limit_per_user:
            return False, "이미 최대 발급 수량에 도달했습니다."
        
        return True, "발급 가능"
    
    def calculate_discount(self, order_amount, applicable_amount=None):
        """할인 금액 계산"""
        if applicable_amount is None:
            applicable_amount = order_amount
        
        if self.discount_type == 'FIXED':
            discount = min(self.discount_value, applicable_amount)
        elif self.discount_type == 'PERCENTAGE':
            discount = applicable_amount * (self.discount_value / 100)
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        elif self.discount_type == 'FREE_SHIPPING':
            discount = 0  # 배송비는 별도 처리
        else:
            discount = 0
        
        return min(discount, order_amount)


class UserCoupon(models.Model):
    """사용자별 쿠폰 발급 내역"""
    
    STATUS_CHOICES = [
        ('ISSUED', '발급됨'),
        ('USED', '사용됨'),
        ('EXPIRED', '만료됨'),
        ('CANCELLED', '취소됨'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='user_coupons',
        verbose_name='사용자'
    )
    coupon = models.ForeignKey(
        Coupon, 
        on_delete=models.CASCADE, 
        related_name='user_coupons',
        verbose_name='쿠폰'
    )
    
    status = models.CharField(
        '상태', 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='ISSUED'
    )
    
    issued_at = models.DateTimeField('발급일', auto_now_add=True)
    used_at = models.DateTimeField('사용일', null=True, blank=True)
    expires_at = models.DateTimeField('만료일')
    
    order = models.ForeignKey(
        'orders.Order', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='used_coupons',
        verbose_name='사용 주문'
    )
    
    discount_amount = models.DecimalField(
        '할인 금액',
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='실제 적용된 할인 금액'
    )
    
    class Meta:
        verbose_name = '사용자 쿠폰'
        verbose_name_plural = '사용자 쿠폰'
        ordering = ['-issued_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.coupon.name}"
    
    def save(self, *args, **kwargs):
        # 만료일 자동 설정
        if not self.expires_at:
            if self.coupon.days_valid_after_issue:
                from datetime import timedelta
                self.expires_at = timezone.now() + timedelta(days=self.coupon.days_valid_after_issue)
            else:
                self.expires_at = self.coupon.valid_to
        
        super().save(*args, **kwargs)
    
    @property
    def is_valid(self):
        """사용 가능 여부"""
        return (
            self.status == 'ISSUED' and
            timezone.now() <= self.expires_at and
            self.coupon.is_active
        )
    
    @property
    def is_expired(self):
        """만료 여부"""
        return timezone.now() > self.expires_at
    
    def use(self, order, discount_amount):
        """쿠폰 사용 처리"""
        if not self.is_valid:
            raise ValueError("사용할 수 없는 쿠폰입니다.")
        
        self.status = 'USED'
        self.used_at = timezone.now()
        self.order = order
        self.discount_amount = discount_amount
        self.save()
        
        # 쿠폰 사용 횟수 증가
        self.coupon.used_count += 1
        self.coupon.save()
    
    def cancel(self):
        """쿠폰 사용 취소"""
        if self.status != 'USED':
            raise ValueError("사용하지 않은 쿠폰은 취소할 수 없습니다.")
        
        self.status = 'CANCELLED'
        self.save()
        
        # 쿠폰 사용 횟수 감소
        self.coupon.used_count = max(0, self.coupon.used_count - 1)
        self.coupon.save()


class CouponLog(models.Model):
    """쿠폰 활동 로그"""
    
    ACTION_CHOICES = [
        ('CREATED', '생성'),
        ('ISSUED', '발급'),
        ('USED', '사용'),
        ('EXPIRED', '만료'),
        ('CANCELLED', '취소'),
        ('MODIFIED', '수정'),
    ]
    
    coupon = models.ForeignKey(
        Coupon, 
        on_delete=models.CASCADE, 
        related_name='logs',
        verbose_name='쿠폰'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='사용자'
    )
    action = models.CharField('액션', max_length=20, choices=ACTION_CHOICES)
    details = models.JSONField('상세 정보', default=dict)
    created_at = models.DateTimeField('발생일', auto_now_add=True)
    
    class Meta:
        verbose_name = '쿠폰 로그'
        verbose_name_plural = '쿠폰 로그'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.coupon.code} - {self.get_action_display()} - {self.created_at}"