# Shopuda ERP 데이터베이스 스키마

## 개요
Shopuda ERP 시스템의 전체 데이터베이스 구조를 정리한 문서입니다. Django ORM을 사용하여 구현되었으며, 현재 SQLite를 사용하고 있으나 PostgreSQL로 마이그레이션 가능합니다.

## 앱별 모델 구조

### 1. accounts (사용자 및 권한 관리)

#### User (사용자)
- **테이블명**: `users`
- **설명**: Django AbstractUser를 확장한 커스텀 사용자 모델
- **주요 필드**:
  - `username`: 사용자명 (unique)
  - `email`: 이메일 주소
  - `user_type`: 사용자 타입 (CUSTOMER/STAFF/ADMIN)
  - `admin_level`: 관리자 권한 레벨 (0-5)
  - `phone_number`: 전화번호
  - `birth_date`: 생년월일
  - `gender`: 성별 (M/F/O)
  - `postal_code`: 우편번호
  - `address`: 주소
  - `detail_address`: 상세주소
  - `is_email_verified`: 이메일 인증 여부
  - `is_phone_verified`: 전화번호 인증 여부
  - `marketing_agreed`: 마케팅 수신 동의
  - `terms_agreed`: 이용약관 동의
  - `privacy_agreed`: 개인정보처리방침 동의
  - `profile_image`: 프로필 이미지
  - `total_purchase_amount`: 총 구매 금액
  - `purchase_count`: 구매 횟수
  - `last_purchase_date`: 마지막 구매일
  - `points`: 포인트
  - `membership_level`: 회원 등급 (BRONZE/SILVER/GOLD/PLATINUM/DIAMOND)
  - `created_at`: 가입일
  - `updated_at`: 수정일
  - `withdrawal_date`: 탈퇴일
  - `withdrawal_reason`: 탈퇴 사유

#### ShippingAddress (배송지)
- **테이블명**: `shipping_addresses`
- **설명**: 사용자별 배송지 관리
- **주요 필드**:
  - `user`: 사용자 (FK)
  - `nickname`: 배송지 별칭
  - `recipient_name`: 수령인 이름
  - `phone_number`: 전화번호
  - `postal_code`: 우편번호
  - `address`: 주소
  - `detail_address`: 상세주소
  - `is_default`: 기본 배송지 여부

#### PointHistory (포인트 내역)
- **테이블명**: `point_histories`
- **설명**: 포인트 적립/사용 내역
- **주요 필드**:
  - `user`: 사용자 (FK)
  - `point_type`: 포인트 타입 (EARN/USE/EXPIRE/CANCEL)
  - `amount`: 포인트 금액
  - `balance`: 잔액
  - `description`: 설명
  - `order_id`: 주문 번호
  - `expire_date`: 만료일

#### UserPermission (사용자 권한)
- **테이블명**: `user_permissions`
- **설명**: 세부 권한 관리
- **주요 필드**:
  - `user`: 사용자 (FK)
  - `permission`: 권한 코드
  - `granted_by`: 권한 부여자 (FK)
  - `granted_at`: 권한 부여일
  - `expires_at`: 권한 만료일
  - `is_active`: 활성 상태

### 2. core (시스템 핵심 기능)

#### SystemSettings (시스템 설정)
- **테이블명**: `core_systemsettings`
- **설명**: 전역 시스템 설정 (싱글톤)
- **주요 필드**:
  - 브랜드 설정: `site_name`, `site_tagline`, `site_logo_url`
  - 회원가입 설정: `signup_enabled`, `welcome_points_enabled`, `welcome_points_amount`
  - 회원 등급 기준: `membership_*_threshold` (bronze/silver/gold/platinum/diamond)
  - 포인트 설정: `points_enabled`, `points_rate`, `points_expiry_days`
  - 주문 설정: `order_prefix`, `order_cancel_days`, `auto_confirm_days`
  - 재고 설정: `low_stock_threshold`, `stock_alert_enabled`
  - 상품 설정: `product_review_enabled`, `review_points_amount`
  - 알림 설정: `email_notifications_enabled`, `sms_notifications_enabled`
  - 시스템 설정: `maintenance_mode`, `maintenance_message`
  - 통화 설정: `currency_symbol`, `currency_code`
  - 업무 시간: `business_hours_start`, `business_hours_end`

