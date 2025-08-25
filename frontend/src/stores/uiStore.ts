// UI 상태 관리 스토어
import { create } from 'zustand'

interface UIState {
  // 모바일 메뉴
  isMobileMenuOpen: boolean
  
  // 검색
  isSearchOpen: boolean
  searchQuery: string
  
  // 장바구니 사이드바
  isCartSidebarOpen: boolean
  
  // 로딩 상태들
  isPageLoading: boolean
  
  // 알림/토스트
  notifications: Array<{
    id: string
    type: 'success' | 'error' | 'info' | 'warning'
    message: string
    timestamp: number
  }>
  
  // Actions
  toggleMobileMenu: () => void
  closeMobileMenu: () => void
  
  toggleSearch: () => void
  setSearchQuery: (query: string) => void
  clearSearch: () => void
  
  toggleCartSidebar: () => void
  closeCartSidebar: () => void
  
  setPageLoading: (loading: boolean) => void
  
  addNotification: (notification: Omit<UIState['notifications'][0], 'id' | 'timestamp'>) => void
  removeNotification: (id: string) => void
  clearNotifications: () => void
}

export const useUIStore = create<UIState>((set, get) => ({
  // Initial State
  isMobileMenuOpen: false,
  isSearchOpen: false,
  searchQuery: '',
  isCartSidebarOpen: false,
  isPageLoading: false,
  notifications: [],
  
  // Mobile Menu Actions
  toggleMobileMenu: () => {
    set(state => ({ isMobileMenuOpen: !state.isMobileMenuOpen }))
  },
  
  closeMobileMenu: () => {
    set({ isMobileMenuOpen: false })
  },
  
  // Search Actions
  toggleSearch: () => {
    set(state => ({ isSearchOpen: !state.isSearchOpen }))
  },
  
  setSearchQuery: (searchQuery) => {
    set({ searchQuery })
  },
  
  clearSearch: () => {
    set({ searchQuery: '', isSearchOpen: false })
  },
  
  // Cart Sidebar Actions
  toggleCartSidebar: () => {
    set(state => ({ isCartSidebarOpen: !state.isCartSidebarOpen }))
  },
  
  closeCartSidebar: () => {
    set({ isCartSidebarOpen: false })
  },
  
  // Loading Actions
  setPageLoading: (isPageLoading) => {
    set({ isPageLoading })
  },
  
  // Notification Actions
  addNotification: (notification) => {
    const id = Date.now().toString()
    const timestamp = Date.now()
    
    set(state => ({
      notifications: [
        ...state.notifications,
        { ...notification, id, timestamp }
      ]
    }))
    
    // 5초 후 자동 제거
    setTimeout(() => {
      get().removeNotification(id)
    }, 5000)
  },
  
  removeNotification: (id) => {
    set(state => ({
      notifications: state.notifications.filter(n => n.id !== id)
    }))
  },
  
  clearNotifications: () => {
    set({ notifications: [] })
  }
}))