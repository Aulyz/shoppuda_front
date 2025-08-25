// JWT 기반 인증 훅들
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

import { authService } from '@/api'
import { useAuthStore } from '@/stores/authStore'
import { LoginRequest, RegisterRequest } from '@/types/api'

// 로그인 훅
export const useLogin = () => {
  const navigate = useNavigate()
  const setAuth = useAuthStore((state) => state.setAuth)
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (credentials: LoginRequest) => authService.login(credentials),
    onSuccess: (data) => {
      const { access, refresh, user } = data
      setAuth(user, access, refresh)
      
      // React Query 캐시에 사용자 정보 저장
      queryClient.setQueryData(['currentUser'], user)
      
      toast.success(`안녕하세요, ${user.first_name || user.username}님!`)
      navigate('/')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 
                    error.response?.data?.message || 
                    '로그인에 실패했습니다.'
      toast.error(message)
    }
  })
}

// 회원가입 훅
export const useRegister = () => {
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (userData: RegisterRequest) => authService.register(userData),
    onSuccess: () => {
      toast.success('회원가입이 완료되었습니다! 로그인해주세요.')
      navigate('/login')
    },
    onError: (error: any) => {
      const errorData = error.response?.data
      
      if (errorData && typeof errorData === 'object') {
        // Django 폼 에러 처리
        const errorMessages = Object.values(errorData).flat()
        errorMessages.forEach(message => toast.error(message as string))
      } else {
        toast.error('회원가입에 실패했습니다.')
      }
    }
  })
}

// 로그아웃 훅
export const useLogout = () => {
  const navigate = useNavigate()
  const clearAuth = useAuthStore((state) => state.clearAuth)
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => authService.logout(),
    onSuccess: () => {
      clearAuth()
      queryClient.clear()
      toast.success('로그아웃되었습니다.')
      navigate('/')
    },
    onError: () => {
      // 로그아웃은 실패해도 클라이언트에서 정리
      clearAuth()
      queryClient.clear()
      navigate('/')
    }
  })
}

// 현재 사용자 정보 조회 훅
export const useCurrentUser = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  return useQuery({
    queryKey: ['currentUser'],
    queryFn: () => authService.getProfile(),
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000, // 5분
    retry: false,
    onError: () => {
      // 사용자 정보 조회 실패 시 로그아웃 처리
      useAuthStore.getState().clearAuth()
    }
  })
}

// 프로필 수정 훅
export const useUpdateProfile = () => {
  const queryClient = useQueryClient()
  const updateUser = useAuthStore((state) => state.updateUser)

  return useMutation({
    mutationFn: (userData: any) => authService.updateProfile(userData),
    onSuccess: (updatedUser) => {
      updateUser(updatedUser)
      queryClient.setQueryData(['currentUser'], updatedUser)
      toast.success('프로필이 업데이트되었습니다.')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '프로필 업데이트에 실패했습니다.'
      toast.error(message)
    }
  })
}

// 비밀번호 변경 훅
export const useChangePassword = () => {
  return useMutation({
    mutationFn: (passwordData: { old_password: string; new_password: string }) => 
      authService.changePassword(passwordData),
    onSuccess: () => {
      toast.success('비밀번호가 변경되었습니다.')
    },
    onError: (error: any) => {
      const errorData = error.response?.data
      if (errorData?.old_password) {
        toast.error('기존 비밀번호가 올바르지 않습니다.')
      } else {
        toast.error('비밀번호 변경에 실패했습니다.')
      }
    }
  })
}