# Shopuda ERP 프로젝트 가이드

## 프로젝트 개요
**Shopuda ERP**는 Django 기반의 전자상거래 통합 관리 시스템입니다. 관리자용 ERP 시스템과 일반 사용자용 쇼핑몰을 통합한 플랫폼으로, 다중 온라인 쇼핑 플랫폼(쿠팡 등)의 제품, 주문, 재고를 통합 관리하며, 실시간 알림과 자동화된 보고서 기능을 제공합니다.

## 핵심 기능
### 관리자 기능
- 🛍️ **다중 플랫폼 통합**: 쿠팡 등 여러 온라인 마켓플레이스 통합 관리
- 📦 **재고 관리**: 실시간 재고 추적, 자동 알림, 재고 이동 관리
- 📋 **주문 처리**: 주문 접수, 처리, 배송 관리 및 상태 추적
- 📊 **보고서 시스템**: 자동 생성 및 스케줄링, 다양한 포맷 지원
- 🔔 **실시간 알림**: WebSocket 기반 실시간 알림
- 👥 **권한 관리**: 계층적 권한 시스템 및 사용자 역할 관리
- ✉️ **이메일 템플릿 관리**: 자동 발송 이메일 템플릿 및 트리거 설정

### 사용자 기능
- 🛒 **쇼핑몰**: 상품 브라우징, 검색, 상세 정보 조회
- 🛍️ **장바구니**: 상품 담기, 수량 조정, 삭제
- 📦 **주문**: 주문하기, 주문 내역 조회
- 👤 **마이페이지**: 개인정보 관리, 포인트 조회
- ❤️ **위시리스트**: 관심 상품 저장

## 기술 스택
### 백엔드
- **Django 5.x**: 웹 프레임워크
- **Django REST Framework**: API 개발
- **Celery + Redis**: 비동기 작업 처리
- **Django Channels**: WebSocket 지원

### 프론트엔드
- **Tailwind CSS**: 유틸리티 우선 CSS 프레임워크
- **JavaScript (Vanilla)**: 동적 기능 구현
- **다크모드 지원**: 시스템 테마 자동 감지

### 데이터베이스
- **SQLite**: 개발 환경 (현재)
- **PostgreSQL**: 프로덕션 환경 지원

## 프로젝트 구조
```
project/
├── accounts/          # 사용자 계정 및 권한 관리
├── api/              # REST API 엔드포인트
├── core/             # 핵심 시스템 기능 (설정, 이메일, 미들웨어)
├── dashboard/        # 관리자 메인 대시보드
├── inventory/        # 재고 관리 시스템
├── notifications/    # 알림 시스템
├── orders/          # 주문 관리
├── platforms/       # 외부 플랫폼 연동
├── products/        # 제품 카탈로그 관리
├── reports/         # 보고서 생성 및 관리
├── search/          # 통합 검색 기능
├── shop/            # 사용자용 쇼핑몰 앱
├── shopuda/         # Django 프로젝트 설정
├── static/          # 정적 파일 (CSS, JS)
├── templates/       # HTML 템플릿
├── media/           # 업로드된 파일
└── 문서/            # 프로젝트 문서
```

## 주요 모델 구조
### 사용자 시스템 (accounts)
- **User**: 커스텀 사용자 모델 (관리자 레벨 포함)
- **ShippingAddress**: 배송 주소 관리
- **PointHistory**: 포인트 이력 추적

### 제품 관리 (products)
- **Category**: 계층적 카테고리 구조
- **Brand**: 브랜드 정보
- **Product**: 제품 정보 (SKU, 바코드 포함)
- **ProductImage**: 제품 이미지 관리

### 주문 시스템 (orders)
- **Order**: 주문 정보 및 상태 관리
- **OrderItem**: 주문 항목
- **CancelRequest/RefundRequest**: 취소/환불 요청

### 재고 관리 (inventory)
- **StockLevel**: 제품별 재고 수준
- **StockMovement**: 재고 이동 기록
- **StockAlert**: 재고 알림 설정

### 플랫폼 연동 (platforms)
- **Platform**: 연동 플랫폼 정보
- **PlatformProduct**: 플랫폼별 제품 정보
- **Supplier**: 공급업체 관리

### 핵심 시스템 (core)
- **SystemSettings**: 시스템 전역 설정
- **EmailTemplate**: 이메일 템플릿 관리
- **EmailTrigger**: 이메일 자동 발송 트리거

## URL 구조
### 관리자 영역
- `/dashboard/` - 관리자 대시보드
- `/products/` - 상품 관리
- `/orders/` - 주문 관리
- `/inventory/` - 재고 관리
- `/reports/` - 보고서
- `/core/` - 시스템 설정

