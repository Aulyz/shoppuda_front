from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.cache import cache


class SystemSettings(models.Model):
    """시스템 전역 설정"""
    
    # 브랜드 설정
    site_name = models.CharField(
        max_length=100,
        default='Shopuda',
        verbose_name='사이트 이름'
    )
    site_tagline = models.CharField(
        max_length=200,
        default='ERP System',
        blank=True,
        verbose_name='사이트 태그라인'
    )
    site_logo_url = models.URLField(
        blank=True,
        verbose_name='로고 URL',
        help_text='로고 이미지 URL (비어있으면 기본 아이콘 사용)'
    )
    
    # 회원가입 설정
    signup_enabled = models.BooleanField(
        default=True,
        verbose_name='회원가입 허용'
    )
    welcome_points_enabled = models.BooleanField(
        default=True,
        verbose_name='회원가입 포인트 지급'
    )
    welcome_points_amount = models.PositiveIntegerField(
        default=1000,
        verbose_name='회원가입 포인트 금액'
    )
    email_verification_required = models.BooleanField(
        default=False,
        verbose_name='이메일 인증 필수'
    )
    
    # 회원 등급 설정 (금액 단위: 원)
    membership_bronze_threshold = models.PositiveIntegerField(
        default=0,
        verbose_name='브론즈 등급 기준 금액'
    )
    membership_silver_threshold = models.PositiveIntegerField(
        default=500000,
        verbose_name='실버 등급 기준 금액'
    )
    membership_gold_threshold = models.PositiveIntegerField(
        default=1000000,
        verbose_name='골드 등급 기준 금액'
    )
    membership_platinum_threshold = models.PositiveIntegerField(
        default=3000000,
        verbose_name='플래티넘 등급 기준 금액'
    )
    membership_diamond_threshold = models.PositiveIntegerField(
        default=5000000,
        verbose_name='다이아몬드 등급 기준 금액'
    )
    
    # 포인트 설정
    points_enabled = models.BooleanField(
        default=True,
        verbose_name='포인트 시스템 사용'
    )
    points_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='포인트 적립률 (%)',
        help_text='구매 금액의 몇 %를 포인트로 적립할지 설정'
    )
    points_expiry_days = models.PositiveIntegerField(
        default=365,
        verbose_name='포인트 유효기간 (일)',
        help_text='0으로 설정하면 무기한'
    )
    min_points_to_use = models.PositiveIntegerField(
        default=1000,
        verbose_name='포인트 최소 사용 금액'
    )
    
    # 주문 설정
    order_prefix = models.CharField(
        max_length=10,
        default='ORD',
        verbose_name='주문번호 접두사'
    )
    order_cancel_days = models.PositiveIntegerField(
        default=7,
        verbose_name='주문 취소 가능 기간 (일)',
        help_text='주문 후 며칠까지 취소 가능한지'
    )
    auto_confirm_days = models.PositiveIntegerField(
        default=7,
        verbose_name='자동 구매확정 기간 (일)',
        help_text='배송완료 후 며칠 후 자동 구매확정'
    )
    
    # 재고 설정
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        verbose_name='재고 부족 기준 수량'
    )
    stock_alert_enabled = models.BooleanField(
        default=True,
        verbose_name='재고 알림 사용'
    )
    negative_stock_allowed = models.BooleanField(
        default=False,
        verbose_name='마이너스 재고 허용'
    )
    
    # 상품 설정
    product_review_enabled = models.BooleanField(
        default=True,
        verbose_name='상품 리뷰 기능 사용'
    )
    review_points_enabled = models.BooleanField(
        default=True,
        verbose_name='리뷰 작성 포인트 지급'
    )
    review_points_amount = models.PositiveIntegerField(
        default=100,
        verbose_name='리뷰 포인트 금액'
    )
    photo_review_bonus_points = models.PositiveIntegerField(
        default=200,
        verbose_name='포토리뷰 추가 포인트'
    )
    
    # 알림 설정
    email_notifications_enabled = models.BooleanField(
        default=True,
        verbose_name='이메일 알림 사용'
    )
    sms_notifications_enabled = models.BooleanField(
        default=False,
        verbose_name='SMS 알림 사용'
    )
    order_notification_admin = models.BooleanField(
        default=True,
        verbose_name='주문 시 관리자 알림'
    )
    
    # 시스템 설정
    maintenance_mode = models.BooleanField(
        default=False,
        verbose_name='유지보수 모드',
        help_text='활성화하면 관리자만 접속 가능'
    )
    maintenance_message = models.TextField(
        blank=True,
        verbose_name='유지보수 메시지'
    )
    
    # 통화 설정
    currency_symbol = models.CharField(
        max_length=10,
        default='₩',
        verbose_name='통화 기호'
    )
    currency_code = models.CharField(
        max_length=3,
        default='KRW',
        verbose_name='통화 코드'
    )
    
    # 업무 시간 설정
    business_hours_start = models.TimeField(
        default='09:00',
        verbose_name='업무 시작 시간'
    )
    business_hours_end = models.TimeField(
        default='18:00',
        verbose_name='업무 종료 시간'
    )
    
    # 메타 정보
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='수정일'
    )
    updated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='수정자'
    )
    
    class Meta:
        verbose_name = '시스템 설정'
        verbose_name_plural = '시스템 설정'
    
    def save(self, *args, **kwargs):
        # 단일 인스턴스만 존재하도록 보장
        self.pk = 1
        super().save(*args, **kwargs)
        # 캐시 초기화
        cache.delete('system_settings')
    
    def delete(self, *args, **kwargs):
        # 삭제 방지
        pass
    
    @classmethod
    def get_settings(cls):
        """설정 가져오기 (캐시 사용)"""
        settings = cache.get('system_settings')
        if settings is None:
            settings, created = cls.objects.get_or_create(pk=1)
            cache.set('system_settings', settings, 3600)  # 1시간 캐시
        return settings


class EmailTemplate(models.Model):
    """이메일 템플릿"""
    
    TEMPLATE_TYPES = [
        ('welcome', '회원가입 환영'),
        ('order_confirm', '주문 확인'),
        ('order_shipped', '배송 시작'),
        ('order_delivered', '배송 완료'),
        ('password_reset', '비밀번호 재설정'),
        ('point_earned', '포인트 적립'),
        ('point_expired', '포인트 만료 예정'),
        ('low_stock', '재고 부족 알림'),
    ]
    
    template_type = models.CharField(
        max_length=50,
        choices=TEMPLATE_TYPES,
        unique=True,
        verbose_name='템플릿 타입'
    )
    subject = models.CharField(
        max_length=200,
        verbose_name='제목'
    )
    body = models.TextField(
        verbose_name='내용',
        help_text='사용 가능한 변수: {{user_name}}, {{site_name}}, {{order_number}} 등'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='활성화'
    )
    
    class Meta:
        verbose_name = '이메일 템플릿'
        verbose_name_plural = '이메일 템플릿'
    
    def __str__(self):
        return f"{self.get_template_type_display()} - {self.subject}"