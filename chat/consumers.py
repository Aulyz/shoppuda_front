import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import ChatSession, ChatMessage, ChatNote

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print(f"ChatConsumer connect called")  # 디버깅용
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.session_group_name = f'chat_{self.session_id}'
        self.user = self.scope['user']
        print(f"Session ID: {self.session_id}, User: {self.user}")  # 디버깅용
        
        # 그룹에 참가
        await self.channel_layer.group_add(
            self.session_group_name,
            self.channel_name
        )
        
        await self.accept()
        print(f"WebSocket accepted for session {self.session_id}")  # 디버깅용
        
        # 세션 상태 업데이트
        if self.user.is_authenticated and self.user.user_type in ['STAFF', 'ADMIN']:
            await self.update_session_status('active')
            await self.send_system_message('상담원이 연결되었습니다.')
        else:
            await self.send_system_message('고객님이 연결되었습니다.')
            # 새 채팅 상담 알림을 관리자 대시보드에 전송
            await self.notify_new_chat_session()
    
    async def disconnect(self, close_code):
        # 연결 종료 전에 상대방에게 알림
        user_type = await self.get_sender_type()
        if user_type == 'agent':
            await self.send_system_message('상담원이 채팅을 종료했습니다.')
        else:
            await self.send_system_message('고객님이 채팅을 종료했습니다.')
        
        # 그룹에서 나가기
        await self.channel_layer.group_discard(
            self.session_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        print(f"Received data: {text_data}")  # 디버깅용
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        print(f"Message type: {message_type}")  # 디버깅용
        
        if message_type == 'message':
            await self.handle_message(data)
        elif message_type == 'typing':
            await self.handle_typing(data)
        elif message_type == 'read':
            await self.handle_read(data)
        elif message_type == 'end_chat':
            await self.handle_end_chat(data)
        elif message_type == 'rating':
            await self.handle_rating(data)
    
    async def handle_message(self, data):
        content = data.get('message', '') or data.get('content', '')  # 'message' 필드도 체크
        file_url = data.get('file_url', '')
        message_type = data.get('message_type', 'text')
        print(f"Handling message: {content}")  # 디버깅용
        
        # 메시지 저장
        message = await self.save_message(content, message_type, file_url)
        print(f"Message saved: {message.id}")  # 디버깅용
        
        # 그룹의 모든 사용자에게 메시지 전송
        await self.channel_layer.group_send(
            self.session_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': str(message.id),
                    'content': content,
                    'sender': self.user.username if self.user.is_authenticated else '익명',
                    'sender_type': await self.get_sender_type(),
                    'message_type': message_type,
                    'file_url': file_url,
                    'created_at': message.created_at.isoformat(),
                }
            }
        )
    
    async def handle_typing(self, data):
        is_typing = data.get('is_typing', False)
        
        await self.channel_layer.group_send(
            self.session_group_name,
            {
                'type': 'typing_indicator',
                'data': {
                    'user': self.user.username if self.user.is_authenticated else '익명',
                    'is_typing': is_typing,
                }
            }
        )
    
    async def handle_read(self, data):
        message_id = data.get('message_id')
        if message_id:
            await self.mark_message_as_read(message_id)
    
    async def handle_end_chat(self, data):
        reason = data.get('reason', 'user_request')
        
        # 종료 사유에 따른 메시지
        if reason == 'inactivity':
            message = '5분 이상 응답이 없어 채팅이 자동으로 종료되었습니다.'
        elif reason == 'page_unload':
            message = '고객이 페이지를 떠나 채팅이 종료되었습니다.'
        else:
            message = '채팅이 종료되었습니다.'
            
        await self.update_session_status('closed')
        await self.send_system_message(message)
        
        await self.channel_layer.group_send(
            self.session_group_name,
            {
                'type': 'chat_ended',
                'data': {'reason': reason}
            }
        )
        
        # 관리자 대시보드에도 알림
        await self.channel_layer.group_send(
            'agent_dashboard',
            {
                'type': 'session_status_update',
                'data': {
                    'session_id': str(self.session_id),
                    'status': 'closed',
                    'reason': reason
                }
            }
        )
    
    async def handle_rating(self, data):
        rating = data.get('rating')
        feedback = data.get('feedback', '')
        
        await self.save_rating(rating, feedback)
        await self.send_system_message(f'평가해 주셔서 감사합니다. (평점: {rating}/5)')
    
    # WebSocket 이벤트 핸들러
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'data': event['message']
        }))
    
    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'data': event['data']
        }))
    
    async def chat_ended(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_ended',
            'data': event['data']
        }))
    
    async def system_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'system',
            'data': event['data']
        }))
    
    # 헬퍼 메서드
    async def send_system_message(self, content):
        message = await self.save_system_message(content)
        
        await self.channel_layer.group_send(
            self.session_group_name,
            {
                'type': 'system_message',
                'data': {
                    'content': content,
                    'created_at': message.created_at.isoformat(),
                }
            }
        )
    
    @database_sync_to_async
    def save_message(self, content, message_type='text', file_url=''):
        session = ChatSession.objects.get(id=self.session_id)
        sender_type = self.get_sender_type_sync()
        
        return ChatMessage.objects.create(
            session=session,
            sender=self.user if self.user.is_authenticated else None,
            sender_type=sender_type,
            message_type=message_type,
            content=content,
            file_url=file_url
        )
    
    @database_sync_to_async
    def save_system_message(self, content):
        session = ChatSession.objects.get(id=self.session_id)
        
        return ChatMessage.objects.create(
            session=session,
            sender=None,
            sender_type='system',
            message_type='system',
            content=content
        )
    
    @database_sync_to_async
    def get_sender_type(self):
        return self.get_sender_type_sync()
    
    def get_sender_type_sync(self):
        if not self.user.is_authenticated:
            return 'customer'
        elif self.user.user_type in ['STAFF', 'ADMIN']:
            return 'agent'
        else:
            return 'customer'
    
    @database_sync_to_async
    def update_session_status(self, status):
        session = ChatSession.objects.get(id=self.session_id)
        session.status = status
        
        if status == 'active' and not session.started_at:
            session.started_at = timezone.now()
            if self.user.is_authenticated and self.user.user_type in ['STAFF', 'ADMIN']:
                session.agent = self.user
        elif status == 'closed' and not session.ended_at:
            session.ended_at = timezone.now()
        
        session.save()
    
    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        try:
            message = ChatMessage.objects.get(id=message_id, session_id=self.session_id)
            if not message.is_read:
                message.is_read = True
                message.read_at = timezone.now()
                message.save()
        except ChatMessage.DoesNotExist:
            pass
    
    @database_sync_to_async
    def save_rating(self, rating, feedback):
        session = ChatSession.objects.get(id=self.session_id)
        session.rating = rating
        session.feedback = feedback
        session.save()
    
    @database_sync_to_async
    def notify_new_chat_session(self):
        """새 채팅 세션을 관리자 대시보드에 알림"""
        session = ChatSession.objects.get(id=self.session_id)
        
        # 관리자 대시보드에 알림
        return self.channel_layer.group_send(
            'agent_dashboard',
            {
                'type': 'new_chat_session',
                'data': {
                    'id': str(session.id),
                    'session_number': session.session_number,
                    'customer_name': session.customer_name or (session.customer.username if session.customer else '익명'),
                    'subject': session.subject or '상담 요청',
                    'created_at': session.created_at.isoformat(),
                }
            }
        )


