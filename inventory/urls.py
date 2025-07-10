# inventory/urls.py - 완성된 재고 관리 URL 설정
from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # 재고 현황 및 대시보드
    path('', views.inventory_overview, name='overview'),  # 새로 추가된 overview 뷰
    path('stock-overview/', views.stock_overview, name='stock_overview'),  # 기존 뷰
    path('list/', views.StockListView.as_view(), name='list'),
    
    # 재고 조정
    path('adjustment/', views.stock_adjustment, name='adjustment'),
    path('adjustment/apply/', views.apply_stock_adjustment, name='apply_stock_adjustment'),
    path('adjustment/bulk/', views.apply_bulk_stock_adjustment, name='apply_bulk_stock_adjustment'),
    
    # 재고 이동 관리
    path('movements/', views.StockMovementListView.as_view(), name='movements'),
    
    # 재고 상태별 목록
    path('low-stock/', views.LowStockListView.as_view(), name='low_stock'),
    path('out-of-stock/', views.OutOfStockListView.as_view(), name='out_of_stock'),
    path('overstock/', views.OverstockListView.as_view(), name='overstock'),
    
    # 데이터 내보내기
    path('export/', views.export_stock_data, name='export_stock_data'),
    path('export/movements/', views.export_movement_data, name='export_movement_data'),
    
    # API 엔드포인트
    path('api/stock-check/', views.stock_check_api, name='api_stock_check'),
    path('api/adjust/', views.stock_adjust_api, name='api_stock_adjust'),
]