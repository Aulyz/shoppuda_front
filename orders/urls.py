# File: orders/urls.py
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # 기본 주문 관리
    path('', views.OrderListView.as_view(), name='list'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.OrderUpdateView.as_view(), name='edit'),
    path('<int:pk>/status/', views.order_status_update, name='status_update'),
    path('bulk-action/', views.order_bulk_action, name='bulk_action'),
    path('export-csv/', views.order_export_csv, name='export_csv'),
    
    # 상태별 주문 조회
    path('pending/', views.PendingOrderListView.as_view(), name='pending'),
    path('processing/', views.ProcessingOrderListView.as_view(), name='processing'),
    path('shipped/', views.ShippedOrderListView.as_view(), name='shipped'),
    path('delivered/', views.DeliveredOrderListView.as_view(), name='delivered'),
    path('cancelled/', views.CancelledOrderListView.as_view(), name='cancelled'),
    
    # 주문 액션
    path('<int:pk>/print/', views.order_print, name='print'),
    path('<int:pk>/duplicate/', views.order_duplicate, name='duplicate'),
    path('<int:pk>/cancel/', views.order_cancel, name='cancel'),
    path('<int:pk>/refund/', views.order_refund, name='refund'),
    
    # 이메일 관련
    path('<int:pk>/send-email/', views.send_order_email, name='send_email'),

    # 배송 관리
    path('<int:pk>/shipping/', views.order_shipping_update, name='shipping_update'),
    path('<int:pk>/tracking/', views.order_tracking_update, name='tracking_update'),
]