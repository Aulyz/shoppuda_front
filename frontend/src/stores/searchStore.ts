// 검색 기록 및 필터 스토어
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { ProductFilters } from '@/types/api'

interface SearchState {
  // 검색 기록
  recentSearches: string[]
  
  // 현재 필터 상태
  currentFilters: ProductFilters
  
  // 인기 검색어 (서버에서 받아와서 저장)
  popularSearches: string[]
  
  // Actions
  addRecentSearch: (query: string) => void
  removeRecentSearch: (query: string) => void
  clearRecentSearches: () => void
  
  setCurrentFilters: (filters: ProductFilters) => void
  updateFilter: (key: keyof ProductFilters, value: any) => void
  clearFilters: () => void
  
  setPopularSearches: (searches: string[]) => void
}

export const useSearchStore = create<SearchState>()(
  persist(
    (set, get) => ({
      // Initial State
      recentSearches: [],
      currentFilters: {},
      popularSearches: [],
      
      // Actions
      addRecentSearch: (query) => {
        const trimmedQuery = query.trim()
        if (!trimmedQuery) return
        
        set(state => {
          const filtered = state.recentSearches.filter(s => s !== trimmedQuery)
          return {
            recentSearches: [trimmedQuery, ...filtered].slice(0, 10) // 최대 10개만 저장
          }
        })
      },
      
      removeRecentSearch: (query) => {
        set(state => ({
          recentSearches: state.recentSearches.filter(s => s !== query)
        }))
      },
      
      clearRecentSearches: () => {
        set({ recentSearches: [] })
      },
      
      setCurrentFilters: (currentFilters) => {
        set({ currentFilters })
      },
      
      updateFilter: (key, value) => {
        set(state => ({
          currentFilters: {
            ...state.currentFilters,
            [key]: value
          }
        }))
      },
      
      clearFilters: () => {
        set({ currentFilters: {} })
      },
      
      setPopularSearches: (popularSearches) => {
        set({ popularSearches })
      }
    }),
    {
      name: 'shopuda-search',
      partialize: (state) => ({
        recentSearches: state.recentSearches,
        currentFilters: state.currentFilters,
      }),
    }
  )
)