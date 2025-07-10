# inventory/apps.py - Django 앱 설정
from django.apps import AppConfig

class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'
    verbose_name = '재고 관리'
    
    def ready(self):
        """앱이 준비되었을 때 실행되는 메서드"""
        # 시그널 import (시그널 등록)
        try:
            from . import signals
            signals.connect_signals()
        except ImportError as e:
            print(f"재고 관리 시그널 연결 실패: {e}")
        
        # 관리자 인라인 추가
        try:
            from .admin import add_stock_inlines_to_product_admin
            add_stock_inlines_to_product_admin()
        except Exception as e:
            print(f"Product 관리자 인라인 추가 실패: {e}")
        
        # 기본 설정 확인
        self.check_settings()
    
    def check_settings(self):
        """필요한 설정들이 올바르게 되어있는지 확인"""
        from django.conf import settings
        
        # 재고 알림 이메일 설정 확인
        if not hasattr(settings, 'ENABLE_STOCK_EMAIL_ALERTS'):
            setattr(settings, 'ENABLE_STOCK_EMAIL_ALERTS', False)
        
        if not hasattr(settings, 'STOCK_ALERT_RECIPIENTS'):
            setattr(settings, 'STOCK_ALERT_RECIPIENTS', [])
        
        # 로깅 설정 확인
        if not hasattr(settings, 'LOGGING'):
            # 기본 로깅 설정
            setattr(settings, 'LOGGING', {
                'version': 1,
                'disable_existing_loggers': False,
                'handlers': {
                    'file': {
                        'level': 'INFO',
                        'class': 'logging.FileHandler',
                        'filename': 'inventory.log',
                    },
                },
                'loggers': {
                    'inventory': {
                        'handlers': ['file'],
                        'level': 'INFO',
                        'propagate': True,
                    },
                },
            })