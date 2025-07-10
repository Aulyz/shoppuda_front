from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views

app_name = 'api'

router = DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'orders', views.OrderViewSet)
router.register(r'platforms', views.PlatformViewSet)
router.register(r'stock-movements', views.StockMovementViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
    path('dashboard/stats/', views.DashboardStatsView.as_view(), name='dashboard_stats'),
    path('products/search/', views.ProductSearchView.as_view(), name='product_search'),
    path('sync/platforms/', views.PlatformSyncView.as_view(), name='platform_sync'),
]