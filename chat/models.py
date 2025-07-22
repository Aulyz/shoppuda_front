from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class ChatSession(models.Model):
    """채팅 세션 모델"""
    SESSION_STATUS_CHOICES = [
        ('waiting', '대기중'),
        ('active', '진행중'),
        ('closed', '종료'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    
    # 고객 정보
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_sessions')
    customer_name = models.CharField(max_length=100, null=True, blank=True)
    customer_email = models.EmailField(null=True, blank=True)
    customer_phone = models.CharField(max_length=20, null=True, blank=True)
    
    # 상담원 정보
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='agent_chat_sessions')
    
    # 세션 정보
    status = models.CharField(max_length=10, choices=SESSION_STATUS_CHOICES, default='waiting')
    subject = models.CharField(max_length=200, null=True, blank=True)
    
    # 시간 정보
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # 평가
    rating = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'chat_sessions'
        ordering = ['-created_at']
        verbose_name = '채팅 세션'
        verbose_name_plural = '채팅 세션'
        
    def save(self, *args, **kwargs):
        if not self.session_number:
            # 세션 번호 자동 생성 (예: CHAT20250122001)
            today = timezone.now().strftime('%Y%m%d')
            count = ChatSession.objects.filter(session_number__startswith=f'CHAT{today}').count() + 1
            self.session_number = f'CHAT{today}{count:03d}'
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f'{self.session_number} - {self.customer_name or self.customer or "익명"}'


class ChatMessage(models.Model):
    """채팅 메시지 모델"""
    MESSAGE_TYPE_CHOICES = [
        ('text', '텍스트'),
        ('image', '이미지'),
        ('file', '파일'),
        ('system', '시스템'),
    ]
    
    SENDER_TYPE_CHOICES = [
        ('customer', '고객'),
        ('agent', '상담원'),
        ('system', '시스템'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    
    # 발신자 정보
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    sender_type = models.CharField(max_length=10, choices=SENDER_TYPE_CHOICES)
    
    # 메시지 내용
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default='text')
    content = models.TextField()
    file_url = models.URLField(null=True, blank=True)
    
    # 시간 정보
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # 메시지는 수정 불가능 (읽기 전용)
    
    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']
        verbose_name = '채팅 메시지'
        verbose_name_plural = '채팅 메시지'
        # 메시지 수정 방지를 위한 권한 설정
        permissions = [
            ('can_read_messages', 'Can read chat messages'),
        ]
        
    def __str__(self):
        return f'{self.session.session_number} - {self.sender_type}: {self.content[:50]}'


class ChatNote(models.Model):
    """상담원의 채팅 메모 모델"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='notes')
    agent = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # 메모 내용
    content = models.TextField()
    is_important = models.BooleanField(default=False)
    
    # 시간 정보
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_notes'
        ordering = ['-created_at']
        verbose_name = '채팅 메모'
        verbose_name_plural = '채팅 메모'
        
    def __str__(self):
        return f'{self.session.session_number} - 메모 by {self.agent.username}'


class ChatQuickReply(models.Model):
    """빠른 답변 템플릿"""
    title = models.CharField(max_length=100)
    content = models.TextField()
    category = models.CharField(max_length=50, null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_quick_replies'
        ordering = ['-usage_count', 'title']
        verbose_name = '빠른 답변'
        verbose_name_plural = '빠른 답변'
        
    def __str__(self):
        return self.title


class ChatStatistics(models.Model):
    """채팅 통계 (일별)"""
    date = models.DateField(unique=True)
    total_sessions = models.IntegerField(default=0)
    completed_sessions = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0)  # 초 단위
    avg_session_duration = models.FloatField(default=0)  # 분 단위
    avg_rating = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_statistics'
        ordering = ['-date']
        verbose_name = '채팅 통계'
        verbose_name_plural = '채팅 통계'
        
    def __str__(self):
        return f'{self.date} 통계'
