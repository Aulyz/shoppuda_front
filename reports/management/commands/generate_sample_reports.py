# reports/management/commands/generate_sample_reports.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import json

from reports.models import ReportTemplate, ReportSchedule


class Command(BaseCommand):
    help = '샘플 보고서 템플릿과 스케줄을 생성합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='보고서를 생성할 사용자명 (기본: admin)',
            default='admin'
        )

    def handle(self, *args, **options):
        username = options['user']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'사용자 "{username}"을 찾을 수 없습니다.')
            )
            return

        # 샘플 보고서 템플릿들
        templates_data = [
            {
                'name': '일일 재고 현황',
                'description': '매일 오전 9시에 생성되는 재고 현황 보고서',
                'report_type': 'INVENTORY',
                'frequency': 'DAILY',
                'configuration': {
                    'include_low_stock': True,
                    'include_out_of_stock': True,
                    'group_by_category': True,
                    'show_trend': False
                },
                'is_public': True
            },
            {
                'name': '주간 매출 분석',
                'description': '매주 월요일에 생성되는 주간 매출 분석 보고서',
                'report_type': 'SALES',
                'frequency': 'WEEKLY',
                'configuration': {
                    'period_days': 7,
                    'include_charts': True,
                    'group_by_platform': True,
                    'top_products_count': 10
                },
                'is_public': True
            },
            {
                'name': '월간 재무 보고서',
                'description': '매월 1일에 생성되는 종합 재무 보고서',
                'report_type': 'FINANCIAL',
                'frequency': 'MONTHLY',
                'configuration': {
                    'include_profit_loss': True,
                    'include_inventory_value': True,
                    'compare_previous_period': True,
                    'include_forecasting': False
                },
                'is_public': False
            },
            {
                'name': '플랫폼별 성과 분석',
                'description': '플랫폼별 판매 성과 및 수수료 분석',
                'report_type': 'PLATFORM',
                'frequency': 'WEEKLY',
                'configuration': {
                    'include_commission_analysis': True,
                    'include_conversion_rates': True,
                    'compare_platforms': True
                },
                'is_public': True
            },
            {
                'name': '상품 성과 분석',
                'description': '상품별 판매량, 수익성 분석 보고서',
                'report_type': 'PRODUCT',
                'frequency': 'MONTHLY',
                'configuration': {
                    'min_sales_threshold': 1,
                    'include_profit_margin': True,
                    'include_category_analysis': True,
                    'top_performers_count': 20
                },
                'is_public': True
            },
            {
                'name': '주문 처리 현황',
                'description': '주문 처리 상태별 현황 및 배송 분석',
                'report_type': 'ORDER',
                'frequency': 'DAILY',
                'configuration': {
                    'include_pending_orders': True,
                    'include_shipping_analysis': True,
                    'include_return_analysis': True
                },
                'is_public': True
            },
            {
                'name': '재고 부족 알림',
                'description': '재고가 부족한 상품들의 긴급 보고서',
                'report_type': 'INVENTORY',
                'frequency': 'DAILY',
                'configuration': {
                    'only_low_stock': True,
                    'urgency_threshold': 5,
                    'include_reorder_suggestions': True
                },
                'is_public': False
            },
            {
                'name': '고객 분석 보고서',
                'description': '고객 구매 패턴 및 충성도 분석',
                'report_type': 'CUSTOM',
                'frequency': 'MONTHLY',
                'configuration': {
                    'analyze_repeat_customers': True,
                    'include_demographics': False,
                    'segment_by_purchase_value': True
                },
                'is_public': False
            }
        ]

        created_templates = []
        
        for template_data in templates_data:
            template, created = ReportTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    'description': template_data['description'],
                    'report_type': template_data['report_type'],
                    'frequency': template_data['frequency'],
                    'configuration': template_data['configuration'],
                    'is_public': template_data['is_public'],
                    'created_by': user,
                }
            )
            
            if created:
                created_templates.append(template)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 템플릿 생성: {template.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ 템플릿 이미 존재: {template.name}')
                )

        # 샘플 스케줄 생성
        schedules_data = [
            {
                'template_name': '일일 재고 현황',
                'name': '매일 오전 9시 재고 현황',
                'schedule_type': 'CRON',
                'cron_expression': '0 9 * * *',  # 매일 오전 9시
                'email_recipients': ['manager@shopuda.com', 'warehouse@shopuda.com']
            },
            {
                'template_name': '주간 매출 분석',
                'name': '매주 월요일 매출 분석',
                'schedule_type': 'CRON',
                'cron_expression': '0 10 * * 1',  # 매주 월요일 오전 10시
                'email_recipients': ['sales@shopuda.com', 'ceo@shopuda.com']
            },
            {
                'template_name': '월간 재무 보고서',
                'name': '매월 1일 재무 보고서',
                'schedule_type': 'CRON',
                'cron_expression': '0 8 1 * *',  # 매월 1일 오전 8시
                'email_recipients': ['finance@shopuda.com', 'ceo@shopuda.com']
            },
            {
                'template_name': '재고 부족 알림',
                'name': '매일 재고 부족 확인',
                'schedule_type': 'INTERVAL',
                'interval_days': 1,
                'email_recipients': ['warehouse@shopuda.com']
            }
        ]

        created_schedules = []
        
        for schedule_data in schedules_data:
            try:
                template = ReportTemplate.objects.get(
                    name=schedule_data['template_name']
                )
                
                # 다음 실행일 계산
                next_run = timezone.now() + timedelta(hours=1)
                
                schedule, created = ReportSchedule.objects.get_or_create(
                    name=schedule_data['name'],
                    defaults={
                        'template': template,
                        'schedule_type': schedule_data['schedule_type'],
                        'cron_expression': schedule_data.get('cron_expression', ''),
                        'interval_days': schedule_data.get('interval_days'),
                        'next_run': next_run,
                        'email_recipients': schedule_data['email_recipients'],
                        'created_by': user,
                        'is_active': False  # 기본적으로 비활성화
                    }
                )
                
                if created:
                    created_schedules.append(schedule)
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ 스케줄 생성: {schedule.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠ 스케줄 이미 존재: {schedule.name}')
                    )
                    
            except ReportTemplate.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'✗ 템플릿을 찾을 수 없음: {schedule_data["template_name"]}')
                )

        # 결과 요약
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('샘플 데이터 생성 완료!'))
        self.stdout.write(f'생성된 템플릿: {len(created_templates)}개')
        self.stdout.write(f'생성된 스케줄: {len(created_schedules)}개')
        
        if created_schedules:
            self.stdout.write('\n' + self.style.WARNING('주의사항:'))
            self.stdout.write('- 생성된 스케줄들은 기본적으로 비활성화되어 있습니다.')
            self.stdout.write('- 관리자 페이지에서 스케줄을 활성화하고 이메일 주소를 확인하세요.')
            self.stdout.write('- Celery가 실행 중이어야 스케줄이 동작합니다.')
        
        # 샘플 보고서 북마크 생성
        self.create_sample_bookmarks(user)
        
        self.stdout.write('\n' + self.style.SUCCESS('모든 샘플 데이터 생성이 완료되었습니다!'))

    def create_sample_bookmarks(self, user):
        """샘플 북마크 생성"""
        from reports.models import ReportBookmark
        
        bookmarks_data = [
            {
                'template_name': '일일 재고 현황',
                'name': '긴급 재고 확인',
                'configuration': {
                    'only_critical': True,
                    'threshold': 3
                }
            },
            {
                'template_name': '주간 매출 분석',
                'name': '주요 플랫폼 매출',
                'configuration': {
                    'platforms': ['네이버', '쿠팡', '지마켓']
                }
            }
        ]
        
        created_bookmarks = 0
        
        for bookmark_data in bookmarks_data:
            try:
                template = ReportTemplate.objects.get(
                    name=bookmark_data['template_name']
                )
                
                bookmark, created = ReportBookmark.objects.get_or_create(
                    user=user,
                    template=template,
                    defaults={
                        'name': bookmark_data['name'],
                        'configuration': bookmark_data['configuration']
                    }
                )
                
                if created:
                    created_bookmarks += 1
                    
            except ReportTemplate.DoesNotExist:
                pass
        
        if created_bookmarks > 0:
            self.stdout.write(f'생성된 북마크: {created_bookmarks}개')