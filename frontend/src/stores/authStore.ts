// JWT 기반 인증 스토어
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { User } from '@/types/api'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  
  // Actions
  setAuth: (user: User, accessToken: string, refreshToken: string) => void
  updateUser: (user: Partial<User>) => void
  clearAuth: () => void
  setTokens: (accessToken: string, refreshToken: string) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial State
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      
      // Actions
      setAuth: (user, accessToken, refreshToken) => {
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
        })
      },
      
      updateUser: (userData) => {
        const currentUser = get().user
        if (currentUser) {
          set({
            user: { ...currentUser, ...userData }
          })
        }
      },
      
      clearAuth: () => {
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        })
      },
      
      setTokens: (accessToken, refreshToken) => {
        set({ accessToken, refreshToken })
      }
    }),
    {
      name: 'shopuda-auth',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)