# notifications/management/commands/cleanup_notifications.py
import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from notifications.models import Notification
from django.conf import settings

class Command(BaseCommand):
    help = '오래된 알림을 정리합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=getattr(settings, 'NOTIFICATION_SETTINGS', {}).get('RETENTION_DAYS', 30),
            help='삭제할 알림의 기준 일수 (기본값: 30일)'
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # 읽은 알림 중 오래된 것들 삭제
        deleted_count = Notification.objects.filter(
            is_read=True,
            created_at__lt=cutoff_date
        ).delete()[0]
        
        self.stdout.write(
            self.style.SUCCESS(
                f'{deleted_count}개의 오래된 알림을 정리했습니다.'
            )
        )