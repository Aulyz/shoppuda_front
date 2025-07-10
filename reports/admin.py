# reports/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db.models import Count, Sum

from .models import (
    ReportTemplate, GeneratedReport, ReportSchedule, 
    ReportAccess, ReportBookmark
)

@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'report_type_badge', 'frequency_badge', 
        'is_active_status', 'created_by', 'created_at'
    ]
    list_filter = ['report_type', 'frequency', 'is_active', 'is_public', 'created_at']
    search_fields = ['name', 'description', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'description', 'report_type', 'frequency')
        }),
        ('설정', {
            'fields': ('configuration',),
            'classes': ('collapse',)
        }),
        ('권한', {
            'fields': ('created_by', 'is_active', 'is_public')
        }),
        ('시간 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def report_type_badge(self, obj):
        """보고서 유형 배지"""
        colors = {
            'INVENTORY': '#10B981',
            'SALES': '#3B82F6', 
            'FINANCIAL': '#8B5CF6',
            'PLATFORM': '#F59E0B',
            'PRODUCT': '#EF4444',
            'ORDER': '#06B6D4',
            'CUSTOM': '#6B7280',
        }
        color = colors.get(obj.report_type, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_report_type_display()
        )
    report_type_badge.short_description = '보고서 유형'
    
    def frequency_badge(self, obj):
        """생성 주기 배지"""
        colors = {
            'DAILY': '#059669',
            'WEEKLY': '#0369A1',
            'MONTHLY': '#7C2D12',
            'QUARTERLY': '#581C87',
            'YEARLY': '#BE123C',
            'ON_DEMAND': '#6B7280',
        }
        color = colors.get(obj.frequency, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 8px; font-size: 10px;">{}</span>',
            color, obj.get_frequency_display()
        )
    frequency_badge.short_description = '생성 주기'
    
    def is_active_status(self, obj):
        """활성 상태 표시"""
        if obj.is_active:
            return format_html(
                '<span style="color: #059669; font-weight: bold;">●</span> 활성'
            )
        else:
            return format_html(
                '<span style="color: #DC2626; font-weight: bold;">●</span> 비활성'
            )
    is_active_status.short_description = '상태'

@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'template_link', 'status_badge', 'format',
        'file_size_display', 'generated_by', 'generated_at'
    ]
    list_filter = ['status', 'format', 'template__report_type', 'generated_at']
    search_fields = ['title', 'template__name', 'generated_by__username']
    readonly_fields = [
        'report_id', 'generated_at', 'generation_time', 
        'row_count', 'file_size'
    ]
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        ('보고서 정보', {
            'fields': ('report_id', 'template', 'title', 'status', 'format')
        }),
        ('기간', {
            'fields': ('period_start', 'period_end')
        }),
        ('파일 정보', {
            'fields': ('file_path', 'file_size', 'expires_at')
        }),
        ('데이터 정보', {
            'fields': ('data', 'summary'),
            'classes': ('collapse',)
        }),
        ('생성 정보', {
            'fields': ('generated_by', 'generated_at', 'generation_time', 'row_count')
        }),
    )
    
    actions = ['mark_as_expired', 'regenerate_reports']
    
    def template_link(self, obj):
        """템플릿 링크"""
        url = reverse('admin:reports_reporttemplate_change', args=[obj.template.pk])
        return format_html('<a href="{}">{}</a>', url, obj.template.name)
    template_link.short_description = '템플릿'
    
    def status_badge(self, obj):
        """상태 배지"""
        colors = {
            'PENDING': '#F59E0B',
            'GENERATING': '#3B82F6',
            'COMPLETED': '#10B981',
            'FAILED': '#EF4444',
            'EXPIRED': '#6B7280',
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = '상태'
    
    def file_size_display(self, obj):
        """파일 크기 표시"""
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "-"
    file_size_display.short_description = '파일 크기'
    
    def mark_as_expired(self, request, queryset):
        """선택된 보고서를 만료로 표시"""
        updated = queryset.update(status='EXPIRED')
        self.message_user(
            request, f"{updated}개의 보고서가 만료로 표시되었습니다.",
            messages.SUCCESS
        )
    mark_as_expired.short_description = "선택된 보고서를 만료로 표시"
    
    def regenerate_reports(self, request, queryset):
        """선택된 보고서 재생성"""
        # 실제 구현에서는 비동기 작업으로 처리
        for report in queryset:
            report.status = 'PENDING'
            report.save()
        
        self.message_user(
            request, f"{queryset.count()}개의 보고서 재생성을 요청했습니다.",
            messages.SUCCESS
        )
    regenerate_reports.short_description = "선택된 보고서 재생성"

@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'template_link', 'schedule_type', 'next_run',
        'last_run', 'is_active_status', 'created_by'
    ]
    list_filter = ['schedule_type', 'is_active', 'created_at']
    search_fields = ['name', 'template__name', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at', 'last_run']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'template', 'is_active')
        }),
        ('스케줄 설정', {
            'fields': ('schedule_type', 'cron_expression', 'interval_days')
        }),
        ('실행 정보', {
            'fields': ('next_run', 'last_run')
        }),
        ('수신자', {
            'fields': ('email_recipients',)
        }),
        ('시간 정보', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['run_now', 'activate_schedules', 'deactivate_schedules']
    
    def template_link(self, obj):
        """템플릿 링크"""
        url = reverse('admin:reports_reporttemplate_change', args=[obj.template.pk])
        return format_html('<a href="{}">{}</a>', url, obj.template.name)
    template_link.short_description = '템플릿'
    
    def is_active_status(self, obj):
        """활성 상태 표시"""
        if obj.is_active:
            return format_html(
                '<span style="color: #059669; font-weight: bold;">●</span> 활성'
            )
        else:
            return format_html(
                '<span style="color: #DC2626; font-weight: bold;">●</span> 비활성'
            )
    is_active_status.short_description = '상태'
    
    def run_now(self, request, queryset):
        """선택된 스케줄 즉시 실행"""
        from .utils import ReportScheduler
        
        success_count = 0
        for schedule in queryset.filter(is_active=True):
            if ReportScheduler.send_scheduled_report(schedule.id):
                success_count += 1
        
        self.message_user(
            request, f"{success_count}개의 스케줄이 성공적으로 실행되었습니다.",
            messages.SUCCESS
        )
    run_now.short_description = "선택된 스케줄 즉시 실행"
    
    def activate_schedules(self, request, queryset):
        """선택된 스케줄 활성화"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, f"{updated}개의 스케줄이 활성화되었습니다.",
            messages.SUCCESS
        )
    activate_schedules.short_description = "선택된 스케줄 활성화"
    
    def deactivate_schedules(self, request, queryset):
        """선택된 스케줄 비활성화"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, f"{updated}개의 스케줄이 비활성화되었습니다.",
            messages.SUCCESS
        )
    deactivate_schedules.short_description = "선택된 스케줄 비활성화"

