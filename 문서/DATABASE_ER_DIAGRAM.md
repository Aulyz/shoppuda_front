# Shopuda ERP ER 다이어그램

## Entity Relationship Diagram (텍스트 형식)

### 범례
- `PK`: Primary Key
- `FK`: Foreign Key
- `UK`: Unique Key
- `NN`: Not Null
- `AI`: Auto Increment
- `1:1`: One-to-One 관계
- `1:N`: One-to-Many 관계
- `N:M`: Many-to-Many 관계

## 주요 엔티티 및 관계

### 1. 사용자 관리 도메인

```
┌─────────────────────────────────────────────────────────────┐
│                            User                              │
├─────────────────────────────────────────────────────────────┤
│ PK │ id                 │ INTEGER    │ AI, NN              │
│ UK │ username           │ VARCHAR    │ NN                  │
│ UK │ email             │ VARCHAR    │ NN                  │
│    │ user_type         │ VARCHAR    │ NN (ENUM)           │
│    │ admin_level       │ INTEGER    │ NN (0-5)            │
│    │ phone_number      │ VARCHAR    │                     │
│    │ points            │ INTEGER    │ NN, DEFAULT 0       │
│    │ membership_level  │ VARCHAR    │ NN (ENUM)           │
│    │ created_at        │ DATETIME   │ NN                  │
└─────────────────────────────────────────────────────────────┘
           │                    │                    │
           │ 1:N                │ 1:N                │ 1:N
           ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ ShippingAddress │  │  PointHistory   │  │ UserPermission  │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ PK │ id         │  │ PK │ id         │  │ PK │ id         │
│ FK │ user_id    │  │ FK │ user_id    │  │ FK │ user_id    │
│    │ nickname   │  │    │ point_type │  │ UK │ permission │
│    │ address    │  │    │ amount     │  │    │ expires_at │
│    │ is_default │  │    │ balance    │  │    │ is_active  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 2. 상품 관리 도메인

```
┌─────────────────────────────────────────────────────────────┐
│                          Product                             │
├─────────────────────────────────────────────────────────────┤
│ PK │ id                 │ UUID       │ NN                  │
│ UK │ sku               │ VARCHAR    │ NN                  │
│    │ name              │ VARCHAR    │ NN                  │
│ FK │ category_id       │ INTEGER    │                     │
│ FK │ brand_id          │ INTEGER    │                     │
│    │ cost_price        │ DECIMAL    │ NN                  │
│    │ selling_price     │ DECIMAL    │ NN                  │
│    │ stock_quantity    │ INTEGER    │ NN, DEFAULT 0       │
│    │ status            │ VARCHAR    │ NN (ENUM)           │
└─────────────────────────────────────────────────────────────┘
     │         │              │                │
     │ N:1     │ N:1          │ 1:N            │ 1:1
     ▼         ▼              ▼                ▼
┌──────────┐ ┌─────────┐ ┌──────────────┐ ┌────────────┐
│ Category │ │  Brand  │ │ProductImage  │ │StockLevel  │
├──────────┤ ├─────────┤ ├──────────────┤ ├────────────┤
│ PK │ id  │ │ PK │ id │ │ PK │ id      │ │ PK │ id    │
│ UK │ code│ │ UK │code│ │ FK │product_id│ │ FK │product│
│ FK │parent│ │    │name│ │    │ image   │ │    │min_stock│
└──────────┘ └─────────┘ └──────────────┘ └────────────┘
```

### 3. 주문 관리 도메인

```
┌─────────────────────────────────────────────────────────────┐
│                           Order                              │
├─────────────────────────────────────────────────────────────┤
│ PK │ id                 │ INTEGER    │ AI, NN              │
│ UK │ order_number      │ VARCHAR    │ NN                  │
│ FK │ user_id           │ INTEGER    │                     │
│ FK │ platform_id       │ INTEGER    │                     │
│    │ customer_name     │ VARCHAR    │ NN                  │
│    │ status            │ VARCHAR    │ NN (ENUM)           │
│    │ total_amount      │ DECIMAL    │ NN                  │
│    │ order_date        │ DATETIME   │ NN                  │
└─────────────────────────────────────────────────────────────┘
           │                    │
           │ 1:N                │ N:1
           ▼                    ▼
