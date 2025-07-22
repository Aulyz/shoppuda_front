from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # 고객용
    path('start/', views.start_chat, name='start_chat'),
    path('start/ajax/', views.start_chat_ajax, name='start_chat_ajax'),
    path('room/<uuid:session_id>/', views.chat_room, name='chat_room'),
    path('widget/', views.chat_widget, name='chat_widget'),
    
    # 상담원용
    path('agent/dashboard/', views.agent_dashboard, name='agent_dashboard'),
    path('agent/join/<uuid:session_id>/', views.join_chat_session, name='join_chat_session'),
    path('agent/history/', views.chat_history, name='chat_history'),
    path('agent/detail/<uuid:session_id>/', views.chat_detail, name='chat_detail'),
    
    # 빠른 답변
    path('quick-reply/add/', views.add_quick_reply, name='add_quick_reply'),
    path('quick-reply/list/', views.quick_reply_list, name='quick_reply_list'),
    path('quick-reply/update-usage/', views.update_quick_reply_usage, name='update_quick_reply_usage'),
]