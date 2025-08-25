// 모든 스토어를 통합 export
export { useAuthStore } from './authStore'
export { useCartStore } from './cartStore'
export { useUIStore } from './uiStore'
export { useWishlistStore } from './wishlistStore'
export { useSearchStore } from './searchStore'

// 스토어 초기화 함수 (앱 시작 시 호출)
export const initializeStores = () => {
  // 필요한 경우 스토어들의 초기화 로직
  console.log('Stores initialized')
}