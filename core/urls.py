from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # 시스템 설정
    path('settings/', views.system_settings_view, name='system_settings'),
    
    # 이메일 템플릿 관리
    path('email-templates/', views.EmailTemplateListView.as_view(), name='email_template_list'),
    path('email-templates/<str:template_type>/edit/', views.email_template_edit, name='email_template_edit'),
]