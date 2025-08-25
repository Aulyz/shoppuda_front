// src/api/services/cartService.ts - 장바구니 서비스
import apiClient from '../config'
import { Cart } from '../../types/api'

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

  // 장바구니 비우기 (전체 삭제)
  clearCart: async (): Promise<void> => {
    // Django에 해당 엔드포인트가 없다면 각 아이템을 개별 삭제
    const cart = await cartService.getCart()
    await Promise.all(
      cart.items.map(item => cartService.removeFromCart(item.product.id))
    )
  }
}