@admin.register(ReportAccess)
class ReportAccessAdmin(admin.ModelAdmin):
    list_display = [
        'report_title', 'user', 'action_badge', 
        'ip_address', 'accessed_at'
    ]
    list_filter = ['action', 'accessed_at']
    search_fields = [
        'report__title', 'user__username', 
        'ip_address', 'user_agent'
    ]
    readonly_fields = ['accessed_at']
    date_hierarchy = 'accessed_at'
    
    def report_title(self, obj):
        """보고서 제목"""
        return obj.report.title
    report_title.short_description = '보고서'
    
    def action_badge(self, obj):
        """액션 배지"""
        colors = {
            'VIEW': '#3B82F6',
            'DOWNLOAD': '#10B981',
            'SHARE': '#F59E0B',
            'DELETE': '#EF4444',
        }
        color = colors.get(obj.action, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 8px; font-size: 10px; font-weight: bold;">{}</span>',
            color, obj.get_action_display()
        )
    action_badge.short_description = '액션'
    
    def has_add_permission(self, request):
        """추가 권한 제거 (시스템에서 자동 생성)"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """수정 권한 제거 (로그는 수정 불가)"""
        return False

@admin.register(ReportBookmark)
class ReportBookmarkAdmin(admin.ModelAdmin):
    list_display = [
        'bookmark_name', 'user', 'template_link', 'created_at'
    ]
    list_filter = ['template__report_type', 'created_at']
    search_fields = ['name', 'user__username', 'template__name']
    readonly_fields = ['created_at']
    
    def bookmark_name(self, obj):
        """북마크 이름"""
        return obj.name or obj.template.name
    bookmark_name.short_description = '북마크 이름'
    
    def template_link(self, obj):
        """템플릿 링크"""
        url = reverse('admin:reports_reporttemplate_change', args=[obj.template.pk])
        return format_html('<a href="{}">{}</a>', url, obj.template.name)
    template_link.short_description = '템플릿'

# 커스텀 관리 뷰
class ReportSummaryAdmin(admin.ModelAdmin):
    """보고서 요약 관리 뷰"""
    
    def changelist_view(self, request, extra_context=None):
        """관리자 목록 뷰 오버라이드"""
        
        # 보고서 통계
        total_templates = ReportTemplate.objects.filter(is_active=True).count()
        total_generated = GeneratedReport.objects.count()
        total_schedules = ReportSchedule.objects.filter(is_active=True).count()
        
        # 최근 7일간 생성된 보고서
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        recent_reports = GeneratedReport.objects.filter(
            generated_at__gte=week_ago
        ).count()
        
        # 보고서 유형별 통계
        template_stats = ReportTemplate.objects.values('report_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 사용자별 보고서 생성 통계
        user_stats = GeneratedReport.objects.values(
            'generated_by__username'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # 월별 보고서 생성 추이
        monthly_stats = GeneratedReport.objects.extra(
            select={'month': "DATE_FORMAT(generated_at, '%%Y-%%m')"}
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        extra_context = extra_context or {}
        extra_context.update({
            'total_templates': total_templates,
            'total_generated': total_generated,
            'total_schedules': total_schedules,
            'recent_reports': recent_reports,
            'template_stats': template_stats,
            'user_stats': user_stats,
            'monthly_stats': monthly_stats,
        })
        
        return super().changelist_view(request, extra_context)

# 관리자 사이트 커스터마이징
admin.site.site_header = "Shopuda ERP 보고서 관리"
admin.site.site_title = "보고서 관리"
admin.site.index_title = "보고서 시스템 관리"

# 추가 관리 기능들
def cleanup_expired_reports():
    """만료된 보고서 정리"""
    from django.core.management.base import BaseCommand
    import os
    
    expired_reports = GeneratedReport.objects.filter(
        expires_at__lt=timezone.now()
    )
    
    deleted_count = 0
    for report in expired_reports:
        if report.file_path and os.path.exists(report.file_path):
            try:
                os.remove(report.file_path)
                deleted_count += 1
            except OSError:
                pass
        report.delete()
    
    return deleted_count

def get_report_usage_stats():
    """보고서 사용 통계"""
    stats = {
        'total_reports': GeneratedReport.objects.count(),
        'total_downloads': ReportAccess.objects.filter(action='DOWNLOAD').count(),
        'active_templates': ReportTemplate.objects.filter(is_active=True).count(),
        'scheduled_reports': ReportSchedule.objects.filter(is_active=True).count(),
    }
    
    # 가장 인기 있는 보고서 유형
    popular_types = ReportTemplate.objects.values('report_type').annotate(
        usage_count=Count('generatedreport')
    ).order_by('-usage_count')
    
    stats['popular_types'] = list(popular_types)
    
    return stats