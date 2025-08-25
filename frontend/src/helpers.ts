// 유틸리티 함수들
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'  // 수정된 import

// Tailwind CSS 클래스 병합 함수
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// 가격 포맷팅
export function formatPrice(price: number): string {
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
  }).format(price)
}

// 숫자에 천단위 콤마 추가
export function formatNumber(num: number): string {
  return new Intl.NumberFormat('ko-KR').format(num)
}

// 할인율 계산
export function calculateDiscountPercentage(originalPrice: number, discountPrice: number): number {
  if (originalPrice <= 0 || discountPrice >= originalPrice) return 0
  return Math.round(((originalPrice - discountPrice) / originalPrice) * 100)
}

// 디바운스 함수
export function debounce<T extends (...args: any[]) => void>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout
  return (...args: Parameters<T>) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

// 날짜 포맷팅
export function formatDate(date: string | Date, options?: Intl.DateTimeFormatOptions): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  
  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }
  
  return new Intl.DateTimeFormat('ko-KR', { ...defaultOptions, ...options }).format(dateObj)
}

// 상대 시간 포맷팅 (몇 분 전, 몇 시간 전 등)
export function formatRelativeTime(date: string | Date): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000)
  
  if (diffInSeconds < 60) return '방금 전'
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}분 전`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}시간 전`
  if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)}일 전`
  
  return formatDate(dateObj)
}

// 이미지 URL 처리
export function getImageUrl(imagePath: string | undefined | null): string {
  if (!imagePath) return '/placeholder-image.jpg'
  
  // 이미 전체 URL인 경우
  if (imagePath.startsWith('http')) return imagePath
  
  // 상대 경로인 경우 BASE_URL 추가
  const baseUrl = import.meta.env.VITE_STATIC_URL || 'http://localhost:8000'
  return `${baseUrl.replace(/\/$/, '')}${imagePath.startsWith('/') ? '' : '/'}${imagePath}`
}

// 평점을 별점으로 변환
export function getRatingStars(rating: number): { fullStars: number; hasHalfStar: boolean; emptyStars: number } {
  const fullStars = Math.floor(rating)
  const hasHalfStar = rating % 1 >= 0.5
  const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0)
  
  return { fullStars, hasHalfStar, emptyStars }
}

// 문자열 자르기 (말줄임)
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// URL 파라미터 생성
export function buildQueryString(params: Record<string, any>): string {
  const searchParams = new URLSearchParams()
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        value.forEach(item => searchParams.append(key, item.toString()))
      } else {
        searchParams.append(key, value.toString())
      }
    }
  })
  
  return searchParams.toString()
}

// 로컬스토리지 안전하게 사용
export const storage = {
  get: <T>(key: string, defaultValue?: T): T | null => {
    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : defaultValue ?? null
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error)
      return defaultValue ?? null
    }
  },
  
  set: (key: string, value: any): void => {
    try {
      window.localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error)
    }
  },
  
  remove: (key: string): void => {
    try {
      window.localStorage.removeItem(key)
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error)
    }
  },
  
  clear: (): void => {
    try {
      window.localStorage.clear()
    } catch (error) {
      console.warn('Error clearing localStorage:', error)
    }
  }
}

// 이메일 유효성 검사
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

// 전화번호 포맷팅 (한국 번호)
export function formatPhoneNumber(phone: string): string {
  const cleaned = phone.replace(/\D/g, '')
  
  if (cleaned.length === 11) {
    return cleaned.replace(/(\d{3})(\d{4})(\d{4})/, '$1-$2-$3')
  } else if (cleaned.length === 10) {
    return cleaned.replace(/(\d{3})(\d{3})(\d{4})/, '$1-$2-$3')
  }
  
  return phone
}

// 파일 크기 포맷팅
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 색상 밝기 계산 (접근성을 위한)
export function getContrastColor(hexColor: string): 'light' | 'dark' {
  const r = parseInt(hexColor.slice(1, 3), 16)
  const g = parseInt(hexColor.slice(3, 5), 16)
  const b = parseInt(hexColor.slice(5, 7), 16)
  
  // 밝기 계산
  const brightness = (r * 299 + g * 587 + b * 114) / 1000
  
  return brightness > 128 ? 'dark' : 'light'
}

// 랜덤 ID 생성
export function generateId(prefix?: string): string {
  const timestamp = Date.now().toString(36)
  const randomStr = Math.random().toString(36).substring(2)
  return prefix ? `${prefix}_${timestamp}_${randomStr}` : `${timestamp}_${randomStr}`
}

// 상품 상태 체크
export function getProductStatus(product: { stock_quantity: number; status: string }) {
  if (product.status !== 'ACTIVE') return 'inactive'
  if (product.stock_quantity === 0) return 'out_of_stock'
  if (product.stock_quantity <= 10) return 'low_stock'
  return 'in_stock'
}

// 주문 상태 한글 변환
export function getOrderStatusText(status: string): string {
  const statusMap: Record<string, string> = {
    'PENDING': '주문 대기',
    'CONFIRMED': '주문 확인',
    'PROCESSING': '처리 중',
    'SHIPPED': '배송 중',
    'DELIVERED': '배송 완료',
    'CANCELLED': '주문 취소'
  }
  
  return statusMap[status] || status
}

// 결제 상태 한글 변환
export function getPaymentStatusText(status: string): string {
  const statusMap: Record<string, string> = {
    'PENDING': '결제 대기',
    'COMPLETED': '결제 완료',
    'FAILED': '결제 실패',
    'REFUNDED': '환불 완료'
  }
  
  return statusMap[status] || status
}