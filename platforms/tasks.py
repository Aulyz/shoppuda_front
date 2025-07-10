# File: platforms/tasks.py
from celery import shared_task
from django.utils import timezone
from django.db.models import F
from django.core.mail import send_mail
from django.conf import settings
from .models import Platform, PlatformProduct
from products.models import Product
from inventory.models import StockMovement
import requests
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@shared_task
def sync_platform_products(platform_id):
    """플랫폼 상품 동기화"""
    try:
        platform = Platform.objects.get(id=platform_id, is_active=True)
        
        logger.info(f"Starting sync for platform: {platform.name}")
        
        # 플랫폼별 API 호출 로직
        if platform.platform_type == 'SMARTSTORE':
            result = sync_smartstore_products(platform)
        elif platform.platform_type == 'COUPANG':
            result = sync_coupang_products(platform)
        elif platform.platform_type == 'GMARKET':
            result = sync_gmarket_products(platform)
        elif platform.platform_type == 'AUCTION':
            result = sync_auction_products(platform)
        elif platform.platform_type == '11ST':
            result = sync_11st_products(platform)
        else:
            logger.warning(f"Unsupported platform type: {platform.platform_type}")
            return {'success': False, 'message': f'지원하지 않는 플랫폼: {platform.platform_type}'}
        
        logger.info(f"Sync completed for platform: {platform.name} - {result}")
        return result
        
    except Platform.DoesNotExist:
        error_msg = f"Platform with id {platform_id} not found"
        logger.error(error_msg)
        return {'success': False, 'message': error_msg}
    except Exception as e:
        error_msg = f"Error syncing platform {platform_id}: {str(e)}"
        logger.error(error_msg)
        return {'success': False, 'message': error_msg}

