# search/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from products.models import Product, Category
from orders.models import Order
from django.contrib.auth.models import User
import json

@method_decorator(login_required, name='dispatch')
class SearchView(LoginRequiredMixin, TemplateView):
    template_name = 'search/search_results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        search_type = self.request.GET.get('type', 'all')
        
        if query:
            context.update(self.perform_search(query, search_type))
        
        context['query'] = query
        context['search_type'] = search_type
        return context
    
    def perform_search(self, query, search_type):
        results = {}
        
        if search_type == 'all' or search_type == 'products':
            # 상품 검색
            product_results = Product.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(sku__icontains=query)
            ).select_related('category')
            
            results['products'] = product_results[:10]
            results['products_count'] = product_results.count()
        
        if search_type == 'all' or search_type == 'orders':
            # 주문 검색
            order_results = Order.objects.filter(
                Q(order_number__icontains=query) |
                Q(customer_name__icontains=query) |
                Q(customer_email__icontains=query)
            ).select_related('user')
            
            results['orders'] = order_results[:10]
            results['orders_count'] = order_results.count()
        
        if search_type == 'all' or search_type == 'categories':
            # 카테고리 검색
            category_results = Category.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )
            
            results['categories'] = category_results[:10]
            results['categories_count'] = category_results.count()
        
        return results

@login_required
def search_api(request):
    """AJAX 검색 API"""
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'all')
    limit = int(request.GET.get('limit', 5))
    
    if not query:
        return JsonResponse({
            'results': [],
            'total_count': 0
        })
    
    results = []
    total_count = 0
    
    if search_type == 'all' or search_type == 'products':
        # 상품 검색
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sku__icontains=query)
        ).select_related('category')[:limit]
        
        for product in products:
            results.append({
                'type': 'product',
                'id': product.id,
                'title': product.name,
                'subtitle': f"SKU: {product.sku}",
                'url': f'/products/{product.id}/',
                'icon': 'fas fa-box',
                'color': 'text-blue-500',
                'extra': {
                    'category': product.category.name if product.category else '',
                    'price': float(product.price),
                    'stock': product.stock_quantity
                }
            })
        
        total_count += products.count()
    
    if search_type == 'all' or search_type == 'orders':
        # 주문 검색
        orders = Order.objects.filter(
            Q(order_number__icontains=query) |
            Q(customer_name__icontains=query) |
            Q(customer_email__icontains=query)
        ).select_related('user')[:limit]
        
        for order in orders:
            results.append({
                'type': 'order',
                'id': order.id,
                'title': f"주문 #{order.order_number}",
                'subtitle': f"고객: {order.customer_name}",
                'url': f'/orders/{order.id}/',
                'icon': 'fas fa-shopping-cart',
                'color': 'text-green-500',
                'extra': {
                    'total_amount': float(order.total_amount),
                    'status': order.status,
                    'created_at': order.created_at.isoformat()
                }
            })
        
        total_count += orders.count()
    
    if search_type == 'all' or search_type == 'categories':
        # 카테고리 검색
        categories = Category.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )[:limit]
        
        for category in categories:
            results.append({
                'type': 'category',
                'id': category.id,
                'title': category.name,
                'subtitle': category.description or '',
                'url': f'/products/categories/{category.id}/',
                'icon': 'fas fa-tags',
                'color': 'text-purple-500',
                'extra': {
                    'product_count': category.products.count()
                }
            })
        
        total_count += categories.count()
    
    return JsonResponse({
        'results': results,
        'total_count': total_count,
        'query': query
    })

@login_required
def quick_search_api(request):
    """빠른 검색 API - 드롭다운용"""
    query = request.GET.get('q', '')
    
    if not query or len(query) < 2:
        return JsonResponse({
            'results': []
        })
    
    results = []
    
    # 상품 검색 (최대 3개)
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(sku__icontains=query)
    ).select_related('category')[:3]
    
    for product in products:
        results.append({
            'type': 'product',
            'title': product.name,
            'subtitle': f"SKU: {product.sku}",
            'url': f'/products/{product.id}/',
            'icon': 'fas fa-box'
        })
    
    # 주문 검색 (최대 3개)
    orders = Order.objects.filter(
        Q(order_number__icontains=query) |
        Q(customer_name__icontains=query)
    )[:3]
    
    for order in orders:
        results.append({
            'type': 'order',
            'title': f"주문 #{order.order_number}",
            'subtitle': f"고객: {order.customer_name}",
            'url': f'/orders/{order.id}/',
            'icon': 'fas fa-shopping-cart'
        })
    
    # 카테고리 검색 (최대 2개)
    categories = Category.objects.filter(
        name__icontains=query
    )[:2]
    
    for category in categories:
        results.append({
            'type': 'category',
            'title': category.name,
            'subtitle': '카테고리',
            'url': f'/products/categories/{category.id}/',
            'icon': 'fas fa-tags'
        })
    
    return JsonResponse({
        'results': results
    })