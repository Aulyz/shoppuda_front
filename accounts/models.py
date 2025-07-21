from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """쇼핑몰 사용자 커스텀 모델"""
    
    # 사용자 타입
    USER_TYPE_CHOICES = [
        ('CUSTOMER', '고객'),
        ('STAFF', '직원'),
        ('ADMIN', '관리자'),
    ]
    
    # 관리자 권한 레벨
    ADMIN_LEVEL_CHOICES = [
        (0, '권한 없음'),
        (1, '읽기 전용'),
        (2, '일반 관리자'),
        (3, '중간 관리자'),
        (4, '상위 관리자'),
        (5, '최고 관리자'),
    ]
    
    # 성별
    GENDER_CHOICES = [
        ('M', '남성'),
        ('F', '여성'),
        ('O', '기타'),
    ]
    
    # 기본 정보
    user_type = models.CharField(
        max_length=10, 
        choices=USER_TYPE_CHOICES, 
        default='CUSTOMER',
        verbose_name='사용자 타입'
    )
    
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name='전화번호'
    )
    
    birth_date = models.DateField(
        blank=True, 
        null=True,
        verbose_name='생년월일'
    )
    
    gender = models.CharField(
        max_length=1, 
        choices=GENDER_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='성별'
    )
    
    # 주소 정보
    postal_code = models.CharField(
        max_length=10, 
        blank=True, 
        null=True,
        verbose_name='우편번호'
    )
    
    address = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='주소'
    )
    
    detail_address = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='상세주소'
    )
    
    # 마케팅 및 약관 동의
    is_email_verified = models.BooleanField(
        default=False,
        verbose_name='이메일 인증 여부'
    )
    
    is_phone_verified = models.BooleanField(
        default=False,
        verbose_name='전화번호 인증 여부'
    )
    
    marketing_agreed = models.BooleanField(
        default=False,
        verbose_name='마케팅 수신 동의'
    )
    
    terms_agreed = models.BooleanField(
        default=False,
        verbose_name='이용약관 동의'
    )
    
    privacy_agreed = models.BooleanField(
        default=False,
        verbose_name='개인정보처리방침 동의'
    )
    
    # 추가 정보
    profile_image = models.ImageField(
        upload_to='profiles/', 
        blank=True, 
        null=True,
        verbose_name='프로필 이미지'
    )
    
    memo = models.TextField(
        blank=True, 
        null=True,
        verbose_name='메모'
    )
    
    # 쇼핑몰 관련 정보
    total_purchase_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        verbose_name='총 구매 금액'
    )
    
    purchase_count = models.PositiveIntegerField(
        default=0,
        verbose_name='구매 횟수'
    )
    
    last_purchase_date = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name='마지막 구매일'
    )
    
    # 포인트/적립금
    points = models.PositiveIntegerField(
        default=0,
        verbose_name='포인트'
    )
    
    # 회원 등급
    MEMBERSHIP_CHOICES = [
        ('BRONZE', '브론즈'),
        ('SILVER', '실버'),
        ('GOLD', '골드'),
        ('PLATINUM', '플래티넘'),
        ('DIAMOND', '다이아몬드'),
    ]
    
    membership_level = models.CharField(
        max_length=10, 
        choices=MEMBERSHIP_CHOICES, 
        default='BRONZE',
        verbose_name='회원 등급'
    )
    
    # 관리자 권한 레벨 (관리자만 해당)
    admin_level = models.IntegerField(
        choices=ADMIN_LEVEL_CHOICES,
        default=0,
        verbose_name='관리자 권한 레벨',
        help_text='관리자 타입 사용자에게만 적용됩니다.'
    )
    
    # 메타 정보
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='가입일'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='수정일'
    )
    
    withdrawal_date = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name='탈퇴일'
    )
    
    withdrawal_reason = models.TextField(
        blank=True, 
        null=True,
        verbose_name='탈퇴 사유'
    )
    
    class Meta:
        db_table = 'users'
        verbose_name = '사용자'
        verbose_name_plural = '사용자'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.get_full_name() or self.email})"
    
    def get_full_address(self):
        """전체 주소 반환"""
        if self.address:
            return f"{self.address} {self.detail_address or ''}".strip()
        return ""
    
    def update_purchase_info(self, amount):
        """구매 정보 업데이트"""
        from django.utils import timezone
        self.total_purchase_amount += amount
        self.purchase_count += 1
        self.last_purchase_date = timezone.now()
        self.update_membership_level()
        self.save()
    
    def update_membership_level(self):
        """구매 금액에 따른 회원 등급 자동 업데이트"""
        amount = self.total_purchase_amount
        if amount >= 5000000:  # 500만원 이상
            self.membership_level = 'DIAMOND'
        elif amount >= 3000000:  # 300만원 이상
            self.membership_level = 'PLATINUM'
        elif amount >= 1000000:  # 100만원 이상
            self.membership_level = 'GOLD'
        elif amount >= 500000:  # 50만원 이상
            self.membership_level = 'SILVER'
        else:
            self.membership_level = 'BRONZE'
    
    def add_points(self, points):
        """포인트 추가"""
        self.points += points
        self.save()
    
    def use_points(self, points):
        """포인트 사용"""
        if self.points >= points:
            self.points -= points
            self.save()
            return True
        return False
    
    def has_permission(self, permission_code):
        """특정 권한 보유 여부 확인"""
        # 최고 관리자는 모든 권한 보유
        if self.user_type == 'ADMIN' and self.admin_level == 5:
            return True
        
        # 권한 레벨에 따른 기본 권한 체크
        if self.user_type == 'ADMIN':
            # 읽기 권한은 레벨 1 이상
            if permission_code.endswith('_view') and self.admin_level >= 1:
                return True
            
            # 생성/수정 권한은 레벨 2 이상
            if permission_code in ['product_create', 'product_edit', 'order_edit'] and self.admin_level >= 2:
                return True
            
            # 삭제/취소 권한은 레벨 3 이상
            if permission_code in ['product_delete', 'order_cancel', 'user_edit'] and self.admin_level >= 3:
                return True
            
            # 시스템/재무 권한은 레벨 4 이상
            if permission_code.startswith(('system_', 'financial_')) and self.admin_level >= 4:
                return True
        
        # 개별 권한 체크
        from django.utils import timezone
        permission = self.permissions.filter(
            permission=permission_code,
            is_active=True
        ).first()
        
        if permission and not permission.is_expired:
            return True
        
        return False
    
    def get_permissions(self):
        """사용자가 가진 모든 유효한 권한 목록 반환"""
        permissions = set()
        
        # 관리자 레벨에 따른 기본 권한
        if self.user_type == 'ADMIN':
            if self.admin_level >= 5:
                # 최고 관리자는 모든 권한
                from .models import UserPermission
                return [perm[0] for perm in UserPermission.PERMISSION_CHOICES]
            
            if self.admin_level >= 1:
                # 조회 권한
                from .models import UserPermission
                permissions.update([p[0] for p in UserPermission.PERMISSION_CHOICES if p[0].endswith('_view')])
            
            if self.admin_level >= 2:
                # 일반 관리 권한
                permissions.update(['product_create', 'product_edit', 'order_edit', 'inventory_edit'])
            
            if self.admin_level >= 3:
                # 중간 관리 권한
                permissions.update(['product_delete', 'order_cancel', 'user_edit', 'report_create', 'report_export'])
            
            if self.admin_level >= 4:
                # 상위 관리 권한
                from .models import UserPermission
                permissions.update([p[0] for p in UserPermission.PERMISSION_CHOICES if p[0].startswith(('system_', 'financial_', 'platform_'))])
        
        # 개별 부여된 권한
        from django.utils import timezone
        individual_perms = self.permissions.filter(
            is_active=True
        ).exclude(
            expires_at__lt=timezone.now()
        ).values_list('permission', flat=True)
        
        permissions.update(individual_perms)
        
        return list(permissions)


