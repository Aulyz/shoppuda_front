import apiClient, { tokenManager } from './config'
import {
  ApiResponse,
  PaginatedResponse,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  User,
  Product,
  ProductFilters,
  Category,
  Brand,
  Banner,
  SearchSuggestion,
  Cart,
  CartItem,
  WishlistItem,
  ShippingAddress,
  Order
} from './types'

// ====================== 인증 서비스 ======================

export const authService = {
  // 로그인
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/login/', credentials)
    const { access, refresh, user } = response.data
    
    // 토큰 저장
    tokenManager.setTokens(access, refresh)
    localStorage.setItem('user', JSON.stringify(user))
    
    return response.data
  },

  // 회원가입
  register: async (userData: RegisterRequest): Promise<User> => {
    const response = await apiClient.post<User>('/auth/register/', userData)
    return response.data
  },

  // 로그아웃
  logout: (): void => {
    tokenManager.clearTokens()
  },

  // 프로필 조회
  getProfile: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/profile/')
    return response.data
  },

  // 프로필 업데이트
  updateProfile: async (userData: Partial<User>): Promise<User> => {
    const response = await apiClient.patch<User>('/auth/profile/', userData)
    localStorage.setItem('user', JSON.stringify(response.data))
    return response.data
  },

  // 현재 사용자 정보 (로컬스토리지에서)
  getCurrentUser: (): User | null => {
    const userStr = localStorage.getItem('user')
    return userStr ? JSON.parse(userStr) : null
  }
}

// ====================== 상품 서비스 ======================

export const productService = {
  // 상품 목록 조회 (임시 Mock 데이터)
  getProducts: async (filters?: ProductFilters): Promise<PaginatedResponse<Product>> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const mockProducts: Product[] = [
          {
            id: "1",
            sku: "PROD001",
            name: "프리미엄 무선 이어폰",
            slug: "premium-wireless-earphones",
            description: "고급 무선 이어폰입니다.",
            brand: { id: 1, name: "Apple", code: "APPLE", is_active: true },
            category: { id: 2, name: "전자제품", slug: "electronics", parent: null, is_active: true, sort_order: 2 },
            status: 'ACTIVE',
            price: 129000,
            selling_price: 129000,
            discount_price: 89000,
            stock_quantity: 50,
            min_stock_level: 10,
            is_featured: true,
            is_digital: false,
            images: [{ id: 1, image: "https://images.unsplash.com/photo-1572569511254-d8f925fe2cbb?w=400&h=400&fit=crop", alt_text: "이어폰", is_primary: true, sort_order: 1 }],
            tags: [],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            rating: 4.8,
            review_count: 324,
            is_new: true
          }
        ]
        
        resolve({
          results: mockProducts,
          count: mockProducts.length,
          next: null,
          previous: null
        })
      }, 100)
    })
  },

  // 상품 상세 조회
  getProduct: async (id: string): Promise<Product> => {
    const response = await apiClient.get<Product>(`/shop/products/${id}/`)
    return response.data
  },

  // 추천 상품 조회 (임시 Mock 데이터)
  getFeaturedProducts: async (limit = 8): Promise<Product[]> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve([])
      }, 100)
    })
  },

  // 신상품 조회 (임시 Mock 데이터)
  getNewProducts: async (limit = 6): Promise<Product[]> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve([])
      }, 100)
    })
  },

  // 상품 검색 자동완성
  searchSuggestions: async (query: string): Promise<SearchSuggestion[]> => {
    const response = await apiClient.get<ApiResponse<SearchSuggestion[]>>(
      `/shop/search/suggestions/?q=${encodeURIComponent(query)}`
    )
    return response.data.data || []
  }
}

// ====================== 카테고리 & 브랜드 서비스 ======================

export const categoryService = {
  // 카테고리 목록 조회 (임시 Mock 데이터)
  getCategories: async (): Promise<Category[]> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve([
          { id: 1, name: "의류", slug: "clothing", parent: null, is_active: true, sort_order: 1, product_count: 245 },
          { id: 2, name: "전자제품", slug: "electronics", parent: null, is_active: true, sort_order: 2, product_count: 156 },
          { id: 3, name: "화장품", slug: "cosmetics", parent: null, is_active: true, sort_order: 3, product_count: 89 },
          { id: 4, name: "가전제품", slug: "appliances", parent: null, is_active: true, sort_order: 4, product_count: 67 },
          { id: 5, name: "도서", slug: "books", parent: null, is_active: true, sort_order: 5, product_count: 234 },
          { id: 6, name: "스포츠", slug: "sports", parent: null, is_active: true, sort_order: 6, product_count: 123 }
        ])
      }, 100)
    })
  },

  // 카테고리 상세 조회
  getCategory: async (id: number): Promise<Category> => {
    const response = await apiClient.get<Category>(`/shop/categories/${id}/`)
    return response.data
  }
}

