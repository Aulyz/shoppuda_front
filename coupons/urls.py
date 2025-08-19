from django.urls import path
from . import views

app_name = 'coupons'

urlpatterns = [
    # 쿠폰 관리 (관리자)
    path('admin/', views.CouponListView.as_view(), name='admin_list'),
    path('admin/create/', views.CouponCreateView.as_view(), name='admin_create'),
    path('admin/<int:pk>/edit/', views.CouponUpdateView.as_view(), name='admin_edit'),
    path('admin/<int:pk>/delete/', views.CouponDeleteView.as_view(), name='admin_delete'),
    path('admin/<int:pk>/detail/', views.CouponDetailView.as_view(), name='admin_detail'),
    path('admin/<int:pk>/duplicate/', views.duplicate_coupon, name='admin_duplicate'),
    path('admin/<int:pk>/toggle-active/', views.toggle_coupon_active, name='admin_toggle_active'),
    
    # 쿠폰 발급 관리
    path('admin/issue/', views.IssueCouponView.as_view(), name='admin_issue'),
    path('admin/issue/bulk/', views.BulkIssueCouponView.as_view(), name='admin_bulk_issue'),
    path('admin/issued/', views.IssuedCouponListView.as_view(), name='admin_issued_list'),
    
    # 쿠폰 통계
    path('admin/stats/', views.CouponStatsView.as_view(), name='admin_stats'),
    
    # 사용자 쿠폰 (고객)
    path('my/', views.MyCouponListView.as_view(), name='my_list'),
    path('claim/', views.ClaimCouponView.as_view(), name='claim'),
    path('available/', views.AvailableCouponListView.as_view(), name='available'),
    
    # API
    path('api/validate/', views.validate_coupon_api, name='api_validate'),
    path('api/calculate-discount/', views.calculate_discount_api, name='api_calculate_discount'),
]