#### EmailTemplate (이메일 템플릿)
- **테이블명**: `core_emailtemplate`
- **설명**: 이메일 템플릿 관리
- **주요 필드**:
  - `template_type`: 템플릿 타입
  - `subject`: 제목
  - `body`: 내용 (변수 지원)
  - `is_active`: 활성화 여부

#### EmailTrigger (이메일 트리거)
- **테이블명**: `core_emailtrigger`
- **설명**: 이메일 자동 발송 설정
- **주요 필드**:
  - `name`: 트리거 이름
  - `event`: 이벤트 타입
  - `email_template`: 이메일 템플릿 (FK)
  - `is_active`: 활성화 여부
  - `delay_value`: 지연 시간
  - `delay_unit`: 시간 단위
  - `conditions`: 발송 조건 (JSON)

### 3. products (상품 관리)

#### Category (카테고리)
- **테이블명**: `products_category`
- **설명**: 계층적 상품 카테고리
- **주요 필드**:
  - `name`: 카테고리명
  - `code`: 카테고리 코드 (unique)
  - `description`: 설명
  - `icon`: 아이콘 클래스
  - `parent`: 상위 카테고리 (self FK)
  - `sort_order`: 정렬 순서
  - `is_active`: 활성 상태

#### Brand (브랜드)
- **테이블명**: `products_brand`
- **설명**: 브랜드 정보
- **주요 필드**:
  - `name`: 브랜드명 (unique)
  - `code`: 브랜드 코드 (unique)
  - `description`: 설명
  - `logo`: 로고 이미지
  - `website`: 웹사이트 URL
  - `is_active`: 활성 상태

#### Product (상품)
- **테이블명**: `products_product`
- **설명**: 상품 마스터 정보
- **주요 필드**:
  - `id`: UUID (PK)
  - `sku`: SKU (unique)
  - `name`: 상품명
  - `category`: 카테고리 (FK)
  - `brand`: 브랜드 (FK)
  - `short_description`: 간단 설명
  - `description`: 상세 설명
  - `status`: 상태 (ACTIVE/INACTIVE/DISCONTINUED)
  - `is_featured`: 추천 상품 여부
  - 가격 정보: `cost_price`, `selling_price`, `discount_price`
  - 재고 정보: `stock_quantity`, `min_stock_level`, `max_stock_level`
  - 물리적 정보: `weight`, `dimensions_length`, `dimensions_width`, `dimensions_height`
  - `barcode`: 바코드
  - `tags`: 태그 (쉼표 구분)
  - `created_by`: 생성자 (FK)

#### ProductImage (상품 이미지)
- **테이블명**: `products_productimage`
- **설명**: 상품 이미지 관리
- **주요 필드**:
  - `product`: 상품 (FK)
  - `image`: 이미지 파일
  - `alt_text`: 대체 텍스트
  - `is_primary`: 대표 이미지 여부
  - `sort_order`: 정렬 순서

#### ProductPriceHistory (가격 이력)
- **테이블명**: `products_productpricehistory`
- **설명**: 상품 가격 변경 이력
- **주요 필드**:
  - `product`: 상품 (FK)
  - `cost_price`: 원가
  - `selling_price`: 판매가
  - `discount_price`: 할인가
  - `reason`: 변경 사유
  - `changed_by`: 변경자 (FK)

### 4. orders (주문 관리)

