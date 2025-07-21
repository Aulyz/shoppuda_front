# notifications/management/commands/send_test_notification.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from notifications.utils import send_notification

User = get_user_model()

class Command(BaseCommand):
    help = '테스트 알림을 발송합니다'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='알림을 받을 사용자명')
        parser.add_argument(
            '--type',
            type=str,
            default='info',
            choices=['order', 'stock', 'payment', 'system', 'warning', 'info'],
            help='알림 타입'
        )

    def handle(self, *args, **options):
        username = options['username']
        notification_type = options['type']
        
        try:
            user = User.objects.get(username=username)
            
            notification = send_notification(
                user=user,
                title='테스트 알림',
                message=f'이것은 {notification_type} 타입의 테스트 알림입니다.',
                notification_type=notification_type,
                url='/dashboard/'
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'{username}에게 테스트 알림을 발송했습니다. (ID: {notification.id})'
                )
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'사용자 "{username}"을 찾을 수 없습니다.')
            )