def sync_smartstore_products(platform):
    """스마트스토어 상품 동기화"""
    try:
        headers = {
            'Authorization': f'Bearer {platform.api_key}',
            'Content-Type': 'application/json',
            'X-Timestamp': str(int(timezone.now().timestamp())),
        }
        
        # API 요청 (실제 API 엔드포인트에 맞게 수정 필요)
        response = requests.get(
            f"{platform.api_url}/v1/products",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            products_data = data.get('products', [])
            
            updated_count = 0
            error_count = 0
            
            for product_data in products_data:
                try:
                    result = update_platform_product(platform, product_data)
                    if result['success']:
                        updated_count += 1
                    else:
                        error_count += 1
                        logger.warning(f"Failed to update product: {result['message']}")
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing product {product_data.get('id')}: {str(e)}")
            
            return {
                'success': True,
                'message': f'스마트스토어 동기화 완료: {updated_count}개 업데이트, {error_count}개 오류',
                'updated_count': updated_count,
                'error_count': error_count
            }
        else:
            error_msg = f"API request failed with status {response.status_code}: {response.text}"
            logger.error(error_msg)
            return {'success': False, 'message': error_msg}
            
    except requests.RequestException as e:
        error_msg = f"Network error during smartstore sync: {str(e)}"
        logger.error(error_msg)
        return {'success': False, 'message': error_msg}
    except Exception as e:
        error_msg = f"Unexpected error during smartstore sync: {str(e)}"
        logger.error(error_msg)
        return {'success': False, 'message': error_msg}

def sync_coupang_products(platform):
    """쿠팡 상품 동기화"""
    try:
        # 쿠팡 API 인증 헤더 (실제 구현 시 HMAC 서명 필요)
        headers = {
            'Authorization': f'Bearer {platform.api_key}',
            'X-COUPANG-APICredentials': platform.api_secret,
            'Content-Type': 'application/json',
        }
        
        response = requests.get(
            f"{platform.api_url}/v2/providers/seller_api/apis/api/v1/marketplace/seller-products",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            products_data = data.get('data', [])
            
            updated_count = 0
            error_count = 0
            
            for product_data in products_data:
                try:
                    # 쿠팡 데이터 형식에 맞게 변환
                    normalized_data = {
                        'id': product_data.get('vendorItemId'),
                        'sku': product_data.get('sellerProductId'),
                        'name': product_data.get('sellerProductName'),
                        'price': product_data.get('salePrice', 0),
                        'stock': product_data.get('quantity', 0),
                        'is_active': product_data.get('displayStatus') == 'ON_SALE'
                    }
                    
                    result = update_platform_product(platform, normalized_data)
                    if result['success']:
                        updated_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing coupang product: {str(e)}")
            
            return {
                'success': True,
                'message': f'쿠팡 동기화 완료: {updated_count}개 업데이트, {error_count}개 오류',
                'updated_count': updated_count,
                'error_count': error_count
            }
        else:
            return {'success': False, 'message': f'쿠팡 API 오류: {response.status_code}'}
            
    except Exception as e:
        error_msg = f"쿠팡 동기화 오류: {str(e)}"
        logger.error(error_msg)
        return {'success': False, 'message': error_msg}

def sync_gmarket_products(platform):
    """G마켓 상품 동기화 (기본 구조)"""
    # G마켓 API 구현 예시
    return {'success': True, 'message': 'G마켓 동기화는 준비중입니다.'}

def sync_auction_products(platform):
    """옥션 상품 동기화 (기본 구조)"""
    # 옥션 API 구현 예시
    return {'success': True, 'message': '옥션 동기화는 준비중입니다.'}

def sync_11st_products(platform):
    """11번가 상품 동기화 (기본 구조)"""
    # 11번가 API 구현 예시
    return {'success': True, 'message': '11번가 동기화는 준비중입니다.'}

def update_platform_product(platform, product_data):
    """플랫폼 상품 정보 업데이트"""
    try:
        # SKU로 상품 매칭
        sku = product_data.get('sku')
        if not sku:
            return {'success': False, 'message': 'SKU가 없습니다.'}
        
        try:
            product = Product.objects.get(sku=sku)
        except Product.DoesNotExist:
            return {'success': False, 'message': f'SKU {sku}에 해당하는 상품을 찾을 수 없습니다.'}
        
        # 플랫폼 상품 정보 업데이트 또는 생성
        platform_product, created = PlatformProduct.objects.update_or_create(
            product=product,
            platform=platform,
            platform_product_id=str(product_data.get('id', '')),
            defaults={
                'platform_sku': product_data.get('platform_sku', ''),
                'platform_price': product_data.get('price', 0),
                'platform_stock': product_data.get('stock', 0),
                'is_active': product_data.get('is_active', True),
                'last_sync_at': timezone.now(),
            }
        )
        
        # 재고 변동 확인 및 기록
        stock_changed = False
        if not created:
            old_stock = product.stock_quantity
            new_stock = product_data.get('stock', 0)
            
            if old_stock != new_stock:
                stock_changed = True
                
                # 재고 이동 기록 생성
                StockMovement.objects.create(
                    product=product,
                    movement_type='ADJUST',
                    quantity=new_stock - old_stock,
                    previous_stock=old_stock,
                    current_stock=new_stock,
                    reference_number=f"PLATFORM_SYNC_{platform.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
                    notes=f"{platform.name} 플랫폼 동기화로 인한 재고 조정"
                )
                
                # 마스터 재고 업데이트
                product.stock_quantity = new_stock
                product.save(update_fields=['stock_quantity'])
        
        action = '생성' if created else ('업데이트(재고변동)' if stock_changed else '업데이트')
        return {
            'success': True, 
            'message': f'상품 {action}: {product.sku}',
            'created': created,
            'stock_changed': stock_changed
        }
        
    except Exception as e:
        error_msg = f"상품 업데이트 오류: {str(e)}"
        logger.error(error_msg)
        return {'success': False, 'message': error_msg}

@shared_task
def sync_all_platforms():
    """모든 활성 플랫폼 동기화"""
    active_platforms = Platform.objects.filter(is_active=True)
    
    if not active_platforms.exists():
        logger.info("No active platforms found for sync")
        return {'success': True, 'message': '활성화된 플랫폼이 없습니다.'}
    
    results = []
    for platform in active_platforms:
        # 각 플랫폼을 개별 태스크로 실행
        task_result = sync_platform_products.delay(platform.id)
        results.append({
            'platform_id': platform.id,
            'platform_name': platform.name,
            'task_id': task_result.id
        })
    
    logger.info(f"Initiated sync for {active_platforms.count()} platforms")
    return {
        'success': True,
        'message': f'{active_platforms.count()}개 플랫폼 동기화가 시작되었습니다.',
        'results': results
    }

@shared_task
def generate_low_stock_alert():
    """재고 부족 알림 생성"""
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('min_stock_level'),
        status='ACTIVE'
    ).select_related('brand', 'category')
    
    if not low_stock_products.exists():
        logger.info("No low stock products found")
        return {'success': True, 'message': '재고 부족 상품이 없습니다.'}
    
    # 재고 부족 상품 목록 생성
    low_stock_list = []
    for product in low_stock_products:
        low_stock_list.append({
            'sku': product.sku,
            'name': product.name,
            'current_stock': product.stock_quantity,
            'min_stock': product.min_stock_level,
            'brand': product.brand.name if product.brand else '브랜드 없음',
            'category': product.category.name if product.category else '카테고리 없음'
        })
    
    # 이메일 알림 발송
    try:
        send_low_stock_email(low_stock_list)
        logger.info(f"Low stock alert sent for {len(low_stock_list)} products")
    except Exception as e:
        logger.error(f"Failed to send low stock email: {str(e)}")
    
    # 슬랙 알림 발송 (선택사항)
    try:
        send_low_stock_slack(low_stock_list)
    except Exception as e:
        logger.error(f"Failed to send slack notification: {str(e)}")
    
    return {
        'success': True,
        'message': f'{len(low_stock_list)}개 재고 부족 상품에 대한 알림을 발송했습니다.',
        'low_stock_count': len(low_stock_list)
    }

def send_low_stock_email(low_stock_list):
    """재고 부족 이메일 알림 발송"""
    if not low_stock_list:
        return
    
    subject = f'[Shopuda ERP] 재고 부족 알림 - {len(low_stock_list)}개 상품'
    
    # 이메일 본문 생성
    message = f"재고 부족 상품 {len(low_stock_list)}개가 발견되었습니다.\n\n"
    message += "상품 목록:\n"
    message += "-" * 80 + "\n"
    
    for product in low_stock_list:
        message += f"SKU: {product['sku']}\n"
        message += f"상품명: {product['name']}\n"
        message += f"브랜드: {product['brand']}\n"
        message += f"카테고리: {product['category']}\n"
        message += f"현재 재고: {product['current_stock']}개\n"
        message += f"최소 재고: {product['min_stock']}개\n"
        message += "-" * 80 + "\n"
    
    message += f"\n\n확인 시간: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    message += "Shopuda ERP 시스템"
    
    # 관리자 이메일로 발송
    admin_emails = [admin[1] for admin in getattr(settings, 'ADMINS', [])]
    if admin_emails:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=False,
        )

