# File: platforms/urls.py
from django.urls import path
from . import views

app_name = 'platforms'

urlpatterns = [
    # 플랫폼 관리
    path('', views.PlatformListView.as_view(), name='list'),
    path('<int:pk>/', views.PlatformDetailView.as_view(), name='detail'),
    path('create/', views.PlatformCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.PlatformUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.platform_delete, name='delete'),
    
    # 동기화 관리
    path('sync/', views.PlatformSyncDashboardView.as_view(), name='sync'),
    path('<int:pk>/sync/', views.platform_sync, name='platform_sync'),
    path('sync/all/', views.sync_all_platforms, name='sync_all'),
    path('sync/status/', views.sync_status, name='sync_status'),
    
    # 플랫폼 상품 관리
    path('<int:pk>/products/', views.platform_products, name='products'),
    path('<int:pk>/products/sync/', views.sync_platform_products, name='sync_products'),
    path('<int:pk>/orders/', views.platform_orders, name='orders'),
    path('<int:pk>/orders/sync/', views.sync_platform_orders, name='sync_orders'),
    
    # 설정 관리
    path('settings/', views.PlatformSettingsView.as_view(), name='settings'),
    path('<int:pk>/settings/', views.PlatformSettingUpdateView.as_view(), name='platform_settings'),
    path('<int:pk>/test/', views.platform_test_connection, name='test_connection'),
    
    # API 키 관리
    path('<int:pk>/api-keys/', views.platform_api_keys, name='api_keys'),
    path('<int:pk>/api-keys/test/', views.test_api_keys, name='test_api_keys'),
    
    # 매핑 관리
    path('<int:pk>/mapping/', views.platform_mapping, name='mapping'),
    path('<int:pk>/mapping/categories/', views.category_mapping, name='category_mapping'),
    path('<int:pk>/mapping/attributes/', views.attribute_mapping, name='attribute_mapping'),
]