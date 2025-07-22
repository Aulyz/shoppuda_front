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
    path('shop/cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('shop/checkout/', views.checkout, name='checkout'),
    path('shop/orders/', views.order_list, name='order_list'),
    path('shop/orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('shop/mypage/', views.mypage, name='mypage'),
    path('shop/wishlist/', views.wishlist, name='wishlist'),
]