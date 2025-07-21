from django.urls import path
from . import views
from . import views_admin

app_name = 'accounts'

urlpatterns = [
    # 인증 관련
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    
    # 프로필 관련
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('password/change/', views.password_change_view, name='password_change'),
    path('withdrawal/', views.withdrawal_view, name='withdrawal'),
    
    # 배송지 관련
    path('shipping-addresses/', views.ShippingAddressListView.as_view(), name='shipping_addresses'),
    path('shipping-addresses/add/', views.ShippingAddressCreateView.as_view(), name='shipping_address_add'),
    path('shipping-addresses/<int:pk>/edit/', views.ShippingAddressUpdateView.as_view(), name='shipping_address_edit'),
    path('shipping-addresses/<int:pk>/delete/', views.ShippingAddressDeleteView.as_view(), name='shipping_address_delete'),
    
    # 포인트 관련
    path('points/', views.point_history_view, name='point_history'),
    
    # API
    path('check-username/', views.check_username, name='check_username'),
    path('check-email/', views.check_email, name='check_email'),
    
    # 관리자 권한 관리
    path('admin/users/', views_admin.AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/create/', views_admin.AdminCreateUserView.as_view(), name='admin_user_create'),
    path('admin/users/<int:user_id>/', views_admin.user_detail_view, name='admin_user_detail'),
    path('admin/users/<int:user_id>/permissions/', views_admin.user_permissions_management, name='user_permissions'),
    path('admin/users/<int:user_id>/change-type/', views_admin.change_user_type, name='change_user_type'),
    path('admin/permissions/dashboard/', views_admin.permission_dashboard, name='permission_dashboard'),
]