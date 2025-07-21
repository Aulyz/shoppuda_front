# reports/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import json

from .models import ReportTemplate, ReportSchedule, ReportBookmark
from products.models import Category, Brand
from platforms.models import Platform

User = get_user_model()

class ReportFilterForm(forms.Form):
    """보고서 필터 폼"""
    
    # 공통 필터
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700'
        }),
        label='시작일'
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700'
        }),
        label='종료일'
    )
    
    # 상품 관련 필터
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="전체 카테고리",
        widget=forms.Select(attrs={
            'class': 'form-select rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700'
        }),
        label='카테고리'
    )
    
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all(),
        required=False,
        empty_label="전체 브랜드",
        widget=forms.Select(attrs={
            'class': 'form-select rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700'
        }),
        label='브랜드'
    )
    
    # 플랫폼 필터
    platform = forms.ModelChoiceField(
        queryset=Platform.objects.filter(is_active=True),
        required=False,
        empty_label="전체 플랫폼",
        widget=forms.Select(attrs={
            'class': 'form-select rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700'
        }),
        label='플랫폼'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError('시작일은 종료일보다 이전이어야 합니다.')
            
            if (end_date - start_date).days > 365:
                raise ValidationError('최대 1년까지만 조회할 수 있습니다.')
        
        return cleaned_data

class InventoryReportForm(ReportFilterForm):
    """재고 보고서 폼"""
    
    STOCK_STATUS_CHOICES = [
        ('', '전체'),
        ('normal', '정상'),
        ('low', '재고부족'),
        ('out', '품절'),
    ]
    
    stock_status = forms.ChoiceField(
        choices=STOCK_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700'
        }),
        label='재고 상태'
    )
    
    include_inactive = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox rounded text-blue-600'
        }),
        label='비활성 상품 포함'
    )

class SalesReportForm(ReportFilterForm):
    """매출 보고서 폼"""
    
    PERIOD_CHOICES = [
        ('7', '최근 7일'),
        ('30', '최근 30일'),
        ('90', '최근 90일'),
        ('365', '최근 1년'),
        ('custom', '사용자 정의'),
    ]
    
    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        initial='30',
        widget=forms.Select(attrs={
            'class': 'form-select rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700',
            'onchange': 'toggleCustomPeriod(this.value)'
        }),
        label='기간'
    )
    
    ORDER_STATUS_CHOICES = [
        ('', '전체'),
        ('PENDING', '대기중'),
        ('PROCESSING', '처리중'),
        ('SHIPPED', '배송중'),
        ('DELIVERED', '배송완료'),
        ('CANCELLED', '취소'),
        ('RETURNED', '반품'),
    ]
    
    order_status = forms.ChoiceField(
        choices=ORDER_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700'
        }),
        label='주문 상태'
    )
    
    include_tax = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox rounded text-blue-600'
        }),
        label='세금 포함'
    )

class ReportTemplateForm(forms.ModelForm):
    """보고서 템플릿 폼"""
    
    class Meta:
        model = ReportTemplate
        fields = [
            'name', 'description', 'report_type', 'frequency',
            'configuration', 'is_public'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700',
                'placeholder': '보고서 템플릿 이름을 입력하세요'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700',
                'rows': 3,
                'placeholder': '보고서 템플릿에 대한 설명을 입력하세요'
            }),
            'report_type': forms.Select(attrs={
                'class': 'form-select rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700'
            }),
            'frequency': forms.Select(attrs={
                'class': 'form-select rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700'
            }),
            'configuration': forms.Textarea(attrs={
                'class': 'form-textarea rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700',
                'rows': 5,
                'placeholder': 'JSON 형식의 설정을 입력하세요'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-checkbox rounded text-blue-600'
            }),
        }
        labels = {
            'name': '템플릿 이름',
            'description': '설명',
            'report_type': '보고서 유형',
            'frequency': '생성 주기',
            'configuration': '설정 (JSON)',
            'is_public': '공개 템플릿',
        }
    
    def clean_configuration(self):
        """설정 JSON 유효성 검사"""
        configuration = self.cleaned_data.get('configuration')
        if configuration:
            try:
                json.loads(configuration)
            except json.JSONDecodeError:
                raise ValidationError('올바른 JSON 형식이 아닙니다.')
        return configuration

