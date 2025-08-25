// src/api/services/productService.ts - 상품 관련 서비스
import apiClient from '../config'
import { 
  Product, 
  ProductDetail, 
  ProductFilters, 
  PaginatedResponse,
  Category,
  Brand
} from '../types'

export const productService = {
  // 상품 목록 조회 - Django의 /shop/products/ 사용
  getProducts: async (filters?: ProductFilters): Promise<PaginatedResponse<Product>> => {
    const params = new URLSearchParams()
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString())
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

  // 인기 상품 조회 (is_featured=true 필터 사용)
  getFeaturedProducts: async (limit = 8): Promise<Product[]> => {
    const response = await apiClient.get<PaginatedResponse<Product>>(
      `/shop/products/?is_featured=true&page_size=${limit}`
    )
    return response.data.results
  },

  // 신상품 조회 (최신순 정렬)
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
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString())
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