┌─────────────────────┐  ┌─────────────────┐
│     OrderItem       │  │    Platform     │
├─────────────────────┤  ├─────────────────┤
│ PK │ id             │  │ PK │ id         │
│ FK │ order_id       │  │    │ name       │
│ FK │ product_id     │  │    │ platform_type│
│    │ quantity       │  │    │ api_key    │
│    │ unit_price     │  │    │ is_active  │
└─────────────────────┘  └─────────────────┘
```

### 4. 재고 관리 도메인

```
┌─────────────────────────────────────────────────────────────┐
│                       StockMovement                          │
├─────────────────────────────────────────────────────────────┤
│ PK │ id                 │ INTEGER    │ AI, NN              │
│ FK │ product_id        │ UUID       │ NN                  │
│    │ movement_type     │ VARCHAR    │ NN (ENUM)           │
│    │ quantity          │ INTEGER    │ NN                  │
│    │ previous_stock    │ INTEGER    │ NN                  │
│    │ current_stock     │ INTEGER    │ NN                  │
│ FK │ order_id          │ INTEGER    │                     │
│    │ created_at        │ DATETIME   │ NN                  │
└─────────────────────────────────────────────────────────────┘
           │
           │ N:1
           ▼
┌─────────────────────────────────────────────────────────────┐
│                        Product                               │
└─────────────────────────────────────────────────────────────┘
           │
           │ 1:N
           ▼
┌─────────────────────────────────────────────────────────────┐
│                       StockAlert                             │
├─────────────────────────────────────────────────────────────┤
│ PK │ id                 │ INTEGER    │ AI, NN              │
│ FK │ product_id        │ UUID       │ NN                  │
│    │ alert_type        │ VARCHAR    │ NN (ENUM)           │
│    │ status            │ VARCHAR    │ NN (ENUM)           │
│    │ message           │ TEXT       │ NN                  │
└─────────────────────────────────────────────────────────────┘
```

### 5. 플랫폼 연동 도메인

```
┌─────────────────────┐         ┌─────────────────────┐
│      Platform       │         │      Product        │
├─────────────────────┤         ├─────────────────────┤
│ PK │ id             │         │ PK │ id             │
│    │ name           │         │    │ sku            │
│    │ platform_type  │         │    │ name           │
└─────────────────────┘         └─────────────────────┘
           │                               │
           │ 1:N                     N:1   │
           ▼                               ▼
         ┌─────────────────────────────────────┐
         │          PlatformProduct            │
         ├─────────────────────────────────────┤
         │ PK │ id                             │
         │ FK │ platform_id                   │
         │ FK │ product_id                    │
         │ UK │ platform_id + platform_product_id│
         │    │ platform_price               │
         │    │ platform_stock               │
         └─────────────────────────────────────┘
```

### 6. 알림 시스템

```
┌─────────────────────────────────────────────────────────────┐
│                       Notification                           │
├─────────────────────────────────────────────────────────────┤
│ PK │ id                 │ INTEGER    │ AI, NN              │
│ FK │ user_id           │ INTEGER    │ NN                  │
│    │ title             │ VARCHAR    │ NN                  │
│    │ message           │ TEXT       │ NN                  │
│    │ notification_type │ VARCHAR    │ NN (ENUM)           │
│    │ is_read           │ BOOLEAN    │ NN, DEFAULT FALSE   │
│    │ created_at        │ DATETIME   │ NN                  │
└─────────────────────────────────────────────────────────────┘
```

### 7. 보고서 시스템

```
┌─────────────────────┐         ┌─────────────────────┐
│   ReportTemplate    │         │   GeneratedReport   │
├─────────────────────┤         ├─────────────────────┤
│ PK │ id             │ 1:N     │ PK │ id             │
│    │ name           ├────────▶│ FK │ template_id    │
│    │ report_type    │         │ UK │ report_id(UUID)│
│    │ frequency      │         │    │ status         │
└─────────────────────┘         └─────────────────────┘
           │                               │
           │ 1:N                     N:1   │
           ▼                               ▼
