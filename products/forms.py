# products/forms.py - 상품 관련 폼
from django import forms
from django.forms import inlineformset_factory
from .models import Product, ProductImage, Brand, Category
from django.core.exceptions import ValidationError
from PIL import Image
import re

class ProductForm(forms.ModelForm):
    """상품 등록/수정 폼"""
    
    class Meta:
        model = Product
        fields = [
            'sku', 'name', 'category', 'brand', 'short_description', 'description',
            'status', 'is_featured', 'cost_price', 'selling_price', 'discount_price',
            'stock_quantity', 'min_stock_level', 'max_stock_level',
            'weight', 'dimensions_length', 'dimensions_width', 'dimensions_height',
            'barcode', 'tags'
        ]
        
        widgets = {
            'sku': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200',
                'placeholder': '예: PROD-001'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200',
                'placeholder': '상품명을 입력하세요'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200'
            }),
            'brand': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200'
            }),
            'short_description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200 resize-none',
                'rows': 3,
                'placeholder': '상품의 간단한 설명을 입력하세요'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200 resize-none',
                'rows': 5,
                'placeholder': '상품의 상세한 설명을 입력하세요'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200'
            }),
            'cost_price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 pr-8 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200',
                'min': 0,
                'step': 100,
                'placeholder': '0'
            }),
            'selling_price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 pr-8 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200',
                'min': 0,
                'step': 100,
                'placeholder': '0'
            }),
            'discount_price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 pr-8 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200',
                'min': 0,
                'step': 100,
                'placeholder': '0'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200',
                'min': 0,
                'placeholder': '0'
            }),
            'min_stock_level': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200',
                'min': 0,
                'placeholder': '10'
            }),
            'max_stock_level': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200',
                'min': 1,
                'placeholder': '1000'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200',
                'min': 0,
                'step': 0.1,
                'placeholder': '0'
            }),
            'dimensions_length': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200',
                'min': 0,
                'step': 0.1,
                'placeholder': '0'
            }),
            'dimensions_width': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200',
                'min': 0,
                'step': 0.1,
                'placeholder': '0'
            }),
            'dimensions_height': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200',
                'min': 0,
                'step': 0.1,
                'placeholder': '0'
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200',
                'placeholder': '바코드를 입력하세요'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200',
                'placeholder': '태그1, 태그2, 태그3'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-emerald-600 focus:ring-emerald-500'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 카테고리와 브랜드 쿼리셋 설정
        self.fields['category'].queryset = Category.objects.filter(is_active=True).order_by('sort_order', 'name')
        self.fields['brand'].queryset = Brand.objects.filter(is_active=True).order_by('name')
        
        # 선택 필드에 빈 옵션 추가
        self.fields['category'].empty_label = "카테고리를 선택하세요"
        self.fields['brand'].empty_label = "브랜드를 선택하세요 (선택사항)"
        
        # 필수 필드 설정
        self.fields['sku'].required = True
        self.fields['name'].required = True
        self.fields['category'].required = True
        self.fields['cost_price'].required = True
        self.fields['selling_price'].required = True
        self.fields['stock_quantity'].required = True
    
    def clean_sku(self):
        """SKU 중복 검사"""
        sku = self.cleaned_data.get('sku')
        if sku:
            sku = sku.upper().strip()
            if self.instance.pk:
                # 수정시: 본인 제외하고 중복 검사
                if Product.objects.filter(sku=sku).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('이미 사용 중인 SKU입니다.')
            else:
                # 생성시: 전체 중복 검사
                if Product.objects.filter(sku=sku).exists():
                    raise forms.ValidationError('이미 사용 중인 SKU입니다.')
        return sku
    
    def clean(self):
        """전체 폼 유효성 검사"""
        cleaned_data = super().clean()
        
        cost_price = cleaned_data.get('cost_price')
        selling_price = cleaned_data.get('selling_price')
        discount_price = cleaned_data.get('discount_price')
        min_stock = cleaned_data.get('min_stock_level')
        max_stock = cleaned_data.get('max_stock_level')
        
        # 가격 검증
        if cost_price is not None and selling_price is not None:
            if selling_price <= cost_price:
                raise forms.ValidationError('판매가는 원가보다 높아야 합니다.')
        
        if discount_price and selling_price:
            if discount_price >= selling_price:
                raise forms.ValidationError('할인가는 판매가보다 낮아야 합니다.')
        
        # 재고 검증
        if min_stock is not None and max_stock is not None:
            if max_stock <= min_stock:
                raise forms.ValidationError('최대 재고는 최소 재고보다 커야 합니다.')
        
        return cleaned_data

