# reports/apps.py
from django.apps import AppConfig

class ReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reports'
    verbose_name = '보고서 관리'
    
    def ready(self):
        """앱이 준비되었을 때 실행"""
        import reports.signals