try:
    from celery import shared_task
    from django.core.mail import send_mail
    from django.conf import settings
    
    @shared_task
    def process_bulk_import(file_path, user_id):
        """대용량 상품 가져오기 백그라운드 처리"""
        import os
        from django.contrib.auth import get_user_model
        from .views import process_import_file
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
            result = process_import_file(file_path, user)
            
            # 결과 이메일 발송
            send_mail(
                subject='상품 가져오기 완료',
                message=f'''
                상품 가져오기가 완료되었습니다.
                
                성공: {result["success_count"]}개
                실패: {result["error_count"]}개
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True
            )
            
            return result
            
        finally:
            # 임시 파일 삭제
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    @shared_task
    def sync_platform_products():
        """플랫폼 상품 동기화 태스크"""
        from platforms.models import Platform
        
        active_platforms = Platform.objects.filter(is_active=True, auto_sync=True)
        
        for platform in active_platforms:
            try:
                # 플랫폼별 동기화 로직 실행
                # 실제 구현은 각 플랫폼의 API에 따라 달라집니다
                pass
            except Exception as e:
                # 에러 로깅
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'플랫폼 {platform.name} 동기화 실패: {str(e)}')
    
    @shared_task
    def check_low_stock():
        """재고 부족 상품 체크 및 알림"""
        from products.models import Product
        from django.contrib.auth import get_user_model
        from django.db import models
        User = get_user_model()
        
        low_stock_products = Product.objects.filter(
            stock_quantity__lte=models.F('min_stock_level'),
            status='ACTIVE'
        )
        
        if low_stock_products.exists():
            # 관리자에게 이메일 발송
            admin_users = User.objects.filter(is_staff=True, email__isnull=False)
            
            product_list = '\n'.join([
                f'- {p.name} (SKU: {p.sku}): {p.stock_quantity}개 남음'
                for p in low_stock_products[:10]  # 최대 10개만 표시
            ])
            
            for admin in admin_users:
                send_mail(
                    subject='[Shopuda ERP] 재고 부족 알림',
                    message=f'''
                    재고가 부족한 상품이 {low_stock_products.count()}개 있습니다.
                    
                    {product_list}
                    
                    ERP 시스템에서 확인해주세요.
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin.email],
                    fail_silently=True
                )

except ImportError:
    # Celery가 설치되지 않은 경우 더미 함수 제공
    def process_bulk_import(file_path, user_id):
        pass
    
    def sync_platform_products():
        pass
    
    def check_low_stock():
        pass