from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import View, ListView
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from accounts.permissions import admin_level_required, permission_required
from .models import SystemSettings, EmailTemplate
from .forms import SystemSettingsForm, EmailTemplateForm


@login_required
@admin_level_required(4)
def system_settings_view(request):
    """시스템 설정 뷰"""
    settings = SystemSettings.get_settings()
    active_tab = request.GET.get('tab', 'brand')
    
    if request.method == 'POST':
        # 현재 탭 정보를 POST에서도 가져오기
        active_tab = request.POST.get('active_tab', 'brand')
        form = SystemSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            settings = form.save(commit=False)
            settings.updated_by = request.user
            settings.save()
            messages.success(request, '시스템 설정이 저장되었습니다.')
            return redirect(f"{reverse_lazy('core:system_settings')}?tab={active_tab}")
        else:
            # 폼 에러 디버깅
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = SystemSettingsForm(instance=settings)
    
    context = {
        'form': form,
        'settings': settings,
        'active_tab': active_tab
    }
    return render(request, 'core/system_settings.html', context)


@method_decorator(login_required, name='dispatch')
@method_decorator(admin_level_required(4), name='dispatch')
class EmailTemplateListView(ListView):
    """이메일 템플릿 목록"""
    model = EmailTemplate
    template_name = 'core/email_template_list.html'
    context_object_name = 'templates'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 검색 기능
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(subject__icontains=search) | 
                Q(body__icontains=search)
            )
        
        # 타입 필터
        template_type = self.request.GET.get('template_type')
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        
        # 활성 상태 필터
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('template_type')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['template_types'] = EmailTemplate.TEMPLATE_TYPES
        return context


@login_required
@admin_level_required(4)
def email_template_edit(request, template_type):
    """이메일 템플릿 편집"""
    template, created = EmailTemplate.objects.get_or_create(
        template_type=template_type,
        defaults={
            'subject': _get_default_subject(template_type),
            'body': _get_default_body(template_type)
        }
    )
    
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, f'이메일 템플릿이 저장되었습니다.')
            return redirect('core:email_template_list')
    else:
        form = EmailTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
        'template_type_display': dict(EmailTemplate.TEMPLATE_TYPES).get(template_type),
        'available_variables': _get_available_variables(template_type)
    }
    return render(request, 'core/email_template_edit.html', context)


def _get_default_subject(template_type):
    """기본 이메일 제목"""
    defaults = {
        'welcome': '[{{site_name}}] 회원가입을 환영합니다!',
        'order_confirm': '[{{site_name}}] 주문이 확인되었습니다 - {{order_number}}',
        'order_shipped': '[{{site_name}}] 상품이 발송되었습니다 - {{order_number}}',
        'order_delivered': '[{{site_name}}] 상품이 배송완료되었습니다 - {{order_number}}',
        'password_reset': '[{{site_name}}] 비밀번호 재설정 안내',
        'point_earned': '[{{site_name}}] 포인트가 적립되었습니다',
        'point_expired': '[{{site_name}}] 포인트 만료 예정 안내',
        'low_stock': '[{{site_name}}] 재고 부족 알림',
    }
    return defaults.get(template_type, '')


def _get_default_body(template_type):
    """기본 이메일 본문"""
    defaults = {
        'welcome': '''안녕하세요 {{user_name}}님,

{{site_name}}에 가입해주셔서 감사합니다!

{% if welcome_points_enabled %}
회원가입 축하 포인트 {{welcome_points_amount}}P가 지급되었습니다.
{% endif %}

즐거운 쇼핑 되세요!

감사합니다.
{{site_name}} 드림''',
        
        'order_confirm': '''안녕하세요 {{user_name}}님,

주문이 정상적으로 접수되었습니다.

주문번호: {{order_number}}
주문일시: {{order_date}}
결제금액: {{order_total}}

주문하신 상품:
{{order_items}}

배송 준비가 완료되면 다시 안내드리겠습니다.

감사합니다.
{{site_name}} 드림''',
        
        'order_shipped': '''안녕하세요 {{user_name}}님,

주문하신 상품이 발송되었습니다.

주문번호: {{order_number}}
송장번호: {{tracking_number}}
택배사: {{courier}}

배송 추적: {{tracking_url}}

감사합니다.
{{site_name}} 드림''',
    }
    return defaults.get(template_type, '')


def _get_available_variables(template_type):
    """템플릿 타입별 사용 가능한 변수"""
    common_vars = ['{{site_name}}', '{{user_name}}', '{{user_email}}']
    
    type_specific_vars = {
        'welcome': ['{{welcome_points_amount}}', '{{welcome_points_enabled}}'],
        'order_confirm': ['{{order_number}}', '{{order_date}}', '{{order_total}}', '{{order_items}}'],
        'order_shipped': ['{{order_number}}', '{{tracking_number}}', '{{courier}}', '{{tracking_url}}'],
        'order_delivered': ['{{order_number}}', '{{delivery_date}}'],
        'password_reset': ['{{reset_link}}', '{{reset_token}}'],
        'point_earned': ['{{point_amount}}', '{{point_reason}}', '{{point_balance}}'],
        'point_expired': ['{{point_amount}}', '{{expire_date}}', '{{point_balance}}'],
        'low_stock': ['{{product_name}}', '{{product_sku}}', '{{current_stock}}', '{{threshold}}'],
    }
    
    return common_vars + type_specific_vars.get(template_type, [])