# reports/tasks.py
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from datetime import timedelta
import os
import logging

from .models import ReportSchedule, GeneratedReport
from .utils import ReportGenerator, ExportManager, ReportScheduler
from .models import ReportTemplate
import datetime

logger = logging.getLogger(__name__)

@shared_task
def generate_scheduled_reports():
    """스케줄된 보고서들을 확인하고 생성"""
    now = timezone.now()
    
    # 실행해야 할 스케줄들 조회
    due_schedules = ReportSchedule.objects.filter(
        is_active=True,
        next_run__lte=now
    )
    
    success_count = 0
    error_count = 0
    
    for schedule in due_schedules:
        try:
            result = ReportScheduler.send_scheduled_report(schedule.id)
            if result:
                success_count += 1
                logger.info(f"스케줄 보고서 생성 성공: {schedule.name}")
            else:
                error_count += 1
                logger.error(f"스케줄 보고서 생성 실패: {schedule.name}")
        except Exception as e:
            error_count += 1
            logger.error(f"스케줄 보고서 생성 중 오류: {schedule.name} - {str(e)}")
    
    return {
        'success_count': success_count,
        'error_count': error_count,
        'total_processed': due_schedules.count()
    }

@shared_task
def cleanup_expired_reports():
    """만료된 보고서 정리"""
    now = timezone.now()
    
    # 만료된 보고서들 조회
    expired_reports = GeneratedReport.objects.filter(
        expires_at__lt=now
    )
    
    deleted_count = 0
    file_deleted_count = 0
    
    for report in expired_reports:
        # 파일 삭제
        if report.file_path and os.path.exists(report.file_path):
            try:
                os.remove(report.file_path)
                file_deleted_count += 1
            except OSError as e:
                logger.warning(f"파일 삭제 실패: {report.file_path} - {str(e)}")
        
        # 데이터베이스에서 삭제
        report.delete()
        deleted_count += 1
    
    logger.info(f"만료된 보고서 정리 완료: {deleted_count}개 삭제, {file_deleted_count}개 파일 삭제")
    
    return {
        'deleted_reports': deleted_count,
        'deleted_files': file_deleted_count
    }

@shared_task
def generate_report_async(template_id, user_id, filters=None, format_type='excel'):
    """비동기 보고서 생성"""
    try:
        from django.contrib.auth.models import User
        from .models import ReportTemplate
        
        template = ReportTemplate.objects.get(id=template_id)
        user = User.objects.get(id=user_id)
        filters = filters or {}
        
        # 보고서 생성 레코드 생성
        report = GeneratedReport.objects.create(
            template=template,
            title=f"{template.name} - {timezone.now().strftime('%Y-%m-%d %H:%M')}",
            period_start=timezone.now() - timedelta(days=30),
            period_end=timezone.now(),
            status='GENERATING',
            format=format_type.upper(),
            generated_by=user
        )
        
        try:
            # 보고서 데이터 생성
            generator = ReportGenerator(user=user)
            
            if template.report_type == 'INVENTORY':
                report_data = generator.generate_inventory_report(filters)
            elif template.report_type == 'SALES':
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=30)
                report_data = generator.generate_sales_report(start_date, end_date, filters)
            elif template.report_type == 'FINANCIAL':
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=30)
                report_data = generator.generate_financial_report(start_date, end_date)
            else:
                raise ValueError(f"지원하지 않는 보고서 유형: {template.report_type}")
            
            # 파일 생성
            export_manager = ExportManager(report_data)
            file_content, filename = export_manager.to_excel()
            
            # 파일 저장
            reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            
            file_path = os.path.join(reports_dir, f"{report.report_id}_{filename}")
            with open(file_path, 'wb') as f:
                f.write(file_content.getvalue())
            
            # 보고서 정보 업데이트
            report.status = 'COMPLETED'
            report.file_path = file_path
            report.file_size = os.path.getsize(file_path)
            report.data = report_data
            report.row_count = len(report_data.get('products', []))
            report.generation_time = (timezone.now() - report.generated_at).total_seconds()
            report.save()
            
            logger.info(f"보고서 생성 성공: {report.title}")
            return {'success': True, 'report_id': str(report.report_id)}
            
        except Exception as e:
            # 오류 발생 시 상태 업데이트
            report.status = 'FAILED'
            report.save()
            logger.error(f"보고서 생성 실패: {report.title} - {str(e)}")
            raise
    
    except Exception as e:
        logger.error(f"비동기 보고서 생성 오류: {str(e)}")
        return {'success': False, 'error': str(e)}

