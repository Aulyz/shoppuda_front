// 장바구니 관련 훅들
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { cartService } from '@/api'
import { useAuthStore } from '@/stores/authStore'

// 장바구니 조회 훅
export const useCart = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  return useQuery({
    queryKey: ['cart'],
    queryFn: () => cartService.getCart(),
    enabled: isAuthenticated,
    staleTime: 30 * 1000, // 30초 (장바구니는 자주 업데이트)
  })
}

// 장바구니 추가 훅
export const useAddToCart = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ productId, quantity = 1 }: { productId: string; quantity?: number }) =>
      cartService.addToCart(productId, quantity),
    onSuccess: (updatedCart) => {
      queryClient.setQueryData(['cart'], updatedCart)
      toast.success('장바구니에 추가되었습니다!')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '장바구니 추가에 실패했습니다.'
      toast.error(message)
    }
  })
}

// 장바구니 아이템 수량 수정 훅
export const useUpdateCartItem = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ productId, quantity }: { productId: string; quantity: number }) =>
      cartService.updateCartItem(productId, quantity),
    onSuccess: (updatedCart) => {
      queryClient.setQueryData(['cart'], updatedCart)
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '수량 변경에 실패했습니다.'
      toast.error(message)
    }
  })
}

// 장바구니에서 아이템 제거 훅
export const useRemoveFromCart = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (productId: string) => cartService.removeFromCart(productId),
    onSuccess: (updatedCart) => {
      queryClient.setQueryData(['cart'], updatedCart)
      toast.success('상품이 장바구니에서 제거되었습니다.')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '상품 제거에 실패했습니다.'
      toast.error(message)
    }
  })
}

// 장바구니 비우기 훅
export const useClearCart = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => cartService.clearCart(),
    onSuccess: () => {
      queryClient.setQueryData(['cart'], {
        id: 0,
        items: [],
        total_quantity: 0,
        total_price: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
      toast.success('장바구니가 비워졌습니다.')
    },
    onError: () => {
      toast.error('장바구니 비우기에 실패했습니다.')
    }
  })
}