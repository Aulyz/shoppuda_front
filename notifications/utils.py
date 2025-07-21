from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification

def send_notification(user, title, message, notification_type='info', url=None):
    """사용자에게 실시간 알림 전송"""
    try:
        # DB에 알림 저장
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            url=url
        )
        
        # WebSocket을 통해 실시간 전송
        channel_layer = get_channel_layer()
        if channel_layer:
            group_name = f"user_{user.id}"
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_notification',
                    'data': {
                        'id': notification.id,
                        'title': notification.title,
                        'message': notification.message,
                        'notification_type': notification.notification_type,
                        'created_at': notification.created_at.isoformat(),
                        'is_read': notification.is_read,
                        'url': notification.url,
                        'icon': notification.get_icon(),
                        'color': notification.get_color()
                    }
                }
            )
        
        return notification
    except Exception as e:
        print(f"알림 발송 오류: {e}")
        return None

def send_order_notification(user, order):
    """주문 관련 알림 전송"""
    try:
        return send_notification(
            user=user,
            title=f"새로운 주문 #{order.order_number}",
            message=f"주문 금액: {order.total_amount:,}원",
            notification_type='order',
            url=f'/orders/{order.id}/'
        )
    except AttributeError as e:
        # 필드가 없는 경우 기본값 사용
        order_number = getattr(order, 'order_number', order.id)
        total_amount = getattr(order, 'total_amount', 0)
        return send_notification(
            user=user,
            title=f"새로운 주문 #{order_number}",
            message=f"주문이 접수되었습니다.",
            notification_type='order',
            url=f'/orders/{order.id}/'
        )

def send_stock_alert(user, product, current_stock):
    """재고 부족 알림 전송"""
    try:
        return send_notification(
            user=user,
            title=f"재고 부족 알림",
            message=f"{product.name} - 현재 재고: {current_stock}개",
            notification_type='stock',
            url=f'/products/{product.id}/'
        )
    except Exception as e:
        print(f"재고 알림 발송 오류: {e}")
        return None

# 테스트용 알림 발송 함수
def send_test_notifications():
    """테스트 알림들을 발송하는 함수"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # 첫 번째 관리자 사용자에게 테스트 알림 발송
    admin_user = User.objects.filter(is_staff=True).first()
    if admin_user:
        # 다양한 타입의 테스트 알림 발송
        notifications = [
            {
                'title': '새로운 주문이 접수되었습니다',
                'message': '주문 #12345 - 고객: 김철수님',
                'type': 'order'
            },
            {
                'title': '재고 부족 경고',
                'message': '노트북 상품의 재고가 5개 이하입니다',
                'type': 'stock'
            },
            {
                'title': '결제 완료',
                'message': '주문 #12344에 대한 결제가 완료되었습니다',
                'type': 'payment'
            },
            {
                'title': '시스템 업데이트',
                'message': '시스템이 성공적으로 업데이트되었습니다',
                'type': 'system'
            }
        ]
        
        for notif in notifications:
            send_notification(
                user=admin_user,
                title=notif['title'],
                message=notif['message'],
                notification_type=notif['type'],
                url='/dashboard/'
            )
        
        print(f"{len(notifications)}개의 테스트 알림을 {admin_user.username}에게 발송했습니다.")
    else:
        print("관리자 사용자를 찾을 수 없습니다.")