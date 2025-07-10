# dashboard/urls.py

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('chart-data/', views.dashboard_chart_data, name='chart_data'),
    path('stats/', views.dashboard_stats, name='stats'),
    path('recent-orders/', views.dashboard_recent_orders, name='recent_orders'),
]