class ReportScheduleForm(forms.ModelForm):
    """보고서 스케줄 폼"""
    
    email_recipients_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700',
            'rows': 3,
            'placeholder': '이메일 주소를 줄바꿈으로 구분하여 입력하세요\nexample1@example.com\nexample2@example.com'
        }),
        label='수신자 이메일',
        help_text='이메일 주소를 줄바꿈으로 구분하여 입력하세요'
    )
    
    class Meta:
        model = ReportSchedule
        fields = [
            'name', 'template', 'schedule_type', 'cron_expression',
            'interval_days', 'next_run', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700',
                'placeholder': '스케줄 이름을 입력하세요'
            }),
            'template': forms.Select(attrs={
                'class': 'form-select rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700'
            }),
            'schedule_type': forms.Select(attrs={
                'class': 'form-select rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700',
                'onchange': 'toggleScheduleFields(this.value)'
            }),
            'cron_expression': forms.TextInput(attrs={
                'class': 'form-input rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700',
                'placeholder': '예: 0 9 * * 1 (매주 월요일 9시)'
            }),
            'interval_days': forms.NumberInput(attrs={
                'class': 'form-input rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700',
                'min': 1,
                'max': 365
            }),
            'next_run': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-input rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox rounded text-blue-600'
            }),
        }
        labels = {
            'name': '스케줄 이름',
            'template': '보고서 템플릿',
            'schedule_type': '스케줄 유형',
            'cron_expression': 'Cron 표현식',
            'interval_days': '간격 (일)',
            'next_run': '다음 실행일',
            'is_active': '활성 상태',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 사용자가 접근 가능한 템플릿만 표시
        if user:
            self.fields['template'].queryset = ReportTemplate.objects.filter(
                Q(created_by=user) | Q(is_public=True),
                is_active=True
            )
        
        # 기존 인스턴스가 있는 경우 이메일 목록을 텍스트로 변환
        if self.instance and self.instance.pk:
            email_list = self.instance.email_recipients or []
            self.fields['email_recipients_text'].initial = '\n'.join(email_list)
    
    def clean_email_recipients_text(self):
        """이메일 수신자 유효성 검사"""
        email_text = self.cleaned_data.get('email_recipients_text')
        if email_text:
            emails = [email.strip() for email in email_text.split('\n') if email.strip()]
            
            # 이메일 형식 검증
            from django.core.validators import validate_email
            for email in emails:
                try:
                    validate_email(email)
                except ValidationError:
                    raise ValidationError(f'올바르지 않은 이메일 형식: {email}')
            
            return emails
        return []
    
    def clean_cron_expression(self):
        """Cron 표현식 유효성 검사"""
        cron_expression = self.cleaned_data.get('cron_expression')
        schedule_type = self.cleaned_data.get('schedule_type')
        
        if schedule_type == 'CRON' and not cron_expression:
            raise ValidationError('Cron 스케줄 유형에는 Cron 표현식이 필요합니다.')
        
        # 기본적인 Cron 표현식 검증 (5개 필드)
        if cron_expression:
            parts = cron_expression.split()
            if len(parts) != 5:
                raise ValidationError('Cron 표현식은 5개의 필드를 가져야 합니다. (분 시 일 월 요일)')
        
        return cron_expression
    
    def clean_interval_days(self):
        """간격 일수 유효성 검사"""
        interval_days = self.cleaned_data.get('interval_days')
        schedule_type = self.cleaned_data.get('schedule_type')
        
        if schedule_type == 'INTERVAL' and not interval_days:
            raise ValidationError('간격 스케줄 유형에는 간격 일수가 필요합니다.')
        
        return interval_days
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # 이메일 수신자 목록 저장
        email_recipients = self.cleaned_data.get('email_recipients_text', [])
        instance.email_recipients = email_recipients
        
        if commit:
            instance.save()
        return instance

class ReportBookmarkForm(forms.ModelForm):
    """보고서 북마크 폼"""
    
    class Meta:
        model = ReportBookmark
        fields = ['name', 'template', 'configuration']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700',
                'placeholder': '북마크 이름 (선택사항)'
            }),
            'template': forms.Select(attrs={
                'class': 'form-select rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700'
            }),
            'configuration': forms.Textarea(attrs={
                'class': 'form-textarea rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700',
                'rows': 4,
                'placeholder': 'JSON 형식의 북마크 설정 (선택사항)'
            }),
        }
        labels = {
            'name': '북마크 이름',
            'template': '보고서 템플릿',
            'configuration': '설정 (JSON)',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 사용자가 접근 가능한 템플릿만 표시
        if user:
            self.fields['template'].queryset = ReportTemplate.objects.filter(
                Q(created_by=user) | Q(is_public=True),
                is_active=True
            )

class QuickReportForm(forms.Form):
    """빠른 보고서 생성 폼"""
    
    REPORT_TYPE_CHOICES = [
        ('inventory', '재고 현황'),
        ('sales_daily', '일일 매출'),
        ('sales_weekly', '주간 매출'),
        ('sales_monthly', '월간 매출'),
        ('low_stock', '재고부족 상품'),
        ('top_products', '인기 상품'),
    ]
    
    FORMAT_CHOICES = [
        ('excel', 'Excel (.xlsx)'),
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700'
        }),
        label='보고서 유형'
    )
    
    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        initial='excel',
        widget=forms.Select(attrs={
            'class': 'form-select rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700'
        }),
        label='파일 형식'
    )
    
    email_send = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox rounded text-blue-600'
        }),
        label='이메일로 전송'
    )
    
    email_address = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-input rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700',
            'placeholder': '이메일 주소를 입력하세요'
        }),
        label='이메일 주소'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        email_send = cleaned_data.get('email_send')
        email_address = cleaned_data.get('email_address')
        
        if email_send and not email_address:
            raise ValidationError('이메일 전송을 선택한 경우 이메일 주소가 필요합니다.')
        
        return cleaned_data

