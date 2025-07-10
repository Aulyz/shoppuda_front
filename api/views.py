# File: api/views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from datetime import timedelta

from products.models import Product, Category, Brand
from orders.models import Order, OrderItem
from platforms.models import Platform, PlatformProduct
from inventory.models import StockMovement
from .serializers import (
    ProductSerializer, ProductDetailSerializer,
    OrderSerializer, OrderDetailSerializer,
    PlatformSerializer, StockMovementSerializer,
    CategorySerializer, BrandSerializer
)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('brand', 'category').prefetch_related('images')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'brand', 'category', 'is_featured']
    search_fields = ['name', 'sku', 'barcode']
    ordering_fields = ['created_at', 'name', 'selling_price', 'stock_quantity']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """재고 부족 상품 목록"""
        low_stock_products = self.queryset.filter(
            stock_quantity__lte=F('min_stock_level'),
            status='ACTIVE'
        )
        
        page = self.paginate_queryset(low_stock_products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(low_stock_products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def adjust_stock(self, request, pk=None):
        """재고 조정"""
        product = self.get_object()
        new_quantity = request.data.get('quantity')
        reason = request.data.get('reason', '재고 조정')
        
        if new_quantity is None:
            return Response(
                {'error': '수량을 입력해주세요.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_quantity = int(new_quantity)
            if new_quantity < 0:
                return Response(
                    {'error': '수량은 0 이상이어야 합니다.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {'error': '올바른 수량을 입력해주세요.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        current_stock = product.stock_quantity
        adjustment = new_quantity - current_stock
        
        if adjustment != 0:
            # 재고 이동 기록 생성
            StockMovement.objects.create(
                product=product,
                movement_type='ADJUST',
                quantity=adjustment,
                previous_stock=current_stock,
                current_stock=new_quantity,
                reference_number=f"API_ADJ_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
                notes=reason,
                created_by=request.user
            )
            
            # 상품 재고 업데이트
            product.stock_quantity = new_quantity
            product.save()
        
        serializer = self.get_serializer(product)
        return Response(serializer.data)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related('platform').prefetch_related('items__product')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'platform']
    search_fields = ['order_number', 'customer_name', 'customer_email']
    ordering_fields = ['order_date', 'total_amount']
    ordering = ['-order_date']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrderDetailSerializer
        return OrderSerializer
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """주문 상태 업데이트"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'error': '올바른 상태를 선택해주세요.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = order.status
        order.status = new_status
        
        # 상태별 추가 처리
        if new_status == 'SHIPPED' and old_status != 'SHIPPED':
            order.shipped_date = timezone.now()
        elif new_status == 'DELIVERED' and old_status != 'DELIVERED':
            order.delivered_date = timezone.now()
        
        order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)

class PlatformViewSet(viewsets.ModelViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """플랫폼 동기화"""
        platform = self.get_object()
        
        if not platform.is_active:
            return Response(
                {'error': '비활성화된 플랫폼입니다.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 비동기 작업 실행
        from platforms.tasks import sync_platform_products
        sync_platform_products.delay(platform.id)
        
        return Response({'message': '동기화가 시작되었습니다.'})

class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockMovement.objects.select_related('product', 'created_by')
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['movement_type', 'product']
    search_fields = ['product__name', 'product__sku', 'reference_number']
    ordering = ['-created_at']

class DashboardStatsView(APIView):
    """대시보드 통계 API"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # 상품 통계
        total_products = Product.objects.filter(status='ACTIVE').count()
        low_stock_products = Product.objects.filter(
            stock_quantity__lte=F('min_stock_level'),
            status='ACTIVE'
        ).count()
        
        # 주문 통계
        today_orders = Order.objects.filter(order_date__date=today).count()
        week_orders = Order.objects.filter(order_date__date__gte=week_ago).count()
        month_revenue = Order.objects.filter(
            order_date__date__gte=month_ago,
            status__in=['CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # 매출 차트 데이터 (최근 30일)
        daily_sales = Order.objects.filter(
            order_date__date__gte=month_ago,
            status__in=['CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED']
        ).extra(
            select={'day': 'date(order_date)'}
        ).values('day').annotate(
            total=Sum('total_amount'),
            count=Count('id')
        ).order_by('day')
        
        # 상품 상태별 통계
        product_status = Product.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        return Response({
            'products': {
                'total': total_products,
                'low_stock': low_stock_products,
            },
            'orders': {
                'today': today_orders,
                'week': week_orders,
                'month_revenue': float(month_revenue),
            },
            'charts': {
                'daily_sales': list(daily_sales),
                'product_status': list(product_status),
            }
        })

class ProductSearchView(APIView):
    """상품 검색 API"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        query = request.GET.get('q', '')
        
        if len(query) < 2:
            return Response({'products': []})
        
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(sku__icontains=query)
        ).select_related('brand')[:20]
        
        data = [
            {
                'id': str(product.id),
                'sku': product.sku,
                'name': product.name,
                'brand': product.brand.name if product.brand else '',
                'price': str(product.final_price),
                'stock': product.stock_quantity,
                'image': product.images.filter(is_primary=True).first().image.url if product.images.filter(is_primary=True).exists() else None,
            }
            for product in products
        ]
        
        return Response({'products': data})

class PlatformSyncView(APIView):
    """플랫폼 일괄 동기화 API"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        platform_ids = request.data.get('platform_ids', [])
        
        if not platform_ids:
            # 모든 활성 플랫폼
            platforms = Platform.objects.filter(is_active=True)
        else:
            platforms = Platform.objects.filter(id__in=platform_ids, is_active=True)
        
        if not platforms.exists():
            return Response(
                {'error': '동기화할 플랫폼이 없습니다.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 비동기 작업 실행
        from platforms.tasks import sync_platform_products
        for platform in platforms:
            sync_platform_products.delay(platform.id)
        
        return Response({
            'message': f'{platforms.count()}개 플랫폼 동기화가 시작되었습니다.',
            'platforms': [platform.name for platform in platforms]
        })