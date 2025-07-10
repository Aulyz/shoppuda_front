from django.apps import AppConfig

class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'
    verbose_name = '주문'

    def ready(self):
        import orders.signals  # 주문 관련 시그널 등록