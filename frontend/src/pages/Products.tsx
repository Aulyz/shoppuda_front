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
import { productService, categoryService, brandService } from '../api/services'
import { Product, ProductFilters, Category, Brand } from '../api/types'

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
    featured: searchParams.get('featured') === 'true',
    new: searchParams.get('new') === 'true',
    page: searchParams.get('page') ? Number(searchParams.get('page')) : 1,
    ordering: searchParams.get('sort') || '-created_at'
  }

  // TanStack Query로 데이터 fetch
  const { data: productsData, isLoading: productsLoading, error: productsError } = useQuery({
    queryKey: ['products', filters],
    queryFn: () => productService.getProducts(filters),
    staleTime: 5 * 60 * 1000, // 5분
  })

  const { data: categories, isLoading: categoriesLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: categoryService.getCategories,
    staleTime: 30 * 60 * 1000, // 30분
  })

  const { data: brands, isLoading: brandsLoading } = useQuery({
    queryKey: ['brands'],
    queryFn: brandService.getBrands,
    staleTime: 30 * 60 * 1000, // 30분
  })

  // 필터 업데이트 함수
  const updateFilters = (newFilters: Partial<ProductFilters>) => {
    const newParams = new URLSearchParams(searchParams)
    
    Object.entries(newFilters).forEach(([filterKey, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        newParams.set(filterKey, value.toString())
      } else {
        newParams.delete(filterKey)
      }
    })
    
    // 페이지 리셋 (검색이나 필터 변경 시)
    const changedKeys = Object.keys(newFilters)
    if (!changedKeys.includes('page')) {
      newParams.delete('page')
    }
    
    setSearchParams(newParams)
  }

  // 검색 처리
  const handleSearch = (query: string) => {
    updateFilters({ search: query })
  }

  // 정렬 처리
  const handleSort = (ordering: string) => {
    updateFilters({ ordering })
  }

  // 페이지네이션
  const handlePageChange = (page: number) => {
    updateFilters({ page })
  }

  // 위시리스트 토글
  const toggleWishlist = (productId: string) => {
    setWishlist(prev => {
      const newWishlist = new Set(prev)
      if (newWishlist.has(productId)) {
        newWishlist.delete(productId)
      } else {
        newWishlist.add(productId)
      }
      return newWishlist
    })
  }

  // 필터 초기화
  const clearFilters = () => {
    setSearchParams(new URLSearchParams())
  }

  // 로딩 상태
  if (productsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  // 에러 상태
  if (productsError) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            상품을 불러올 수 없습니다
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            잠시 후 다시 시도해주세요.
          </p>
          <button 
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            새로고침
          </button>
        </div>
      </div>
    )
  }

  const products = productsData?.results || []
  const totalCount = productsData?.count || 0
  const hasNextPage = !!productsData?.next
  const hasPrevPage = !!productsData?.previous

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* 헤더 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">상품</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            총 {totalCount.toLocaleString()}개의 상품
          </p>
        </div>
        
        {/* 검색 */}
        <div className="mt-4 sm:mt-0 flex items-center space-x-4">
          <div className="relative">
            <input
              type="text"
              placeholder="상품 검색..."
              value={filters.search}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-64 pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          </div>
          
          {/* 필터 토글 */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="p-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <AdjustmentsHorizontalIcon className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* 사이드바 필터 */}
        <div className={`lg:w-64 space-y-6 ${showFilters ? 'block' : 'hidden lg:block'}`}>
          {/* 카테고리 필터 */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">카테고리</h3>
            {categoriesLoading ? (
              <div className="animate-pulse space-y-2">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                ))}
              </div>
            ) : (
              <div className="space-y-2">
                <button
                  onClick={() => updateFilters({ category: undefined })}
                  className={`block w-full text-left px-3 py-2 rounded-md text-sm ${
                    !filters.category
                      ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  전체 카테고리
                </button>
                {categories?.map((category) => (
                  <button
                    key={category.id}
                    onClick={() => updateFilters({ category: category.id })}
                    className={`block w-full text-left px-3 py-2 rounded-md text-sm ${
                      filters.category === category.id
                        ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    {category.name}
                    {category.product_count && (
                      <span className="ml-2 text-xs text-gray-500">({category.product_count})</span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* 브랜드 필터 */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">브랜드</h3>
            {brandsLoading ? (
              <div className="animate-pulse space-y-2">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                ))}
              </div>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                <button
                  onClick={() => updateFilters({ brand: undefined })}
                  className={`block w-full text-left px-3 py-2 rounded-md text-sm ${
                    !filters.brand
                      ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  전체 브랜드
                </button>
                {brands?.map((brand) => (
                  <button
                    key={brand.id}
                    onClick={() => updateFilters({ brand: brand.id })}
                    className={`block w-full text-left px-3 py-2 rounded-md text-sm ${
                      filters.brand === brand.id
                        ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    {brand.name}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* 가격 필터 */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">가격</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">최소 가격</label>
                <input
                  type="number"
                  value={filters.min_price || ''}
                  onChange={(e) => updateFilters({ min_price: e.target.value ? Number(e.target.value) : undefined })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 dark:text-gray-300 mb-1">최대 가격</label>
                <input
                  type="number"
                  value={filters.max_price || ''}
                  onChange={(e) => updateFilters({ max_price: e.target.value ? Number(e.target.value) : undefined })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                  placeholder="무제한"
                />
              </div>
            </div>
          </div>

          {/* 필터 초기화 */}
          <button
            onClick={clearFilters}
            className="w-full px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
          >
            필터 초기화
          </button>
        </div>

        {/* 메인 콘텐츠 */}
        <div className="flex-1">
          {/* 정렬 및 뷰 옵션 */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600 dark:text-gray-400">정렬:</span>
              <select
                value={filters.ordering}
                onChange={(e) => handleSort(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
              >
                <option value="-created_at">최신순</option>
                <option value="selling_price">가격 낮은순</option>
                <option value="-selling_price">가격 높은순</option>
                <option value="name">이름순</option>
                <option value="-rating">평점순</option>
              </select>
            </div>

            <div className="text-sm text-gray-600 dark:text-gray-400">
              {products.length}개 상품 표시 중
            </div>
          </div>

          {/* 상품 그리드 */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {products.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onToggleWishlist={toggleWishlist}
                isWished={wishlist.has(product.id)}
              />
            ))}
          </div>

          {/* 상품이 없을 때 */}
          {products.length === 0 && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                검색 결과가 없습니다
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                다른 검색어나 필터로 시도해보세요.
              </p>
              <button
                onClick={clearFilters}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                전체 상품 보기
              </button>
            </div>
          )}

          {/* 페이지네이션 */}
          {totalCount > 20 && (
            <div className="flex items-center justify-center mt-12 space-x-2">
              <button
                onClick={() => handlePageChange((filters.page || 1) - 1)}
                disabled={!hasPrevPage}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                이전
              </button>
              
              <span className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">
                {filters.page || 1} / {Math.ceil(totalCount / 20)}
              </span>
              
              <button
                onClick={() => handlePageChange((filters.page || 1) + 1)}
                disabled={!hasNextPage}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                다음
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// 상품 카드 컴포넌트
interface ProductCardProps {
  product: Product
  onToggleWishlist: (productId: string) => void
  isWished: boolean
}

const ProductCard: React.FC<ProductCardProps> = ({ product, onToggleWishlist, isWished }) => {
  const discountPercentage = product.discount_price 
    ? Math.round(((product.selling_price - product.discount_price) / product.selling_price) * 100)
    : 0

  return (
    <Link to={`/products/${product.id}`} className="group">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden border border-gray-200 dark:border-gray-700">
        <div className="relative overflow-hidden">
          <img 
            src={product.images?.[0]?.image || '/placeholder-product.jpg'} 
            alt={product.name}
            className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300"
          />
          
          {/* 상품 뱃지 */}
          <div className="absolute top-3 left-3 flex flex-col space-y-1">
            {product.is_new && (
              <span className="px-2 py-1 bg-green-500 text-white text-xs font-bold rounded-md">
                NEW
              </span>
            )}
            {discountPercentage > 0 && (
              <span className="px-2 py-1 bg-red-500 text-white text-xs font-bold rounded-md">
                -{discountPercentage}%
              </span>
            )}
            {product.is_featured && (
              <span className="px-2 py-1 bg-orange-500 text-white text-xs font-bold rounded-md">
                추천
              </span>
            )}
          </div>

          {/* 찜하기 버튼 */}
          <button
            onClick={(e) => {
              e.preventDefault()
              onToggleWishlist(product.id)
            }}
            className="absolute top-3 right-3 p-2 bg-white dark:bg-gray-800 rounded-full shadow-md hover:shadow-lg transition-all opacity-0 group-hover:opacity-100"
          >
            {isWished ? (
              <HeartSolidIcon className="w-4 h-4 text-red-500" />
            ) : (
              <HeartIcon className="w-4 h-4 text-gray-400" />
            )}
          </button>

          {/* 장바구니 버튼 */}
          <div className="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={(e) => {
                e.preventDefault()
                // TODO: 장바구니 추가 기능
                console.log('Add to cart:', product.id)
              }}
              className="p-2 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-colors"
            >
              <ShoppingCartIcon className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="p-4">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
            {product.name}
          </h3>
          
          {/* 브랜드 */}
          {product.brand && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
              {product.brand.name}
            </p>
          )}
          
          {/* 가격 */}
          <div className="flex items-center space-x-2 mb-2">
            {product.discount_price ? (
              <>
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  {product.discount_price.toLocaleString()}원
                </span>
                <span className="text-sm text-gray-500 line-through">
                  {product.selling_price.toLocaleString()}원
                </span>
              </>
            ) : (
              <span className="text-lg font-bold text-gray-900 dark:text-white">
                {product.selling_price.toLocaleString()}원
              </span>
            )}
          </div>

          {/* 평점 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1">
              <StarIcon className="w-4 h-4 text-yellow-400 fill-current" />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {product.rating || 0} ({product.review_count || 0})
              </span>
            </div>
            
            {/* 재고 상태 */}
            <div className="text-xs">
              {product.stock_quantity === 0 ? (
                <span className="text-red-500">품절</span>
              ) : product.stock_quantity <= product.min_stock_level ? (
                <span className="text-orange-500">품귀</span>
              ) : (
                <span className="text-green-500">재고있음</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </Link>
  )
}

export default Products