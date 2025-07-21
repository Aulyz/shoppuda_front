
# notifications/consumers.py
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Notification

User = get_user_model()

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return
            
        # 사용자별 그룹 생성
        self.group_name = f"user_{self.user.id}"
        
        # 그룹에 채널 추가
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        # WebSocket 연결 수락
        await self.accept()
        
        # 연결 시 읽지 않은 알림 전송
        await self.send_unread_notifications()
    
    async def disconnect(self, close_code):
        # 그룹에서 채널 제거
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """클라이언트로부터 메시지 수신"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'mark_read':
                # 알림 읽음 처리
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
                
            elif message_type == 'mark_all_read':
                # 모든 알림 읽음 처리
                await self.mark_all_notifications_read()
                
        except json.JSONDecodeError:
            pass
    
    async def send_notification(self, event):
        """그룹으로부터 알림 메시지 수신 및 전송"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['data']
        }))
    
    async def send_unread_notifications(self):
        """읽지 않은 알림들을 전송"""
        notifications = await self.get_unread_notifications()
        
        for notification in notifications:
            await self.send(text_data=json.dumps({
                'type': 'notification',
                'data': {
                    'id': notification.id,
                    'title': notification.title,
                    'message': notification.message,
                    'notification_type': notification.notification_type,
                    'created_at': notification.created_at.isoformat(),
                    'is_read': notification.is_read,
                    'url': notification.url,
                    'icon': notification.get_icon(),
                    'color': notification.get_color()
                }
            }))
    
    @database_sync_to_async
    def get_unread_notifications(self):
        """읽지 않은 알림 조회"""
        return list(self.user.notifications.filter(is_read=False).order_by('-created_at')[:10])
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """특정 알림을 읽음 처리"""
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=self.user
            )
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
            return True
        except Notification.DoesNotExist:
            return False
    
    @database_sync_to_async
    def mark_all_notifications_read(self):
        """모든 알림을 읽음 처리"""
        self.user.notifications.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return True