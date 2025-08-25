// 주문 관련 훅들
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { orderService } from '@/api'
import { useAuthStore } from '@/stores/authStore'

// 주문 목록 조회 훅
export const useOrders = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  return useQuery({
    queryKey: ['orders'],
    queryFn: () => orderService.getOrders(),
    enabled: isAuthenticated,
    staleTime: 60 * 1000, // 1분
  })
}

// 주문 상세 조회 훅
export const useOrder = (id: number) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  return useQuery({
    queryKey: ['order', id],
    queryFn: () => orderService.getOrder(id),
    enabled: isAuthenticated && !!id,
    staleTime: 2 * 60 * 1000, // 2분
  })
}

// 주문 취소 훅
export const useCancelOrder = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (orderId: number) => orderService.cancelOrder(orderId),
    onSuccess: (_, orderId) => {
      // 주문 목록과 상세 정보 갱신
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['order', orderId] })
      toast.success('주문이 취소되었습니다.')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '주문 취소에 실패했습니다.'
      toast.error(message)
    }
  })
}

// 주문 생성 훅
export const useCreateOrder = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (orderData: any) => orderService.createOrder(orderData),
    onSuccess: () => {
      // 주문 목록과 장바구니 갱신
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['cart'] })
      toast.success('주문이 완료되었습니다!')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '주문 처리에 실패했습니다.'
      toast.error(message)
    }
  })
}