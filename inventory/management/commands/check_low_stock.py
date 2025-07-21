# File: inventory/management/commands/check_low_stock.py
from django.core.management.base import BaseCommand
from django.db.models import F
from products.models import Product

class Command(BaseCommand):
    help = '재고 부족 상품 확인'

    def add_arguments(self, parser):
        parser.add_argument(
            '--send-alert',
            action='store_true',
            help='재고 부족 알림 발송'
        )

    def handle(self, *args, **options):
        from core.models import SystemSettings
        settings = SystemSettings.get_settings()
        
        # 시스템 설정에서 재고 부족 기준 가져오기
        low_stock_threshold = settings.low_stock_threshold
        
        low_stock_products = Product.objects.filter(
            stock_quantity__lte=low_stock_threshold,
            status='ACTIVE'
        ).select_related('brand', 'category')

        if not low_stock_products.exists():
            self.stdout.write(
                self.style.SUCCESS('재고 부족 상품이 없습니다.')
            )
            return

        self.stdout.write(
            self.style.WARNING(f'재고 부족 상품 {low_stock_products.count()}개 발견 (기준: {low_stock_threshold}개 이하)')
        )

        for product in low_stock_products:
            self.stdout.write(
                f'- {product.sku}: {product.name} '
                f'(현재: {product.stock_quantity}개)'
            )

        # 재고 알림이 활성화되어 있고 알림 발송 옵션이 있는 경우
        if options['send_alert'] and settings.stock_alert_enabled:
            from platforms.tasks import generate_low_stock_alert
            generate_low_stock_alert.delay()
            self.stdout.write(
                self.style.SUCCESS('재고 부족 알림을 발송했습니다.')
            )
        elif options['send_alert'] and not settings.stock_alert_enabled:
            self.stdout.write(
                self.style.WARNING('재고 알림이 시스템 설정에서 비활성화되어 있습니다.')
            )