from django.apps import AppConfig

class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'
    verbose_name = '상품'

    def ready(self):
        import products.signals  # 상품 관련 시그널 등록