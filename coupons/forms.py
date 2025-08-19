from django import forms
from django.utils import timezone
from .models import Coupon, UserCoupon
from accounts.models import User
from products.models import Category, Product


class CouponForm(forms.ModelForm):
    """쿠폰 생성/수정 폼"""
    
    class Meta:
        model = Coupon
        fields = [
            'code', 'name', 'description',
            'discount_type', 'discount_value', 'max_discount_amount',
            'min_order_amount', 'exclude_sale_items',
            'issue_type', 'total_quantity',
            'usage_limit_total', 'usage_limit_per_user',
            'valid_from', 'valid_to', 'days_valid_after_issue',
            'applicable_categories', 'applicable_products',
            'target_membership_levels', 'target_users',
            'is_active', 'is_stackable'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': '비워두면 자동 생성됩니다'
            }),
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 3
            }),
            'discount_type': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'discount_value': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'step': '0.01'
            }),
            'max_discount_amount': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'step': '0.01'
            }),
            'min_order_amount': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'step': '0.01'
            }),
            'issue_type': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'total_quantity': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'usage_limit_total': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'usage_limit_per_user': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'valid_from': forms.DateTimeInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'type': 'datetime-local'
            }),
            'valid_to': forms.DateTimeInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'type': 'datetime-local'
            }),
            'days_valid_after_issue': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'applicable_categories': forms.SelectMultiple(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 select2',
                'multiple': 'multiple'
            }),
            'applicable_products': forms.SelectMultiple(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 select2',
                'multiple': 'multiple'
            }),
            'target_users': forms.SelectMultiple(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 select2',
                'multiple': 'multiple'
            }),
            'exclude_sale_items': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 dark:border-gray-600 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 dark:border-gray-600 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'is_stackable': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 dark:border-gray-600 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
        }
    
    target_membership_levels = forms.MultipleChoiceField(
        choices=[
            ('BRONZE', '브론즈'),
            ('SILVER', '실버'),
            ('GOLD', '골드'),
            ('PLATINUM', '플래티넘'),
            ('DIAMOND', '다이아몬드'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        label='대상 회원 등급'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 날짜 형식 조정
        if self.instance.pk:
            if self.instance.valid_from:
                self.initial['valid_from'] = self.instance.valid_from.strftime('%Y-%m-%dT%H:%M')
            if self.instance.valid_to:
                self.initial['valid_to'] = self.instance.valid_to.strftime('%Y-%m-%dT%H:%M')
    
    def clean(self):
        cleaned_data = super().clean()
        
        # 유효 기간 검증
        valid_from = cleaned_data.get('valid_from')
        valid_to = cleaned_data.get('valid_to')
        
        if valid_from and valid_to:
            if valid_from >= valid_to:
                raise forms.ValidationError('유효 종료일은 시작일보다 늦어야 합니다.')
        
        # 할인 타입별 검증
        discount_type = cleaned_data.get('discount_type')
        discount_value = cleaned_data.get('discount_value')
        
        if discount_type == 'PERCENTAGE' and discount_value:
            if discount_value > 100:
                raise forms.ValidationError('할인율은 100%를 초과할 수 없습니다.')
        
        # 수량 제한 검증
        total_quantity = cleaned_data.get('total_quantity')
        usage_limit_total = cleaned_data.get('usage_limit_total')
        
        if total_quantity and usage_limit_total:
            if usage_limit_total > total_quantity:
                raise forms.ValidationError('사용 제한은 발급 수량을 초과할 수 없습니다.')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # target_membership_levels JSON 변환
        if 'target_membership_levels' in self.cleaned_data:
            instance.target_membership_levels = list(self.cleaned_data['target_membership_levels'])
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


class IssueCouponForm(forms.Form):
    """개별 쿠폰 발급 폼"""
    
    coupon = forms.ModelChoiceField(
        queryset=Coupon.objects.filter(is_active=True),
        label='쿠폰',
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
    )
    
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        label='사용자',
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 select2'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 유효한 쿠폰만 표시
        self.fields['coupon'].queryset = Coupon.objects.filter(
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_to__gte=timezone.now()
        )


class BulkIssueCouponForm(forms.Form):
    """대량 쿠폰 발급 폼"""
    
    TARGET_TYPE_CHOICES = [
        ('ALL', '모든 회원'),
        ('MEMBERSHIP', '회원 등급별'),
        ('SPECIFIC', '특정 회원 선택'),
        ('NEW', '신규 회원'),
    ]
    
    coupon = forms.ModelChoiceField(
        queryset=Coupon.objects.filter(is_active=True),
        label='쿠폰',
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
    )
    
    target_type = forms.ChoiceField(
        choices=TARGET_TYPE_CHOICES,
        label='발급 대상',
        widget=forms.RadioSelect()
    )
    
    membership_levels = forms.MultipleChoiceField(
        choices=[
            ('BRONZE', '브론즈'),
            ('SILVER', '실버'),
            ('GOLD', '골드'),
            ('PLATINUM', '플래티넘'),
            ('DIAMOND', '다이아몬드'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        label='회원 등급'
    )
    
    specific_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 select2',
            'multiple': 'multiple'
        }),
        label='특정 회원'
    )
    
    days_since_join = forms.IntegerField(
        required=False,
        initial=7,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500'
        }),
        label='가입 후 일수'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        target_type = cleaned_data.get('target_type')
        
        if target_type == 'MEMBERSHIP':
            if not cleaned_data.get('membership_levels'):
                raise forms.ValidationError('회원 등급을 선택해주세요.')
        
        elif target_type == 'SPECIFIC':
            if not cleaned_data.get('specific_users'):
                raise forms.ValidationError('발급할 회원을 선택해주세요.')
        
        elif target_type == 'NEW':
            if not cleaned_data.get('days_since_join'):
                raise forms.ValidationError('가입 후 일수를 입력해주세요.')
        
        return cleaned_data


class ClaimCouponForm(forms.Form):
    """쿠폰 코드 입력 폼"""
    
    code = forms.CharField(
        label='쿠폰 코드',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': '쿠폰 코드를 입력하세요',
            'style': 'text-transform: uppercase;'
        })
    )
    
    def clean_code(self):
        code = self.cleaned_data['code']
        return code.upper()  # 대문자로 변환