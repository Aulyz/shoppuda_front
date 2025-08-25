// JWT 기반 인증 서비스
import apiClient, { tokenManager } from '../config'
import { 
  LoginRequest, 
  JWTTokenResponse, 
  RegisterRequest, 
  User 
} from '../types'

export const authService = {
  // 로그인 - Django의 /accounts/user/login/ 엔드포인트 사용
  login: async (credentials: LoginRequest): Promise<JWTTokenResponse> => {
    const response = await apiClient.post<JWTTokenResponse>('/accounts/user/login/', credentials)
    const { access, refresh, user } = response.data
    
    // 토큰과 사용자 정보 저장
    tokenManager.setTokens(access, refresh)
    localStorage.setItem('user', JSON.stringify(user))
    
    return response.data
  },

  // 회원가입 - Django의 /accounts/user/signup/ 엔드포인트 사용
  register: async (userData: RegisterRequest): Promise<User> => {
    const response = await apiClient.post<User>('/accounts/user/signup/', userData)
    return response.data
  },

  // 로그아웃
  logout: async (): Promise<void> => {
    try {
      // 서버에 로그아웃 요청 (선택사항)
      await apiClient.post('/accounts/logout/')
    } catch (error) {
      console.warn('Logout API call failed:', error)
    } finally {
      tokenManager.clearTokens()
    }
  },

  // 프로필 조회 - Django의 /accounts/profile/ 엔드포인트 사용
  getProfile: async (): Promise<User> => {
    const response = await apiClient.get<User>('/accounts/profile/')
    return response.data
  },

  // 프로필 수정 - Django의 /accounts/profile/edit/ 엔드포인트 사용
  updateProfile: async (userData: Partial<User>): Promise<User> => {
    const response = await apiClient.put<User>('/accounts/profile/edit/', userData)
    localStorage.setItem('user', JSON.stringify(response.data))
    return response.data
  },

  // 비밀번호 변경 - Django의 /accounts/password/change/ 엔드포인트 사용
  changePassword: async (passwordData: {
    old_password: string
    new_password: string
  }): Promise<void> => {
    await apiClient.post('/accounts/password/change/', passwordData)
  },

  // JWT 토큰 갱신
  refreshToken: async (): Promise<string> => {
    const refreshToken = tokenManager.getRefreshToken()
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }

    const response = await apiClient.post<{ access: string }>('/api/auth/refresh/', {
      refresh: refreshToken
    })
    
    const { access } = response.data
    tokenManager.setTokens(access, refreshToken)
    
    return access
  },

  // 현재 사용자 정보 (로컬스토리지에서)
  getCurrentUser: (): User | null => {
    const userStr = localStorage.getItem('user')
    return userStr ? JSON.parse(userStr) : null
  }
}