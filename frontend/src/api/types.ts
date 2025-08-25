// ====================== 기본 타입 ======================

export interface BaseEntity {
  id: string
  created_at: string
  updated_at: string
}

// ====================== 인증 관련 타입 ======================

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  password_confirm: string
  first_name: string
  last_name: string
}

export interface LoginResponse {
  access: string
  refresh: string
  user: User
}

export interface User extends BaseEntity {
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  date_joined: string
}

// ====================== 상품 관련 타입 ======================

export interface Category extends BaseEntity {
  name: string
  slug: string
  parent: number | null
  is_active: boolean
  sort_order: number
  product_count?: number
}

export interface Brand extends BaseEntity {
  name: string
  slug: string
  description?: string
  logo?: string
  website?: string
  is_active: boolean
}

export interface Product extends BaseEntity {
  name: string
  code?: string
  description?: string
  selling_price: number
  discount_price?: number
  cost_price?: number
  stock_quantity: number
  images?: string[]
  category?: Category
  brand?: Brand
  status: 'ACTIVE' | 'INACTIVE' | 'DISCONTINUED'
  is_featured?: boolean
  weight?: number
  dimensions?: string
  tags?: string[]
}

export interface ProductFilters {
  search?: string
  category?: string
  brand?: string
  min_price?: string
  max_price?: string
  ordering?: string
  page?: number
  page_size?: number
  status?: string
}

// ====================== 장바구니 관련 타입 ======================

export interface CartItem extends BaseEntity {
  product: Product
  quantity: number
  price: number
  total_price: number
}

export interface Cart extends BaseEntity {
  items: CartItem[]
  total_quantity: number
  total_price: number
  user: number
}

// ====================== 위시리스트 관련 타입 ======================

export interface WishlistItem extends BaseEntity {
  product: Product
  user: number
}

// ====================== 주문 관련 타입 ======================

export interface ShippingAddress extends BaseEntity {
  recipient_name: string
  phone: string
  address_line1: string
  address_line2?: string
  city: string
  state: string
  postal_code: string
  country: string
  is_default?: boolean
}

export interface OrderItem extends BaseEntity {
  product: Product
  quantity: number
  price: number
  total_price: number
}

export interface Order extends BaseEntity {
  order_number: string
  user: number
  items: OrderItem[]
  total_amount: number
  shipping_address: ShippingAddress
  status: 'PENDING' | 'CONFIRMED' | 'PROCESSING' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED'
  payment_status: 'PENDING' | 'COMPLETED' | 'FAILED' | 'REFUNDED'
  notes?: string
}

// ====================== 배너 관련 타입 ======================

export interface Banner extends BaseEntity {
  title: string
  image: string
  link_url?: string
  is_active: boolean
  sort_order: number
  start_date?: string
  end_date?: string
}

// ====================== 검색 관련 타입 ======================

export interface SearchSuggestion {
  id: string
  name: string
  type: 'product' | 'category' | 'brand'
}

// ====================== API 응답 타입 ======================

export interface ApiResponse<T> {
  success: boolean
  data: T
  message?: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

// ====================== 에러 타입 ======================

export interface ApiError {
  message: string
  errors?: Record<string, string[]>
  status?: number
}

// ====================== 폼 관련 타입 ======================

export interface ContactForm {
  name: string
  email: string
  phone?: string
  subject: string
  message: string
}

export interface AddressForm {
  recipient_name: string
  phone: string
  address_line1: string
  address_line2?: string
  city: string
  state: string
  postal_code: string
  country: string
  is_default?: boolean
}

// ====================== 이벤트 및 쿠폰 관련 타입 ======================

export interface Coupon extends BaseEntity {
  code: string
  name: string
  description?: string
  discount_type: 'percentage' | 'fixed'
  discount_value: number
  min_order_amount?: number
  max_discount_amount?: number
  usage_limit?: number
  used_count: number
  valid_from: string
  valid_until: string
  is_active: boolean
}

export interface Event extends BaseEntity {
  title: string
  slug: string
  description: string
  banner_image?: string
  start_date: string
  end_date: string
  is_active: boolean
  featured_products: Product[]
  discount_percentage?: number
}

// ====================== 알림 관련 타입 ======================

export interface Notification extends BaseEntity {
  user: number
  title: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  is_read: boolean
  action_url?: string
}

// ====================== 유틸리티 타입 ======================

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>
export type CreateRequest<T> = Omit<T, 'id' | 'created_at' | 'updated_at'>
export type UpdateRequest<T> = Partial<CreateRequest<T>>

// ====================== 컴포넌트 Props 타입 ======================

export interface ProductCardProps {
  product: Product
  showQuickView?: boolean
  showWishlist?: boolean
  showCompare?: boolean
  className?: string
}

export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
  fullWidth?: boolean
  children: React.ReactNode
  onClick?: () => void
  type?: 'button' | 'submit' | 'reset'
  className?: string
}