from django.core.mail import send_mail
from django.template import Template, Context
from django.conf import settings
from .models import SystemSettings, EmailTemplate
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """이메일 발송 서비스"""
    
    @staticmethod
    def send_templated_email(template_type, recipient_email, context_data=None):
        """템플릿 기반 이메일 발송"""
        
        # 시스템 설정 확인
        system_settings = SystemSettings.get_settings()
        if not system_settings.email_notifications_enabled:
            logger.info(f"Email notifications disabled. Skipping {template_type} email to {recipient_email}")
            return False
        
        # 이메일 템플릿 가져오기
        try:
            email_template = EmailTemplate.objects.get(
                template_type=template_type,
                is_active=True
            )
        except EmailTemplate.DoesNotExist:
            logger.error(f"Email template '{template_type}' not found or inactive")
            return False
        
        # 기본 컨텍스트 데이터
        default_context = {
            'site_name': system_settings.site_name,
            'site_tagline': system_settings.site_tagline,
            'currency_symbol': system_settings.currency_symbol,
        }
        
        # 사용자 정의 컨텍스트 병합
        if context_data:
            default_context.update(context_data)
        
        # 템플릿 렌더링
        try:
            subject_template = Template(email_template.subject)
            body_template = Template(email_template.body)
            
            context = Context(default_context)
            subject = subject_template.render(context)
            body = body_template.render(context)
            
            # 이메일 발송
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            
            logger.info(f"Successfully sent {template_type} email to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send {template_type} email to {recipient_email}: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user):
        """회원가입 환영 이메일"""
        context_data = {
            'user_name': user.get_full_name() or user.username,
            'user_email': user.email,
            'welcome_points_enabled': SystemSettings.get_settings().welcome_points_enabled,
            'welcome_points_amount': SystemSettings.get_settings().welcome_points_amount,
        }
        
        return EmailService.send_templated_email(
            'welcome',
            user.email,
            context_data
        )
    
    @staticmethod
    def send_order_confirmation_email(order):
        """주문 확인 이메일"""
        order_items = []
        for item in order.items.all():
            order_items.append(f"- {item.product.name} x {item.quantity} = {item.total_price:,.0f}원")
        
        context_data = {
            'user_name': order.customer_name,
            'user_email': order.customer_email,
            'order_number': order.order_number,
            'order_date': order.order_date.strftime('%Y-%m-%d %H:%M'),
            'order_total': f"{order.total_amount:,.0f}",
            'order_items': '\n'.join(order_items),
        }
        
        return EmailService.send_templated_email(
            'order_confirm',
            order.customer_email,
            context_data
        )
    
    @staticmethod
    def send_order_shipped_email(order):
        """배송 시작 이메일"""
        context_data = {
            'user_name': order.customer_name,
            'user_email': order.customer_email,
            'order_number': order.order_number,
            'tracking_number': order.tracking_number,
            'courier': order.shipping_method or '택배사',
            'tracking_url': '#',  # 실제 배송 추적 URL로 변경 필요
        }
        
        return EmailService.send_templated_email(
            'order_shipped',
            order.customer_email,
            context_data
        )
    
    @staticmethod
    def send_low_stock_alert(products):
        """재고 부족 알림 이메일"""
        system_settings = SystemSettings.get_settings()
        
        for admin_email in settings.STOCK_ALERT_RECIPIENTS:
            for product in products:
                context_data = {
                    'product_name': product.name,
                    'product_sku': product.sku,
                    'current_stock': product.stock_quantity,
                    'threshold': system_settings.low_stock_threshold,
                }
                
                EmailService.send_templated_email(
                    'low_stock',
                    admin_email,
                    context_data
                )
    
    @staticmethod
    def send_order_cancelled_email(order):
        """주문 취소 이메일"""
        context_data = {
            'user_name': order.customer_name,
            'user_email': order.customer_email,
            'order_number': order.order_number,
            'order_total': f"{order.total_amount:,.0f}",
            'cancel_reason': order.cancel_reason or '고객 요청',
        }
        
        return EmailService.send_templated_email(
            'order_cancelled',
            order.customer_email,
            context_data
        )
    
    @staticmethod
    def send_point_earned_email(user, points):
        """포인트 적립 이메일"""
        context_data = {
            'user_name': user.name,
            'user_email': user.email,
            'point_amount': f"{points:,}",
            'point_balance': f"{user.points:,}",
        }
        
        return EmailService.send_templated_email(
            'point_earned',
            user.email,
            context_data
        )
    
    @staticmethod
    def send_coupon_issued_email(user, coupon):
        """쿠폰 발급 이메일"""
        context_data = {
            'user_name': user.name,
            'user_email': user.email,
            'coupon_code': coupon.code,
            'coupon_discount': f"{coupon.discount_value}{'%' if coupon.discount_type == 'percentage' else '원'}",
            'expire_date': coupon.expire_date.strftime('%Y-%m-%d'),
        }
        
        return EmailService.send_templated_email(
            'coupon_issued',
            user.email,
            context_data
        )