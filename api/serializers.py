# File: api/serializers.py
from rest_framework import serializers
from products.models import Product, ProductImage, Category, Brand
from orders.models import Order, OrderItem
from platforms.models import Platform, PlatformProduct
from inventory.models import StockMovement

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'code', 'parent', 'full_path']

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'code']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'sort_order']

class ProductSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    final_price = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'brand', 'category', 'short_description',
            'selling_price', 'discount_price', 'final_price', 'stock_quantity',
            'min_stock_level', 'status', 'is_featured', 'is_low_stock',
            'primary_image', 'created_at', 'updated_at'
        ]
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return ProductImageSerializer(primary_image).data
        return None

class ProductDetailSerializer(ProductSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    platform_products = serializers.SerializerMethodField()
    
    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + [
            'description', 'cost_price', 'max_stock_level', 'weight',
            'dimensions_length', 'dimensions_width', 'dimensions_height',
            'tags', 'barcode', 'images', 'platform_products'
        ]
    
    def get_platform_products(self, obj):
        platform_products = obj.platform_products.select_related('platform')[:10]
        return PlatformProductSerializer(platform_products, many=True).data

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'unit_price', 'total_price']

class OrderSerializer(serializers.ModelSerializer):
    platform_name = serializers.CharField(source='platform.name', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'platform', 'platform_name', 'customer_name',
            'status', 'total_amount', 'order_date', 'created_at'
        ]

class OrderDetailSerializer(OrderSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + [
            'platform_order_id', 'customer_email', 'customer_phone',
            'shipping_address', 'shipping_zipcode', 'shipping_method',
            'tracking_number', 'shipping_fee', 'discount_amount',
            'shipped_date', 'delivered_date', 'items'
        ]

class PlatformSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Platform
        fields = [
            'id', 'name', 'platform_type', 'is_active', 'product_count',
            'created_at', 'updated_at'
        ]
    
    def get_product_count(self, obj):
        return obj.platformproduct_set.filter(is_active=True).count()

class PlatformProductSerializer(serializers.ModelSerializer):
    platform_name = serializers.CharField(source='platform.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = PlatformProduct
        fields = [
            'id', 'platform', 'platform_name', 'product_name',
            'platform_product_id', 'platform_price', 'platform_stock',
            'is_active', 'last_sync_at'
        ]

class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = StockMovement
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'movement_type',
            'quantity', 'previous_stock', 'current_stock', 'reference_number',
            'notes', 'created_at', 'created_by_name'
        ]