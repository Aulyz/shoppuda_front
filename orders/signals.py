# orders/signals.py (주문 생성 시 알림 발송)
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Order
from notifications.utils import send_order_notification

User = get_user_model()

@receiver(post_save, sender=Order)
def order_created_notification(sender, instance, created, **kwargs):
    """새 주문 생성 시 알림 발송"""
    if created:
        # 관리자들에게 알림 발송
        admin_users = User.objects.filter(is_staff=True)
        for admin in admin_users:
            send_order_notification(admin, instance)