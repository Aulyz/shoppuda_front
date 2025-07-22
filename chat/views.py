from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from .models import ChatSession, ChatMessage, ChatNote, ChatQuickReply
import uuid
import json


def start_chat(request):
    """채팅 시작 (고객용)"""
    # 새 채팅 세션 생성
    session = ChatSession.objects.create()
    
    # 로그인한 사용자인 경우 사용자 정보 연결
    if request.user.is_authenticated:
        session.customer = request.user
        session.customer_name = request.user.get_full_name() or request.user.username
        session.customer_email = request.user.email
        session.save()
    
    # POST 요청인 경우 (비로그인 사용자 정보)
    if request.method == 'POST':
        session.customer_name = request.POST.get('name', '')
        session.customer_email = request.POST.get('email', '')
        session.customer_phone = request.POST.get('phone', '')
        session.subject = request.POST.get('subject', '')
        session.save()
        
        return redirect('chat:chat_room', session_id=session.id)
    
    # 로그인 사용자는 바로 채팅룸으로
    if request.user.is_authenticated:
        return redirect('chat:chat_room', session_id=session.id)
    
    # 비로그인 사용자는 정보 입력 폼 표시
    return render(request, 'chat/start_chat.html')


def chat_room(request, session_id):
    """채팅룸 (고객 및 상담원용)"""
    session = get_object_or_404(ChatSession, id=session_id)
    
    # 권한 확인
    if request.user.is_authenticated:
        # 상담원이거나 본인의 채팅인 경우만 접근 가능
        if not (request.user.user_type in ['STAFF', 'ADMIN'] or session.customer == request.user):
            return redirect('shop:home')
    else:
        # 비로그인 사용자는 세션 쿠키로 확인
        if request.session.get('chat_session_id') != str(session_id):
            request.session['chat_session_id'] = str(session_id)
    
    # 이전 메시지 로드
    messages = session.messages.all().order_by('created_at')
    
    # 상담원인 경우 빠른 답변 로드
    quick_replies = None
    if request.user.is_authenticated and request.user.user_type in ['STAFF', 'ADMIN']:
        quick_replies = ChatQuickReply.objects.filter(is_active=True).order_by('-usage_count')
    
    context = {
        'session': session,
        'messages': messages,
        'quick_replies': quick_replies,
        'is_agent': request.user.is_authenticated and request.user.user_type in ['STAFF', 'ADMIN'],
    }
    
    return render(request, 'chat/chat_room.html', context)


@login_required
def agent_dashboard(request):
    """상담원 대시보드"""
    # 상담원 권한 확인
    if request.user.user_type not in ['STAFF', 'ADMIN']:
        return redirect('dashboard:home')
    
    # 대기중인 채팅
    waiting_sessions = ChatSession.objects.filter(
        status='waiting'
    ).order_by('created_at')
    
    # 진행중인 내 채팅
    my_active_sessions = ChatSession.objects.filter(
        status='active',
        agent=request.user
    ).order_by('-started_at')
    
    # 오늘의 통계
    today = timezone.now().date()
    today_stats = {
        'total_sessions': ChatSession.objects.filter(created_at__date=today).count(),
        'completed_sessions': ChatSession.objects.filter(ended_at__date=today).count(),
        'avg_rating': ChatSession.objects.filter(
            ended_at__date=today,
            rating__isnull=False
        ).aggregate(Avg('rating'))['rating__avg'] or 0,
    }
    
    context = {
        'waiting_sessions': waiting_sessions,
        'my_active_sessions': my_active_sessions,
        'today_stats': today_stats,
    }
    
    return render(request, 'chat/agent_dashboard.html', context)


@login_required
@require_POST
def join_chat_session(request, session_id):
    """상담원이 채팅 세션에 참여"""
    # 디버깅용 로그
    print(f"join_chat_session called: user={request.user}, session_id={session_id}")
    print(f"Method: {request.method}")
    print(f"Headers: {dict(request.headers)}")
    
    # 상담원 권한 확인
    if request.user.user_type not in ['STAFF', 'ADMIN']:
        return JsonResponse({'success': False, 'error': '권한이 없습니다.'})
    
    try:
        session = ChatSession.objects.get(id=session_id, status='waiting')
        session.agent = request.user
        session.status = 'active'
        session.started_at = timezone.now()
        session.save()
        
        return JsonResponse({'success': True, 'redirect_url': f'/chat/room/{session_id}/'})
    except ChatSession.DoesNotExist:
        return JsonResponse({'success': False, 'error': '존재하지 않거나 이미 처리된 채팅입니다.'})


