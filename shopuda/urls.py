from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    # Django 관리자
    path('django-admin/', admin.site.urls),
    
    # 계정 관련 (공통)
    path('accounts/', include('accounts.urls')),
    
    # 관리자용 URL들 (기존 구조 유지하되 접근 제어는 미들웨어로)
    path('dashboard/', include('dashboard.urls')),
    path('products/', include('products.urls')),
    path('orders/', include('orders.urls')),
    path('inventory/', include('inventory.urls')),
    path('platforms/', include('platforms.urls')),
    path('reports/', include('reports.urls')),
    path('core/', include('core.urls')),
    path('notifications/', include('notifications.urls')),
    path('search/', include('search.urls')),
    path('chat/', include('chat.urls')),
    
    # API
    path('api/', include('api.urls')),
    
    # 사용자용 쇼핑몰 (맨 마지막에 위치)
    path('', include('shop.urls')),
]

# 개발 환경에서 미디어 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 관리자 사이트 커스터마이징
admin.site.site_header = 'Shopuda ERP 관리'
admin.site.site_title = 'Shopuda ERP'
admin.site.index_title = 'Shopuda ERP 관리자'
