# inventory/signals.py - 재고 관리 시그널
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User

from products.models import Product
from .models import StockMovement, StockAlert, StockLevel

@receiver(pre_save, sender=Product)
def track_stock_changes(sender, instance, **kwargs):
    """상품 재고 변경 추적"""
    if instance.pk:
        try:
            old_instance = Product.objects.get(pk=instance.pk)
            if old_instance.stock_quantity != instance.stock_quantity:
                # 재고 변경이 감지되면 이전 값을 임시 저장
                instance._old_stock_quantity = old_instance.stock_quantity
            else:
                instance._old_stock_quantity = None
        except Product.DoesNotExist:
            instance._old_stock_quantity = None
    else:
        instance._old_stock_quantity = None

@receiver(post_save, sender=Product)
def handle_stock_change(sender, instance, created, **kwargs):
    """재고 변경 후 처리"""
    if created:
        # 새 상품 생성시 기본 StockLevel 생성
        StockLevel.objects.get_or_create(
            product=instance,
            defaults={
                'min_stock_level': instance.min_stock_level,
                'max_stock_level': instance.max_stock_level,
                'reorder_point': instance.min_stock_level,
                'reorder_quantity': max(50, instance.min_stock_level * 2),
                'safety_stock': max(10, instance.min_stock_level // 2),
            }
        )
        return
    
    # 재고 변경이 있었는지 확인
    old_quantity = getattr(instance, '_old_stock_quantity', None)
    if old_quantity is not None and old_quantity != instance.stock_quantity:
        # 자동 StockMovement 생성 (수동 조정이 아닌 경우)
        if not getattr(instance, '_skip_stock_movement', False):
            create_automatic_stock_movement(instance, old_quantity, instance.stock_quantity)
        
        # 재고 알림 체크
        check_and_create_stock_alerts(instance)
        
        # 재고 변경 정리
        if hasattr(instance, '_old_stock_quantity'):
            delattr(instance, '_old_stock_quantity')

def create_automatic_stock_movement(product, old_quantity, new_quantity):
    """자동 재고 이동 기록 생성"""
    try:
        quantity_change = abs(new_quantity - old_quantity)
        movement_type = 'IN' if new_quantity > old_quantity else 'OUT'
        
        StockMovement.objects.create(
            product=product,
            movement_type=movement_type,
            quantity=quantity_change,
            previous_stock=old_quantity,
            current_stock=new_quantity,
            reference_number=f'AUTO-{timezone.now().strftime("%Y%m%d%H%M%S")}-{product.id}',
            reason='자동 재고 변경 감지',
            notes=f'시스템에서 자동으로 감지된 재고 변경: {old_quantity}개 → {new_quantity}개',
            is_automated=True,
            source_system='DJANGO_ADMIN'
        )
    except Exception as e:
        # 로깅만 하고 에러는 무시 (재고 변경 자체를 방해하지 않기 위해)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'자동 재고 이동 기록 생성 실패: {str(e)}')

def check_and_create_stock_alerts(product):
    """재고 알림 확인 및 생성"""
    current_stock = product.stock_quantity
    
    # 기존 활성 알림들 조회
    active_alerts = StockAlert.objects.filter(
        product=product,
        status='ACTIVE'
    ).values_list('alert_type', flat=True)
    
    alerts_to_create = []
    alerts_to_resolve = []
    
    # 재고 없음 체크
    if current_stock == 0:
        if 'OUT_OF_STOCK' not in active_alerts:
            alerts_to_create.append(create_alert_data(
                product, 'OUT_OF_STOCK', 
                f'{product.name}의 재고가 모두 소진되었습니다.',
                threshold_value=0,
                current_value=current_stock
            ))
        # 다른 알림들은 해결 처리
        alerts_to_resolve.extend(['LOW_STOCK', 'OVERSTOCK'])
    
    # 재고 부족 체크
    elif current_stock <= product.min_stock_level:
        if 'LOW_STOCK' not in active_alerts:
            alerts_to_create.append(create_alert_data(
                product, 'LOW_STOCK',
                f'{product.name}의 재고가 부족합니다. (현재: {current_stock}개, 최소: {product.min_stock_level}개)',
                threshold_value=product.min_stock_level,
                current_value=current_stock
            ))
        # OUT_OF_STOCK과 OVERSTOCK 알림 해결
        alerts_to_resolve.extend(['OUT_OF_STOCK', 'OVERSTOCK'])
    
    # 재고 과다 체크
    elif current_stock > product.max_stock_level:
        if 'OVERSTOCK' not in active_alerts:
            alerts_to_create.append(create_alert_data(
                product, 'OVERSTOCK',
                f'{product.name}의 재고가 과도합니다. (현재: {current_stock}개, 최대: {product.max_stock_level}개)',
                threshold_value=product.max_stock_level,
                current_value=current_stock
            ))
        # 다른 알림들은 해결 처리
        alerts_to_resolve.extend(['OUT_OF_STOCK', 'LOW_STOCK'])
    
    # 정상 재고 상태
    else:
        # 모든 재고 관련 알림 해결
        alerts_to_resolve.extend(['OUT_OF_STOCK', 'LOW_STOCK', 'OVERSTOCK'])
    
    # 알림 생성
    for alert_data in alerts_to_create:
        try:
            alert = StockAlert.objects.create(**alert_data)
            # 이메일 알림 발송 (비동기 처리 권장)
            send_stock_alert_email(alert)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'재고 알림 생성 실패: {str(e)}')
    
    # 알림 해결
    if alerts_to_resolve:
        StockAlert.objects.filter(
            product=product,
            alert_type__in=alerts_to_resolve,
            status='ACTIVE'
        ).update(
            status='RESOLVED',
            resolved_at=timezone.now()
        )

