# reports/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class ReportTemplate(models.Model):
    """보고서 템플릿"""
    REPORT_TYPES = [
        ('INVENTORY', '재고 보고서'),
        ('SALES', '매출 보고서'),
        ('FINANCIAL', '재무 보고서'),
        ('PLATFORM', '플랫폼 보고서'),
        ('PRODUCT', '상품 보고서'),
        ('ORDER', '주문 보고서'),
        ('CUSTOM', '사용자 정의'),
    ]
    
    FREQUENCY_CHOICES = [
        ('DAILY', '일간'),
        ('WEEKLY', '주간'),
        ('MONTHLY', '월간'),
        ('QUARTERLY', '분기'),
        ('YEARLY', '연간'),
        ('ON_DEMAND', '수동'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='템플릿 이름', default='새 보고서 템플릿')
    description = models.TextField(blank=True, verbose_name='설명', default='보고서 템플릿에 대한 설명을 입력하세요.')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, verbose_name='보고서 유형', default='INVENTORY')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='ON_DEMAND', verbose_name='생성 주기')
    
    # 보고서 설정 (JSON)
    configuration = models.JSONField(default=dict, verbose_name='설정')
    
    # 권한 및 접근
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='생성자', blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name='활성 상태', blank=True, null=True)
    is_public = models.BooleanField(default=False, verbose_name='공개 여부', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일', blank=True, null=True)

    class Meta:
        verbose_name = '보고서 템플릿'
        verbose_name_plural = '보고서 템플릿'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"

class GeneratedReport(models.Model):
    """생성된 보고서"""
    STATUS_CHOICES = [
        ('PENDING', '대기중'),
        ('GENERATING', '생성중'),
        ('COMPLETED', '완료'),
        ('FAILED', '실패'),
        ('EXPIRED', '만료'),
    ]
    
    FORMAT_CHOICES = [
        ('HTML', 'HTML'),
        ('PDF', 'PDF'),
        ('EXCEL', 'Excel'),
        ('CSV', 'CSV'),
        ('JSON', 'JSON'),
    ]
    
    report_id = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name='보고서 ID')
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, verbose_name='템플릿', null=True, blank=True)
    title = models.CharField(max_length=200, verbose_name='제목', default='새 보고서')
    
    # 보고서 기간
    period_start = models.DateTimeField(verbose_name='시작일')
    period_end = models.DateTimeField(verbose_name='종료일')
    
    # 생성 정보
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name='상태')
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='HTML', verbose_name='형식')
    
    # 파일 정보
    file_path = models.CharField(max_length=500, blank=True, verbose_name='파일 경로')
    file_size = models.PositiveIntegerField(null=True, blank=True, verbose_name='파일 크기(bytes)')
    
    # 결과 데이터 (JSON)
    data = models.JSONField(default=dict, verbose_name='보고서 데이터')
    summary = models.JSONField(default=dict, verbose_name='요약 정보')
    
    # 생성 관련
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='생성자')
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='만료일')
    
    # 성능 메트릭
    generation_time = models.FloatField(null=True, blank=True, verbose_name='생성 시간(초)')
    row_count = models.PositiveIntegerField(null=True, blank=True, verbose_name='데이터 행 수')
    
    class Meta:
        verbose_name = '생성된 보고서'
        verbose_name_plural = '생성된 보고서'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['status', 'generated_at']),
            models.Index(fields=['template', 'period_start']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.generated_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def is_expired(self):
        """만료 여부 확인"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def get_file_url(self):
        """파일 다운로드 URL"""
        if self.file_path:
            return f"/reports/download/{self.report_id}/"
        return None

class ReportSchedule(models.Model):
    """보고서 스케줄"""
    SCHEDULE_TYPES = [
        ('CRON', 'Cron 표현식'),
        ('INTERVAL', '간격'),
        ('CALENDAR', '달력 기반'),
    ]
    
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, verbose_name='템플릿', null=True, blank=True)
    name = models.CharField(max_length=100, verbose_name='스케줄 이름', default='새 보고서 스케줄')
    
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPES, default='INTERVAL', verbose_name='스케줄 유형')
    cron_expression = models.CharField(max_length=100, blank=True, verbose_name='Cron 표현식')
    interval_days = models.PositiveIntegerField(null=True, blank=True, verbose_name='간격(일)')
    
    # 실행 시간
    next_run = models.DateTimeField(verbose_name='다음 실행일', default=timezone.now)
    last_run = models.DateTimeField(null=True, blank=True, verbose_name='마지막 실행일', default=timezone.now)
    
    # 수신자 정보
    email_recipients = models.JSONField(default=list, verbose_name='이메일 수신자')
    
    # 상태
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='생성자', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일', blank=True, null=True)

    class Meta:
        verbose_name = '보고서 스케줄'
        verbose_name_plural = '보고서 스케줄'
        ordering = ['next_run']
    
    def __str__(self):
        return f"{self.name} - {self.template.name}"

class ReportAccess(models.Model):
    """보고서 접근 로그"""
    report = models.ForeignKey(GeneratedReport, on_delete=models.CASCADE, verbose_name='보고서')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='사용자')
    
    ACTION_CHOICES = [
        ('VIEW', '조회'),
        ('DOWNLOAD', '다운로드'),
        ('SHARE', '공유'),
        ('DELETE', '삭제'),
    ]
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='액션')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP 주소')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    
    accessed_at = models.DateTimeField(auto_now_add=True, verbose_name='접근일')
    
    class Meta:
        verbose_name = '보고서 접근 로그'
        verbose_name_plural = '보고서 접근 로그'
        ordering = ['-accessed_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.report.title} ({self.action})"

class ReportBookmark(models.Model):
    """보고서 북마크"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='사용자')
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, verbose_name='템플릿', null=True, blank=True)
    
    name = models.CharField(max_length=100, blank=True, verbose_name='북마크 이름', default='새 북마크')
    configuration = models.JSONField(default=dict, verbose_name='설정')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    
    class Meta:
        verbose_name = '보고서 북마크'
        verbose_name_plural = '보고서 북마크'
        unique_together = ['user', 'template']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.name or self.template.name}"