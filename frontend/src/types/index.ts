// 기본 타입 정의
export interface BaseEntity {
  id: number;
  created_at: string;
  updated_at: string;
}

// 사용자 관련 타입
export interface User extends BaseEntity {
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  phone?: string;
  is_active: boolean;
  is_staff: boolean;
  profile?: UserProfile;
}

export interface UserProfile extends BaseEntity {
  user: number;
  birth_date?: string;
  gender?: 'M' | 'F' | 'O';
  address?: string;
  postal_code?: string;
  avatar?: string;
}

// 상품 관련 타입
export interface Category extends BaseEntity {
  name: string;
  slug: string;
  description?: string;
  image?: string;
  parent?: number;
  is_active: boolean;
  sort_order: number;
}

export interface Brand extends BaseEntity {
  name: string;
  slug: string;
  description?: string;
  logo?: string;
  website?: string;
  is_active: boolean;
}

export interface ProductImage extends BaseEntity {
  product: number;
  image: string;
  alt_text?: string;
  is_primary: boolean;
  sort_order: number;
}

export interface ProductVariant extends BaseEntity {
  product: number;
  name: string;
  sku: string;
  price: number;
  sale_price?: number;
  stock_quantity: number;
  weight?: number;
  dimensions?: string;
  is_active: boolean;
  attributes: Record<string, string>;
}

export interface Product extends BaseEntity {
  name: string;
  slug: string;
  description: string;
  short_description?: string;
  sku: string;
  category: Category;
  brand?: Brand;
  price: number;
  sale_price?: number;
  stock_quantity: number;
  min_stock_level: number;
  weight?: number;
  dimensions?: string;
  is_active: boolean;
  is_featured: boolean;
  meta_title?: string;
  meta_description?: string;
  images: ProductImage[];
  variants: ProductVariant[];
  tags: string[];
  rating_average: number;
  review_count: number;
}

// 장바구니 관련 타입
export interface CartItem extends BaseEntity {
  product: Product;
  variant?: ProductVariant;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface Cart extends BaseEntity {
  user?: number;
  session_key?: string;
  items: CartItem[];
  total_quantity: number;
  total_price: number;
  is_active: boolean;
}

// 주문 관련 타입
export interface ShippingAddress extends BaseEntity {
  recipient_name: string;
  phone: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  is_default: boolean;
}

export interface OrderItem extends BaseEntity {
  product: Product;
  variant?: ProductVariant;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface Order extends BaseEntity {
  user?: User;
  order_number: string;
  status: 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';
  items: OrderItem[];
  subtotal: number;
  shipping_cost: number;
  tax_amount: number;
  discount_amount: number;
  total_amount: number;
  shipping_address: ShippingAddress;
  payment_method: string;
  payment_status: 'pending' | 'completed' | 'failed' | 'refunded';
  tracking_number?: string;
  notes?: string;
  estimated_delivery?: string;
}

// 리뷰 관련 타입
export interface Review extends BaseEntity {
  product: number;
  user: User;
  rating: number;
  title: string;
  content: string;
  is_verified_purchase: boolean;
  is_approved: boolean;
  helpful_count: number;
  images?: string[];
}

// 찜하기 관련 타입
export interface Wishlist extends BaseEntity {
  user: number;
  product: Product;
}

// API 응답 타입
export interface APIResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: Record<string, string[]>;
}

export interface PaginatedResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}

// 필터 및 검색 관련 타입
export interface ProductFilters {
  category?: number[];
  brand?: number[];
  min_price?: number;
  max_price?: number;
  is_on_sale?: boolean;
  is_featured?: boolean;
  in_stock?: boolean;
  rating_min?: number;
  search?: string;
  tags?: string[];
  sort_by?: 'name' | 'price' | 'created_at' | 'rating' | 'popularity';
  sort_order?: 'asc' | 'desc';
}

export interface SearchParams {
  page?: number;
  page_size?: number;
  filters?: ProductFilters;
}

// 폼 관련 타입
export interface LoginForm {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface SignUpForm {
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  password: string;
  password_confirm: string;
  agree_terms: boolean;
  agree_marketing?: boolean;
}

export interface ContactForm {
  name: string;
  email: string;
  phone?: string;
  subject: string;
  message: string;
}

export interface AddressForm {
  recipient_name: string;
  phone: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  is_default?: boolean;
}

// 이벤트 및 쿠폰 관련 타입
export interface Coupon extends BaseEntity {
  code: string;
  name: string;
  description?: string;
  discount_type: 'percentage' | 'fixed';
  discount_value: number;
  min_order_amount?: number;
  max_discount_amount?: number;
  usage_limit?: number;
  used_count: number;
  valid_from: string;
  valid_until: string;
  is_active: boolean;
}

export interface Event extends BaseEntity {
  title: string;
  slug: string;
  description: string;
  banner_image?: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
  featured_products: Product[];
  discount_percentage?: number;
}

// 알림 관련 타입
export interface Notification extends BaseEntity {
  user: number;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  is_read: boolean;
  action_url?: string;
}

// 플랫폼 연동 관련 타입
export interface Platform extends BaseEntity {
  name: string;
  slug: string;
  api_url: string;
  is_active: boolean;
  sync_enabled: boolean;
  last_sync?: string;
  config: Record<string, any>;
}

// 상태 관리 관련 타입
export interface AppState {
  user: User | null;
  cart: Cart | null;
  wishlist: Product[];
  notifications: Notification[];
  loading: boolean;
  error: string | null;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  loading: boolean;
  error: string | null;
}

export interface CartState {
  items: CartItem[];
  totalQuantity: number;
  totalPrice: number;
  loading: boolean;
  error: string | null;
}

export interface ProductState {
  products: Product[];
  categories: Category[];
  brands: Brand[];
  filters: ProductFilters;
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
  loading: boolean;
  error: string | null;
}

// 유틸리티 타입
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type CreateRequest<T> = Omit<T, 'id' | 'created_at' | 'updated_at'>;
export type UpdateRequest<T> = Partial<CreateRequest<T>>;

// 컴포넌트 Props 타입
export interface ProductCardProps {
  product: Product;
  showQuickView?: boolean;
  showWishlist?: boolean;
  showCompare?: boolean;
  className?: string;
}

export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
}

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

// 환경 변수 타입
export interface EnvConfig {
  API_BASE_URL: string;
  MEDIA_BASE_URL: string;
  APP_NAME: string;
  APP_VERSION: string;
  GOOGLE_ANALYTICS_ID?: string;
  SENTRY_DSN?: string;
}