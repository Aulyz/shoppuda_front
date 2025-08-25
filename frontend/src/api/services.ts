//API 서비스 파일

import apiClient, { tokenManager } from './config'
import {
  PaginatedResponse,
  LoginRequest,
  JWTTokenResponse,
  RegisterRequest,
  User,
  Product,
  ProductDetail,
  ProductFilters,
  Cart,
  WishlistItem,
  WishlistToggleResponse,
  ShippingAddress,
  Order,
  Category,
  Brand
} from '../types/api'

// ====================== 인증 서비스 ======================

export const authService = {
  // 로그인 - Django의 /accounts/user/login/ 사용
  login: async (credentials: LoginRequest): Promise<JWTTokenResponse> => {
    const response = await apiClient.post<JWTTokenResponse>('/accounts/user/login/', credentials)
    const { access, refresh, user } = response.data
    
    // 토큰 저장
    tokenManager.setTokens(access, refresh)
    localStorage.setItem('user', JSON.stringify(user))
    
    return response.data
  },

  // 회원가입 - Django의 /accounts/user/signup/ 사용
  register: async (userData: RegisterRequest): Promise<User> => {
    const response = await apiClient.post<User>('/accounts/user/signup/', userData)
    return response.data
  },

  // 로그아웃
  logout: async (): Promise<void> => {
    try {
      await apiClient.post('/accounts/logout/')
    } catch (error) {
      console.warn('Logout API call failed:', error)
    } finally {
      tokenManager.clearTokens()
    }
  },

  // 프로필 조회 - Django의 /accounts/profile/ 사용
  getProfile: async (): Promise<User> => {
    const response = await apiClient.get<User>('/accounts/profile/')
    return response.data
  },

  // 프로필 업데이트 - Django의 /accounts/profile/edit/ 사용
  updateProfile: async (userData: Partial<User>): Promise<User> => {
    const response = await apiClient.put<User>('/accounts/profile/edit/', userData)
    localStorage.setItem('user', JSON.stringify(response.data))
    return response.data
  },

  // 비밀번호 변경
  changePassword: async (passwordData: {
    old_password: string
    new_password: string
  }): Promise<void> => {
    await apiClient.post('/accounts/password/change/', passwordData)
  },

  // 현재 사용자 정보 (로컬스토리지에서)
  getCurrentUser: (): User | null => {
    const userStr = localStorage.getItem('user')
    return userStr ? JSON.parse(userStr) : null
  }
}

// ====================== 상품 서비스 ======================

export const productService = {
  // 상품 목록 조회 - Django의 /shop/products/ 사용
  getProducts: async (filters?: ProductFilters): Promise<PaginatedResponse<Product>> => {
    const params = new URLSearchParams()
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          if (Array.isArray(value)) {
            value.forEach(item => params.append(key, item.toString()))
          } else {
            params.append(key, value.toString())
          }
        }
      })
    }
    
    const response = await apiClient.get<PaginatedResponse<Product>>(
      `/shop/products/?${params.toString()}`
    )
    return response.data
  },

  // 상품 상세 조회 - Django의 /shop/products/{id}/ 사용
  getProduct: async (id: string): Promise<ProductDetail> => {
    const response = await apiClient.get<ProductDetail>(`/shop/products/${id}/`)
    return response.data
  },

  // 인기 상품 조회
  getFeaturedProducts: async (limit = 8): Promise<Product[]> => {
    const response = await apiClient.get<PaginatedResponse<Product>>(
      `/shop/products/?is_featured=true&page_size=${limit}`
    )
    return response.data.results
  },

  // 신상품 조회
  getNewProducts: async (limit = 6): Promise<Product[]> => {
    const response = await apiClient.get<PaginatedResponse<Product>>(
      `/shop/products/?ordering=-created_at&page_size=${limit}`
    )
    return response.data.results
  },

  // 상품 검색 - Django의 /shop/search/ 사용
  searchProducts: async (query: string, filters?: ProductFilters): Promise<PaginatedResponse<Product>> => {
    const params = new URLSearchParams()
    params.append('search', query)
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '' && key !== 'search') {
          if (Array.isArray(value)) {
            value.forEach(item => params.append(key, item.toString()))
          } else {
            params.append(key, value.toString())
          }
        }
      })
    }
    
    const response = await apiClient.get<PaginatedResponse<Product>>(
      `/shop/search/?${params.toString()}`
    )
    return response.data
  },

  // 검색 자동완성 - Django의 /search/quick/ 사용
  getSearchSuggestions: async (query: string): Promise<string[]> => {
    const response = await apiClient.get<{ suggestions: string[] }>(
      `/search/quick/?q=${encodeURIComponent(query)}`
    )
    return response.data.suggestions || []
  }
}

// ====================== 카테고리 & 브랜드 서비스 ======================

export const categoryService = {
  // 카테고리 목록 조회 (임시 Mock - Django에서 API 제공 시 수정)
  getCategories: async (): Promise<Category[]> => {
    // 실제 API 구현 대기 중이므로 Mock 데이터 반환
    return Promise.resolve([
      { id: 1, name: "의류", slug: "clothing", parent: null, is_active: true, sort_order: 1, product_count: 245 },
      { id: 2, name: "전자제품", slug: "electronics", parent: null, is_active: true, sort_order: 2, product_count: 156 },
      { id: 3, name: "홈&리빙", slug: "home", parent: null, is_active: true, sort_order: 3, product_count: 189 },
      { id: 4, name: "뷰티", slug: "beauty", parent: null, is_active: true, sort_order: 4, product_count: 78 },
      { id: 5, name: "스포츠", slug: "sports", parent: null, is_active: true, sort_order: 5, product_count: 92 },
      { id: 6, name: "도서", slug: "books", parent: null, is_active: true, sort_order: 6, product_count: 134 }
    ])
  }
}