@shared_task
def send_report_email(report_id, recipient_email, subject=None):
    """보고서 이메일 전송"""
    try:
        report = GeneratedReport.objects.get(report_id=report_id)
        
        if not subject:
            subject = f"[Shopuda ERP] {report.title}"
        
        # 이메일 템플릿 렌더링
        html_message = render_to_string('reports/email/report_email.html', {
            'report': report,
            'user': report.generated_by,
        })
        
        # 첨부파일 준비
        attachments = []
        if report.file_path and os.path.exists(report.file_path):
            with open(report.file_path, 'rb') as f:
                file_content = f.read()
                filename = os.path.basename(report.file_path)
                
                # MIME 타입 결정
                if filename.endswith('.xlsx'):
                    mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                elif filename.endswith('.csv'):
                    mime_type = 'text/csv'
                elif filename.endswith('.pdf'):
                    mime_type = 'application/pdf'
                else:
                    mime_type = 'application/octet-stream'
                
                attachments.append((filename, file_content, mime_type))
        
        # 이메일 발송
        send_mail(
            subject=subject,
            message='',
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            attachments=attachments,
            fail_silently=False,
        )
        
        logger.info(f"보고서 이메일 전송 성공: {report.title} -> {recipient_email}")
        return {'success': True}
        
    except Exception as e:
        logger.error(f"보고서 이메일 전송 실패: {str(e)}")
        return {'success': False, 'error': str(e)}

@shared_task
def generate_dashboard_cache():
    """대시보드 캐시 데이터 생성"""
    try:
        from .utils import get_report_summary_stats
        from django.core.cache import cache
        
        # 통계 데이터 생성
        stats = get_report_summary_stats()
        
        # 캐시에 저장 (1시간)
        cache.set('dashboard_stats', stats, 3600)
        
        logger.info("대시보드 캐시 데이터 생성 완료")
        return {'success': True, 'stats': stats}
        
    except Exception as e:
        logger.error(f"대시보드 캐시 생성 실패: {str(e)}")
        return {'success': False, 'error': str(e)}

@shared_task
def update_report_analytics():
    """보고서 분석 데이터 업데이트"""
    try:
        from django.db.models import Count, Avg
        from datetime import datetime
        
        now = timezone.now()
        today = now.date()
        
        # 일일 보고서 생성 통계
        daily_stats = GeneratedReport.objects.filter(
            generated_at__date=today
        ).aggregate(
            total_reports=Count('id'),
            avg_generation_time=Avg('generation_time')
        )
        
        # 가장 인기 있는 보고서 유형
        popular_types = GeneratedReport.objects.values(
            'template__report_type'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # 사용자별 보고서 생성 통계
        user_stats = GeneratedReport.objects.values(
            'generated_by__username'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        analytics_data = {
            'date': today.isoformat(),
            'daily_stats': daily_stats,
            'popular_types': list(popular_types),
            'user_stats': list(user_stats),
            'updated_at': now.isoformat()
        }
        
        # 캐시에 저장
        from django.core.cache import cache
        cache.set('report_analytics', analytics_data, 86400)  # 24시간
        
        logger.info("보고서 분석 데이터 업데이트 완료")
        return {'success': True, 'data': analytics_data}
        
    except Exception as e:
        logger.error(f"보고서 분석 데이터 업데이트 실패: {str(e)}")
        return {'success': False, 'error': str(e)}

@shared_task
def backup_report_data():
    """보고서 데이터 백업"""
    try:
        import json
        from django.core import serializers
        
        # 보고서 템플릿 백업
        templates = list(ReportTemplate.objects.filter(is_active=True))
        
        # 최근 30일 생성된 보고서 메타데이터 백업
        recent_reports = GeneratedReport.objects.filter(
            generated_at__gte=timezone.now() - timedelta(days=30)
        ).exclude(status='FAILED')
        
        backup_data = {
            'backup_date': timezone.now().isoformat(),
            'templates': serializers.serialize('json', templates),
            'reports_metadata': serializers.serialize('json', recent_reports),
        }
        
        # 백업 파일 저장
        backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups', 'reports')
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_filename = f"reports_backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        # 오래된 백업 파일 정리 (30일 이상)
        cutoff_date = timezone.now() - timedelta(days=30)
        for filename in os.listdir(backup_dir):
            file_path = os.path.join(backup_dir, filename)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if timezone.make_aware(file_time) < cutoff_date:
                    os.remove(file_path)
        
        logger.info(f"보고서 데이터 백업 완료: {backup_filename}")
        return {
            'success': True,
            'backup_file': backup_filename,
            'templates_count': len(templates),
            'reports_count': recent_reports.count()
        }
        
    except Exception as e:
        logger.error(f"보고서 데이터 백업 실패: {str(e)}")
        return {'success': False, 'error': str(e)}