┌─────────────────────┐         ┌─────────────────────┐
│   ReportSchedule    │         │    ReportAccess     │
├─────────────────────┤         ├─────────────────────┤
│ PK │ id             │         │ PK │ id             │
│ FK │ template_id    │         │ FK │ report_id      │
│    │ schedule_type  │         │ FK │ user_id        │
│    │ next_run       │         │    │ action         │
└─────────────────────┘         └─────────────────────┘
```

## 주요 관계 설명

### 1. User 중심 관계
- User → Order (1:N): 한 사용자는 여러 주문을 가질 수 있음
- User → ShippingAddress (1:N): 한 사용자는 여러 배송지를 등록할 수 있음
- User → PointHistory (1:N): 한 사용자는 여러 포인트 사용 내역을 가짐
- User → UserPermission (1:N): 한 사용자는 여러 권한을 가질 수 있음
- User → Notification (1:N): 한 사용자는 여러 알림을 받을 수 있음

### 2. Product 중심 관계
- Product → Category (N:1): 여러 상품이 하나의 카테고리에 속함
- Product → Brand (N:1): 여러 상품이 하나의 브랜드에 속함
- Product → ProductImage (1:N): 한 상품은 여러 이미지를 가질 수 있음
- Product → StockMovement (1:N): 한 상품은 여러 재고 이동 내역을 가짐
- Product → StockLevel (1:1): 한 상품은 하나의 재고 수준 설정을 가짐
- Product → OrderItem (1:N): 한 상품은 여러 주문에 포함될 수 있음

### 3. Order 중심 관계
- Order → OrderItem (1:N): 한 주문은 여러 주문 항목을 포함
- Order → User (N:1): 여러 주문이 한 사용자에 속함 (nullable)
- Order → Platform (N:1): 여러 주문이 하나의 플랫폼에서 발생
- Order → StockMovement (1:N): 한 주문은 여러 재고 이동을 발생시킬 수 있음

### 4. Platform 연동 관계
- Platform → PlatformProduct (1:N): 한 플랫폼은 여러 상품 매핑을 가짐
- Product → PlatformProduct (1:N): 한 상품은 여러 플랫폼에 등록될 수 있음
- Platform → Order (1:N): 한 플랫폼에서 여러 주문이 발생

### 5. 보고서 관계
- ReportTemplate → GeneratedReport (1:N): 한 템플릿으로 여러 보고서 생성
- ReportTemplate → ReportSchedule (1:N): 한 템플릿은 여러 스케줄을 가질 수 있음
- GeneratedReport → ReportAccess (1:N): 한 보고서는 여러 접근 로그를 가짐
- User → ReportBookmark (1:N): 한 사용자는 여러 보고서 북마크를 가질 수 있음

## 데이터 무결성 제약조건

### 1. 참조 무결성
- 모든 외래키는 참조 대상이 삭제될 때의 동작을 정의
  - CASCADE: 연관 데이터도 함께 삭제
  - SET_NULL: NULL로 설정
  - PROTECT: 삭제 방지

### 2. 유니크 제약조건
- User: username, email
- Product: sku
- Order: order_number
- Category: code
- Brand: name, code
- PlatformProduct: (platform_id, platform_product_id)
- UserPermission: (user_id, permission)

### 3. 체크 제약조건
- User.admin_level: 0-5 사이의 값
- Product.selling_price > Product.cost_price
- Product.discount_price < Product.selling_price
- StockLevel.min_stock_level < StockLevel.max_stock_level
- Order.total_amount >= 0
- StockMovement.quantity > 0

### 4. 기본값 제약조건
- User.points: 0
- User.membership_level: 'BRONZE'
- Product.stock_quantity: 0
- Product.status: 'ACTIVE'
- Order.status: 'PENDING'
- Notification.is_read: False
- StockAlert.status: 'ACTIVE'

## 인덱싱 전략

### 1. 기본 인덱스
- 모든 Primary Key 필드
- 모든 Foreign Key 필드
- 모든 Unique 필드

### 2. 복합 인덱스
- Order: (platform_id, status)
- StockMovement: (product_id, created_at)
- Notification: (user_id, is_read)
- PlatformProduct: (platform_id, is_active)

### 3. 성능 최적화 인덱스
- Product: name (전문 검색용)
- Order: order_date (날짜 범위 검색용)
- User: email, username (로그인 최적화)
- StockMovement: movement_type, created_at (보고서 생성용)