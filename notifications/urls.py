# notifications/urls.py
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # 알림 목록 페이지
    path('', views.NotificationListView.as_view(), name='list'),
    
    # 알림 API
    path('api/', views.notification_api, name='api'),
    
    # 개별 알림 읽음 처리
    path('mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_read'),
    
    # 모든 알림 읽음 처리
    path('mark-all-read/', views.mark_all_notifications_read, name='mark_all_read'),
    
    # 알림 삭제
    path('delete/<int:notification_id>/', views.delete_notification, name='delete'),
]