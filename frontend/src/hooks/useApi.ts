import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  productService, 
  authService, 
  cartService, 
  wishlistService,
  orderService 
} from '../api/services'
import { ProductFilters, LoginRequest, RegisterRequest } from '../types/api'
import toast from 'react-hot-toast'

// ====================== 상품 관련 훅 ======================

export const useProducts = (filters?: ProductFilters) => {
  return useQuery({
    queryKey: ['products', filters],
    queryFn: () => productService.getProducts(filters),
    staleTime: 5 * 60 * 1000, // 5분
  })
}

export const useProduct = (id: string) => {
  return useQuery({
    queryKey: ['product', id],
    queryFn: () => productService.getProduct(id),
    enabled: !!id,
    staleTime: 10 * 60 * 1000, // 10분
  })
}

export const useFeaturedProducts = (limit = 8) => {
  return useQuery({
    queryKey: ['featured-products', limit],
    queryFn: () => productService.getFeaturedProducts(limit),
    staleTime: 10 * 60 * 1000,
  })
}

// ====================== 인증 관련 훅 ======================

export const useLogin = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (credentials: LoginRequest) => authService.login(credentials),
    onSuccess: (data) => {
      queryClient.setQueryData(['user'], data.user)
      toast.success('로그인되었습니다!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || '로그인에 실패했습니다.')
    }
  })
}

export const useRegister = () => {
  return useMutation({
    mutationFn: (userData: RegisterRequest) => authService.register(userData),
    onSuccess: () => {
      toast.success('회원가입이 완료되었습니다!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || '회원가입에 실패했습니다.')
    }
  })
}

export const useProfile = () => {
  return useQuery({
    queryKey: ['user'],
    queryFn: authService.getProfile,
    enabled: false, // 로그인 상태일 때만 활성화
    staleTime: 15 * 60 * 1000, // 15분
  })
}

// ====================== 장바구니 관련 훅 ======================

export const useCart = () => {
  return useQuery({
    queryKey: ['cart'],
    queryFn: cartService.getCart,
    staleTime: 2 * 60 * 1000, // 2분
  })
}

export const useAddToCart = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ productId, quantity }: { productId: string; quantity: number }) => 
      cartService.addToCart(productId, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] })
      toast.success('장바구니에 추가되었습니다!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || '장바구니 추가에 실패했습니다.')
    }
  })
}

export const useUpdateCartItem = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ productId, quantity }: { productId: string; quantity: number }) => 
      cartService.updateCartItem(productId, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || '수량 변경에 실패했습니다.')
    }
  })
}

export const useRemoveFromCart = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (productId: string) => cartService.removeFromCart(productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] })
      toast.success('상품이 삭제되었습니다.')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || '삭제에 실패했습니다.')
    }
  })
}

// ====================== 위시리스트 관련 훅 ======================

export const useWishlist = () => {
  return useQuery({
    queryKey: ['wishlist'],
    queryFn: wishlistService.getWishlist,
    staleTime: 5 * 60 * 1000,
  })
}

export const useToggleWishlist = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (productId: string) => wishlistService.toggleWishlist(productId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['wishlist'] })
      toast.success(data.added ? '찜목록에 추가되었습니다!' : '찜목록에서 제거되었습니다!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || '찜하기에 실패했습니다.')
    }
  })
}

// ====================== 주문 관련 훅 ======================

export const useOrders = () => {
  return useQuery({
    queryKey: ['orders'],
    queryFn: orderService.getOrders,
    staleTime: 5 * 60 * 1000,
  })
}

export const useOrder = (id: number) => {
  return useQuery({
    queryKey: ['order', id],
    queryFn: () => orderService.getOrder(id),
    enabled: !!id,
    staleTime: 10 * 60 * 1000,
  })
}

export const useCreateOrder = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (orderData: any) => orderService.createOrder(orderData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['cart'] })
      toast.success('주문이 완료되었습니다!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || '주문에 실패했습니다.')
    }
  })
}