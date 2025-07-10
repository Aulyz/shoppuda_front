# File: platforms/management/commands/sync_platforms.py
from django.core.management.base import BaseCommand
from platforms.tasks import sync_all_platforms

class Command(BaseCommand):
    help = '모든 플랫폼 상품 동기화'

    def add_arguments(self, parser):
        parser.add_argument(
            '--platform-id',
            type=int,
            help='특정 플랫폼 ID만 동기화'
        )

    def handle(self, *args, **options):
        platform_id = options.get('platform_id')
        
        if platform_id:
            from platforms.tasks import sync_platform_products
            self.stdout.write(f'플랫폼 ID {platform_id} 동기화를 시작합니다...')
            sync_platform_products.delay(platform_id)
            self.stdout.write(
                self.style.SUCCESS(f'플랫폼 ID {platform_id} 동기화 작업이 큐에 추가되었습니다.')
            )
        else:
            self.stdout.write('모든 플랫폼 동기화를 시작합니다...')
            sync_all_platforms.delay()
            self.stdout.write(
                self.style.SUCCESS('모든 플랫폼 동기화 작업이 큐에 추가되었습니다.')
            )