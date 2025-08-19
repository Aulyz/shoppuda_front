"""
쿠폰 시스템 서비스 레이어
"""
from django.utils import timezone
from django.db import transaction
from .models import Coupon, UserCoupon, CouponLog
import logging

logger = logging.getLogger(__name__)


class CouponService:
    """쿠폰 관련 비즈니스 로직"""
    
    @staticmethod
    @transaction.atomic
    def issue_coupon_to_user(coupon, user, log=True):
        """사용자에게 쿠폰 발급"""
        # 발급 가능 여부 확인
        can_issue, message = coupon.can_issue_to_user(user)
        if not can_issue:
            return False, message
        
        # 만료일 계산
        if coupon.days_valid_after_issue:
            from datetime import timedelta
            expires_at = timezone.now() + timedelta(days=coupon.days_valid_after_issue)
        else:
            expires_at = coupon.valid_to
        
        # 쿠폰 발급
        user_coupon = UserCoupon.objects.create(
            user=user,
            coupon=coupon,
            expires_at=expires_at
        )
        
        # 발급 수량 증가
        coupon.issued_quantity += 1
        coupon.save()
        
        # 로그 기록
        if log:
            CouponLog.objects.create(
                coupon=coupon,
                user=user,
                action='ISSUED',
                details={
                    'user_coupon_id': user_coupon.id,
                    'expires_at': expires_at.isoformat()
                }
            )
        
        logger.info(f"Coupon {coupon.code} issued to user {user.username}")
        return True, user_coupon
    
    @staticmethod
    def issue_coupon_by_code(code, user):
        """쿠폰 코드로 발급"""
        try:
            coupon = Coupon.objects.get(code=code.upper(), is_active=True)
            return CouponService.issue_coupon_to_user(coupon, user)
        except Coupon.DoesNotExist:
            return False, "유효하지 않은 쿠폰 코드입니다."
    
    @staticmethod
    def auto_issue_welcome_coupon(user):
        """회원가입 웰컴 쿠폰 자동 발급"""
        welcome_coupons = Coupon.objects.filter(
            issue_type='WELCOME',
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_to__gte=timezone.now()
        )
        
        results = []
        for coupon in welcome_coupons:
            success, result = CouponService.issue_coupon_to_user(coupon, user)
            if success:
                results.append(result)
        
        return results
    
    @staticmethod
    def auto_issue_birthday_coupon(user):
        """생일 쿠폰 자동 발급"""
        if not user.birth_date:
            return []
        
        today = timezone.now().date()
        if user.birth_date.month != today.month or user.birth_date.day != today.day:
            return []
        
        birthday_coupons = Coupon.objects.filter(
            issue_type='BIRTHDAY',
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_to__gte=timezone.now()
        )
        
        results = []
        for coupon in birthday_coupons:
            # 올해 이미 발급받았는지 확인
            this_year_issued = UserCoupon.objects.filter(
                user=user,
                coupon=coupon,
                issued_at__year=today.year
            ).exists()
            
            if not this_year_issued:
                success, result = CouponService.issue_coupon_to_user(coupon, user)
                if success:
                    results.append(result)
        
        return results
    
    @staticmethod
    @transaction.atomic
    def use_coupon(user_coupon, order, discount_amount):
        """쿠폰 사용 처리"""
        if not user_coupon.is_valid:
            return False, "사용할 수 없는 쿠폰입니다."
        
        try:
            user_coupon.use(order, discount_amount)
            
            # 로그 기록
            CouponLog.objects.create(
                coupon=user_coupon.coupon,
                user=user_coupon.user,
                action='USED',
                details={
                    'order_id': order.id,
                    'discount_amount': str(discount_amount)
                }
            )
            
            logger.info(f"Coupon {user_coupon.coupon.code} used for order {order.order_number}")
            return True, "쿠폰이 적용되었습니다."
            
        except Exception as e:
            logger.error(f"Error using coupon: {e}")
            return False, str(e)
    
    @staticmethod
    @transaction.atomic
    def cancel_coupon_usage(user_coupon):
        """쿠폰 사용 취소"""
        try:
            user_coupon.cancel()
            
            # 로그 기록
            CouponLog.objects.create(
                coupon=user_coupon.coupon,
                user=user_coupon.user,
                action='CANCELLED',
                details={
                    'order_id': user_coupon.order.id if user_coupon.order else None
                }
            )
            
            logger.info(f"Coupon usage cancelled: {user_coupon.coupon.code}")
            return True, "쿠폰 사용이 취소되었습니다."
            
        except Exception as e:
            logger.error(f"Error cancelling coupon: {e}")
            return False, str(e)
    
    @staticmethod
    def validate_coupon_for_order(user_coupon, order_amount, products=None):
        """주문에 대한 쿠폰 유효성 검증"""
        coupon = user_coupon.coupon
        
        # 기본 유효성 확인
        if not user_coupon.is_valid:
            return False, "사용할 수 없는 쿠폰입니다."
        
        # 최소 주문 금액 확인
        if order_amount < coupon.min_order_amount:
            return False, f"최소 주문 금액 ₩{coupon.min_order_amount:,.0f} 이상에서 사용 가능합니다."
        
        # 적용 가능 상품/카테고리 확인
        if products:
            if coupon.applicable_products.exists():
                applicable = any(p in coupon.applicable_products.all() for p in products)
                if not applicable:
                    return False, "해당 상품에는 쿠폰을 사용할 수 없습니다."
            
            if coupon.applicable_categories.exists():
                product_categories = [p.category for p in products if p.category]
                applicable = any(c in coupon.applicable_categories.all() for c in product_categories)
                if not applicable:
                    return False, "해당 카테고리 상품에는 쿠폰을 사용할 수 없습니다."
            
            # 세일 상품 제외 확인
            if coupon.exclude_sale_items:
                has_sale = any(p.discount_price for p in products)
                if has_sale:
                    return False, "세일 상품에는 쿠폰을 사용할 수 없습니다."
        
        return True, "사용 가능"
    
    @staticmethod
    def calculate_discount(coupon, order_amount, applicable_amount=None):
        """쿠폰 할인 금액 계산"""
        return coupon.calculate_discount(order_amount, applicable_amount)
    
    @staticmethod
    def get_user_available_coupons(user, order_amount=None, products=None):
        """사용자가 사용 가능한 쿠폰 목록"""
        user_coupons = UserCoupon.objects.filter(
            user=user,
            status='ISSUED',
            expires_at__gte=timezone.now(),
            coupon__is_active=True
        ).select_related('coupon')
        
        available_coupons = []
        for user_coupon in user_coupons:
            if order_amount:
                is_valid, message = CouponService.validate_coupon_for_order(
                    user_coupon, order_amount, products
                )
                if is_valid:
                    discount = CouponService.calculate_discount(
                        user_coupon.coupon, order_amount
                    )
                    available_coupons.append({
                        'user_coupon': user_coupon,
                        'discount': discount,
                        'message': message
                    })
            else:
                available_coupons.append({
                    'user_coupon': user_coupon,
                    'discount': 0,
                    'message': ''
                })
        
        return available_coupons
    
    @staticmethod
    def expire_old_coupons():
        """만료된 쿠폰 상태 업데이트 (배치 작업)"""
        expired_count = UserCoupon.objects.filter(
            status='ISSUED',
            expires_at__lt=timezone.now()
        ).update(status='EXPIRED')
        
        if expired_count:
            logger.info(f"Expired {expired_count} coupons")
        
        return expired_count