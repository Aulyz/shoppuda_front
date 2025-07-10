# reports/signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import os

from .models import GeneratedReport, ReportSchedule, ReportAccess

@receiver(post_save, sender=GeneratedReport)
def generated_report_post_save(sender, instance, created, **kwargs):
    """생성된 보고서 저장 후 처리"""
    if created:
        # 새 보고서가 생성되었을 때
        
        # 만료일 설정 (기본 30일)
        if not instance.expires_at:
            instance.expires_at = timezone.now() + timezone.timedelta(days=30)
            instance.save(update_fields=['expires_at'])
        
        # 관리자에게 알림 (설정에 따라)
        if getattr(settings, 'REPORTS_NOTIFY_ADMIN', False):
            notify_admin_new_report(instance)
    
    elif instance.status == 'COMPLETED':
        # 보고서 생성이 완료되었을 때
        
        # 요청자에게 완료 알림
        if getattr(settings, 'REPORTS_NOTIFY_USER', True):
            notify_user_report_complete(instance)

@receiver(pre_delete, sender=GeneratedReport)
def generated_report_pre_delete(sender, instance, **kwargs):
    """생성된 보고서 삭제 전 처리"""
    # 파일 시스템에서 실제 파일 삭제
    if instance.file_path and os.path.exists(instance.file_path):
        try:
            os.remove(instance.file_path)
        except OSError:
            pass

@receiver(post_save, sender=ReportSchedule)
def report_schedule_post_save(sender, instance, created, **kwargs):
    """보고서 스케줄 저장 후 처리"""
    if created:
        # 새 스케줄이 생성되었을 때
        
        # 다음 실행일이 설정되지 않은 경우 기본값 설정
        if not instance.next_run:
            if instance.schedule_type == 'INTERVAL' and instance.interval_days:
                instance.next_run = timezone.now() + timezone.timedelta(days=instance.interval_days)
            else:
                instance.next_run = timezone.now() + timezone.timedelta(days=1)
            instance.save(update_fields=['next_run'])

def notify_admin_new_report(report):
    """관리자에게 새 보고서 생성 알림"""
    try:
        subject = f'[Shopuda ERP] 새 보고서 생성: {report.title}'
        message = f"""
        새로운 보고서가 생성되었습니다.
        
        보고서: {report.title}
        유형: {report.template.get_report_type_display()}
        생성자: {report.generated_by.username}
        생성일: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
        상태: {report.get_status_display()}
        
        관리자 페이지에서 확인하세요.
        """
        
        admin_emails = getattr(settings, 'REPORTS_ADMIN_EMAILS', [])
        if admin_emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=True,
            )
    except Exception:
        pass

def notify_user_report_complete(report):
    """사용자에게 보고서 완료 알림"""
    try:
        if report.generated_by.email:
            subject = f'[Shopuda ERP] 보고서 생성 완료: {report.title}'
            message = f"""
            안녕하세요, {report.generated_by.first_name or report.generated_by.username}님
            
            요청하신 보고서가 성공적으로 생성되었습니다.
            
            보고서: {report.title}
            생성일: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
            
            시스템에 로그인하여 보고서를 다운로드하실 수 있습니다.
            
            감사합니다.
            Shopuda ERP 시스템
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[report.generated_by.email],
                fail_silently=True,
            )
    except Exception:
        pass

# 보고서 접근 로그 자동 생성
def log_report_access(report, user, action, request=None):
    """보고서 접근 로그 생성"""
    try:
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        ReportAccess.objects.create(
            report=report,
            user=user,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception:
        pass