### 사용자 영역
- `/` - 쇼핑몰 홈
- `/shop/products/` - 상품 목록
- `/shop/products/<id>/` - 상품 상세
- `/shop/cart/` - 장바구니
- `/shop/checkout/` - 주문하기
- `/shop/mypage/` - 마이페이지
- `/shop/orders/` - 주문 내역
- `/shop/wishlist/` - 위시리스트

## 개발 시 주의사항

### 1. 권한 체크
- 모든 뷰에서 `@permission_required` 데코레이터 사용
- 관리자 레벨 확인: `user.admin_level >= required_level`
- 미들웨어를 통한 자동 접근 제어

### 2. 비동기 작업
- 시간이 오래 걸리는 작업은 Celery 태스크로 처리
- 예: 대량 데이터 가져오기, 보고서 생성

### 3. 실시간 기능
- WebSocket 연결은 `notifications/routing.py` 참조
- 알림 전송: `send_notification()` 함수 사용

### 4. 템플릿 구조
- 모든 페이지는 `base.html` 상속
- Tailwind CSS 클래스 사용
- 다크모드 지원을 위해 `dark:` 접두사 사용
- 반응형 디자인 필수 (모바일/태블릿/데스크톱)
- Alpine.js로 인터랙티브 기능 구현

### 5. API 개발
- ViewSet 기반 구조 사용
- 인증: TokenAuthentication
- 페이지네이션 기본 적용

## 자주 사용하는 명령어
```bash
# 개발 서버 실행
python manage.py runserver

# 마이그레이션
python manage.py makemigrations
python manage.py migrate

# 정적 파일 수집
python manage.py collectstatic

# Celery 워커 실행
celery -A shopuda worker -l info

# Redis 서버 실행
redis-server

# 테스트 실행
python manage.py test

# 관리자 계정 생성
python manage.py createsuperuser
```

## 환경 설정
### 개발 환경 설정
1. 가상환경 활성화: `venv\Scripts\activate` (Windows)
2. 의존성 설치: `pip install -r requirements.txt`
3. 데이터베이스 마이그레이션
4. Redis 서버 실행
5. 개발 서버 실행

### 주요 설정 값
- `DEBUG = True` (개발 환경)
- `ALLOWED_HOSTS = ['*']` (개발 환경)
- `TIME_ZONE = 'Asia/Seoul'`
- `LANGUAGE_CODE = 'ko-kr'`

## 테스트 및 디버깅
- Django Debug Toolbar 사용 가능
- 로그 파일: `logs/django.log`
- 에러 추적: Sentry 연동 가능

## 배포 준비사항
1. `SECRET_KEY` 변경
2. `DEBUG = False` 설정
3. `ALLOWED_HOSTS` 적절히 설정
4. PostgreSQL 데이터베이스 설정
5. 정적 파일 서빙 설정 (Nginx/Apache)
6. Gunicorn/uWSGI 설정
7. SSL 인증서 적용

## 최근 주요 업데이트
### 2024년 1월
- 사용자용 쇼핑몰 기능 추가
- URL 구조 개선 (관리자/사용자 분리)
- 이메일 템플릿 시스템 확장
- 이메일 자동 발송 트리거 기능 추가
- 접근 제어 미들웨어 구현

### 2025년 1월 22일
- **상품 목록 페이지 (`shop/product_list.html`) 구현**
  - 완전 반응형 디자인 (모바일/태블릿/데스크톱 최적화)
  - 계층적 카테고리 시스템 (상위 카테고리 선택 시 하위 카테고리 포함)
  - 호버 기반 카테고리 드롭다운 메뉴
  - 상품 정렬 기능 (최신순/가격순/이름순)
  - 재고 상태 실시간 표시
  - 할인율 배지 표시
  - 장바구니 빠른 추가 기능

- **시스템 설정 동적 적용**
  - `core.context_processors.system_settings` 수정
  - 사이트 이름, 태그라인, 로고를 모든 템플릿에서 사용 가능
  - `{{ site_name }}`, `{{ site_tagline }}`, `{{ site_logo_url }}` 변수 제공

- **사용자 전용 회원가입 페이지**
  - `templates/accounts/user_signup.html` 생성
  - 관리자 대시보드 요소 완전 제거
  - `shop/base.html` 템플릿 상속

- **통합 검색 기능**
  - `shop.views.search` 뷰 추가
  - 헤더 및 홈페이지 검색바 구현
  - 상품명, 설명, 브랜드, 카테고리, SKU 검색 지원
  - `templates/shop/search_results.html` 검색 결과 페이지

- **상품 상세 페이지**
  - `templates/shop/product_detail.html` 생성
  - 이미지 갤러리 (Alpine.js 활용)
  - 탭 기반 정보 표시
  - 관련 상품 추천 섹션