export const brandService = {
  // 브랜드 목록 조회 (임시 Mock 데이터)
  getBrands: async (): Promise<Brand[]> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve([
          { id: 1, name: "Apple", code: "APPLE", description: "Apple Inc.", is_active: true },
          { id: 2, name: "Samsung", code: "SAMSUNG", description: "Samsung Electronics", is_active: true },
          { id: 3, name: "Nike", code: "NIKE", description: "Nike Inc.", is_active: true }
        ])
      }, 100)
    })
  },

  // 브랜드 상세 조회
  getBrand: async (id: number): Promise<Brand> => {
    const response = await apiClient.get<Brand>(`/shop/brands/${id}/`)
    return response.data
  }
}

// ====================== 배너 서비스 ======================

export const bannerService = {
  // 메인 배너 조회 (임시 Mock 데이터)
  getMainBanners: async (): Promise<Banner[]> => {
    // TODO: 실제 API 연동 시 교체
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve([
          {
            id: 1,
            title: "신상품 특가 할인",
            subtitle: "최대 50% 할인된 가격으로 만나보세요",
            image: "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1200&h=600&fit=crop",
            link: "/products",
            button_text: "지금 쇼핑하기",
            is_active: true,
            order: 1
          }
        ])
      }, 100)
    })
  }
}

// ====================== 장바구니 서비스 ======================

export const cartService = {
  // 장바구니 조회
  getCart: async (): Promise<Cart> => {
    const response = await apiClient.get<Cart>('/shop/cart/')
    return response.data
  },

  // 장바구니에 상품 추가
  addToCart: async (productId: string, quantity = 1): Promise<CartItem> => {
    const response = await apiClient.post<CartItem>('/shop/cart/', {
      product_id: productId,
      quantity
    })
    return response.data
  },

  // 장바구니 아이템 수량 업데이트
  updateCartItem: async (itemId: number, quantity: number): Promise<CartItem> => {
    const response = await apiClient.patch<CartItem>(`/shop/cart/${itemId}/`, {
      quantity
    })
    return response.data
  },

  // 장바구니 아이템 삭제
  removeFromCart: async (itemId: number): Promise<void> => {
    await apiClient.delete(`/shop/cart/${itemId}/`)
  },

  // 장바구니 전체 비우기
  clearCart: async (): Promise<void> => {
    await apiClient.delete('/shop/cart/')
  }
}

// ====================== 위시리스트 서비스 ======================

export const wishlistService = {
  // 위시리스트 조회
  getWishlist: async (): Promise<WishlistItem[]> => {
    const response = await apiClient.get<PaginatedResponse<WishlistItem>>('/shop/wishlist/')
    return response.data.results
  },

  // 위시리스트에 추가/제거 토글
  toggleWishlist: async (productId: string): Promise<{ added: boolean }> => {
    const response = await apiClient.post<{ added: boolean }>('/shop/wishlist/toggle/', {
      product_id: productId
    })
    return response.data
  },

  // 위시리스트에서 제거
  removeFromWishlist: async (itemId: number): Promise<void> => {
    await apiClient.delete(`/shop/wishlist/${itemId}/`)
  }
}

// ====================== 주소 서비스 ======================

export const addressService = {
  // 배송지 목록 조회
  getAddresses: async (): Promise<ShippingAddress[]> => {
    const response = await apiClient.get<PaginatedResponse<ShippingAddress>>('/shop/addresses/')
    return response.data.results
  },

  // 배송지 추가
  addAddress: async (address: Omit<ShippingAddress, 'id'>): Promise<ShippingAddress> => {
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

// ====================== 주문 서비스 ======================

export const orderService = {
  // 주문 목록 조회
  getOrders: async (): Promise<Order[]> => {
    const response = await apiClient.get<PaginatedResponse<Order>>('/shop/orders/')
    return response.data.results
  },

  // 주문 상세 조회
  getOrder: async (id: number): Promise<Order> => {
    const response = await apiClient.get<Order>(`/shop/orders/${id}/`)
    return response.data
  },

  // 주문 생성
  createOrder: async (orderData: any): Promise<Order> => {
    const response = await apiClient.post<Order>('/shop/orders/', orderData)
    return response.data
  },

  // 주문 취소
  cancelOrder: async (id: number): Promise<void> => {
    await apiClient.post(`/shop/orders/${id}/cancel/`)
  }
}

// ====================== 유틸리티 함수 ======================

export const apiUtils = {
  // 이미지 URL 변환 (상대 경로를 절대 경로로)
  getImageUrl: (imagePath: string): string => {
    if (!imagePath) return ''
    if (imagePath.startsWith('http')) return imagePath
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    return `${baseUrl.replace('/api', '')}${imagePath}`
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