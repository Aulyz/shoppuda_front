# notifications/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('order', '주문'),
        ('stock', '재고'),
        ('payment', '결제'),
        ('system', '시스템'),
        ('warning', '경고'),
        ('info', '정보'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    url = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def get_icon(self):
        """알림 타입별 아이콘 반환"""
        icons = {
            'order': 'fas fa-shopping-cart',
            'stock': 'fas fa-warehouse',
            'payment': 'fas fa-credit-card',
            'system': 'fas fa-cog',
            'warning': 'fas fa-exclamation-triangle',
            'info': 'fas fa-info-circle',
        }
        return icons.get(self.notification_type, 'fas fa-bell')
    
    def get_color(self):
        """알림 타입별 색상 반환"""
        colors = {
            'order': 'text-blue-500',
            'stock': 'text-orange-500',
            'payment': 'text-green-500',
            'system': 'text-gray-500',
            'warning': 'text-red-500',
            'info': 'text-blue-500',
        }
        return colors.get(self.notification_type, 'text-gray-500')