//API 설정

import axios, { AxiosInstance, AxiosResponse } from 'axios'
import toast from 'react-hot-toast'

// API 기본 설정 - /api 제거 (Django URL 구조에 맞춤)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const API_TIMEOUT = 30000 // 30초

// Axios 인스턴스 생성
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // CORS 쿠키 지원
})

// JWT 토큰 관리 유틸리티 (수정됨)
export const tokenManager = {
  getAccessToken: (): string | null => {
    return localStorage.getItem('access_token')
  },
  
  getRefreshToken: (): string | null => {
    return localStorage.getItem('refresh_token')
  },
  
  setTokens: (accessToken: string, refreshToken: string): void => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
  },
  
  clearTokens: (): void => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  },
  
  isAuthenticated: (): boolean => {
    return !!tokenManager.getAccessToken()
  }
}

// Request 인터셉터 - JWT 토큰 자동 첨부
apiClient.interceptors.request.use(
  (config) => {
    const token = tokenManager.getAccessToken()
    if (token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${token}` // JWT 형식
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response 인터셉터 - 토큰 갱신 및 에러 처리
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config as any

    // 401 에러이고 토큰 갱신을 시도하지 않은 경우
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = tokenManager.getRefreshToken()
        if (refreshToken) {
          // JWT 토큰 갱신 요청 (엔드포인트 확인 필요)
          const response = await axios.post(`${API_BASE_URL}/api/auth/refresh/`, {
            refresh: refreshToken
          })
          
          const { access } = response.data
          tokenManager.setTokens(access, refreshToken)
          
          // 원래 요청에 새 토큰 적용 후 재시도
          originalRequest.headers.Authorization = `Bearer ${access}`
          return apiClient(originalRequest)
        }
      } catch (refreshError) {
        // 리프레시 토큰도 만료된 경우
        tokenManager.clearTokens()
        toast.error('로그인이 만료되었습니다. 다시 로그인해주세요.')
        
        // 현재 페이지가 로그인 페이지가 아닌 경우에만 리다이렉트
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
    }

    // 에러 메시지 처리
    const errorMessage = (error.response?.data as any)?.detail || 
                        (error.response?.data as any)?.message || 
                        error.message

    // 401 에러가 아닌 경우에만 토스트 표시
    if (error.response?.status !== 401 && errorMessage) {
      toast.error(errorMessage)
    }

    return Promise.reject(error)
  }
)

export default apiClient