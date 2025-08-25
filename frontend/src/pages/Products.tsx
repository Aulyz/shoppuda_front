import React, { useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { 
  MagnifyingGlassIcon, 
  AdjustmentsHorizontalIcon,
  Squares2X2Icon,
  ListBulletIcon 
} from '@heroicons/react/24/outline'
import { useProducts } from '../hooks/useApi'
import { ProductFilters, Product } from '../types/api'
import { apiUtils } from '../api/services'

interface ProductCardProps {
  product: Product
  viewMode: 'grid' | 'list'
}

const ProductCard: React.FC<ProductCardProps> = ({ product, viewMode }) => {
  const discountPercentage = product.discount_price 
    ? apiUtils.calculateDiscountPercentage(product.selling_price, product.discount_price)
    : 0

  if (viewMode === 'list') {
    return (
      <Link 
        to={`/products/${product.id}`}
        className="flex bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-lg transition-all duration-200 overflow-hidden border border-gray-200 dark:border-gray-700 p-4"
      >
        <div className="w-32 h-32 flex-shrink-0 overflow-hidden bg-gray-100 dark:bg-gray-700 rounded-lg">
          {product.images && product.images.length > 0 ? (
            <img
              src={apiUtils.getImageUrl(product.images[0].image)}
              alt={product.images[0].alt_text || product.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-400">
              <span className="text-sm">이미지 없음</span>
            </div>
          )}
        </div>
        
        <div className="flex-1 ml-4">
          <h3 className="font-medium text-gray-900 dark:text-white mb-2 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
            {product.name}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
            {product.description || '상품 설명이 없습니다.'}
          </p>
          
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              {product.discount_price ? (
                <div className="flex items-center space-x-2">
                  <span className="text-xl font-bold text-blue-600 dark:text-blue-400">
                    {apiUtils.formatPrice(product.discount_price)}
                  </span>
                  <span className="text-sm text-red-500 bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded">
                    {discountPercentage}%
                  </span>
                </div>
              ) : (
                <span className="text-xl font-bold text-gray-900 dark:text-white">
                  {apiUtils.formatPrice(product.selling_price)}
                </span>
              )}
              
              {product.discount_price && (
                <div className="text-sm text-gray-500 dark:text-gray-400 line-through">
                  {apiUtils.formatPrice(product.selling_price)}
                </div>
              )}
            </div>
            
            <div className="text-right">
              {product.stock_quantity > 0 ? (
                <div className="text-sm text-green-600 dark:text-green-400">
                  재고 {product.stock_quantity}개
                </div>
              ) : (
                <div className="text-sm text-red-600 dark:text-red-400">품절</div>
              )}
            </div>
          </div>
        </div>
      </Link>
    )
  }

  // 그리드 뷰
  return (
    <Link 
      to={`/products/${product.id}`}
      className="group block bg-white dark:bg-gray-800 rounded-xl shadow-sm hover:shadow-lg transition-all duration-200 overflow-hidden border border-gray-200 dark:border-gray-700"
    >
      <div className="aspect-square overflow-hidden bg-gray-100 dark:bg-gray-700">
        {product.images && product.images.length > 0 ? (
          <img
            src={apiUtils.getImageUrl(product.images[0].image)}
            alt={product.images[0].alt_text || product.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <span>이미지 없음</span>
          </div>
        )}
      </div>
      
      <div className="p-4">
        <h3 className="font-medium text-gray-900 dark:text-white mb-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors line-clamp-2">
          {product.name}
        </h3>
        
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            {product.discount_price ? (
              <div className="flex items-center space-x-2">
                <span className="text-lg font-bold text-blue-600 dark:text-blue-400">
                  {apiUtils.formatPrice(product.discount_price)}
                </span>
                <span className="text-sm text-red-500 bg-red-50 dark:bg-red-900/20 px-1.5 py-0.5 rounded">
                  {discountPercentage}%
                </span>
              </div>
            ) : (
              <span className="text-lg font-bold text-gray-900 dark:text-white">
                {apiUtils.formatPrice(product.selling_price)}
              </span>
            )}
            
            {product.discount_price && (
              <div className="text-sm text-gray-500 dark:text-gray-400 line-through">
                {apiUtils.formatPrice(product.selling_price)}
              </div>
            )}
          </div>
        </div>
        
        {product.stock_quantity <= 10 && product.stock_quantity > 0 && (
          <div className="mt-2 text-sm text-orange-600 dark:text-orange-400">
            재고 {product.stock_quantity}개 남음
          </div>
        )}
        
        {product.stock_quantity === 0 && (
          <div className="mt-2 text-sm text-red-600 dark:text-red-400">
            품절
          </div>
        )}
      </div>
    </Link>
  )
}

const Products: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [showFilters, setShowFilters] = useState(false)
  
  // URL에서 필터 정보 가져오기
  const filters: ProductFilters = {
    search: searchParams.get('search') || undefined,
    category: searchParams.get('category') ? parseInt(searchParams.get('category')!) : undefined,
    brand: searchParams.get('brand') ? parseInt(searchParams.get('brand')!) : undefined,
    min_price: searchParams.get('min_price') ? parseInt(searchParams.get('min_price')!) : undefined,
    max_price: searchParams.get('max_price') ? parseInt(searchParams.get('max_price')!) : undefined,
    ordering: searchParams.get('ordering') || '-created_at',
    page: parseInt(searchParams.get('page') || '1'),
    page_size: 12
  }

  // API 호출
  const { data, isLoading, error, isFetching } = useProducts(filters)

  const handleFilterChange = (key: string, value: string | null) => {
    const newParams = new URLSearchParams(searchParams)
    if (value) {
      newParams.set(key, value)
    } else {
      newParams.delete(key)
    }
    newParams.delete('page') // 필터 변경 시 페이지 초기화
    setSearchParams(newParams)
  }

  const handlePageChange = (page: number) => {
    const newParams = new URLSearchParams(searchParams)
    newParams.set('page', page.toString())
    setSearchParams(newParams)
  }

  const handleSearch = (searchTerm: string) => {
    handleFilterChange('search', searchTerm || null)
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* 헤더 */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4 sm:mb-0">
            상품 목록
          </h1>
          
          <div className="flex items-center space-x-4">
            {/* 검색 */}
            <div className="relative">
              <input
                type="text"
                placeholder="상품 검색..."
                defaultValue={filters.search || ''}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSearch((e.target as HTMLInputElement).value)
                  }
                }}
                className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <MagnifyingGlassIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
            </div>
            
            {/* 뷰 모드 토글 */}
            <div className="flex items-center bg-white dark:bg-gray-800 rounded-lg border border-gray-300 dark:border-gray-600">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded-l-lg ${
                  viewMode === 'grid' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                <Squares2X2Icon className="h-5 w-5" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-r-lg ${
                  viewMode === 'list' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                <ListBulletIcon className="h-5 w-5" />
              </button>
            </div>
            
            {/* 필터 토글 */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <AdjustmentsHorizontalIcon className="h-5 w-5 mr-2" />
              필터
            </button>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* 사이드바 필터 */}
          {showFilters && (
            <div className="w-full lg:w-64 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              
              {/* 정렬 */}
              <div className="mb-6">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-3">정렬</h3>
                <select
                  value={filters.ordering || '-created_at'}
                  onChange={(e) => handleFilterChange('ordering', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="-created_at">최신순</option>
                  <option value="selling_price">가격 낮은순</option>
                  <option value="-selling_price">가격 높은순</option>
                  <option value="name">이름순</option>
                </select>
              </div>

              {/* 가격 범위 */}
              <div className="mb-6">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-3">가격 범위</h3>
                <div className="space-y-2">
                  <input
                    type="number"
                    placeholder="최소 가격"
                    defaultValue={filters.min_price || ''}
                    onChange={(e) => handleFilterChange('min_price', e.target.value || null)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <input
                    type="number"
                    placeholder="최대 가격"
                    defaultValue={filters.max_price || ''}
                    onChange={(e) => handleFilterChange('max_price', e.target.value || null)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* 필터 초기화 */}
              <button
                onClick={() => setSearchParams(new URLSearchParams())}
                className="w-full px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                필터 초기화
              </button>
            </div>
          )}

          {/* 상품 목록 */}
          <div className="flex-1">
            
            {/* 결과 정보 */}
            <div className="flex items-center justify-between mb-6">
              <div className="text-gray-600 dark:text-gray-400">
                {data ? (
                  <>전체 <span className="font-semibold">{data.count}</span>개 상품</>
                ) : (
                  '상품을 불러오는 중...'
                )}
              </div>
              
              {isFetching && (
                <div className="text-sm text-blue-600 dark:text-blue-400">
                  업데이트 중...
                </div>
              )}
            </div>

            {/* 로딩 상태 */}
            {isLoading ? (
              <div className={
                viewMode === 'grid' 
                  ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
                  : "space-y-4"
              }>
                {[...Array(8)].map((_, i) => (
                  <div key={i} className="animate-pulse">
                    {viewMode === 'grid' ? (
                      <>
                        <div className="aspect-square bg-gray-200 dark:bg-gray-700 rounded-lg mb-4"></div>
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
                        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
                      </>
                    ) : (
                      <div className="flex p-4 bg-white dark:bg-gray-800 rounded-lg">
                        <div className="w-32 h-32 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
                        <div className="flex-1 ml-4 space-y-2">
                          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <div className="text-red-500 mb-2">상품을 불러오는 중 오류가 발생했습니다</div>
                <p className="text-gray-600 dark:text-gray-400">잠시 후 다시 시도해주세요</p>
              </div>
            ) : !data?.results || data.results.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-gray-500 dark:text-gray-400 mb-2">검색된 상품이 없습니다</div>
                <p className="text-gray-600 dark:text-gray-400">다른 검색어나 필터를 사용해보세요</p>
              </div>
            ) : (
              <>
                {/* 상품 그리드/리스트 */}
                <div className={
                  viewMode === 'grid' 
                    ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8"
                    : "space-y-4 mb-8"
                }>
                  {data.results.map((product) => (
                    <ProductCard 
                      key={product.id} 
                      product={product} 
                      viewMode={viewMode}
                    />
                  ))}
                </div>

                {/* 페이지네이션 */}
                {data.count > filters.page_size! && (
                  <div className="flex justify-center">
                    <nav className="flex items-center space-x-2">
                      {/* 이전 페이지 */}
                      <button
                        onClick={() => handlePageChange(filters.page! - 1)}
                        disabled={!data.previous}
                        className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-gray-800 dark:border-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-white"
                      >
                        이전
                      </button>

                      {/* 다음 페이지 */}
                      <button
                        onClick={() => handlePageChange(filters.page! + 1)}
                        disabled={!data.next}
                        className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-gray-800 dark:border-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-white"
                      >
                        다음
                      </button>
                    </nav>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Products