def create_alert_data(product, alert_type, message, threshold_value=None, current_value=None):
    """알림 데이터 생성"""
    return {
        'product': product,
        'alert_type': alert_type,
        'message': message,
        'threshold_value': threshold_value,
        'current_value': current_value,
    }

def send_stock_alert_email(alert):
    """재고 알림 이메일 발송"""
    try:
        if not getattr(settings, 'ENABLE_STOCK_EMAIL_ALERTS', False):
            return
        
        # 알림 수신자 목록 (설정에서 가져오거나 관리자들)
        recipients = getattr(settings, 'STOCK_ALERT_RECIPIENTS', [])
        if not recipients:
            # 기본적으로 staff 사용자들에게 발송
            recipients = list(User.objects.filter(
                is_staff=True, 
                is_active=True,
                email__isnull=False
            ).exclude(email='').values_list('email', flat=True))
        
        if not recipients:
            return
        
        subject = f'[Shopuda ERP] 재고 알림 - {alert.get_alert_type_display()}'
        
        message = f"""
재고 알림이 발생했습니다.

상품 정보:
- 상품명: {alert.product.name}
- SKU: {alert.product.sku}
- 브랜드: {alert.product.brand.name if alert.product.brand else 'N/A'}

알림 내용:
- 유형: {alert.get_alert_type_display()}
- 메시지: {alert.message}
- 현재 재고: {alert.current_value}개
- 기준값: {alert.threshold_value}개

발생 시간: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}

재고 조정이 필요한 경우 ERP 시스템에 로그인하여 처리해주세요.

이 메시지는 자동으로 발송된 메일입니다.
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@shopuda.com'),
            recipient_list=recipients,
            fail_silently=True  # 이메일 발송 실패가 시스템을 중단시키지 않도록
        )
        
        # 이메일 발송 기록
        alert.is_email_sent = True
        alert.email_sent_at = timezone.now()
        alert.save(update_fields=['is_email_sent', 'email_sent_at'])
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'재고 알림 이메일 발송 실패: {str(e)}')

@receiver(post_save, sender=StockMovement)
def update_product_stock_from_movement(sender, instance, created, **kwargs):
    """StockMovement 생성시 상품 재고 자동 업데이트 (옵션)"""
    # 이 기능은 StockMovement가 재고의 소스 오브 트루스인 경우에만 사용
    # 현재는 Product.stock_quantity가 소스 오브 트루스이므로 비활성화
    pass

@receiver(post_save, sender=StockLevel)
def sync_product_stock_levels(sender, instance, created, **kwargs):
    """StockLevel 변경시 Product의 재고 수준 동기화"""
    try:
        product = instance.product
        
        # Product 모델의 재고 수준 필드가 있는 경우 동기화
        if hasattr(product, 'min_stock_level') and hasattr(product, 'max_stock_level'):
            product_updated = False
            
            if product.min_stock_level != instance.min_stock_level:
                product.min_stock_level = instance.min_stock_level
                product_updated = True
            
            if product.max_stock_level != instance.max_stock_level:
                product.max_stock_level = instance.max_stock_level
                product_updated = True
            
            if product_updated:
                # StockMovement 생성 방지
                product._skip_stock_movement = True
                product.save(update_fields=['min_stock_level', 'max_stock_level'])
                
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Product 재고 수준 동기화 실패: {str(e)}')

# 앱 시작시 시그널 연결
def connect_signals():
    """시그널 연결 함수"""
    # 이미 위에서 @receiver 데코레이터로 연결되어 있음
    pass