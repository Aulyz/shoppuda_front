# reports/urls.py - 기존 구조 유지하며 새 재고 리포트 추가
from django.urls import path, include
from . import views

app_name = 'reports'

urlpatterns = [
    # 기존 보고서 (그대로 유지)
    path('', views.reports_dashboard, name='dashboard'),
    path('inventory/', views.inventory_reports, name='inventory_old'),  # 기존 재고 리포트
    path('sales/', views.sales_reports, name='sales'),
    path('financial/', views.financial_reports, name='financial'),
    path('export/<str:report_type>/', views.export_report, name='export'),
    
    # 새로운 고급 재고 리포트 (실제 데이터 연동)
    path('inventory-advanced/', views.InventoryReportView.as_view(), name='inventory'),
    path('inventory-advanced/data/', views.inventory_report_data, name='inventory_data'),
    path('inventory-advanced/chart-data/', views.inventory_chart_data, name='inventory_chart_data'),
    path('inventory-advanced/export/', views.export_inventory_report, name='export_inventory'),
    path('inventory-advanced/alerts/', views.inventory_alerts_api, name='inventory_alerts'),
    
    # 기존 기능들 (그대로 유지)
    path('templates/', views.ReportTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.ReportTemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/edit/', views.ReportTemplateUpdateView.as_view(), name='template_edit'),
    path('templates/<int:pk>/delete/', views.ReportTemplateDeleteView.as_view(), name='template_delete'),
    
    path('generated/', views.GeneratedReportListView.as_view(), name='generated_list'),
    path('generated/<uuid:report_id>/', views.GeneratedReportDetailView.as_view(), name='generated_detail'),
    path('download/<uuid:report_id>/', views.download_report, name='download'),
    
    path('schedules/', views.ReportScheduleListView.as_view(), name='schedule_list'),
    path('schedules/create/', views.ReportScheduleCreateView.as_view(), name='schedule_create'),
    path('schedules/<int:pk>/edit/', views.ReportScheduleUpdateView.as_view(), name='schedule_edit'),
    path('schedules/<int:pk>/toggle/', views.toggle_schedule, name='schedule_toggle'),
    
    path('api/', include([
        path('chart-data/', views.get_chart_data, name='api_chart_data'),
        path('dashboard-summary/', views.api_dashboard_summary, name='api_dashboard_summary'),
        path('report-status/<uuid:report_id>/', views.api_report_status, name='api_report_status'),
        path('generate-report/', views.api_generate_report, name='api_generate_report'),
        path('quick-stats/', views.api_quick_stats, name='api_quick_stats'),
    ])),
    
    path('bookmarks/', views.ReportBookmarkListView.as_view(), name='bookmark_list'),
    path('bookmarks/add/', views.add_bookmark, name='add_bookmark'),
    path('bookmarks/<int:pk>/delete/', views.delete_bookmark, name='delete_bookmark'),
    
    path('advanced/', views.advanced_reports, name='advanced'),
    path('compare/', views.comparison_reports, name='compare'),
    path('trends/', views.trend_analysis, name='trends'),
    
    path('realtime/', views.realtime_dashboard, name='realtime'),
    path('alerts/', views.report_alerts, name='alerts'),
]