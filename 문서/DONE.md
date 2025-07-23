# DONE

## 시스템 설정 동적 적용
**완료일**: 2025-07-22
- core.context_processors.system_settings 수정
- 사이트 이름, 태그라인, 로고를 모든 템플릿에서 사용 가능
- shop/base.html, shop/home.html에 {{ site_name }} 적용

## 사용자 전용 회원가입 페이지
**완료일**: 2025-07-22
- templates/accounts/user_signup.html 생성
- 관리자 대시보드 요소 제거
- shop/base.html 템플릿 상속
- accounts.views.SignUpView 템플릿 경로 수정

## 통합 검색 기능
**완료일**: 2025-07-22
- shop.views.search 뷰 구현
- 헤더 및 홈페이지 검색바 추가
- 상품명, 설명, 브랜드, 카테고리, SKU 검색
- templates/shop/search_results.html 생성

## 상품 상세 페이지
**완료일**: 2025-07-22
- templates/shop/product_detail.html 생성
- 반응형 이미지 갤러리 구현
- 탭 기반 정보 표시 (설명, 상세정보, 배송정보)
- 관련 상품 추천 섹션

## 상품 이미지 시스템 개선
**완료일**: 2025-07-22
- ProductImage 모델에 image_type 필드 추가
- 이미지 타입별 제한 차별화 (primary/gallery/detail)
- 상세 이미지 크기 제한 해제
- ProductImageForm 조건부 검증 구현

## 데이터베이스 마이그레이션 문제 해결
**완료일**: 2025-07-22
- orders 앱 마이그레이션 충돌 해결
- 0004_merge_20250722_1100.py 병합 마이그레이션 생성
- 데이터베이스 재생성

## 세션 테이블 오류 해결
**완료일**: 2025-07-22
- django_session 테이블 수동 생성
- reports 관련 테이블 생성
- core_emailtrigger 테이블 생성
- create_superuser.py 스크립트 작성 및 실행

## 실시간 채팅 상담 시스템
**완료일**: 2025-07-22
- chat 앱 생성 및 모델 설계
  - ChatSession: 채팅 세션 관리
  - ChatMessage: 채팅 메시지 (수정 불가)
  - ChatNote: 상담원 메모
  - ChatQuickReply: 빠른 답변 템플릿
  - ChatStatistics: 채팅 통계
- WebSocket 기반 실시간 통신 구현
  - ChatConsumer: 채팅 메시지 처리
  - AgentDashboardConsumer: 상담원 대시보드 실시간 업데이트
- 고객용 기능
  - 채팅 시작 페이지
  - 실시간 채팅룸
  - 채팅 위젯 (모든 쇼핑몰 페이지에 표시)
- 상담원용 기능
  - 상담원 대시보드
  - 채팅 이력 조회
  - 채팅별 메모 기능
  - 빠른 답변 관리
- 보안 및 권한
  - 채팅 메시지 수정/삭제 불가 (읽기 전용)
  - 상담원만 모든 채팅 조회 가능

## 회원가입 중복확인 버그 수정
**완료일**: 2025-07-22
- check_username 함수에서 @login_required 데코레이터 제거
- check_email 함수에서 @login_required 데코레이터 제거
- 로그인 여부에 따른 조건부 처리 추가

## 사용자 전용 장바구니 페이지
**완료일**: 2025-07-23
- templates/shop/cart.html 생성
- 세션 기반 장바구니 시스템
- 수량 변경 기능 (update_cart_item 뷰 추가)
- 장바구니 상품별 소계 및 전체 합계 표시
- 빈 장바구니 상태 처리
- 반응형 디자인 적용

## 사용자 마이페이지 완전 구현
**완료일**: 2025-07-23
- templates/shop/mypage.html 생성
- 사용자 정보 표시 및 수정 기능
- 회원 등급 및 포인트 표시
- 최근 주문 내역 표시
- 포인트 내역 표시
- 배송지 관리 (추가/수정/삭제)
- Daum 우편번호 API 연동
- update_profile, add_address, delete_address 뷰 추가

## 사용자/관리자 인증 시스템 분리
**완료일**: 2025-07-23
- 사용자 전용 로그인 페이지 (user_login.html)
- 사용자 전용 비밀번호 변경 페이지 (user_password_change.html)
- 관리자 패널 접근 차단 미들웨어 강화
- URL 패턴 분리 (/accounts/user/login/, /accounts/user/signup/)
- 사용자 타입별 리다이렉션 처리

## 주문 관리 시스템 구현
**완료일**: 2025-07-23
- templates/shop/order_list.html 생성
- templates/shop/order_detail.html 생성
- 주문 상태별 표시 및 진행 상황 시각화
- 주문 취소 기능 (cancel_order 뷰)
- 송장번호 표시 및 배송 추적
- 주문서 인쇄 기능
- 반응형 디자인 적용

## 위시리스트 시스템 구현
**완료일**: 2025-07-23
- Wishlist 모델 생성 (shop/models.py)
- templates/shop/wishlist.html 생성
- 위시리스트 토글 기능 (toggle_wishlist 뷰)
- AJAX 기반 실시간 업데이트
- 장바구니 추가 및 바로구매 기능
- 전체 삭제 기능
- 토스트 알림 시스템