class ShippingAddress(models.Model):
    """배송지 정보"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='shipping_addresses',
        verbose_name='사용자'
    )
    
    nickname = models.CharField(
        max_length=50,
        verbose_name='배송지 별칭'
    )
    
    recipient_name = models.CharField(
        max_length=50,
        verbose_name='수령인 이름'
    )
    
    phone_number = models.CharField(
        max_length=20,
        verbose_name='전화번호'
    )
    
    postal_code = models.CharField(
        max_length=10,
        verbose_name='우편번호'
    )
    
    address = models.CharField(
        max_length=200,
        verbose_name='주소'
    )
    
    detail_address = models.CharField(
        max_length=200,
        verbose_name='상세주소'
    )
    
    is_default = models.BooleanField(
        default=False,
        verbose_name='기본 배송지'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='생성일'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='수정일'
    )
    
    class Meta:
        db_table = 'shipping_addresses'
        verbose_name = '배송지'
        verbose_name_plural = '배송지'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.nickname}"
    
    def save(self, *args, **kwargs):
        # 기본 배송지로 설정 시 다른 배송지의 기본 설정 해제
        if self.is_default:
            ShippingAddress.objects.filter(
                user=self.user, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class PointHistory(models.Model):
    """포인트 사용 내역"""
    POINT_TYPE_CHOICES = [
        ('EARN', '적립'),
        ('USE', '사용'),
        ('EXPIRE', '소멸'),
        ('CANCEL', '취소'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='point_histories',
        verbose_name='사용자'
    )
    
    point_type = models.CharField(
        max_length=10, 
        choices=POINT_TYPE_CHOICES,
        verbose_name='포인트 타입'
    )
    
    amount = models.IntegerField(
        verbose_name='포인트 금액'
    )
    
    balance = models.IntegerField(
        verbose_name='잔액'
    )
    
    description = models.CharField(
        max_length=200,
        verbose_name='설명'
    )
    
    order_id = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        verbose_name='주문 번호'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='생성일'
    )
    
    expire_date = models.DateField(
        blank=True, 
        null=True,
        verbose_name='만료일'
    )
    
    class Meta:
        db_table = 'point_histories'
        verbose_name = '포인트 내역'
        verbose_name_plural = '포인트 내역'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_point_type_display()} {self.amount}P"


class UserPermission(models.Model):
    """사용자별 세부 권한 관리"""
    
    PERMISSION_CHOICES = [
        # 사용자 관리
        ('user_view', '사용자 조회'),
        ('user_create', '사용자 생성'),
        ('user_edit', '사용자 수정'),
        ('user_delete', '사용자 삭제'),
        ('user_permission', '사용자 권한 관리'),
        
        # 상품 관리
        ('product_view', '상품 조회'),
        ('product_create', '상품 생성'),
        ('product_edit', '상품 수정'),
        ('product_delete', '상품 삭제'),
        ('product_price', '상품 가격 관리'),
        
        # 주문 관리
        ('order_view', '주문 조회'),
        ('order_edit', '주문 수정'),
        ('order_cancel', '주문 취소'),
        ('order_refund', '환불 처리'),
        
        # 재고 관리
        ('inventory_view', '재고 조회'),
        ('inventory_edit', '재고 수정'),
        ('inventory_move', '재고 이동'),
        
        # 보고서
        ('report_view', '보고서 조회'),
        ('report_create', '보고서 생성'),
        ('report_export', '보고서 내보내기'),
        ('report_schedule', '보고서 스케줄 관리'),
        
        # 플랫폼 관리
        ('platform_view', '플랫폼 조회'),
        ('platform_manage', '플랫폼 관리'),
        ('platform_sync', '플랫폼 동기화'),
        
        # 시스템 설정
        ('system_view', '시스템 설정 조회'),
        ('system_config', '시스템 설정 변경'),
        ('system_backup', '시스템 백업'),
        
        # 재무 관리
        ('financial_view', '재무 조회'),
        ('financial_manage', '재무 관리'),
        ('financial_export', '재무 데이터 내보내기'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='permissions',
        verbose_name='사용자'
    )
    
    permission = models.CharField(
        max_length=50,
        choices=PERMISSION_CHOICES,
        verbose_name='권한'
    )
    
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='granted_permissions',
        verbose_name='권한 부여자'
    )
    
    granted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='권한 부여일'
    )
    
    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='권한 만료일',
        help_text='비어있으면 무기한'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='활성 상태'
    )
    
    class Meta:
        db_table = 'user_permissions'
        verbose_name = '사용자 권한'
        verbose_name_plural = '사용자 권한'
        unique_together = ['user', 'permission']
        ordering = ['user', 'permission']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_permission_display()}"
    
    @property
    def is_expired(self):
        """권한 만료 여부 확인"""
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False