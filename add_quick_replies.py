import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopuda.settings')
django.setup()

from chat.models import ChatQuickReply
from accounts.models import User

# 샘플 빠른 답변 데이터
quick_replies = [
    {
        'title': '인사말',
        'category': '인사',
        'content': '안녕하세요! 무엇을 도와드릴까요?'
    },
    {
        'title': '감사 인사',
        'category': '인사',
        'content': '문의해 주셔서 감사합니다. 즐거운 쇼핑되세요!'
    },
    {
        'title': '배송 안내',
        'category': '배송',
        'content': '주문하신 상품은 결제 완료 후 영업일 기준 2-3일 이내에 배송됩니다. 배송 추적은 마이페이지에서 확인하실 수 있습니다.'
    },
    {
        'title': '교환/반품 안내',
        'category': '교환/반품',
        'content': '상품 수령 후 7일 이내에 교환/반품이 가능합니다. 단, 상품 태그를 제거하거나 착용한 경우에는 교환/반품이 불가능합니다.'
    },
    {
        'title': '결제 수단',
        'category': '결제',
        'content': '신용카드, 체크카드, 무통장입금, 카카오페이, 네이버페이 등 다양한 결제 수단을 이용하실 수 있습니다.'
    },
    {
        'title': '회원 혜택',
        'category': '회원',
        'content': '회원 가입 시 즉시 사용 가능한 3,000원 할인 쿠폰을 드립니다. 또한 구매 금액의 1%를 포인트로 적립해드립니다.'
    },
    {
        'title': '영업 시간',
        'category': '기타',
        'content': '고객센터 운영시간은 평일 09:00 ~ 18:00입니다. 주말 및 공휴일은 휴무입니다.'
    },
    {
        'title': '주문 확인',
        'category': '주문',
        'content': '주문 내역은 마이페이지 > 주문 내역에서 확인하실 수 있습니다. 주문번호를 알려주시면 더 빠르게 확인해드릴 수 있습니다.'
    }
]

# 첫 번째 관리자 계정 찾기
try:
    admin_user = User.objects.filter(user_type='ADMIN').first()
    if not admin_user:
        admin_user = User.objects.filter(is_superuser=True).first()
    
    # 빠른 답변 추가
    for reply_data in quick_replies:
        reply, created = ChatQuickReply.objects.get_or_create(
            title=reply_data['title'],
            defaults={
                'content': reply_data['content'],
                'category': reply_data['category'],
                'created_by': admin_user,
                'is_active': True
            }
        )
        if created:
            print(f"빠른 답변 추가: {reply.title}")
        else:
            print(f"이미 존재: {reply.title}")
    
    print(f"\n총 {ChatQuickReply.objects.count()}개의 빠른 답변이 등록되었습니다.")
    
except Exception as e:
    print(f"오류 발생: {e}")
    print("관리자 계정이 없어 빠른 답변을 추가할 수 없습니다.")