from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Product, ProductPriceHistory
from notifications.utils import send_stock_alert

User = get_user_model()

@receiver(pre_save, sender=Product)
def create_price_history(sender, instance, **kwargs):
    """상품 가격 변경 시 이력 생성"""
    if instance.pk:  # 기존 상품 업데이트인 경우
        try:
            old_product = Product.objects.get(pk=instance.pk)
            
            # 가격이 변경된 경우에만 이력 생성
            if (old_product.cost_price != instance.cost_price or 
                old_product.selling_price != instance.selling_price or 
                old_product.discount_price != instance.discount_price):
                
                ProductPriceHistory.objects.create(
                    product=instance,
                    cost_price=old_product.cost_price,
                    selling_price=old_product.selling_price,
                    discount_price=old_product.discount_price,
                    reason='가격 변경'
                )
        except Product.DoesNotExist:
            pass

@receiver(post_save, sender=Product)
def update_stock_movements(sender, instance, created, **kwargs):
    """상품 생성 시 초기 재고 이동 기록 생성"""
    if created and instance.stock_quantity > 0:
        try:
            from inventory.models import StockMovement
            StockMovement.objects.create(
                product=instance,
                movement_type='IN',
                quantity=instance.stock_quantity,
                previous_stock=0,
                current_stock=instance.stock_quantity,
                reason='초기 재고 등록',
                created_by=instance.created_by
            )
        except ImportError:
            pass

@receiver(post_save, sender=Product)
def stock_low_notification(sender, instance, **kwargs):
    """재고 부족 시 알림 발송"""
    # low_stock_threshold 필드가 있는 경우에만 체크
    if hasattr(instance, 'low_stock_threshold') and hasattr(instance, 'stock_quantity'):
        if instance.stock_quantity <= getattr(instance, 'low_stock_threshold', 10):
            # 재고 관리자들에게 알림 발송
            try:
                from django.contrib.auth.models import Group
                User = get_user_model()
                stock_managers = User.objects.filter(
                    groups__name='Stock Managers'
                )
                
                if not stock_managers.exists():
                    # 그룹이 없으면 관리자들에게 발송
                    stock_managers = User.objects.filter(is_staff=True)
                
                for manager in stock_managers:
                    send_stock_alert(manager, instance, instance.stock_quantity)
            except Exception as e:
                print(f"재고 알림 발송 오류: {e}")