from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import ChatSession, ChatMessage, ChatNote, ChatQuickReply, ChatStatistics


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('sender', 'sender_type', 'message_type', 'content', 'created_at', 'is_read')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False
        
    def has_change_permission(self, request, obj=None):
        return False


class ChatNoteInline(admin.TabularInline):
    model = ChatNote
    extra = 1
    fields = ('content', 'is_important', 'agent')
    readonly_fields = ('agent',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('content',)
        return self.readonly_fields


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('session_number', 'customer_display', 'agent', 'status', 'subject', 'created_at', 'rating_display')
    list_filter = ('status', 'created_at', 'rating')
    search_fields = ('session_number', 'customer_name', 'customer_email', 'subject')
    readonly_fields = ('id', 'session_number', 'created_at', 'started_at', 'ended_at')
    inlines = [ChatMessageInline, ChatNoteInline]
    
    fieldsets = (
        ('세션 정보', {
            'fields': ('id', 'session_number', 'status', 'subject')
        }),
        ('고객 정보', {
            'fields': ('customer', 'customer_name', 'customer_email', 'customer_phone')
        }),
        ('상담원 정보', {
            'fields': ('agent',)
        }),
        ('시간 정보', {
            'fields': ('created_at', 'started_at', 'ended_at')
        }),
        ('평가', {
            'fields': ('rating', 'feedback')
        }),
    )
    
    def customer_display(self, obj):
        if obj.customer:
            return obj.customer.username
        return obj.customer_name or '익명'
    customer_display.short_description = '고객'
    
    def rating_display(self, obj):
        if obj.rating:
            stars = '★' * obj.rating + '☆' * (5 - obj.rating)
            return format_html('<span style="color: #f39c12;">{}</span>', stars)
        return '-'
    rating_display.short_description = '평가'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'sender_type', 'content_preview', 'message_type', 'created_at', 'is_read')
    list_filter = ('sender_type', 'message_type', 'is_read', 'created_at')
    search_fields = ('content', 'session__session_number')
    readonly_fields = ('id', 'session', 'sender', 'sender_type', 'message_type', 'content', 'file_url', 'created_at', 'is_read', 'read_at')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '내용'
    
    def has_add_permission(self, request):
        return False
        
    def has_change_permission(self, request, obj=None):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ChatNote)
class ChatNoteAdmin(admin.ModelAdmin):
    list_display = ('session', 'agent', 'content_preview', 'is_important', 'created_at')
    list_filter = ('is_important', 'created_at')
    search_fields = ('content', 'session__session_number')
    readonly_fields = ('created_at', 'updated_at')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '내용'


@admin.register(ChatQuickReply)
class ChatQuickReplyAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'usage_count', 'is_active', 'created_by')
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'content')
    readonly_fields = ('usage_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('title', 'category', 'content')
        }),
        ('상태', {
            'fields': ('is_active', 'usage_count')
        }),
        ('기록', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(ChatStatistics)
class ChatStatisticsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_sessions', 'completed_sessions', 'avg_response_time_display', 'avg_session_duration_display', 'avg_rating_display')
    list_filter = ('date',)
    readonly_fields = ('date', 'total_sessions', 'completed_sessions', 'avg_response_time', 'avg_session_duration', 'avg_rating', 'created_at', 'updated_at')
    
    def avg_response_time_display(self, obj):
        return f'{obj.avg_response_time:.1f}초'
    avg_response_time_display.short_description = '평균 응답시간'
    
    def avg_session_duration_display(self, obj):
        return f'{obj.avg_session_duration:.1f}분'
    avg_session_duration_display.short_description = '평균 상담시간'
    
    def avg_rating_display(self, obj):
        if obj.avg_rating:
            return f'{obj.avg_rating:.1f} / 5.0'
        return '-'
    avg_rating_display.short_description = '평균 평점'
