// 위시리스트 관련 훅들
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { wishlistService } from '@/api'
import { useAuthStore } from '@/stores/authStore'

// 위시리스트 조회 훅
export const useWishlist = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  return useQuery({
    queryKey: ['wishlist'],
    queryFn: () => wishlistService.getWishlist(),
    enabled: isAuthenticated,
    staleTime: 2 * 60 * 1000, // 2분
  })
}

// 위시리스트 토글 훅
export const useToggleWishlist = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (productId: string) => wishlistService.toggleWishlist(productId),
    onSuccess: (result, productId) => {
      // 위시리스트 캐시 업데이트
      queryClient.invalidateQueries({ queryKey: ['wishlist'] })
      
      if (result.added) {
        toast.success('찜 목록에 추가되었습니다!')
      } else {
        toast.success('찜 목록에서 제거되었습니다.')
      }
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '찜하기에 실패했습니다.'
      toast.error(message)
    }
  })
}