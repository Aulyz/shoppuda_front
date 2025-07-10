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
        low_stock_products = Product.objects.filter(
            stock_quantity__lte=F('min_stock_level'),
            status='ACTIVE'
        ).select_related('brand', 'category')

        if not low_stock_products.exists():
            self.stdout.write(
                self.style.SUCCESS('재고 부족 상품이 없습니다.')
            )
            return

        self.stdout.write(
            self.style.WARNING(f'재고 부족 상품 {low_stock_products.count()}개 발견')
        )

        for product in low_stock_products:
            self.stdout.write(
                f'- {product.sku}: {product.name} '
                f'(현재: {product.stock_quantity}, 최소: {product.min_stock_level})'
            )

        if options['send_alert']:
            from platforms.tasks import generate_low_stock_alert
            generate_low_stock_alert.delay()
            self.stdout.write(
                self.style.SUCCESS('재고 부족 알림을 발송했습니다.')
            )