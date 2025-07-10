# File: platforms/forms.py
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML, Div
from .models import Platform

class PlatformForm(forms.ModelForm):
    class Meta:
        model = Platform
        fields = [
            'name', 'platform_type', 'api_key', 'api_secret', 
            'api_url', 'is_active'
        ]
        widgets = {
            'api_key': forms.PasswordInput(attrs={'class': 'form-control'}),
            'api_secret': forms.PasswordInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<h4>기본 정보</h4>'),
            Row(
                Column('name', css_class='form-group col-md-6'),
                Column('platform_type', css_class='form-group col-md-6'),
            ),
            Div(
                'is_active',
                css_class='form-check mt-2'
            ),
            
            HTML('<h4 class="mt-4">API 설정</h4>'),
            'api_url',
            Row(
                Column('api_key', css_class='form-group col-md-6'),
                Column('api_secret', css_class='form-group col-md-6'),
            ),
            
            Submit('submit', '저장', css_class='btn btn-primary'),
        )

class PlatformSyncForm(forms.Form):
    SYNC_CHOICES = [
        ('products', '상품 동기화'),
        ('orders', '주문 동기화'),
        ('all', '전체 동기화'),
    ]
    
    sync_type = forms.ChoiceField(
        choices=SYNC_CHOICES,
        widget=forms.RadioSelect(),
        label='동기화 유형'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'sync_type',
            Submit('submit', '동기화 시작', css_class='btn btn-primary'),
        )