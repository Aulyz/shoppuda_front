// src/api/services/wishlistService.ts - 위시리스트 서비스
import apiClient from '../config'
import { WishlistItem } from '../../types/api'

export const wishlistService = {
  // 위시리스트 조회 - Django의 /shop/wishlist/ 사용
  getWishlist: async (): Promise<WishlistItem[]> => {
    const response = await apiClient.get<WishlistItem[]>('/shop/wishlist/')
    return response.data
  },

  // 위시리스트 토글 - Django의 /shop/wishlist/toggle/{product_id}/ 사용
  toggleWishlist: async (productId: string): Promise<{ added: boolean }> => {
    const response = await apiClient.post<{ added: boolean }>(`/shop/wishlist/toggle/${productId}/`)
    return response.data
  }
}