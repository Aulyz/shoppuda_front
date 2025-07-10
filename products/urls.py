# products/urls.py - 완전한 상품 관리 URL 설정
from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # 상품 목록 및 검색
    path('', views.product_list, name='list'),
    
    # 상품 CRUD
    path('create/', views.product_create, name='create'),
    path('<uuid:pk>/', views.product_detail, name='detail'),
    path('<uuid:pk>/edit/', views.product_edit, name='edit'),
    path('<uuid:pk>/delete/', views.product_delete, name='delete'),
    
    # 상품 일괄 작업
    path('bulk-action/', views.product_bulk_action, name='bulk_action'),
    path('bulk-delete/', views.product_bulk_delete, name='bulk_delete'),
    path('bulk-update/', views.product_bulk_update, name='bulk_update'),
    
    # 상품 복제
    path('<uuid:pk>/clone/', views.product_clone, name='clone'),
    
    # ====================== 브랜드 관리 URL ======================
    
    # 브랜드 목록
    path('brands/', views.BrandListView.as_view(), name='brand_list'),
    path('brands/create/', views.BrandCreateView.as_view(), name='brand_create'),
    # 브랜드 상세 (필요한 경우)
    path('brands/<int:pk>/', views.BrandDetailView.as_view(), name='brand_detail'),
    path('brands/<int:pk>/edit/', views.BrandUpdateView.as_view(), name='brand_update'),
    path('brands/<int:pk>/delete/', views.BrandDeleteView.as_view(), name='brand_delete'),
    # 브랜드 AJAX API (템플릿의 Alpine.js와 연동)
    path('brands/bulk-action/', views.brand_bulk_action, name='brand_bulk_action'),
    path('brands/check-code/', views.check_brand_code, name='check_brand_code'),
    path('brands/stats/', views.brand_stats, name='brand_stats'),
    
    # 카테고리 관리 (웹페이지)
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/', views.category_detail, name='category_detail'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # 카테고리 AJAX API (템플릿의 Alpine.js와 연동)
    path('api/categories/create/', views.category_ajax_create, name='category_ajax_create'),
    path('api/categories/<int:pk>/update/', views.category_ajax_update, name='category_ajax_update'),
    path('api/categories/<int:pk>/delete/', views.category_ajax_delete, name='category_ajax_delete'),
    path('api/categories/bulk-action/', views.category_bulk_action, name='category_bulk_action'),
    path('api/categories/check-delete/<int:pk>', views.category_delete_check, name='category_delete_check'),

    # AJAX API
    path('api/check-sku/', views.check_sku, name='check_sku'),
    path('api/get-categories/', views.get_categories_api, name='get_categories_api'),
    path('api/get-brands/', views.get_brands_api, name='get_brands_api'),
    path('api/product-autocomplete/', views.product_autocomplete, name='product_autocomplete'),
    path('api/<uuid:pk>/quick-info/', views.product_quick_info, name='product_quick_info'),
    path('api/dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
    
    # 이미지 관리
    path('<uuid:pk>/images/', views.product_images, name='product_images'),
    path('<uuid:pk>/images/upload/', views.upload_product_image, name='upload_product_image'),
    path('images/<int:image_id>/delete/', views.delete_product_image, name='delete_product_image'),
    path('images/<int:image_id>/set-primary/', views.set_primary_image, name='set_primary_image'),
    
    # 재고 관련
    path('<uuid:pk>/stock/', views.product_stock_detail, name='product_stock'),
    path('<uuid:pk>/stock/adjust/', views.adjust_product_stock, name='adjust_stock'),
    path('<uuid:pk>/stock/history/', views.product_stock_history, name='stock_history'),
    
    # 데이터 내보내기
    path('export/csv/', views.export_products_csv, name='export_csv'),
    path('export/excel/', views.export_products_excel, name='export_excel'),
    path('export/template/', views.download_import_template, name='import_template'),
    
    # 데이터 가져오기
    path('import/', views.import_products, name='import'),
    path('import/preview/', views.import_preview, name='import_preview'),
    path('import/confirm/', views.import_confirm, name='import_confirm'),
    
    # 상품 상태 변경
    path('<uuid:pk>/activate/', views.activate_product, name='activate'),
    path('<uuid:pk>/deactivate/', views.deactivate_product, name='deactivate'),
    path('<uuid:pk>/feature/', views.feature_product, name='feature'),
    path('<uuid:pk>/unfeature/', views.unfeature_product, name='unfeature'),
    
    # 가격 관리
    path('<uuid:pk>/price-history/', views.product_price_history, name='price_history'),
    path('<uuid:pk>/update-price/', views.update_product_price, name='update_price'),
    path('bulk-price-update/', views.bulk_price_update, name='bulk_price_update'),
    
    # 태그 관리
    path('tags/', views.tag_list, name='tag_list'),
    path('tags/autocomplete/', views.tag_autocomplete, name='tag_autocomplete'),
    
    # 통계 및 보고서
    path('stats/', views.product_stats, name='stats'),
    path('reports/low-stock/', views.low_stock_report, name='low_stock_report'),
    path('reports/bestsellers/', views.bestsellers_report, name='bestsellers_report'),
    path('reports/slow-movers/', views.slow_movers_report, name='slow_movers_report'),
    
    # 웹훅 및 외부 연동
    path('webhook/stock-update/', views.webhook_stock_update, name='webhook_stock_update'),
]