export const brandService = {
  // 브랜드 목록 조회 (임시 Mock - Django에서 API 제공 시 수정)
  getBrands: async (): Promise<Brand[]> => {
    return Promise.resolve([
      { id: 1, name: "Nike", code: "NIKE", is_active: true },
      { id: 2, name: "Adidas", code: "ADIDAS", is_active: true },
      { id: 3, name: "Samsung", code: "SAMSUNG", is_active: true },
      { id: 4, name: "Apple", code: "APPLE", is_active: true },
      { id: 5, name: "LG", code: "LG", is_active: true }
    ])
  }
}

// ====================== 장바구니 서비스 ======================

export const cartService = {
  // 장바구니 조회 - Django의 /shop/cart/ 사용
  getCart: async (): Promise<Cart> => {
    const response = await apiClient.get<Cart>('/shop/cart/')
    return response.data
  },

  // 장바구니에 상품 추가 - Django의 /shop/cart/add/{product_id}/ 사용
  addToCart: async (productId: string, quantity: number = 1): Promise<Cart> => {
    const response = await apiClient.post<Cart>(`/shop/cart/add/${productId}/`, {
      quantity
    })
    return response.data
  },

  // 장바구니 아이템 수량 수정 - Django의 /shop/cart/update/{product_id}/ 사용
  updateCartItem: async (productId: string, quantity: number): Promise<Cart> => {
    const response = await apiClient.put<Cart>(`/shop/cart/update/${productId}/`, {
      quantity
    })
    return response.data
  },

  // 장바구니에서 아이템 제거 - Django의 /shop/cart/remove/{product_id}/ 사용
  removeFromCart: async (productId: string): Promise<Cart> => {
    const response = await apiClient.delete<Cart>(`/shop/cart/remove/${productId}/`)
    return response.data
  },

  // 장바구니 비우기 (각 아이템을 개별 삭제)
  clearCart: async (): Promise<void> => {
    const cart = await cartService.getCart()
    await Promise.all(
      cart.items.map(item => cartService.removeFromCart(item.product.id))
    )
  }
}

// ====================== 위시리스트 서비스 ======================

export const wishlistService = {
  // 위시리스트 조회 - Django의 /shop/wishlist/ 사용
  getWishlist: async (): Promise<WishlistItem[]> => {
    const response = await apiClient.get<WishlistItem[]>('/shop/wishlist/')
    return response.data
  },

  // 위시리스트 토글 - Django의 /shop/wishlist/toggle/{product_id}/ 사용
  toggleWishlist: async (productId: string): Promise<WishlistToggleResponse> => {
    const response = await apiClient.post<WishlistToggleResponse>(`/shop/wishlist/toggle/${productId}/`)
    return response.data
  }
}

// ====================== 주문 서비스 ======================

export const orderService = {
  // 주문 목록 조회 - Django의 /shop/orders/ 사용
  getOrders: async (): Promise<Order[]> => {
    const response = await apiClient.get<PaginatedResponse<Order>>('/shop/orders/')
    return response.data.results
  },

  // 주문 상세 조회 - Django의 /shop/orders/{id}/ 사용
  getOrder: async (id: number): Promise<Order> => {
    const response = await apiClient.get<Order>(`/shop/orders/${id}/`)
    return response.data
  },

  // 주문 취소 - Django의 /shop/orders/{id}/cancel/ 사용
  cancelOrder: async (id: number): Promise<void> => {
    await apiClient.post(`/shop/orders/${id}/cancel/`)
  },

  // 주문 생성 (결제 페이지에서 사용)
  createOrder: async (orderData: any): Promise<Order> => {
    const response = await apiClient.post<Order>('/shop/checkout/', orderData)
    return response.data
  }
}

// ====================== 배송지 서비스 ======================

export const addressService = {
  // 배송지 목록 조회
  getAddresses: async (): Promise<ShippingAddress[]> => {
    const response = await apiClient.get<ShippingAddress[]>('/shop/addresses/')
    return response.data
  },

  // 배송지 추가
  addAddress: async (address: Omit<ShippingAddress, 'id' | 'created_at' | 'updated_at'>): Promise<ShippingAddress> => {
    const response = await apiClient.post<ShippingAddress>('/shop/addresses/', address)
    return response.data
  },

  // 배송지 수정
  updateAddress: async (id: number, address: Partial<ShippingAddress>): Promise<ShippingAddress> => {
    const response = await apiClient.patch<ShippingAddress>(`/shop/addresses/${id}/`, address)
    return response.data
  },

  // 배송지 삭제
  deleteAddress: async (id: number): Promise<void> => {
    await apiClient.delete(`/shop/addresses/${id}/`)
  }
}

// ====================== 유틸리티 함수 ======================

export const apiUtils = {
  // 이미지 URL 변환 (상대 경로를 절대 경로로)
  getImageUrl: (imagePath: string): string => {
    if (!imagePath) return '/placeholder-image.jpg'
    if (imagePath.startsWith('http')) return imagePath
    const baseUrl = import.meta.env.VITE_STATIC_URL || 'http://localhost:8000'
    return `${baseUrl.replace(/\/$/, '')}${imagePath.startsWith('/') ? '' : '/'}${imagePath}`
  },

  // 가격 포맷팅
  formatPrice: (price: number): string => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW'
    }).format(price)
  },

  // 할인율 계산
  calculateDiscountPercentage: (originalPrice: number, discountPrice: number): number => {
    return Math.round(((originalPrice - discountPrice) / originalPrice) * 100)
  }
}