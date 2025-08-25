import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  HeartIcon,
  ShoppingCartIcon,
  StarIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  MinusIcon,
  PlusIcon,
  ShareIcon,
  TruckIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline'
import { HeartIcon as HeartSolidIcon, StarIcon as StarSolidIcon } from '@heroicons/react/24/solid'
import { productService } from '../api/services'
import { Product } from '../types/api'
import toast from 'react-hot-toast'

const ProductDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [currentImageIndex, setCurrentImageIndex] = useState(0)
  const [quantity, setQuantity] = useState(1)
  const [isWished, setIsWished] = useState(false)
  const [selectedTab, setSelectedTab] = useState<'description' | 'reviews' | 'shipping'>('description')

  // 상품 상세 정보 fetch
  const { data: product, isLoading, error } = useQuery({
    queryKey: ['product', id],
    queryFn: () => productService.getProduct(id!),
    enabled: !!id,
    staleTime: 10 * 60 * 1000, // 10분
  })

  // 로딩 상태
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">상품 정보를 불러오는 중...</p>
        </div>
      </div>
    )
  }

  // 에러 상태
  if (error || !product) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">😞</div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            상품을 찾을 수 없습니다
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            요청하신 상품이 존재하지 않거나 삭제되었습니다.
          </p>
          <button
            onClick={() => navigate('/products')}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            상품 목록으로 돌아가기
          </button>
        </div>
      </div>
    )
  }

  const images = product.images || []
  const discountPercentage = product.discount_price 
    ? Math.round(((product.selling_price - product.discount_price) / product.selling_price) * 100)
    : 0

  const handleQuantityChange = (newQuantity: number) => {
    if (newQuantity >= 1 && newQuantity <= product.stock_quantity) {
      setQuantity(newQuantity)
    }
  }

  const handleAddToCart = () => {
    toast.success(`${product.name} ${quantity}개가 장바구니에 추가되었습니다.`)
    // TODO: 실제 장바구니 로직 구현
  }

  const handleBuyNow = () => {
    toast.success('주문 페이지로 이동합니다.')
    // TODO: 주문 페이지로 이동
  }

  const handleToggleWishlist = () => {
    setIsWished(!isWished)
    toast.success(isWished ? '찜목록에서 제거되었습니다.' : '찜목록에 추가되었습니다.')
    // TODO: 실제 찜목록 로직 구현
  }

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: product.name,
        text: product.description,
        url: window.location.href,
      })
    } else {
      navigator.clipboard.writeText(window.location.href)
      toast.success('링크가 클립보드에 복사되었습니다.')
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* 뒤로가기 버튼 */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center space-x-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-6 transition-colors"
      >
        <ChevronLeftIcon className="w-5 h-5" />
        <span>뒤로가기</span>
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
        {/* 이미지 갤러리 */}
        <div className="space-y-4">
          {/* 메인 이미지 */}
          <div className="relative aspect-square bg-gray-100 dark:bg-gray-800 rounded-xl overflow-hidden">
            <img
              src={images[currentImageIndex]?.image || '/placeholder-product.jpg'}
              alt={product.name}
              className="w-full h-full object-cover"
            />
            
            {/* 상품 뱃지 */}
            <div className="absolute top-4 left-4 flex flex-col space-y-2">
              {/* TODO: Add is_new field to ProductDetail type */ false && (
                <span className="px-3 py-1 bg-green-500 text-white text-sm font-bold rounded-md">
                  NEW
                </span>
              )}
              {discountPercentage > 0 && (
                <span className="px-3 py-1 bg-red-500 text-white text-sm font-bold rounded-md">
                  -{discountPercentage}%
                </span>
              )}
              {product.is_featured && (
                <span className="px-3 py-1 bg-orange-500 text-white text-sm font-bold rounded-md">
                  추천
                </span>
              )}
            </div>

            {/* 이미지 네비게이션 */}
            {images.length > 1 && (
              <>
                <button
                  onClick={() => setCurrentImageIndex((prev) => (prev - 1 + images.length) % images.length)}
                  className="absolute left-4 top-1/2 transform -translate-y-1/2 p-2 bg-white bg-opacity-80 rounded-full hover:bg-opacity-100 transition-all"
                >
                  <ChevronLeftIcon className="w-5 h-5 text-gray-900" />
                </button>
                <button
                  onClick={() => setCurrentImageIndex((prev) => (prev + 1) % images.length)}
                  className="absolute right-4 top-1/2 transform -translate-y-1/2 p-2 bg-white bg-opacity-80 rounded-full hover:bg-opacity-100 transition-all"
                >
                  <ChevronRightIcon className="w-5 h-5 text-gray-900" />
                </button>
              </>
            )}
          </div>

          {/* 썸네일 이미지 */}
          {images.length > 1 && (
            <div className="flex space-x-2 overflow-x-auto">
              {images.map((image, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentImageIndex(index)}
                  className={`flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 transition-colors ${
                    index === currentImageIndex
                      ? 'border-blue-500'
                      : 'border-gray-200 dark:border-gray-700'
                  }`}
                >
                  <img
                    src={image.image}
                    alt={`${product.name} ${index + 1}`}
                    className="w-full h-full object-cover"
                  />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 상품 정보 */}
        <div className="space-y-6">
          {/* 기본 정보 */}
          <div>
            {product.brand && (
              <p className="text-blue-600 dark:text-blue-400 font-medium mb-2">
                {product.brand.name}
              </p>
            )}
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              {product.name}
            </h1>
            
            {/* 평점 */}
            <div className="flex items-center space-x-4 mb-6">
              <div className="flex items-center space-x-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <StarSolidIcon
                    key={star}
                    className={`w-5 h-5 ${
                      star <= Math.round(product.average_rating || 0)
                        ? 'text-yellow-400'
                        : 'text-gray-300 dark:text-gray-600'
                    }`}
                  />
                ))}
                <span className="text-gray-600 dark:text-gray-400 ml-2">
                  ({product.review_count || 0}개 리뷰)
                </span>
              </div>
            </div>

            {/* 가격 */}
            <div className="space-y-2 mb-6">
              {product.discount_price ? (
                <>
                  <div className="flex items-center space-x-3">
                    <span className="text-3xl font-bold text-gray-900 dark:text-white">
                      {product.discount_price.toLocaleString()}원
                    </span>
                    <span className="text-xl text-gray-500 line-through">
                      {product.selling_price.toLocaleString()}원
                    </span>
                  </div>
                  <p className="text-red-600 dark:text-red-400 font-medium">
                    {discountPercentage}% 할인 중
                  </p>
                </>
              ) : (
                <span className="text-3xl font-bold text-gray-900 dark:text-white">
                  {product.selling_price.toLocaleString()}원
                </span>
              )}
            </div>
          </div>

          {/* 재고 상태 */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-gray-700 dark:text-gray-300">재고</span>
              <div className="flex items-center space-x-2">
                {product.stock_quantity > 0 ? (
                  <>
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-green-600 dark:text-green-400">
                      {product.stock_quantity}개 남음
                    </span>
                  </>
                ) : (
                  <>
                    <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    <span className="text-red-600 dark:text-red-400">품절</span>
                  </>
                )}
              </div>
            </div>

            {/* 수량 선택 */}
            <div className="flex items-center justify-between mb-6">
              <span className="text-gray-700 dark:text-gray-300">수량</span>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => handleQuantityChange(quantity - 1)}
                  disabled={quantity <= 1}
                  className="p-1 rounded-md border border-gray-300 dark:border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  <MinusIcon className="w-4 h-4" />
                </button>
                <span className="text-lg font-medium min-w-[2rem] text-center">
                  {quantity}
                </span>
                <button
                  onClick={() => handleQuantityChange(quantity + 1)}
                  disabled={quantity >= product.stock_quantity}
                  className="p-1 rounded-md border border-gray-300 dark:border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  <PlusIcon className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* 액션 버튼 */}
          <div className="space-y-4">
            <div className="flex space-x-4">
              <button
                onClick={handleAddToCart}
                disabled={product.stock_quantity === 0}
                className="flex-1 flex items-center justify-center space-x-2 px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ShoppingCartIcon className="w-5 h-5" />
                <span>장바구니 담기</span>
              </button>
              
              <button
                onClick={handleToggleWishlist}
                className={`p-3 rounded-lg border transition-colors ${
                  isWished
                    ? 'border-red-300 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400'
                    : 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                }`}
              >
                {isWished ? (
                  <HeartSolidIcon className="w-5 h-5" />
                ) : (
                  <HeartIcon className="w-5 h-5" />
                )}
              </button>

              <button
                onClick={handleShare}
                className="p-3 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <ShareIcon className="w-5 h-5" />
              </button>
            </div>

            <button
              onClick={handleBuyNow}
              disabled={product.stock_quantity === 0}
              className="w-full px-6 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-lg"
            >
              {product.stock_quantity === 0 ? '품절' : '바로 구매'}
            </button>
          </div>

          {/* 배송 정보 */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-6 space-y-4">
            <div className="flex items-center space-x-3">
              <TruckIcon className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  무료배송
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  30,000원 이상 구매 시
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <ShieldCheckIcon className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  교환/환불 보장
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  구매 후 7일 이내
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 상세 정보 탭 */}
      <div className="mt-16">
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="flex space-x-8">
            {[
              { key: 'description', label: '상품설명' },
              { key: 'reviews', label: '리뷰' },
              { key: 'shipping', label: '배송/교환/환불' },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setSelectedTab(tab.key as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  selectedTab === tab.key
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="py-8">
          {selectedTab === 'description' && (
            <div className="prose dark:prose-invert max-w-none">
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                {product.description}
              </p>
              
              {/* 상품 상세 정보 */}
              <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-semibold mb-4">상품 정보</h3>
                  <dl className="space-y-2">
                    <div className="flex justify-between">
                      <dt className="text-gray-600 dark:text-gray-400">SKU</dt>
                      <dd className="text-gray-900 dark:text-white">{product.sku}</dd>
                    </div>
                    {product.brand && (
                      <div className="flex justify-between">
                        <dt className="text-gray-600 dark:text-gray-400">브랜드</dt>
                        <dd className="text-gray-900 dark:text-white">{product.brand.name}</dd>
                      </div>
                    )}
                    {product.category && (
                      <div className="flex justify-between">
                        <dt className="text-gray-600 dark:text-gray-400">카테고리</dt>
                        <dd className="text-gray-900 dark:text-white">{product.category.name}</dd>
                      </div>
                    )}
                  </dl>
                </div>
              </div>
            </div>
          )}

          {selectedTab === 'reviews' && (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">📝</div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                리뷰 기능 준비 중
              </h3>
              <p className="text-gray-500 dark:text-gray-400">
                곧 고객 리뷰를 확인하실 수 있습니다.
              </p>
            </div>
          )}

          {selectedTab === 'shipping' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">배송 정보</h3>
                <ul className="space-y-2 text-gray-700 dark:text-gray-300">
                  <li>• 무료배송: 30,000원 이상 구매 시</li>
                  <li>• 배송지역: 전국 (제주 및 도서산간 지역 추가비용 발생)</li>
                  <li>• 배송기간: 주문 후 1-3일 (주말 및 공휴일 제외)</li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold mb-4">교환/환불 정책</h3>
                <ul className="space-y-2 text-gray-700 dark:text-gray-300">
                  <li>• 교환/환불 기간: 상품 수령 후 7일 이내</li>
                  <li>• 교환/환불 조건: 상품 태그 미제거, 미사용 상품</li>
                  <li>• 반품 배송비: 고객 부담 (단순 변심 시)</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 관련 상품 (추후 구현) */}
      <div className="mt-16">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          관련 상품
        </h2>
        <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-xl">
          <div className="text-4xl mb-4">🔄</div>
          <p className="text-gray-500 dark:text-gray-400">
            관련 상품 추천 기능을 준비 중입니다.
          </p>
        </div>
      </div>
    </div>
  )
}

export default ProductDetail