#### Order (주문)
- **테이블명**: `orders_order`
- **설명**: 주문 정보
- **주요 필드**:
  - `order_number`: 주문번호 (unique)
  - `user`: 회원 (FK, nullable)
  - `platform`: 플랫폼 (FK)
  - `platform_order_id`: 플랫폼 주문 ID
  - 고객 정보: `customer_name`, `customer_email`, `customer_phone`
  - 배송 정보: `shipping_address`, `shipping_zipcode`, `shipping_method`, `tracking_number`
  - `status`: 상태 (PENDING/CONFIRMED/PROCESSING/SHIPPED/DELIVERED/CANCELLED/REFUNDED)
  - 금액 정보: `total_amount`, `shipping_fee`, `discount_amount`
  - 일시 정보: `order_date`, `shipped_date`, `delivered_date`, `cancelled_date`, `refunded_date`
  - `notes`: 메모

#### OrderItem (주문 상품)
- **테이블명**: `orders_orderitem`
- **설명**: 주문별 상품 정보
- **주요 필드**:
  - `order`: 주문 (FK)
  - `product`: 상품 (FK)
  - `quantity`: 수량
  - `unit_price`: 단가
  - `total_price`: 총 금액

### 5. inventory (재고 관리)

#### StockMovement (재고 이동)
- **테이블명**: `inventory_stockmovement`
- **설명**: 재고 이동 이력
- **주요 필드**:
  - `product`: 상품 (FK)
  - `movement_type`: 이동 유형 (IN/OUT/ADJUST/TRANSFER/RETURN/DAMAGE/SALE/PURCHASE/CANCEL/CORRECTION)
  - `quantity`: 수량
  - `previous_stock`: 이전 재고
  - `current_stock`: 현재 재고
  - `reference_number`: 참조 번호
  - `reason`: 사유
  - `order`: 관련 주문 (FK, nullable)
  - `platform`: 플랫폼 (FK, nullable)
  - `warehouse`: 창고
  - 비용 정보: `unit_cost`, `total_cost`
  - `created_by`: 생성자 (FK)
  - `is_automated`: 자동 처리 여부
  - `source_system`: 소스 시스템

#### StockAlert (재고 알림)
- **테이블명**: `inventory_stockalert`
- **설명**: 재고 알림 관리
- **주요 필드**:
  - `product`: 상품 (FK)
  - `alert_type`: 알림 유형 (LOW_STOCK/OUT_OF_STOCK/OVERSTOCK/EXPIRY_WARNING/SLOW_MOVING)
  - `status`: 상태 (ACTIVE/RESOLVED/DISMISSED)
  - `message`: 알림 메시지
  - `threshold_value`: 임계값
  - `current_value`: 현재값
  - `is_email_sent`: 이메일 발송 여부
  - `resolved_by`: 해결자 (FK)

#### StockLevel (재고 수준)
- **테이블명**: `inventory_stocklevel`
- **설명**: 상품별 재고 수준 설정
- **주요 필드**:
  - `product`: 상품 (OneToOne)
  - `min_stock_level`: 최소 재고
  - `max_stock_level`: 최대 재고
  - `reorder_point`: 재주문 시점
  - `reorder_quantity`: 재주문 수량
  - `safety_stock`: 안전 재고
  - `warehouse`: 창고
  - `auto_reorder_enabled`: 자동 재주문 활성화
  - `lead_time_days`: 리드타임
  - `is_seasonal`: 계절성 상품 여부
  - `seasonal_factor`: 계절성 계수

#### InventoryTransaction (재고 트랜잭션)
- **테이블명**: `inventory_inventorytransaction`
- **설명**: 복수 상품 재고 처리
- **주요 필드**:
  - `transaction_number`: 트랜잭션 번호 (unique)
  - `transaction_type`: 트랜잭션 유형 (ADJUSTMENT/TRANSFER/STOCKTAKE/BULK_UPDATE/PLATFORM_SYNC)
  - `status`: 상태 (PENDING/PROCESSING/COMPLETED/FAILED/CANCELLED)
  - `description`: 설명
  - 처리 정보: `total_items`, `processed_items`, `failed_items`
  - `created_by`: 생성자 (FK)
  - `metadata`: 메타데이터 (JSON)

