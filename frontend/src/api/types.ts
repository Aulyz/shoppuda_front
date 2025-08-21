// 공통 응답 타입
export interface ApiResponse<T = any> {
  data: T
  message?: string
  success?: boolean
}

export interface PaginatedResponse<T> {
  results: T[]
  count: number
  next: string | null
  previous: string | null
}

// 사용자 관련 타입
export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  user_type: 'CUSTOMER' | 'STAFF' | 'ADMIN'
  is_active: boolean
  date_joined: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access: string
  refresh: string
  user: User
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  password_confirm: string
  first_name?: string
  last_name?: string
}

// 상품 관련 타입
export interface Category {
  id: number
  name: string
  slug: string
  parent: number | null
  is_active: boolean
  sort_order: number
  product_count?: number
}

export interface Brand {
  id: number
  name: string
  code: string
  description?: string
  is_active: boolean
}

export interface ProductImage {
  id: number
  image: string
  alt_text?: string
  is_primary: boolean
  sort_order: number
}

export interface Product {
  id: string
  sku: string
  name: string
  slug: string
  description: string
  short_description?: string
  brand: Brand | null
  category: Category | null
  status: 'ACTIVE' | 'INACTIVE' | 'DRAFT'
  price: number
  selling_price: number
  discount_price?: number
  cost_price?: number
  stock_quantity: number
  min_stock_level: number
  weight?: number
  dimensions?: string
  is_featured: boolean
  is_digital: boolean
  meta_title?: string
  meta_description?: string
  images: ProductImage[]
  tags: string[]
  created_at: string
  updated_at: string
  
  // 계산된 필드
  discount_percentage?: number
  is_new?: boolean
  is_low_stock?: boolean
  is_out_of_stock?: boolean
  rating?: number
  review_count?: number
}

// 상품 필터링 파라미터
export interface ProductFilters {
  category?: number
  brand?: number
  search?: string
  min_price?: number
  max_price?: number
  in_stock?: boolean
  featured?: boolean
  new?: boolean
  page?: number
  page_size?: number
  ordering?: string
}

// 장바구니 관련 타입
export interface CartItem {
  id: number
  product: Product
  quantity: number
  price: number
  total_price: number
}

export interface Cart {
  items: CartItem[]
  total_items: number
  total_price: number
  total_discount: number
  final_price: number
}

// 위시리스트 타입
export interface WishlistItem {
  id: number
  product: Product
  added_at: string
}

// 주문 관련 타입
export interface ShippingAddress {
  id: number
  nickname: string
  recipient_name: string
  phone_number: string
  address: string
  detail_address: string
  postal_code: string
  is_default: boolean
}

export interface OrderItem {
  id: number
  product: Product
  quantity: number
  price: number
  total_price: number
}

export interface Order {
  id: number
  order_number: string
  status: 'PENDING' | 'CONFIRMED' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED'
  items: OrderItem[]
  shipping_address: ShippingAddress
  total_amount: number
  shipping_fee: number
  discount_amount: number
  final_amount: number
  payment_method: string
  payment_status: string
  created_at: string
  updated_at: string
}

// 검색 관련 타입
export interface SearchSuggestion {
  id: string
  name: string
  type: 'product' | 'category' | 'brand'
  image?: string
  price?: number
}

export interface SearchFilters {
  query: string
  category?: number
  brand?: number
  min_price?: number
  max_price?: number
  sort?: string
}

// 배너 관련 타입
export interface Banner {
  id: number
  title: string
  subtitle: string
  image: string
  link: string
  button_text: string
  is_active: boolean
  order: number
}

// 에러 타입
export interface ApiError {
  message: string
  code?: string
  details?: Record<string, string[]>
}