# notifications/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.generic import ListView
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Notification
import json

@method_decorator(login_required, name='dispatch')
class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = self.request.user.notifications.all()
        
        # 필터링
        notification_type = self.request.GET.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        # 검색
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(message__icontains=search)
            )
        
        # 읽음 상태 필터
        read_status = self.request.GET.get('read')
        if read_status == 'unread':
            queryset = queryset.filter(is_read=False)
        elif read_status == 'read':
            queryset = queryset.filter(is_read=True)
        
        return queryset

@login_required
@require_http_methods(["GET"])
def notification_api(request):
    """알림 API - 읽지 않은 알림 개수 및 최신 알림 반환"""
    user = request.user
    
    # 읽지 않은 알림 개수
    unread_count = user.notifications.filter(is_read=False).count()
    
    # 최신 알림 5개
    recent_notifications = user.notifications.all()[:5]
    
    notifications_data = []
    for notification in recent_notifications:
        notifications_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'created_at': notification.created_at.isoformat(),
            'is_read': notification.is_read,
            'url': notification.url,
            'icon': notification.get_icon(),
            'color': notification.get_color(),
            'time_ago': notification.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return JsonResponse({
        'unread_count': unread_count,
        'notifications': notifications_data
    })

@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """특정 알림을 읽음 처리"""
    try:
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            user=request.user
        )
        
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        return JsonResponse({
            'success': True,
            'message': '알림을 읽음 처리했습니다.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': '알림 읽음 처리에 실패했습니다.'
        }, status=400)

@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """모든 알림을 읽음 처리"""
    try:
        request.user.notifications.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'message': '모든 알림을 읽음 처리했습니다.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': '알림 읽음 처리에 실패했습니다.'
        }, status=400)

@login_required
@require_http_methods(["DELETE"])
def delete_notification(request, notification_id):
    """알림 삭제"""
    try:
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            user=request.user
        )
        
        notification.delete()
        
        return JsonResponse({
            'success': True,
            'message': '알림을 삭제했습니다.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': '알림 삭제에 실패했습니다.'
        }, status=400)


# notifications/urls.py
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='list'),
    path('api/', views.notification_api, name='api'),
    path('mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_notifications_read, name='mark_all_read'),
    path('delete/<int:notification_id>/', views.delete_notification, name='delete'),
]


# notifications/admin.py
from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')