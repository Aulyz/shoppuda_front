// API 타입 정의 (consolidated and enhanced)

// ================== 기본 응답 타입 ==================
export interface ApiResponse<T = any> {
  data?: T
  message?: string
  detail?: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

// ================== 인증 관련 ==================
export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  user_type: 'CUSTOMER' | 'STAFF' | 'ADMIN'
  is_active: boolean
  date_joined: string
  phone?: string
  birth_date?: string
  marketing_agreed?: boolean
}

export interface LoginRequest {
  username: string
  password: string
}

export interface JWTTokenResponse {
  access: string
  refresh: string
  user: User
}

export interface LoginResponse extends JWTTokenResponse {}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  password_confirm: string
  first_name: string
  last_name: string
  phone?: string
  marketing_agreed?: boolean
}

// ================== 상품 관련 ==================
export interface Category {
  id: number
  name: string
  code?: string
  slug?: string
  parent: number | null
  full_path?: string
  is_active: boolean
  sort_order?: number
  product_count?: number
  image?: string
}

export interface Brand {
  id: number
  name: string
  code: string
  description?: string
  logo?: string
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
  slug?: string
  brand: Brand | null
  category: Category | null
  short_description?: string
  description?: string
  selling_price: number
  discount_price?: number
  final_price?: number
  cost_price?: number
  stock_quantity: number
  min_stock_level: number
  max_stock_level?: number
  status: 'ACTIVE' | 'INACTIVE' | 'DRAFT'
  is_featured: boolean
  is_digital?: boolean
  is_low_stock?: boolean
  weight?: number
  dimensions_length?: number
  dimensions_width?: number
  dimensions_height?: number
  barcode?: string
  tags?: string[]
  images?: ProductImage[]
  primary_image?: ProductImage
  meta_title?: string
  meta_description?: string
  created_at: string
  updated_at: string
  discount_percentage?: number
  is_on_sale?: boolean
  is_out_of_stock?: boolean
  average_rating?: number
  review_count?: number
}

export interface ProductDetail extends Product {
  images: ProductImage[]
}

export interface ProductFilters {
  search?: string
  category?: number | number[]
  brand?: number | number[]
  status?: string
  is_featured?: boolean
  min_price?: number
  max_price?: number
  page?: number
  page_size?: number
  ordering?: string
  is_on_sale?: boolean
  in_stock?: boolean
  rating_min?: number
  tags?: string[]
  sort_by?: 'name' | 'price' | 'created_at' | 'rating' | 'popularity'
  sort_order?: 'asc' | 'desc'
}

// ================== 장바구니 관련 ==================
export interface CartItem {
  id: number
  product: Product
  quantity: number
  unit_price: number
  total_price: number
  created_at?: string
  updated_at?: string
}

export interface Cart {
  id: number
  user?: User
  session_key?: string
  items: CartItem[]
  total_quantity: number
  total_price: number
  created_at: string
  updated_at: string
}

export interface CartAddRequest {
  product_id: string
  quantity: number
}

export interface CartUpdateRequest {
  quantity: number
}

// ================== 위시리스트 관련 ==================
export interface WishlistItem {
  id: number
  product: Product
  user?: number
  created_at: string
}

export interface WishlistToggleResponse {
  added: boolean
  message?: string
}

// ================== 배송지 관련 ==================
export interface ShippingAddress {
  id: number
  user?: number
  recipient_name: string
  phone: string
  address_line1: string
  address_line2?: string
  city: string
  state: string
  postal_code: string
  country: string
  is_default: boolean
  created_at?: string
  updated_at?: string
}

// ================== 주문 관련 ==================
export interface OrderItem {
  id: number
  product: Product
  quantity: number
  unit_price: number
  total_price: number
}

export interface Order {
  id: number
  order_number: string
  user?: User
  status: 'PENDING' | 'CONFIRMED' | 'PROCESSING' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED'
  items: OrderItem[]
  subtotal: number
  shipping_cost: number
  tax_amount: number
  discount_amount: number
  total_amount: number
  shipping_address: ShippingAddress
  payment_method: string
  payment_status: 'PENDING' | 'COMPLETED' | 'FAILED' | 'REFUNDED'
  tracking_number?: string
  estimated_delivery?: string
  notes?: string
  order_date: string
  created_at: string
  updated_at: string
  shipped_date?: string
  delivered_date?: string
}

// ================== 검색 관련 ==================
export interface SearchSuggestion {
  id: number
  query: string
  type: 'product' | 'category' | 'brand'
  count?: number
}

export interface SearchResult {
  products: PaginatedResponse<Product>
  categories: Category[]
  brands: Brand[]
  total_count: number
}

// ================== 기타 ==================
export interface Banner {
  id: number
  title: string
  description?: string
  image: string
  link_url?: string
  is_active: boolean
  display_order: number
  start_date?: string
  end_date?: string
  created_at: string
}

export interface Notification {
  id: number
  user: number
  title: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  is_read: boolean
  action_url?: string
  created_at: string
}

export interface ApiError {
  detail?: string
  message?: string
  errors?: Record<string, string[]>
  code?: string
}