# File: inventory/forms.py
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML
from .models import StockMovement
from products.models import Product

class StockAdjustmentForm(forms.Form):
    REASON_CHOICES = [
        ('손상', '손상'),
        ('분실', '분실'),
        ('도난', '도난'),
        ('재고실사', '재고실사'),
        ('기타', '기타'),
    ]
    
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(status='ACTIVE'),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        label='상품'
    )
    new_quantity = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='새 재고 수량'
    )
    reason = forms.ChoiceField(
        choices=REASON_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='조정 사유'
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        label='메모'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'product',
            'new_quantity',
            'reason',
            'notes',
            Submit('submit', '재고 조정', css_class='btn btn-primary'),
        )

class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ['product', 'quantity', 'reference_number', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control select2'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['product'].queryset = Product.objects.filter(status='ACTIVE')
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'product',
            'quantity',
            'reference_number',
            'notes',
            Submit('submit', '처리', css_class='btn btn-primary'),
        )