### 6. core (핵심 시스템)

#### SystemSettings (시스템 설정)
- **테이블명**: `core_systemsettings`
- **설명**: 시스템 전역 설정 (싱글톤 패턴)
- **주요 필드**:
  - `site_name`: 사이트 이름
  - `site_tagline`: 사이트 태그라인
  - `site_description`: 사이트 설명
  - `contact_email`: 연락처 이메일
  - `contact_phone`: 연락처 전화번호
  - `business_registration_number`: 사업자등록번호
  - `business_address`: 사업장 주소
  - `business_owner`: 대표자명
  - `currency`: 통화
  - `default_tax_rate`: 기본 세율
  - `low_stock_threshold`: 재고 부족 임계값
  - `order_prefix`: 주문번호 접두사
  - `enable_email_notifications`: 이메일 알림 활성화
  - `email_host`, `email_port`, `email_use_tls`, `email_host_user`, `email_host_password`: 이메일 서버 설정
  - `maintenance_mode`: 유지보수 모드
  - `maintenance_message`: 유지보수 메시지
  - `google_analytics_id`: Google Analytics ID
  - `facebook_pixel_id`: Facebook Pixel ID
  - `naver_analytics_id`: 네이버 애널리틱스 ID
  - `kakao_javascript_key`: 카카오 JavaScript 키
  - `welcome_points_enabled`: 회원가입 포인트 지급 여부
  - `welcome_points_amount`: 회원가입 포인트 금액

#### EmailTemplate (이메일 템플릿)
- **테이블명**: `core_emailtemplate`
- **설명**: 자동 발송 이메일 템플릿
- **주요 필드**:
  - `template_type`: 템플릿 타입 (unique)
    - welcome, order_confirm, order_shipped, order_delivered, order_cancelled, order_refunded
    - password_reset, point_earned, point_expired, point_used
    - low_stock, product_restock, cart_abandoned, review_request
    - coupon_issued, coupon_expiring, membership_upgrade, birthday_greeting
  - `subject`: 이메일 제목
  - `body`: 이메일 본문 (Django 템플릿 문법 지원)
  - `is_active`: 활성화 여부
  - `created_at`, `updated_at`: 생성/수정 일시

#### EmailTrigger (이메일 트리거)
- **테이블명**: `core_emailtrigger`
- **설명**: 이메일 자동 발송 조건 설정
- **주요 필드**:
  - `name`: 트리거 이름
  - `event`: 이벤트 타입
    - user_register, order_created, order_paid, order_shipped, order_delivered
    - order_cancelled, order_refunded, point_earned, point_expire_soon, point_used
    - cart_abandoned, review_request, coupon_issued, coupon_expire_soon
    - membership_changed, birthday, product_restock
  - `email_template`: 이메일 템플릿 (FK)
  - `is_active`: 활성화 여부
  - `delay_value`: 지연 시간
  - `delay_unit`: 시간 단위 (minutes/hours/days)
  - `conditions`: 발송 조건 (JSON)
  - `created_at`, `updated_at`: 생성/수정 일시
- **유니크 제약**: (event, email_template)

### 7. platforms (플랫폼 연동)

#### Platform (플랫폼)
- **테이블명**: `platforms_platform`
- **설명**: 외부 플랫폼 정보
- **주요 필드**:
  - `name`: 플랫폼명
  - `platform_type`: 플랫폼 유형 (SMARTSTORE/COUPANG/GMARKET 등)
  - API 정보: `api_key`, `api_secret`, `api_url`, `api_endpoint`
  - `is_active`: 활성 상태
  - 동기화 설정: `sync_enabled`, `sync_interval`, `last_sync_at`
  - `last_sync_status`: 마지막 동기화 상태
  - `last_sync_message`: 마지막 동기화 메시지
  - `description`: 설명