- **상품 이미지 시스템 개선**
  - `ProductImage` 모델에 `image_type` 필드 추가
  - 이미지 타입: primary(대표), gallery(갤러리), detail(상세)
  - 대표 이미지만 크기 제한 (800x800px, 2MB)
  - 상세 이미지는 제한 없음 (긴 홍보물 지원)
  - `ProductImageForm` 조건부 검증 로직 추가

- **데이터베이스 문제 해결**
  - orders 앱 마이그레이션 충돌 해결
  - `0004_merge_20250122_1100.py` 병합 마이그레이션 생성
  - django_session 테이블 수동 생성
  - reports, core 관련 테이블 생성
  - `create_superuser.py` 스크립트로 관리자 계정 생성

- **실시간 채팅 상담 시스템 구현**
  - `chat` 앱 생성 및 5개 모델 설계 (ChatSession, ChatMessage, ChatNote, ChatQuickReply, ChatStatistics)
  - WebSocket 기반 실시간 통신 (`consumers.py`)
  - 고객용 채팅 인터페이스 및 위젯
  - 상담원용 대시보드 및 관리 기능
  - 채팅 메시지 수정 불가 보안 정책 적용
  - 상담원 전용 메모 기능
  - 빠른 답변 템플릿 시스템

- **회원가입 중복확인 버그 수정**
  - `accounts.views.check_username` 로그인 제한 해제
  - `accounts.views.check_email` 로그인 제한 해제 및 조건부 처리

- **채팅 시스템 개선 (추가 작업)**
  - 채팅 위젯을 팝업 형태로 변경
    - `templates/chat/widget.html` 수정
    - `chat.views.start_chat_ajax` 뷰 추가
    - AJAX를 통한 채팅 세션 생성
  - WebSocket 연결 안정성 개선
    - 페이지 로드 시 즉시 연결
    - 재연결 로직 개선
  - 메시지 발신자 구분 개선
    - `sender_type`과 `sender` 모두 확인
    - 관리자/고객 메시지 정확히 구분
  - 사용자 경험 개선
    - 5분 비활성 시 자동 종료
    - 페이지 이탈 시 경고 메시지
    - 입력중 표시 기능
    - 자동 스크롤 및 커스텀 스크롤바
  - 알림 기능
    - 새 채팅 시작 시 관리자 알림
    - 상대방 종료 시 시스템 메시지

### 2025년 1월 23일
- **사용자 전용 장바구니 시스템**
  - `templates/shop/cart.html` 구현
  - 세션 기반 장바구니 (로그인 필수)
  - 수량 변경 기능 (`shop.views.update_cart_item`)
  - 실시간 소계 및 합계 계산
  - 빈 장바구니 상태 처리

- **마이페이지 완전 구현**
  - `templates/shop/mypage.html` 생성
  - 회원정보 수정 (`shop.views.update_profile`)
  - 회원 등급 및 포인트 시스템 표시
  - 배송지 관리 기능 (`add_address`, `delete_address`)
  - Daum 우편번호 API 연동
  - 최근 주문 내역 및 포인트 내역 표시

- **사용자/관리자 인증 분리**
  - 사용자 전용 로그인 (`accounts/user_login.html`)
  - 사용자 전용 비밀번호 변경 (`accounts/user_password_change.html`)
  - URL 패턴 분리 (`/accounts/user/login/`, `/accounts/user/signup/`)
  - `AdminAccessMiddleware` 강화 (Django admin 포함 차단)
  - 사용자 타입별 자동 리다이렉션

- **주문 관리 시스템**
  - `templates/shop/order_list.html` - 주문 목록
  - `templates/shop/order_detail.html` - 주문 상세
  - 주문 진행 상태 시각화 (5단계 프로그레스)
  - 주문 취소 기능 (`shop.views.cancel_order`)
  - 송장번호 및 배송 추적
  - 주문서 인쇄 기능 (인쇄용 CSS)

- **위시리스트 시스템**
  - `Wishlist` 모델 생성 (`shop/models.py`)
  - `templates/shop/wishlist.html` 구현
  - 위시리스트 토글 (`shop.views.toggle_wishlist`)
  - AJAX 기반 실시간 업데이트
  - 장바구니 추가 및 바로구매 연동
  - 토스트 알림 시스템

## 추가 참고사항
- 모든 금액은 원(₩) 단위로 저장
- 날짜/시간은 한국 시간대(KST) 기준
- 파일 업로드 크기 제한: 10MB
- 세션 타임아웃: 30분
- 프로젝트 총 코드: 약 60,000줄
  - Python: 약 25,000줄
  - HTML: 약 31,000줄
  - JS/CSS: 약 4,000줄
- 앱 개수: 14개 (chat 앱 추가)
- 모델 개수: 46개 (Wishlist 추가)