from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from products.models import Product, Category
from orders.models import Order, OrderItem
from core.models import SystemSettings


def home(request):
    """쇼핑몰 홈페이지"""
    # 추천 상품 (활성화된 상품 중 최신 8개)
    featured_products = Product.objects.filter(status='ACTIVE').order_by('-created_at')[:8]
    
    # 카테고리
    categories = Category.objects.filter(parent__isnull=True, is_active=True)
    
    # 시스템 설정
    system_settings = SystemSettings.get_settings()
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'system_settings': system_settings,
    }
    return render(request, 'shop/home.html', context)


def product_list(request):
    """상품 목록"""
    products = Product.objects.filter(status='ACTIVE')
    
    # 카테고리 필터
    category_id = request.GET.get('category')
    selected_category = None
    if category_id:
        category = get_object_or_404(Category, id=category_id)
        selected_category = category
        
        # 선택된 카테고리와 모든 하위 카테고리의 상품 가져오기
        categories_to_filter = [category]
        
        # 모든 하위 카테고리 찾기 (재귀적으로)
        def get_descendants(cat):
            children = Category.objects.filter(parent=cat, is_active=True)
            descendants = list(children)
            for child in children:
                descendants.extend(get_descendants(child))
            return descendants
        
        categories_to_filter.extend(get_descendants(category))
        
        # 카테고리 리스트로 필터링
        products = products.filter(category__in=categories_to_filter)
    
    # 검색
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # 정렬
    sort_by = request.GET.get('sort', '-created_at')
    products = products.order_by(sort_by)
    
    # 카테고리 트리 구조 생성 (사이드바용)
    def build_category_tree():
        root_categories = Category.objects.filter(parent__isnull=True, is_active=True)
        
        def build_tree(categories):
            tree = []
            for cat in categories:
                children = Category.objects.filter(parent=cat, is_active=True)
                tree.append({
                    'category': cat,
                    'children': build_tree(children) if children else []
                })
            return tree
        
        return build_tree(root_categories)
    
    context = {
        'products': products,
        'categories': Category.objects.filter(is_active=True),
        'category_tree': build_category_tree(),
        'current_category': category_id,
        'selected_category': selected_category,
        'search_query': search_query,
    }
    return render(request, 'shop/product_list.html', context)


def product_detail(request, pk):
    """상품 상세"""
    product = get_object_or_404(Product, pk=pk, status='ACTIVE')
    related_products = Product.objects.filter(
        category=product.category,
        status='ACTIVE'
    ).exclude(pk=pk)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'shop/product_detail.html', context)


@login_required
def cart_view(request):
    """장바구니"""
    # 세션 기반 장바구니 구현
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            price = product.effective_price
            subtotal = price * quantity
            total += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'price': price,
                'subtotal': subtotal,
            })
        except Product.DoesNotExist:
            # 상품이 삭제된 경우 장바구니에서 제거
            del cart[product_id]
    
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'shop/cart.html', context)


@login_required
def add_to_cart(request, product_id):
    """장바구니에 추가"""
    product = get_object_or_404(Product, id=product_id, status='ACTIVE')
    cart = request.session.get('cart', {})
    
    quantity = int(request.POST.get('quantity', 1))
    
    if str(product_id) in cart:
        cart[str(product_id)] += quantity
    else:
        cart[str(product_id)] = quantity
    
    request.session['cart'] = cart
    messages.success(request, f'{product.name}이(가) 장바구니에 추가되었습니다.')
    
    return redirect('shop:cart')


@login_required
def remove_from_cart(request, item_id):
    """장바구니에서 제거"""
    cart = request.session.get('cart', {})
    
    if str(item_id) in cart:
        del cart[str(item_id)]
        request.session['cart'] = cart
        messages.success(request, '상품이 장바구니에서 제거되었습니다.')
    
    return redirect('shop:cart')


@login_required
def checkout(request):
    """주문하기"""
    # 구현 예정
    return render(request, 'shop/checkout.html')


@login_required
def order_list(request):
    """주문 목록"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'shop/order_list.html', context)


@login_required
def order_detail(request, pk):
    """주문 상세"""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    
    context = {
        'order': order,
    }
    return render(request, 'shop/order_detail.html', context)


@login_required
def mypage(request):
    """마이페이지"""
    user = request.user
    recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
    
    context = {
        'user': user,
        'recent_orders': recent_orders,
    }
    return render(request, 'shop/mypage.html', context)


@login_required
def wishlist(request):
    """위시리스트"""
    # 구현 예정
    return render(request, 'shop/wishlist.html')


def search(request):
    """상품 검색"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return redirect('shop:product_list')
    
    # 상품 검색 (이름, 설명, 브랜드, 카테고리에서 검색)
    products = Product.objects.filter(status='ACTIVE')
    products = products.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query) |
        Q(short_description__icontains=query) |
        Q(brand__name__icontains=query) |
        Q(category__name__icontains=query) |
        Q(sku__icontains=query)
    ).distinct()
    
    # 정렬
    sort_by = request.GET.get('sort', '-created_at')
    products = products.order_by(sort_by)
    
    # 카테고리 집계 (검색 결과에서 카테고리별 개수)
    categories_with_count = []
    for category in Category.objects.filter(is_active=True):
        count = products.filter(category=category).count()
        if count > 0:
            categories_with_count.append({
                'category': category,
                'count': count
            })
    
    context = {
        'products': products,
        'search_query': query,
        'total_count': products.count(),
        'categories_with_count': categories_with_count,
    }
    return render(request, 'shop/search_results.html', context)