class ProductImageForm(forms.ModelForm):
    """상품 이미지 폼"""
    
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_primary', 'image_type', 'sort_order']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100',
                'accept': 'image/*'
            }),
            'alt_text': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200',
                'placeholder': '이미지 설명'
            }),
            'image_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors duration-200',
                'min': 0
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-emerald-600 focus:ring-emerald-500'
            })
        }
    
    def clean_image(self):
        """이미지 유효성 검사"""
        image = self.cleaned_data.get('image')
        image_type = self.data.get(f'{self.prefix}-image_type', 'gallery')
        
        if image:
            # 대표 이미지와 갤러리 이미지만 크기 제한
            if image_type in ['primary', 'gallery']:
                # 파일 크기 제한 (5MB)
                if image.size > 5 * 1024 * 1024:
                    raise forms.ValidationError('대표 이미지와 갤러리 이미지는 5MB를 초과할 수 없습니다.')
                
                # 이미지 크기 검사
                try:
                    img = Image.open(image)
                    width, height = img.size
                    
                    # 너무 작은 이미지 제한
                    if width < 300 or height < 300:
                        raise forms.ValidationError('대표 이미지와 갤러리 이미지는 최소 300x300 픽셀 이상이어야 합니다.')
                    
                    # 너무 큰 이미지 제한
                    if width > 4000 or height > 4000:
                        raise forms.ValidationError('대표 이미지와 갤러리 이미지는 4000x4000 픽셀을 초과할 수 없습니다.')
                    
                except Exception:
                    raise forms.ValidationError('유효한 이미지 파일이 아닙니다.')
            
            # 상세 이미지는 제한 없음 (긴 포스터, 홍보지 등 허용)
            
        return image

# 상품 이미지 인라인 폼셋
ProductImageFormSet = inlineformset_factory(
    Product, 
    ProductImage, 
    form=ProductImageForm,
    extra=1,
    max_num=10,
    can_delete=True
)

class BrandForm(forms.ModelForm):
    """브랜드 생성/수정 폼"""
    
    class Meta:
        model = Brand
        fields = ['name', 'code', 'description', 'logo', 'website', 'is_active']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-400 dark:focus:border-blue-400 transition-colors duration-200',
                'placeholder': '브랜드명을 입력하세요',
            }),
            'code': forms.TextInput(attrs={
                'class': 'block w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-400 dark:focus:border-blue-400 transition-colors duration-200 font-mono',
                'placeholder': 'BRAND_CODE',
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-400 dark:focus:border-blue-400 transition-colors duration-200 resize-none',
                'rows': 4,
                'placeholder': '브랜드에 대한 설명을 입력하세요...',
            }),
            'website': forms.URLInput(attrs={
                'class': 'block w-full px-4 py-3 pl-12 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-400 dark:focus:border-blue-400 transition-colors duration-200',
                'placeholder': 'https://www.example.com',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['code'].required = True
        
        if not self.instance.pk:  # 새로 생성하는 경우
            self.fields['is_active'].initial = True

    def clean_name(self):
        """브랜드명 유효성 검사"""
        name = self.cleaned_data.get('name', '').strip()
        
        if not name:
            raise ValidationError('브랜드명은 필수 입력 항목입니다.')
        
        if len(name) < 2:
            raise ValidationError('브랜드명은 최소 2자 이상이어야 합니다.')
        
        # 중복 검사
        existing_brand = Brand.objects.filter(name__iexact=name)
        if self.instance.pk:
            existing_brand = existing_brand.exclude(pk=self.instance.pk)
        
        if existing_brand.exists():
            raise ValidationError('이미 존재하는 브랜드명입니다.')
        
        return name

    def clean_code(self):
        """브랜드 코드 유효성 검사"""
        code = self.cleaned_data.get('code', '').strip().upper()
        
        if not code:
            raise ValidationError('브랜드 코드는 필수 입력 항목입니다.')
        
        # 영문 대문자, 숫자, 언더스코어만 허용
        if not re.match(r'^[A-Z0-9_]+$', code):
            raise ValidationError('브랜드 코드는 영문 대문자, 숫자, 언더스코어만 사용할 수 있습니다.')
        
        if len(code) < 2:
            raise ValidationError('브랜드 코드는 최소 2자 이상이어야 합니다.')
        
        # 중복 검사
        existing_brand = Brand.objects.filter(code__iexact=code)
        if self.instance.pk:
            existing_brand = existing_brand.exclude(pk=self.instance.pk)
        
        if existing_brand.exists():
            raise ValidationError('이미 존재하는 브랜드 코드입니다.')
        
        return code

    def clean_logo(self):
        """로고 이미지 유효성 검사"""
        logo = self.cleaned_data.get('logo')
        
        if logo:
            # 파일 크기 제한 (5MB)
            if logo.size > 5 * 1024 * 1024:
                raise ValidationError('로고 파일 크기는 5MB를 초과할 수 없습니다.')
        
        return logo

    def save(self, commit=True):
        """브랜드 저장"""
        brand = super().save(commit=False)
        
        # 코드를 대문자로 변환
        if brand.code:
            brand.code = brand.code.upper()
        
        if commit:
            brand.save()
        
        return brand


class BrandSearchForm(forms.Form):
    """브랜드 검색 폼"""
    
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'block w-full pl-10 pr-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-400 dark:focus:border-blue-400 transition-colors duration-200',
            'placeholder': '브랜드명 또는 코드로 검색...',
            'autocomplete': 'off',
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', '전체'),
            ('active', '활성'),
            ('inactive', '비활성'),
        ],
        widget=forms.Select(attrs={
            'class': 'block w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-400 dark:focus:border-blue-400 transition-colors duration-200',
        })
    )
    
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ('name', '이름순'),
            ('-name', '이름순 (역순)'),
            ('code', '코드순'),
            ('-code', '코드순 (역순)'),
            ('created_at', '생성일순'),
            ('-created_at', '생성일순 (최신순)'),
            ('updated_at', '수정일순'),
            ('-updated_at', '수정일순 (최신순)'),
        ],
        initial='-created_at',
        widget=forms.Select(attrs={
            'class': 'block w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-400 dark:focus:border-blue-400 transition-colors duration-200',
        })
    )

    def clean_search(self):
        """검색어 정리"""
        search = self.cleaned_data.get('search', '').strip()
        
        # 검색어 길이 제한
        if len(search) > 100:
            raise ValidationError('검색어는 100자를 초과할 수 없습니다.')
        
        return search


