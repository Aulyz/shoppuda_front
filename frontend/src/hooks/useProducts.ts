// 상품 관련 훅들
import { useQuery, useInfiniteQuery } from '@tanstack/react-query'
import { productService } from '@/api'
import { ProductFilters } from '@/types/api'

// 상품 목록 조회 훅
export const useProducts = (filters?: ProductFilters) => {
  return useQuery({
    queryKey: ['products', filters],
    queryFn: () => productService.getProducts(filters),
    staleTime: 3 * 60 * 1000, // 3분
    gcTime: 10 * 60 * 1000, // 10분 (기존 cacheTime)
  })
}

// 상품 상세 조회 훅
export const useProduct = (id: string) => {
  return useQuery({
    queryKey: ['product', id],
    queryFn: () => productService.getProduct(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5분
  })
}

// 인기 상품 조회 훅
export const useFeaturedProducts = (limit?: number) => {
  return useQuery({
    queryKey: ['products', 'featured', limit],
    queryFn: () => productService.getFeaturedProducts(limit),
    staleTime: 10 * 60 * 1000, // 10분
  })
}

// 신상품 조회 훅
export const useNewProducts = (limit?: number) => {
  return useQuery({
    queryKey: ['products', 'new', limit],
    queryFn: () => productService.getNewProducts(limit),
    staleTime: 10 * 60 * 1000, // 10분
  })
}

// 상품 검색 훅
export const useSearchProducts = (query: string, filters?: ProductFilters) => {
  return useQuery({
    queryKey: ['products', 'search', query, filters],
    queryFn: () => productService.searchProducts(query, filters),
    enabled: query.length >= 2,
    staleTime: 2 * 60 * 1000, // 2분
  })
}

// 검색 자동완성 훅
export const useSearchSuggestions = (query: string) => {
  return useQuery({
    queryKey: ['search', 'suggestions', query],
    queryFn: () => productService.getSearchSuggestions(query),
    enabled: query.length >= 2,
    staleTime: 5 * 60 * 1000, // 5분
  })
}

// 무한 스크롤 상품 목록 훅
export const useInfiniteProducts = (filters?: ProductFilters) => {
  return useInfiniteQuery({
    queryKey: ['products', 'infinite', filters],
    queryFn: ({ pageParam = 1 }) => 
      productService.getProducts({ ...filters, page: pageParam }),
    getNextPageParam: (lastPage, allPages) => {
      return lastPage.next ? allPages.length + 1 : undefined
    },
    initialPageParam: 1,
    staleTime: 3 * 60 * 1000,
  })
}