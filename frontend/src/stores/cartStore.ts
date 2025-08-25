// 장바구니 스토어 (서버와 동기화)
import { create } from 'zustand'
import { Cart, CartItem } from '@/types/api'

interface CartState {
  cart: Cart | null
  isLoading: boolean
  
  // Actions
  setCart: (cart: Cart) => void
  updateCartItem: (productId: string, quantity: number) => void
  removeCartItem: (productId: string) => void
  clearCart: () => void
  setLoading: (loading: boolean) => void
  
  // Getters
  getTotalQuantity: () => number
  getTotalPrice: () => number
  getItemCount: () => number
  hasItem: (productId: string) => boolean
  getItemQuantity: (productId: string) => number
}

export const useCartStore = create<CartState>((set, get) => ({
  // Initial State
  cart: null,
  isLoading: false,
  
  // Actions
  setCart: (cart) => {
    set({ cart, isLoading: false })
  },
  
  updateCartItem: (productId, quantity) => {
    const { cart } = get()
    if (!cart) return
    
    const updatedItems = cart.items.map(item => 
      item.product.id === productId 
        ? { ...item, quantity, total_price: item.unit_price * quantity }
        : item
    )
    
    const totalQuantity = updatedItems.reduce((sum, item) => sum + item.quantity, 0)
    const totalPrice = updatedItems.reduce((sum, item) => sum + item.total_price, 0)
    
    set({
      cart: {
        ...cart,
        items: updatedItems,
        total_quantity: totalQuantity,
        total_price: totalPrice
      }
    })
  },
  
  removeCartItem: (productId) => {
    const { cart } = get()
    if (!cart) return
    
    const updatedItems = cart.items.filter(item => item.product.id !== productId)
    const totalQuantity = updatedItems.reduce((sum, item) => sum + item.quantity, 0)
    const totalPrice = updatedItems.reduce((sum, item) => sum + item.total_price, 0)
    
    set({
      cart: {
        ...cart,
        items: updatedItems,
        total_quantity: totalQuantity,
        total_price: totalPrice
      }
    })
  },
  
  clearCart: () => {
    set({
      cart: {
        id: 0,
        items: [],
        total_quantity: 0,
        total_price: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    })
  },
  
  setLoading: (isLoading) => {
    set({ isLoading })
  },
  
  // Getters
  getTotalQuantity: () => {
    const { cart } = get()
    return cart?.total_quantity || 0
  },
  
  getTotalPrice: () => {
    const { cart } = get()
    return cart?.total_price || 0
  },
  
  getItemCount: () => {
    const { cart } = get()
    return cart?.items.length || 0
  },
  
  hasItem: (productId) => {
    const { cart } = get()
    return cart?.items.some(item => item.product.id === productId) || false
  },
  
  getItemQuantity: (productId) => {
    const { cart } = get()
    const item = cart?.items.find(item => item.product.id === productId)
    return item?.quantity || 0
  }
}))