@login_required
def chat_history(request):
    """채팅 이력 조회"""
    # 상담원 권한 확인
    if request.user.user_type not in ['STAFF', 'ADMIN']:
        return redirect('dashboard:home')
    
    # 검색 파라미터
    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # 쿼리셋 생성
    sessions = ChatSession.objects.all().select_related('customer', 'agent')
    
    # 검색 필터
    if search_query:
        sessions = sessions.filter(
            Q(session_number__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(customer_email__icontains=search_query) |
            Q(subject__icontains=search_query)
        )
    
    if status_filter:
        sessions = sessions.filter(status=status_filter)
    
    if date_from:
        sessions = sessions.filter(created_at__date__gte=date_from)
    
    if date_to:
        sessions = sessions.filter(created_at__date__lte=date_to)
    
    # 정렬
    sessions = sessions.order_by('-created_at')
    
    # 페이지네이션
    paginator = Paginator(sessions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'chat/chat_history.html', context)


@login_required
def chat_detail(request, session_id):
    """채팅 상세 조회"""
    # 상담원 권한 확인
    if request.user.user_type not in ['STAFF', 'ADMIN']:
        return redirect('dashboard:home')
    
    session = get_object_or_404(ChatSession, id=session_id)
    messages = session.messages.all().order_by('created_at')
    notes = session.notes.all().order_by('-created_at')
    
    # POST 요청 - 메모 추가
    if request.method == 'POST':
        content = request.POST.get('content', '')
        is_important = request.POST.get('is_important', False) == 'on'
        
        if content:
            ChatNote.objects.create(
                session=session,
                agent=request.user,
                content=content,
                is_important=is_important
            )
            return redirect('chat:chat_detail', session_id=session_id)
    
    context = {
        'session': session,
        'messages': messages,
        'notes': notes,
    }
    
    return render(request, 'chat/chat_detail.html', context)


@login_required
@require_POST
def add_quick_reply(request):
    """빠른 답변 추가"""
    # 상담원 권한 확인
    if request.user.user_type not in ['STAFF', 'ADMIN']:
        return JsonResponse({'success': False, 'error': '권한이 없습니다.'})
    
    title = request.POST.get('title', '')
    content = request.POST.get('content', '')
    category = request.POST.get('category', '')
    
    if title and content:
        quick_reply = ChatQuickReply.objects.create(
            title=title,
            content=content,
            category=category,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'id': quick_reply.id,
            'title': quick_reply.title,
            'content': quick_reply.content,
        })
    
    return JsonResponse({'success': False, 'error': '필수 정보가 누락되었습니다.'})


@login_required
def quick_reply_list(request):
    """빠른 답변 관리"""
    # 상담원 권한 확인
    if request.user.user_type not in ['STAFF', 'ADMIN']:
        return redirect('dashboard:home')
    
    quick_replies = ChatQuickReply.objects.all().order_by('category', '-usage_count')
    
    context = {
        'quick_replies': quick_replies,
    }
    
    return render(request, 'chat/quick_reply_list.html', context)


@login_required
@require_POST
def update_quick_reply_usage(request):
    """빠른 답변 사용 횟수 업데이트"""
    quick_reply_id = request.POST.get('id')
    
    try:
        quick_reply = ChatQuickReply.objects.get(id=quick_reply_id)
        quick_reply.usage_count += 1
        quick_reply.save()
        return JsonResponse({'success': True})
    except ChatQuickReply.DoesNotExist:
        return JsonResponse({'success': False})


def chat_widget(request):
    """채팅 위젯 (쇼핑몰 페이지에 삽입용)"""
    return render(request, 'chat/widget.html')


@require_POST
def start_chat_ajax(request):
    """AJAX로 채팅 세션 시작"""
    # 새 채팅 세션 생성
    session = ChatSession.objects.create()
    
    # 로그인한 사용자인 경우
    if request.user.is_authenticated:
        session.customer = request.user
        session.customer_name = request.user.get_full_name() or request.user.username
        session.customer_email = request.user.email
    else:
        # 비로그인 사용자 정보 (POST 데이터에서 가져오기)
        session.customer_name = request.POST.get('name', '')
        session.customer_email = request.POST.get('email', '')
        session.subject = request.POST.get('subject', '')
    
    session.save()
    
    # 세션 ID를 쿠키에 저장 (비로그인 사용자용)
    request.session['chat_session_id'] = str(session.id)
    
    return JsonResponse({
        'success': True,
        'session_id': str(session.id)
    })