class AdvancedFilterForm(forms.Form):
    """고급 필터 폼"""
    
    # 날짜 범위
    date_range_type = forms.ChoiceField(
        choices=[
            ('preset', '미리 설정된 기간'),
            ('custom', '사용자 정의 기간'),
        ],
        initial='preset',
        widget=forms.RadioSelect(attrs={
            'class': 'form-radio text-blue-600',
            'onchange': 'toggleDateRange(this.value)'
        }),
        label='날짜 범위 유형'
    )
    
    preset_range = forms.ChoiceField(
        choices=[
            ('today', '오늘'),
            ('yesterday', '어제'),
            ('this_week', '이번 주'),
            ('last_week', '지난 주'),
            ('this_month', '이번 달'),
            ('last_month', '지난 달'),
            ('this_quarter', '이번 분기'),
            ('last_quarter', '지난 분기'),
            ('this_year', '올해'),
            ('last_year', '작년'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700'
        }),
        label='미리 설정된 기간'
    )
    
    # 금액 범위
    min_amount = forms.DecimalField(
        required=False,
        decimal_places=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700',
            'placeholder': '최소 금액'
        }),
        label='최소 금액'
    )
    
    max_amount = forms.DecimalField(
        required=False,
        decimal_places=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700',
            'placeholder': '최대 금액'
        }),
        label='최대 금액'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        min_amount = cleaned_data.get('min_amount')
        max_amount = cleaned_data.get('max_amount')
        
        if min_amount and max_amount and min_amount > max_amount:
            raise ValidationError('최소 금액은 최대 금액보다 작아야 합니다.')
        
        return cleaned_data