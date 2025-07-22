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
### 2024년 7월
- 사용자용 쇼핑몰 기능 추가
- URL 구조 개선 (관리자/사용자 분리)
- 이메일 템플릿 시스템 확장
- 이메일 자동 발송 트리거 기능 추가
- 접근 제어 미들웨어 구현

### 2025년 7월
- **상품 목록 페이지 (`shop/product_list.html`) 구현**
  - 완전 반응형 디자인 (모바일/태블릿/데스크톱 최적화)
  - 계층적 카테고리 시스템 (상위 카테고리 선택 시 하위 카테고리 포함)
  - 호버 기반 카테고리 드롭다운 메뉴
  - 상품 정렬 기능 (최신순/가격순/이름순)
  - 재고 상태 실시간 표시
  - 할인율 배지 표시
  - 장바구니 빠른 추가 기능

## 추가 참고사항
- 모든 금액은 원(₩) 단위로 저장
- 날짜/시간은 한국 시간대(KST) 기준
- 파일 업로드 크기 제한: 10MB
- 세션 타임아웃: 30분
- 프로젝트 총 코드: 약 51,000줄
  - Python: 약 21,000줄
  - HTML: 약 26,000줄
  - JS/CSS: 약 4,000줄