#### PlatformProduct (플랫폼 상품)
- **테이블명**: `platforms_platformproduct`
- **설명**: 플랫폼별 상품 매핑
- **주요 필드**:
  - `product`: 상품 (FK)
  - `platform`: 플랫폼 (FK)
  - `platform_product_id`: 플랫폼 상품 ID
  - `platform_sku`: 플랫폼 SKU
  - `platform_price`: 플랫폼 판매가
  - `platform_stock`: 플랫폼 재고
  - `is_active`: 플랫폼 활성 상태
  - `last_sync_at`: 마지막 동기화

#### Supplier (공급업체)
- **테이블명**: `platforms_supplier`
- **설명**: 공급업체 정보
- **주요 필드**:
  - `name`: 업체명
  - `code`: 업체 코드 (unique)
  - `contact_person`: 담당자
  - `email`: 이메일
  - `phone`: 전화번호
  - `address`: 주소
  - `is_active`: 활성 상태

### 7. notifications (알림)

#### Notification (알림)
- **테이블명**: `notifications_notification`
- **설명**: 사용자 알림
- **주요 필드**:
  - `user`: 사용자 (FK)
  - `title`: 제목
  - `message`: 내용
  - `notification_type`: 알림 타입 (order/stock/payment/system/warning/info)
  - `url`: 관련 URL
  - `is_read`: 읽음 여부
  - `created_at`: 생성일
  - `read_at`: 읽은 시간

### 8. reports (보고서)

#### ReportTemplate (보고서 템플릿)
- **테이블명**: `reports_reporttemplate`
- **설명**: 보고서 템플릿
- **주요 필드**:
  - `name`: 템플릿 이름
  - `description`: 설명
  - `report_type`: 보고서 유형 (INVENTORY/SALES/FINANCIAL/PLATFORM/PRODUCT/ORDER/CUSTOM)
  - `frequency`: 생성 주기 (DAILY/WEEKLY/MONTHLY/QUARTERLY/YEARLY/ON_DEMAND)
  - `configuration`: 설정 (JSON)
  - `created_by`: 생성자 (FK)
  - `is_active`: 활성 상태
  - `is_public`: 공개 여부

#### GeneratedReport (생성된 보고서)
- **테이블명**: `reports_generatedreport`
- **설명**: 생성된 보고서 인스턴스
- **주요 필드**:
  - `report_id`: 보고서 ID (UUID)
  - `template`: 템플릿 (FK)
  - `title`: 제목
  - 기간: `period_start`, `period_end`
  - `status`: 상태 (PENDING/GENERATING/COMPLETED/FAILED/EXPIRED)
  - `format`: 형식 (HTML/PDF/EXCEL/CSV/JSON)
  - 파일 정보: `file_path`, `file_size`
  - `data`: 보고서 데이터 (JSON)
  - `summary`: 요약 정보 (JSON)
  - `generated_by`: 생성자 (FK)
  - `expires_at`: 만료일
  - 성능: `generation_time`, `row_count`

#### ReportSchedule (보고서 스케줄)
- **테이블명**: `reports_reportschedule`
- **설명**: 보고서 자동 생성 스케줄
- **주요 필드**:
  - `template`: 템플릿 (FK)
  - `name`: 스케줄 이름
  - `schedule_type`: 스케줄 유형 (CRON/INTERVAL/CALENDAR)
  - `cron_expression`: Cron 표현식
  - `interval_days`: 간격(일)
  - 실행 정보: `next_run`, `last_run`
  - `email_recipients`: 이메일 수신자 (JSON)
  - `is_active`: 활성 상태
  - `created_by`: 생성자 (FK)

#### ReportAccess (보고서 접근 로그)
- **테이블명**: `reports_reportaccess`
- **설명**: 보고서 접근 이력
- **주요 필드**:
  - `report`: 보고서 (FK)
  - `user`: 사용자 (FK)
  - `action`: 액션 (VIEW/DOWNLOAD/SHARE/DELETE)
  - `ip_address`: IP 주소
  - `user_agent`: User Agent
  - `accessed_at`: 접근일

