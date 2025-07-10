# orders/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Order, OrderItem
from products.models import Product
from platforms.models import Platform

class OrderForm(forms.ModelForm):
    """주문 생성/수정 폼"""
    
    class Meta:
        model = Order
        fields = [
            'platform', 'customer_name', 'customer_email', 'customer_phone',
            'shipping_address', 'shipping_city', 'shipping_postal_code',
            'billing_address', 'billing_city', 'billing_postal_code',
            'special_instructions', 'shipping_cost', 'discount_amount',
            'tax_rate', 'status'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'placeholder': '고객명'
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'placeholder': 'customer@example.com'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'placeholder': '010-1234-5678'
            }),
            'shipping_address': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'rows': 2,
                'placeholder': '배송 주소'
            }),
            'shipping_city': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'placeholder': '도시'
            }),
            'shipping_postal_code': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'placeholder': '우편번호'
            }),
            'billing_address': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'rows': 2,
                'placeholder': '청구서 주소'
            }),
            'billing_city': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'placeholder': '도시'
            }),
            'billing_postal_code': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'placeholder': '우편번호'
            }),
            'special_instructions': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'rows': 3,
                'placeholder': '특별 요청사항'
            }),
            'shipping_cost': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'step': '0.01',
                'min': '0'
            }),
            'discount_amount': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'step': '0.01',
                'min': '0'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'platform': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'
            }),
            'status': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 활성 플랫폼만 선택 가능
        self.fields['platform'].queryset = Platform.objects.filter(is_active=True)
        
        # 필수 필드 설정
        self.fields['customer_name'].required = True
        self.fields['customer_email'].required = False
        self.fields['platform'].required = True
        
        # 기본값 설정
        if not self.instance.pk:
            self.fields['status'].initial = 'PENDING'
            self.fields['tax_rate'].initial = 10.0  # 기본 세율 10%
    
    def clean_customer_phone(self):
        """전화번호 유효성 검사"""
        phone = self.cleaned_data.get('customer_phone')
        if phone:
            # 간단한 한국 전화번호 형식 검사
            import re
            phone_pattern = re.compile(r'^01[0-9]-\d{4}-\d{4}$')
            if not phone_pattern.match(phone):
                raise ValidationError('올바른 전화번호 형식이 아닙니다. (예: 010-1234-5678)')
        return phone
    
    def clean(self):
        """폼 전체 유효성 검사"""
        cleaned_data = super().clean()
        
        # 할인 금액이 0보다 작지 않도록
        discount_amount = cleaned_data.get('discount_amount', 0)
        if discount_amount and discount_amount < 0:
            raise ValidationError('할인 금액은 0보다 작을 수 없습니다.')
        
        # 배송비가 0보다 작지 않도록
        shipping_cost = cleaned_data.get('shipping_cost', 0)
        if shipping_cost and shipping_cost < 0:
            raise ValidationError('배송비는 0보다 작을 수 없습니다.')
        
        return cleaned_data


class OrderItemForm(forms.ModelForm):
    """주문 아이템 폼"""
    
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'onchange': 'updateProductInfo(this)'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'min': '1',
                'onchange': 'calculateTotal(this)'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'step': '0.01',
                'min': '0',
                'onchange': 'calculateTotal(this)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 활성 상품만 선택 가능
        self.fields['product'].queryset = Product.objects.filter(status='ACTIVE')
        
        # 모든 필드 필수
        for field in self.fields.values():
            field.required = True
    
    def clean(self):
        """폼 유효성 검사"""
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')
        
        if product and quantity:
            # 재고 확인
            if product.stock_quantity < quantity:
                raise ValidationError(
                    f'재고가 부족합니다. 현재 재고: {product.stock_quantity}개'
                )
            
            # 단가가 설정되지 않은 경우 상품 판매가로 설정
            if not cleaned_data.get('unit_price'):
                cleaned_data['unit_price'] = product.selling_price
        
        return cleaned_data


class QuickOrderForm(forms.Form):
    """빠른 주문 생성 폼"""
    customer_name = forms.CharField(
        max_length=100,
        label='고객명',
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': '고객명'
        })
    )
    
    customer_email = forms.EmailField(
        required=False,
        label='이메일',
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'customer@example.com'
        })
    )
    
    customer_phone = forms.CharField(
        max_length=20,
        required=False,
        label='전화번호',
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': '010-1234-5678'
        })
    )
    
    platform = forms.ModelChoiceField(
        queryset=Platform.objects.filter(is_active=True),
        label='플랫폼',
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(status='ACTIVE'),
        label='상품',
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    quantity = forms.IntegerField(
        min_value=1,
        label='수량',
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'min': '1'
        })
    )


class OrderSearchForm(forms.Form):
    """주문 검색 폼"""
    search = forms.CharField(
        required=False,
        label='검색',
        widget=forms.TextInput(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': '주문번호, 고객명, 이메일로 검색...'
        })
    )
    
    platform = forms.ModelChoiceField(
        queryset=Platform.objects.filter(is_active=True),
        required=False,
        label='플랫폼',
        empty_label='모든 플랫폼',
        widget=forms.Select(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', '모든 상태')] + Order.STATUS_CHOICES,
        required=False,
        label='상태',
        widget=forms.Select(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        label='시작일',
        widget=forms.DateInput(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        label='종료일',
        widget=forms.DateInput(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'type': 'date'
        })
    )