// src/api/services/orderService.ts - 주문 서비스
import apiClient from '../config'
import { Order, PaginatedResponse } from '../../types/api'

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