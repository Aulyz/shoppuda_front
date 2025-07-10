# products/models.py - 완전한 상품 모델
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from PIL import Image
import os
from django.utils.text import slugify

class Category(models.Model):
    """상품 카테고리 모델"""
    name = models.CharField('카테고리명', max_length=100)
    code = models.CharField('카테고리 코드', max_length=20, unique=True, blank=True)
    description = models.TextField('설명', blank=True)
    icon = models.CharField(
        '아이콘',
        max_length=50,
        default='fas fa-folder',
        help_text="FontAwesome 아이콘 클래스를 입력하세요"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='상위 카테고리'
    )
    sort_order = models.PositiveIntegerField('정렬 순서', default=0)
    is_active = models.BooleanField('활성 상태', default=True)
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)


    class Meta:
        verbose_name = '카테고리'
        verbose_name_plural = '카테고리'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['parent']),
            models.Index(fields=['sort_order']),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            # 자동으로 코드 생성 (영문명 기반)
            base_code = slugify(self.name).upper().replace('-', '_')[:15]
            counter = 1
            self.code = base_code
            while Category.objects.filter(code=self.code).exclude(pk=self.pk).exists():
                self.code = f"{base_code}_{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:category_detail', kwargs={'pk': self.pk})

    def get_product_count(self):
        """카테고리에 속한 활성 상품 수"""
        try:
            return self.products.filter(status='ACTIVE').count()
        except:
            return 0

    @property
    def full_path(self):
        """전체 카테고리 경로"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name

    @property
    def level(self):
        """카테고리 레벨 (0부터 시작)"""
        if self.parent:
            return self.parent.level + 1
        return 0

    def get_children(self):
        """하위 카테고리들"""
        return self.children.filter(is_active=True).order_by('sort_order', 'name')

    def get_descendants(self):
        """모든 하위 카테고리들 (재귀적)"""
        descendants = []
        for child in self.get_children():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def get_products(self, include_descendants=False):
        """카테고리의 상품들"""
        if include_descendants:
            # 하위 카테고리의 상품들도 포함
            categories = [self] + self.get_descendants()
            try:
                return Product.objects.filter(
                    category__in=categories,
                    status='ACTIVE'
                ).order_by('-created_at')
            except:
                return []
        try:
            return self.products.filter(status='ACTIVE').order_by('-created_at')
        except:
            return []

    def can_delete(self):
        """삭제 가능 여부 확인"""
        # 하위 카테고리가 있으면 삭제 불가
        if self.children.exists():
            return False, "하위 카테고리가 존재합니다."
        
        # 상품이 있으면 삭제 불가
        try:
            if self.products.exists():
                return False, "카테고리에 상품이 존재합니다."
        except:
            pass
        
        return True, ""
    

class Brand(models.Model):
    """브랜드 모델"""
    name = models.CharField('브랜드명', max_length=100, unique=True)
    code = models.CharField('브랜드 코드', max_length=20, unique=True)
    description = models.TextField('설명', blank=True)
    logo = models.ImageField('로고', upload_to='brands/', blank=True)
    website = models.URLField('웹사이트', blank=True)
    is_active = models.BooleanField('활성 상태', default=True)
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        verbose_name = '브랜드'
        verbose_name_plural = '브랜드'
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    """상품 모델"""
    STATUS_CHOICES = [
        ('ACTIVE', '활성'),
        ('INACTIVE', '비활성'),
        ('DISCONTINUED', '단종'),
    ]

    # 기본 식별 정보
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.CharField('SKU', max_length=50, unique=True, db_index=True)
    name = models.CharField('상품명', max_length=200, db_index=True)
    
    # 분류 정보
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='products', verbose_name='카테고리')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, 
                             related_name='products', verbose_name='브랜드')
    
    # 설명
    short_description = models.TextField('간단 설명', max_length=500, blank=True)
    description = models.TextField('상세 설명', blank=True)
    
    # 상태
    status = models.CharField('상태', max_length=20, choices=STATUS_CHOICES, default='ACTIVE', db_index=True)
    is_featured = models.BooleanField('추천 상품', default=False, db_index=True)
    
    # 가격 정보
    cost_price = models.DecimalField('원가', max_digits=12, decimal_places=2, 
                                   validators=[MinValueValidator(0)])
    selling_price = models.DecimalField('판매가', max_digits=12, decimal_places=2, 
                                      validators=[MinValueValidator(0)])
    discount_price = models.DecimalField('할인가', max_digits=12, decimal_places=2, 
                                       null=True, blank=True, validators=[MinValueValidator(0)])
    
    # 재고 정보
    stock_quantity = models.PositiveIntegerField('재고 수량', default=0)
    min_stock_level = models.PositiveIntegerField('최소 재고 수준', default=0)
    max_stock_level = models.PositiveIntegerField('최대 재고 수준', default=1000)
    
    # 물리적 정보
    weight = models.DecimalField('무게(kg)', max_digits=8, decimal_places=3, 
                               null=True, blank=True, validators=[MinValueValidator(0)])
    dimensions_length = models.DecimalField('길이(cm)', max_digits=8, decimal_places=2, 
                                          null=True, blank=True, validators=[MinValueValidator(0)])
    dimensions_width = models.DecimalField('너비(cm)', max_digits=8, decimal_places=2, 
                                         null=True, blank=True, validators=[MinValueValidator(0)])
    dimensions_height = models.DecimalField('높이(cm)', max_digits=8, decimal_places=2, 
                                          null=True, blank=True, validators=[MinValueValidator(0)])
    
    # 추가 정보
    barcode = models.CharField('바코드', max_length=50, blank=True, db_index=True)
    tags = models.TextField('태그', blank=True, help_text='쉼표로 구분')
    
    # 메타 정보
    created_at = models.DateTimeField('생성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='created_products', verbose_name='생성자')

    class Meta:
        verbose_name = '상품'
        verbose_name_plural = '상품'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['status']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def get_absolute_url(self):
        return reverse('products:detail', kwargs={'pk': self.pk})

    @property
    def is_low_stock(self):
        """재고 부족 여부 확인"""
        return self.stock_quantity <= self.min_stock_level

    @property
    def primary_image(self):
        """대표 이미지 반환"""
        return self.images.filter(is_primary=True).first()

    @property
    def all_images(self):
        """모든 이미지 반환"""
        return self.images.all().order_by('sort_order')

    @property
    def stock_status(self):
        """재고 상태 반환"""
        if self.stock_quantity == 0:
            return 'out_of_stock'
        elif self.stock_quantity <= self.min_stock_level:
            return 'low_stock'
        elif self.stock_quantity > self.max_stock_level:
            return 'overstock'
        else:
            return 'normal'

    @property
    def profit_margin(self):
        """수익률 계산"""
        if self.cost_price and self.selling_price and self.selling_price > 0:
            return round(((self.selling_price - self.cost_price) / self.selling_price) * 100, 2)
        return 0

    @property
    def effective_price(self):
        """실제 판매가 (할인가가 있으면 할인가, 없으면 판매가)"""
        return self.discount_price if self.discount_price else self.selling_price

    @property
    def discount_percentage(self):
        """할인율 계산"""
        if self.discount_price and self.selling_price > 0:
            return round(((self.selling_price - self.discount_price) / self.selling_price) * 100, 1)
        return 0

    def save(self, *args, **kwargs):
        # SKU 자동 생성 (없는 경우)
        if not self.sku:
            self.sku = self.generate_sku()
        
        # 유효성 검사
        if self.discount_price and self.discount_price >= self.selling_price:
            raise ValueError('할인가는 판매가보다 낮아야 합니다.')
        
        if self.selling_price <= self.cost_price:
            raise ValueError('판매가는 원가보다 높아야 합니다.')
        
        super().save(*args, **kwargs)

    def generate_sku(self):
        """SKU 자동 생성"""
        from django.utils import timezone
        
        prefix = 'PROD'
        if self.category and self.category.code:
            prefix = self.category.code[:4].upper()
        
        timestamp = timezone.now().strftime('%y%m%d')
        
        # 오늘 생성된 상품 수 계산
        today = timezone.now().date()
        count = Product.objects.filter(created_at__date=today).count() + 1
        
        return f'{prefix}-{timestamp}-{count:03d}'
    
    @property
    def is_valid_product_category(self):
        """상품이 유효한 카테고리에 속하는지 확인"""
        if self.category:
            return True
        return False

class ProductImage(models.Model):
    """상품 이미지 모델"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name='상품')
    image = models.ImageField('이미지', upload_to='products/')
    alt_text = models.CharField('대체 텍스트', max_length=200, blank=True)
    is_primary = models.BooleanField('대표 이미지', default=False)
    sort_order = models.PositiveIntegerField('정렬 순서', default=0)
    created_at = models.DateTimeField('업로드일', auto_now_add=True)

    class Meta:
        verbose_name = '상품 이미지'
        verbose_name_plural = '상품 이미지'
        ordering = ['sort_order', 'created_at']

    def __str__(self):
        return f"{self.product.name} - 이미지 {self.sort_order + 1}"

    def save(self, *args, **kwargs):
        # 첫 번째 이미지는 자동으로 대표 이미지로 설정
        if not self.product.images.exists():
            self.is_primary = True
        
        # 대표 이미지 설정 시 다른 이미지들의 대표 이미지 해제
        if self.is_primary:
            self.product.images.exclude(pk=self.pk).update(is_primary=False)
        
        super().save(*args, **kwargs)
        
        # 이미지 최적화
        self.optimize_image()

    def optimize_image(self):
        """이미지 최적화"""
        if self.image:
            try:
                img = Image.open(self.image.path)
                
                # 이미지가 너무 큰 경우 리사이즈
                max_size = (1200, 1200)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # JPEG로 변환하여 저장 (투명도가 있는 경우 RGB로 변환)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                img.save(self.image.path, 'JPEG', quality=85, optimize=True)
            except Exception:
                pass  # 최적화 실패 시 원본 유지

class ProductPriceHistory(models.Model):
    """상품 가격 이력 모델"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_history', verbose_name='상품')
    cost_price = models.DecimalField('원가', max_digits=12, decimal_places=2)
    selling_price = models.DecimalField('판매가', max_digits=12, decimal_places=2)
    discount_price = models.DecimalField('할인가', max_digits=12, decimal_places=2, null=True, blank=True)
    reason = models.CharField('변경 사유', max_length=200, blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='변경자')
    created_at = models.DateTimeField('변경일', auto_now_add=True)

    class Meta:
        verbose_name = '상품 가격 이력'
        verbose_name_plural = '상품 가격 이력'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