class BrandBulkActionForm(forms.Form):
    """브랜드 일괄 작업 폼"""
    
    ACTION_CHOICES = [
        ('', '작업 선택'),
        ('activate', '활성화'),
        ('deactivate', '비활성화'),
        ('delete', '삭제'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'block w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-400 dark:focus:border-blue-400 transition-colors duration-200',
        })
    )
    
    selected_brands = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    def clean_selected_brands(self):
        """선택된 브랜드 ID 검증"""
        selected = self.cleaned_data.get('selected_brands', '')
        
        if not selected:
            raise ValidationError('작업할 브랜드를 선택해주세요.')
        
        try:
            brand_ids = [int(id.strip()) for id in selected.split(',') if id.strip()]
        except ValueError:
            raise ValidationError('올바르지 않은 브랜드 ID입니다.')
        
        if not brand_ids:
            raise ValidationError('작업할 브랜드를 선택해주세요.')
        
        # 존재하는 브랜드인지 확인
        existing_count = Brand.objects.filter(id__in=brand_ids).count()
        if existing_count != len(brand_ids):
            raise ValidationError('선택된 브랜드 중 일부가 존재하지 않습니다.')
        
        return brand_ids

    def clean(self):
        """전체 폼 유효성 검사"""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        brand_ids = cleaned_data.get('selected_brands', [])
        
        if action == 'delete' and brand_ids:
            # 삭제 전 상품 연결 여부 확인
            brands_with_products = Brand.objects.filter(
                id__in=brand_ids,
                products__isnull=False
            ).distinct()
            
            if brands_with_products.exists():
                brand_names = ', '.join(brands_with_products.values_list('name', flat=True))
                raise ValidationError(
                    f'다음 브랜드들은 연결된 상품이 있어 삭제할 수 없습니다: {brand_names}'
                )
        
        return cleaned_data

class CategoryForm(forms.ModelForm):
    """카테고리 생성/수정 폼"""
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon', 'parent', 'sort_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-emerald-500 focus:border-emerald-500 sm:text-sm',
                'placeholder': '카테고리 이름을 입력하세요',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-emerald-500 focus:border-emerald-500 sm:text-sm',
                'rows': 3,
                'placeholder': '카테고리에 대한 설명을 입력하세요'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-emerald-500 focus:border-emerald-500 sm:text-sm',
                'placeholder': 'fas fa-folder'
            }),
            'parent': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-emerald-500 focus:border-emerald-500 sm:text-sm'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-emerald-500 focus:border-emerald-500 sm:text-sm',
                'min': 0,
                'value': 0
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 자기 자신과 자기 하위 카테고리들을 부모 선택에서 제외
        if self.instance.pk:
            descendants = [self.instance.pk] + [cat.pk for cat in self.instance.get_descendants()]
            self.fields['parent'].queryset = Category.objects.exclude(pk__in=descendants)
        
        # 부모 카테고리 선택 필드 개선
        self.fields['parent'].empty_label = "최상위 카테고리"
        self.fields['parent'].queryset = self.fields['parent'].queryset.filter(is_active=True)

    def clean_parent(self):
        parent = self.cleaned_data.get('parent')
        if parent and self.instance.pk:
            # *** 기존과 parent가 동일하면 그냥 통과 ***
            if parent.pk == self.instance.parent_id:
                return parent

            if parent.pk == self.instance.pk:
                raise ValidationError('자기 자신을 부모 카테고리로 설정할 수 없습니다.')
            # 순환 참조 방지
            if self.instance in parent.get_descendants():
                raise ValidationError('하위 카테고리를 부모로 설정할 수 없습니다.')
        return parent



    def clean(self):
        """전체 폼 유효성 검사"""
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        parent = cleaned_data.get('parent')
        
        # 같은 부모 하에서 이름 중복 방지
        if name:
            queryset = Category.objects.filter(name=name, parent=parent)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError('같은 부모 카테고리 내에 동일한 이름이 이미 존재합니다.')
        
        return cleaned_data