def send_low_stock_slack(low_stock_list):
    """재고 부족 슬랙 알림 발송"""
    slack_webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', None)
    if not slack_webhook_url or not low_stock_list:
        return
    
    # 슬랙 메시지 포맷
    text = f"🚨 재고 부족 알림: {len(low_stock_list)}개 상품"
    
    attachments = []
    for product in low_stock_list[:10]:  # 최대 10개만 표시
        attachment = {
            "color": "danger",
            "fields": [
                {"title": "상품명", "value": product['name'], "short": True},
                {"title": "SKU", "value": product['sku'], "short": True},
                {"title": "현재 재고", "value": f"{product['current_stock']}개", "short": True},
                {"title": "최소 재고", "value": f"{product['min_stock']}개", "short": True},
            ]
        }
        attachments.append(attachment)
    
    if len(low_stock_list) > 10:
        attachments.append({
            "color": "warning",
            "text": f"외 {len(low_stock_list) - 10}개 상품이 더 있습니다."
        })
    
    payload = {
        "text": text,
        "attachments": attachments,
        "username": "Shopuda ERP",
        "icon_emoji": ":warning:"
    }
    
    try:
        response = requests.post(
            slack_webhook_url,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Slack notification failed: {str(e)}")

@shared_task
def cleanup_old_sync_logs():
    """오래된 동기화 로그 정리"""
    # 30일 이전의 재고 이동 기록 중 플랫폼 동기화 관련 기록 정리
    cutoff_date = timezone.now() - timedelta(days=30)
    
    deleted_count = StockMovement.objects.filter(
        created_at__lt=cutoff_date,
        reference_number__startswith='PLATFORM_SYNC_'
    ).delete()[0]
    
    logger.info(f"Cleaned up {deleted_count} old sync log entries")
    return {'success': True, 'message': f'{deleted_count}개의 오래된 동기화 로그를 정리했습니다.'}

@shared_task
def health_check():
    """시스템 상태 확인"""
    try:
        # 데이터베이스 연결 확인
        Platform.objects.count()
        
        # Redis 연결 확인 (Celery를 통해)
        from django.core.cache import cache
        cache.set('health_check', 'ok', 60)
        cache.get('health_check')
        
        return {'success': True, 'message': '시스템 상태 정상'}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {'success': False, 'message': f'시스템 상태 확인 실패: {str(e)}'}

# 주기적 작업 설정 (celery beat)
from celery.schedules import crontab