#### ReportBookmark (보고서 북마크)
- **테이블명**: `reports_reportbookmark`
- **설명**: 사용자별 보고서 북마크
- **주요 필드**:
  - `user`: 사용자 (FK)
  - `template`: 템플릿 (FK)
  - `name`: 북마크 이름
  - `configuration`: 설정 (JSON)

### 9. 기타 앱 (현재 모델 없음)
- **api**: REST API 관련 (모델 없음, ViewSet으로 구현)
- **dashboard**: 대시보드 (모델 없음, 뷰로 구현)
- **search**: 검색 기능 (모델 없음, 다른 모델 검색)
- **shop**: 쇼핑몰 프론트 (모델 없음)

## 주요 관계도

### 사용자-주문-상품 관계
```
User (1) -----> (*) Order (1) -----> (*) OrderItem (*) <----- (1) Product
  |                   |                                              |
  |                   |                                              |
  v                   v                                              v
ShippingAddress    Platform                                     Category
PointHistory                                                     Brand
UserPermission                                                ProductImage
```

### 재고 관리 관계
```
Product (1) -----> (*) StockMovement
   |                        |
   |                        v
   |                  InventoryTransaction
   |
   +-----> (1) StockLevel
   |
   +-----> (*) StockAlert
```

### 플랫폼 연동 관계
```
Platform (1) -----> (*) PlatformProduct (*) <----- (1) Product
     |                                                    |
     |                                                    |
     v                                                    v
   Order                                              Supplier
```

### 보고서 시스템 관계
```
ReportTemplate (1) -----> (*) GeneratedReport (*) <----- (*) ReportAccess
       |                           |                              |
       |                           |                              v
       v                           v                            User
ReportSchedule                ReportBookmark
```

## 인덱스 및 성능 최적화

### 주요 인덱스
1. **User**: username, email, user_type, admin_level
2. **Product**: sku, name, status, is_featured, barcode
3. **Order**: order_number, platform+status, order_date, status
4. **StockMovement**: product+created_at, movement_type+created_at
5. **Notification**: user+is_read, created_at

### 유니크 제약조건
1. **User**: username, email
2. **Product**: sku
3. **Order**: order_number
4. **Category**: code
5. **Brand**: name, code
6. **Platform**: name
7. **UserPermission**: user+permission
8. **PlatformProduct**: platform+platform_product_id

## 데이터베이스 마이그레이션 고려사항

### SQLite → PostgreSQL 마이그레이션 시
1. **JSON 필드**: Django의 JSONField는 PostgreSQL에서 네이티브 지원
2. **UUID 필드**: Product의 UUID 필드는 PostgreSQL에서 효율적
3. **인덱스**: GIN 인덱스를 활용한 JSON 검색 성능 향상 가능
4. **Full-text search**: PostgreSQL의 전문 검색 기능 활용 가능

### 파티셔닝 고려 대상
1. **StockMovement**: created_at 기준 월별 파티셔닝
2. **Order**: order_date 기준 월별 파티셔닝
3. **Notification**: created_at 기준 월별 파티셔닝
4. **PointHistory**: created_at 기준 연도별 파티셔닝

## 14. shop (쇼핑몰)

### Wishlist
- id (BigAutoField): PK
- user (ForeignKey): 사용자 
- product (ForeignKey): 상품
- created_at (DateTimeField): 추가일시
- unique_together: ['user', 'product']

## 보안 고려사항
1. **민감 정보 암호화**: api_key, api_secret 등
2. **개인정보 마스킹**: 로그 및 보고서에서 개인정보 마스킹
3. **접근 권한**: UserPermission을 통한 세밀한 권한 관리
4. **감사 로그**: 중요 변경사항에 대한 이력 추적