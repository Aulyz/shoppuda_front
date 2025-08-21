import axios, { AxiosInstance, AxiosResponse } from 'axios'
import toast from 'react-hot-toast'

// API 기본 설정
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const API_TIMEOUT = 30000 // 30초

// Axios 인스턴스 생성
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 토큰 관리 유틸리티
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

// Request 인터셉터
apiClient.interceptors.request.use(
  (config) => {
    const token = tokenManager.getAccessToken()
    if (token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response 인터셉터
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = tokenManager.getRefreshToken()
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken
          })
          
          const { access } = response.data
          tokenManager.setTokens(access, refreshToken)
          
          // 원래 요청 재시도
          originalRequest.headers.Authorization = `Bearer ${access}`
          return apiClient(originalRequest)
        }
      } catch (refreshError) {
        // 리프레시 토큰도 만료된 경우
        tokenManager.clearTokens()
        toast.error('로그인이 만료되었습니다. 다시 로그인해주세요.')
        window.location.href = '/login'
      }
    }

    // 에러 메시지 처리
    if (error.response?.data?.message) {
      toast.error(error.response.data.message)
    } else if (error.message) {
      toast.error(error.message)
    }

    return Promise.reject(error)
  }
)

export default apiClient