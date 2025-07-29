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
def update_cart_item(request, product_id):
    """장바구니 수량 업데이트"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id, status='ACTIVE')
        cart = request.session.get('cart', {})
        
        quantity = int(request.POST.get('quantity', 1))
        
        # 재고 확인
        if quantity > product.stock_quantity:
            messages.error(request, f'재고가 부족합니다. 현재 재고: {product.stock_quantity}개')
            return redirect('shop:cart')
        
        if quantity > 0:
            cart[str(product_id)] = quantity
            request.session['cart'] = cart
            messages.success(request, '수량이 변경되었습니다.')
        else:
            if str(product_id) in cart:
                del cart[str(product_id)]
                request.session['cart'] = cart
                messages.success(request, '상품이 장바구니에서 제거되었습니다.')
    
    return redirect('shop:cart')


@login_required
def remove_from_cart(request, product_id):
    """장바구니에서 제거"""
    cart = request.session.get('cart', {})
    
    if str(product_id) in cart:
        del cart[str(product_id)]
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
    
    # 배송 완료된 주문 중 후기 작성 가능한 주문
    delivered_orders = Order.objects.filter(
        user=user, 
        status='DELIVERED'
    ).prefetch_related('items__product').order_by('-created_at')[:3]
    
    context = {
        'user': user,
        'recent_orders': recent_orders,
        'delivered_orders': delivered_orders,
    }
    return render(request, 'shop/mypage.html', context)


@login_required
def update_profile(request):
    """프로필 업데이트"""
    if request.method == 'POST':
        user = request.user
        
        # 기본 정보 업데이트
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        
        # 추가 정보 업데이트
        from accounts.models import User
        if hasattr(user, 'phone_number'):
            user.phone_number = request.POST.get('phone_number', '')
            user.birth_date = request.POST.get('birth_date') or None
            user.gender = request.POST.get('gender', '')
            user.postal_code = request.POST.get('postal_code', '')
            user.address = request.POST.get('address', '')
            user.detail_address = request.POST.get('detail_address', '')
            user.marketing_agreed = request.POST.get('marketing_agreed') == 'on'
        
        user.save()
        messages.success(request, '회원정보가 수정되었습니다.')
    
    return redirect('shop:mypage')


@login_required
def add_address(request):
    """배송지 추가"""
    if request.method == 'POST':
        from accounts.models import ShippingAddress
        
        address_id = request.POST.get('address_id')
        if address_id:
            # 수정
            address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
        else:
            # 추가
            address = ShippingAddress(user=request.user)
        
        address.nickname = request.POST.get('nickname')
        address.recipient_name = request.POST.get('recipient_name')
        address.phone_number = request.POST.get('phone_number')
        address.postal_code = request.POST.get('postal_code')
        address.address = request.POST.get('address')
        address.detail_address = request.POST.get('detail_address')
        address.is_default = request.POST.get('is_default') == 'on'
        address.save()
        
        messages.success(request, '배송지가 저장되었습니다.')
    
    return redirect('shop:mypage')


@login_required
def delete_address(request, address_id):
    """배송지 삭제"""
    if request.method == 'POST':
        from accounts.models import ShippingAddress
        address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
        address.delete()
        messages.success(request, '배송지가 삭제되었습니다.')
    
    return redirect('shop:mypage')


@login_required
def password_change(request):
    """비밀번호 변경"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # 현재 비밀번호 확인
        if not request.user.check_password(current_password):
            messages.error(request, '현재 비밀번호가 올바르지 않습니다.')
            return redirect('shop:password_change')
        
        # 새 비밀번호 확인
        if new_password != confirm_password:
            messages.error(request, '새 비밀번호가 일치하지 않습니다.')
            return redirect('shop:password_change')
        
        # 비밀번호 길이 확인
        if len(new_password) < 8:
            messages.error(request, '비밀번호는 8자 이상이어야 합니다.')
            return redirect('shop:password_change')
        
        # 비밀번호 변경
        request.user.set_password(new_password)
        request.user.save()
        
        # 세션 업데이트 (로그아웃 방지)
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)
        
        messages.success(request, '비밀번호가 변경되었습니다.')
        return redirect('shop:mypage')
    
    from core.models import SystemSettings
    context = {
        'site_name': SystemSettings.get_settings().site_name
    }
    return render(request, 'accounts/user_password_change.html', context)


@login_required
def wishlist(request):
    """위시리스트"""
    from .models import Wishlist
    
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'shop/wishlist.html', context)


@login_required
def toggle_wishlist(request, product_id):
    """위시리스트 추가/삭제 토글"""
    from django.http import JsonResponse
    from .models import Wishlist
    
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id, status='ACTIVE')
        
        # 위시리스트에 있는지 확인
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if not created:
            # 이미 있으면 삭제
            wishlist_item.delete()
            is_wishlisted = False
            message = '위시리스트에서 제거되었습니다.'
        else:
            # 없으면 추가됨
            is_wishlisted = True
            message = '위시리스트에 추가되었습니다.'
        
        # 현재 위시리스트 개수
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
        
        return JsonResponse({
            'success': True,
            'is_wishlisted': is_wishlisted,
            'message': message,
            'wishlist_count': wishlist_count
        })
    
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})


@login_required
def cancel_order(request, pk):
    """주문 취소"""
    if request.method == 'POST':
        from django.http import JsonResponse
        from django.utils import timezone
        
        order = get_object_or_404(Order, pk=pk, user=request.user)
        
        # 취소 가능한 상태인지 확인
        if order.status not in ['PENDING', 'CONFIRMED']:
            return JsonResponse({
                'success': False,
                'message': '현재 상태에서는 주문을 취소할 수 없습니다.'
            })
        
        # 주문 취소 처리
        order.status = 'CANCELLED'
        order.cancelled_date = timezone.now()
        order.save()
        
        # 재고 복구
        for item in order.items.all():
            item.product.stock_quantity += item.quantity
            item.product.save()
        
        messages.success(request, '주문이 취소되었습니다.')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})


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
