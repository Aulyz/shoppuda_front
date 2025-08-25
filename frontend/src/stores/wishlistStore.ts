// 위시리스트 스토어
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { WishlistItem, Product } from '@/types/api'

interface WishlistState {
  items: WishlistItem[]
  
  // Actions
  setWishlist: (items: WishlistItem[]) => void
  addToWishlist: (item: WishlistItem) => void
  removeFromWishlist: (productId: string) => void
  clearWishlist: () => void
  
  // Getters
  isWishlisted: (productId: string) => boolean
  getWishlistCount: () => number
}

export const useWishlistStore = create<WishlistState>()(
  persist(
    (set, get) => ({
      // Initial State
      items: [],
      
      // Actions
      setWishlist: (items) => {
        set({ items })
      },
      
      addToWishlist: (item) => {
        set(state => ({
          items: [...state.items.filter(i => i.product.id !== item.product.id), item]
        }))
      },
      
      removeFromWishlist: (productId) => {
        set(state => ({
          items: state.items.filter(item => item.product.id !== productId)
        }))
      },
      
      clearWishlist: () => {
        set({ items: [] })
      },
      
      // Getters
      isWishlisted: (productId) => {
        const { items } = get()
        return items.some(item => item.product.id === productId)
      },
      
      getWishlistCount: () => {
        const { items } = get()
        return items.length
      }
    }),
    {
      name: 'shopuda-wishlist',
    }
  )
)