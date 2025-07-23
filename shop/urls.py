from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.home, name='home'),
    path('shop/products/', views.product_list, name='product_list'),
    path('shop/products/<uuid:pk>/', views.product_detail, name='product_detail'),
    path('shop/search/', views.search, name='search'),
    path('shop/cart/', views.cart_view, name='cart'),
    path('shop/cart/add/<uuid:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('shop/cart/update/<uuid:product_id>/', views.update_cart_item, name='update_cart_item'),
    path('shop/cart/remove/<uuid:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('shop/checkout/', views.checkout, name='checkout'),
    path('shop/orders/', views.order_list, name='order_list'),
    path('shop/orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('shop/orders/<int:pk>/cancel/', views.cancel_order, name='cancel_order'),
    path('shop/mypage/', views.mypage, name='mypage'),
    path('shop/mypage/update/', views.update_profile, name='update_profile'),
    path('shop/mypage/password/', views.password_change, name='password_change'),
    path('shop/mypage/address/add/', views.add_address, name='add_address'),
    path('shop/mypage/address/<int:address_id>/delete/', views.delete_address, name='delete_address'),
    path('shop/wishlist/', views.wishlist, name='wishlist'),
    path('shop/wishlist/toggle/<uuid:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
]