class AgentDashboardConsumer(AsyncWebsocketConsumer):
    """상담원 대시보드용 WebSocket Consumer"""
    
    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated or self.user.user_type not in ['STAFF', 'ADMIN']:
            await self.close()
            return
        
        self.dashboard_group_name = 'agent_dashboard'
        
        # 대시보드 그룹에 참가
        await self.channel_layer.group_add(
            self.dashboard_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # 현재 대기중인 채팅 세션 정보 전송
        await self.send_waiting_sessions()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.dashboard_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'refresh':
            await self.send_waiting_sessions()
        elif action == 'join_chat':
            session_id = data.get('session_id')
            await self.join_chat_session(session_id)
    
    async def new_chat_session(self, event):
        """새로운 채팅 세션 알림"""
        await self.send(text_data=json.dumps({
            'type': 'new_session',
            'data': event['data']
        }))
    
    async def session_status_update(self, event):
        """세션 상태 업데이트"""
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def send_waiting_sessions(self):
        sessions = ChatSession.objects.filter(status='waiting').select_related('customer')
        
        session_data = []
        for session in sessions:
            session_data.append({
                'id': str(session.id),
                'session_number': session.session_number,
                'customer_name': session.customer_name or (session.customer.username if session.customer else '익명'),
                'subject': session.subject or '상담 요청',
                'created_at': session.created_at.isoformat(),
            })
        
        return self.send(text_data=json.dumps({
            'type': 'waiting_sessions',
            'data': session_data
        }))
    
    @database_sync_to_async
    def join_chat_session(self, session_id):
        try:
            session = ChatSession.objects.get(id=session_id, status='waiting')
            session.agent = self.user
            session.status = 'active'
            session.started_at = timezone.now()
            session.save()
            
            # 다른 상담원들에게 알림
            return self.channel_layer.group_send(
                self.dashboard_group_name,
                {
                    'type': 'session_status_update',
                    'data': {
                        'session_id': str(session.id),
                        'status': 'active',
                        'agent': self.user.username
                    }
                }
            )
        except ChatSession.DoesNotExist:
            pass