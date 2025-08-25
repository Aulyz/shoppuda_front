import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import {
  MagnifyingGlassIcon,
  AdjustmentsHorizontalIcon,
  HeartIcon,
  ShoppingCartIcon,
  StarIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline'
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid'

// 수정된 import 경로들
import { productService, categoryService, brandService } from '../api/services'
import { Product, ProductFilters, Category, Brand } from '../types/api'

const Products: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [showFilters, setShowFilters] = useState(false)
  const [wishlist, setWishlist] = useState<Set<string>>(new Set())

  // URL 파라미터에서 필터 상태 추출
  const filters: ProductFilters = {
    search: searchParams.get('search') || '',
    category: searchParams.get('category') ? Number(searchParams.get('category')) : undefined,
    brand: searchParams.get('brand') ? Number(searchParams.get('brand')) : undefined,
    min_price: searchParams.get('min_price') ? Number(searchParams.get('min_price')) : undefined,
    max_price: searchParams.get('max_price') ? Number(searchParams.get('max_price')) : undefined,
    is_featured: searchParams.get('featured') === 'true',
    page: searchParams.get('page') ? Number(searchParams.get('page')) : 1,
    page_size: 20,
    ordering: searchParams.get('ordering') || '-created_at'
  }

  // React Query로 데이터 조회
  const { data: productsData, isLoading: productsLoading, error: productsError } = useQuery({
    queryKey: ['products', filters],
    queryFn: () => productService.getProducts(filters),
    staleTime: 3 * 60 * 1000, // 3분
  })

  const { data: categories, isLoading: categoriesLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoryService.getCategories(),
    staleTime: 10 * 60 * 1000, // 10분
  })

  const { data: brands, isLoading: brandsLoading } = useQuery({
    queryKey: ['brands'],
    queryFn: () => brandService.getBrands(),
    staleTime: 10 * 60 * 1000, // 10분
  })

  // 필터 업데이트 함수
  const updateFilters = (newFilters: Partial<ProductFilters>) => {
    const updatedParams = new URLSearchParams(searchParams)
    
    Object.entries(newFilters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        updatedParams.set(key, value.toString())
      } else {
        updatedParams.delete(key)
      }
    })
    
    // 페이지는 1로 리셋
    updatedParams.set('page', '1')
    
    setSearchParams(updatedParams)
  }

  // 로딩 상태
  if (productsLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-300 rounded mb-6"></div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="bg-white rounded-lg p-4">
                  <div className="aspect-square bg-gray-300 rounded mb-4"></div>
                  <div className="space-y-2">
                    <div className="h-4 bg-gray-300 rounded"></div>
                    <div className="h-4 bg-gray-300 rounded w-3/4"></div>
                    <div className="h-6 bg-gray-300 rounded w-1/2"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // 에러 상태
  if (productsError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">오류가 발생했습니다</h2>
          <p className="text-gray-600 mb-6">상품을 불러오는 중 문제가 발생했습니다.</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
          >
            다시 시도
          </button>
        </div>
      </div>
    )
  }

  const products = productsData?.results || []
  const totalCount = productsData?.count || 0

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 페이지 헤더 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">상품 목록</h1>
          <p className="text-gray-600">총 {totalCount.toLocaleString()}개의 상품</p>
        </div>

        <div className="flex gap-8">
          {/* 필터 사이드바 */}
          <aside className="w-64 flex-shrink-0">
            <div className="bg-white rounded-lg shadow-sm p-6 sticky top-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">필터</h3>
              
              {/* 카테고리 필터 */}
              {!categoriesLoading && categories && (
                <div className="mb-6">
                  <h4 className="text-sm font-medium text-gray-900 mb-3">카테고리</h4>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="category"
                        checked={!filters.category}
                        onChange={() => updateFilters({ category: undefined })}
                        className="mr-2"
                      />
                      전체
                    </label>
                    {categories.map((category) => (
                      <label key={category.id} className="flex items-center">
                        <input
                          type="radio"
                          name="category"
                          checked={filters.category === category.id}
                          onChange={() => updateFilters({ category: category.id })}
                          className="mr-2"
                        />
                        {category.name}
                        {category.product_count && (
                          <span className="ml-1 text-xs text-gray-500">
                            ({category.product_count})
                          </span>
                        )}
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* 브랜드 필터 */}
              {!brandsLoading && brands && (
                <div className="mb-6">
                  <h4 className="text-sm font-medium text-gray-900 mb-3">브랜드</h4>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="brand"
                        checked={!filters.brand}
                        onChange={() => updateFilters({ brand: undefined })}
                        className="mr-2"
                      />
                      전체
                    </label>
                    {brands.map((brand) => (
                      <label key={brand.id} className="flex items-center">
                        <input
                          type="radio"
                          name="brand"
                          checked={filters.brand === brand.id}
                          onChange={() => updateFilters({ brand: brand.id })}
                          className="mr-2"
                        />
                        {brand.name}
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* 가격 필터 */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-900 mb-3">가격대</h4>
                <div className="space-y-3">
                  <div>
                    <input
                      type="number"
                      placeholder="최소 가격"
                      value={filters.min_price || ''}
                      onChange={(e) => updateFilters({ min_price: e.target.value ? Number(e.target.value) : undefined })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    />
                  </div>
                  <div>
                    <input
                      type="number"
                      placeholder="최대 가격"
                      value={filters.max_price || ''}
                      onChange={(e) => updateFilters({ max_price: e.target.value ? Number(e.target.value) : undefined })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    />
                  </div>
                </div>
              </div>

              {/* 기타 옵션 */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">기타 옵션</h4>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={filters.is_featured || false}
                      onChange={(e) => updateFilters({ is_featured: e.target.checked || undefined })}
                      className="mr-2"
                    />
                    인기 상품만
                  </label>
                </div>
              </div>
            </div>
          </aside>

          {/* 상품 목록 */}
          <main className="flex-1">
            {/* 정렬 옵션 */}
            <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">
                  {totalCount.toLocaleString()}개 상품 중 {products.length}개 표시
                </span>
                <select
                  value={filters.ordering || '-created_at'}
                  onChange={(e) => updateFilters({ ordering: e.target.value })}
                  className="text-sm border border-gray-300 rounded-md px-3 py-2"
                >
                  <option value="-created_at">최신순</option>
                  <option value="name">이름순</option>
                  <option value="selling_price">낮은 가격순</option>
                  <option value="-selling_price">높은 가격순</option>
                </select>
              </div>
            </div>

            {/* 상품 그리드 */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {products.map((product) => (
                <div key={product.id} className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-300">
                  <Link to={`/products/${product.id}`}>
                    <div className="aspect-square bg-gray-100 rounded-t-lg overflow-hidden">
                      <img
                        src={product.primary_image?.image || '/placeholder-product.jpg'}
                        alt={product.name}
                        className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = '/placeholder-product.jpg'
                        }}
                      />
                    </div>
                  </Link>
                  
                  <div className="p-4">
                    <Link to={`/products/${product.id}`}>
                      <h3 className="font-medium text-gray-900 hover:text-blue-600 transition-colors duration-200 line-clamp-2 mb-2">
                        {product.name}
                      </h3>
                    </Link>
                    
                    {product.brand && (
                      <p className="text-sm text-gray-500 mb-2">{product.brand.name}</p>
                    )}
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg font-bold text-gray-900">
                          ₩{product.selling_price.toLocaleString()}
                        </span>
                        {product.discount_price && (
                          <span className="text-sm text-gray-500 line-through">
                            ₩{product.discount_price.toLocaleString()}
                          </span>
                        )}
                      </div>
                      
                      <button
                        onClick={() => {
                          // 위시리스트 토글 로직
                          const newWishlist = new Set(wishlist)
                          if (wishlist.has(product.id)) {
                            newWishlist.delete(product.id)
                          } else {
                            newWishlist.add(product.id)
                          }
                          setWishlist(newWishlist)
                        }}
                        className="p-2 text-gray-400 hover:text-red-500 transition-colors duration-200"
                      >
                        {wishlist.has(product.id) ? (
                          <HeartSolidIcon className="w-5 h-5 text-red-500" />
                        ) : (
                          <HeartIcon className="w-5 h-5" />
                        )}
                      </button>
                    </div>
                    
                    {/* 재고 상태 */}
                    {product.is_low_stock && (
                      <p className="text-xs text-orange-600 mt-2">재고 부족</p>
                    )}
                    {product.stock_quantity === 0 && (
                      <p className="text-xs text-red-600 mt-2">품절</p>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* 페이지네이션 */}
            {productsData && (
              <div className="mt-8 flex justify-center">
                <nav className="flex items-center space-x-2">
                  {productsData.previous && (
                    <button
                      onClick={() => updateFilters({ page: (filters.page || 1) - 1 })}
                      className="px-3 py-2 text-sm text-gray-500 hover:text-gray-700"
                    >
                      이전
                    </button>
                  )}
                  
                  <span className="px-3 py-2 text-sm text-gray-900">
                    {filters.page || 1} 페이지
                  </span>
                  
                  {productsData.next && (
                    <button
                      onClick={() => updateFilters({ page: (filters.page || 1) + 1 })}
                      className="px-3 py-2 text-sm text-gray-500 hover:text-gray-700"
                    >
                      다음
                    </button>
                  )}
                </nav>
              </div>
            )}

            {/* 상품이 없을 때 */}
            {products.length === 0 && (
              <div className="text-center py-16">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  검색 결과가 없습니다
                </h3>
                <p className="text-gray-600 mb-6">
                  다른 검색어나 필터를 시도해보세요.
                </p>
                <button
                  onClick={() => {
                    setSearchParams(new URLSearchParams())
                  }}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
                >
                  전체 상품 보기
                </button>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  )
}

export default Products