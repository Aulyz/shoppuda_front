import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import {
  HeartIcon,
  ShoppingCartIcon,
  MinusIcon,
  PlusIcon,
  ShareIcon,
  TruckIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline'
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid'
import { useProduct, useAddToCart, useToggleWishlist } from '../hooks/useApi'
import { apiUtils } from '../api/services'
import toast from 'react-hot-toast'

const ProductDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [currentImageIndex, setCurrentImageIndex] = useState(0)
  const [quantity, setQuantity] = useState(1)
  const [isWished, setIsWished] = useState(false)
  const [selectedTab, setSelectedTab] = useState<'description' | 'reviews' | 'shipping'>('description')

  // API 훅들
  const { data: product, isLoading, error } = useProduct(id!)
  const addToCartMutation = useAddToCart()
  const toggleWishlistMutation = useToggleWishlist()

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
    ? apiUtils.calculateDiscountPercentage(product.selling_price, product.discount_price)
    : 0

  const handleQuantityChange = (newQuantity: number) => {
    if (newQuantity >= 1 && newQuantity <= product.stock_quantity) {
      setQuantity(newQuantity)
    }
  }

  const handleAddToCart = () => {
    addToCartMutation.mutate({ 
      productId: product.id, 
      quantity 
    })
  }

  const handleToggleWishlist = () => {
    toggleWishlistMutation.mutate(product.id)
    setIsWished(!isWished)
  }

  const handleBuyNow = () => {
    // 장바구니에 추가 후 주문 페이지로 이동
    addToCartMutation.mutate({ 
      productId: product.id, 
      quantity 
    }, {
      onSuccess: () => {
        navigate('/cart')
      }
    })
  }

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: product.name,
          text: `${product.name} - Shopuda에서 확인하세요!`,
          url: window.location.href,
        })
      } catch (err) {
        console.log('공유 실패:', err)
      }
    } else {
      // Web Share API를 지원하지 않는 브라우저
      navigator.clipboard.writeText(window.location.href)
      toast.success('링크가 복사되었습니다!')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* 브레드크럼 */}
        <nav className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400 mb-8">
          <Link to="/" className="hover:text-gray-900 dark:hover:text-white">홈</Link>
          <span>/</span>
          <Link to="/products" className="hover:text-gray-900 dark:hover:text-white">상품</Link>
          <span>/</span>
          <span className="text-gray-900 dark:text-white">{product.name}</span>
        </nav>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-16">
          
          {/* 상품 이미지 */}
          <div className="space-y-4">
            <div className="aspect-square overflow-hidden bg-gray-100 dark:bg-gray-700 rounded-xl">
              {images.length > 0 ? (
                <img
                  src={apiUtils.getImageUrl(images[currentImageIndex].image)}
                  alt={product.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400">
                  <span>이미지 없음</span>
                </div>
              )}
            </div>
            
            {/* 썸네일 이미지들 */}
            {images.length > 1 && (
              <div className="flex space-x-2 overflow-x-auto pb-2">
                {images.map((image, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentImageIndex(index)}
                    className={`flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 ${
                      currentImageIndex === index 
                        ? 'border-blue-600 dark:border-blue-400' 
                        : 'border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    <img
                      src={apiUtils.getImageUrl(image.image)}
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
            
            {/* 상품명 및 가격 */}
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
                {product.name}
              </h1>
              
              <div className="flex items-center space-x-4 mb-4">
                {product.discount_price ? (
                  <>
                    <span className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                      {apiUtils.formatPrice(product.discount_price)}
                    </span>
                    <span className="text-xl text-gray-500 dark:text-gray-400 line-through">
                      {apiUtils.formatPrice(product.selling_price)}
                    </span>
                    <span className="text-lg text-red-500 bg-red-50 dark:bg-red-900/20 px-3 py-1 rounded-full">
                      {discountPercentage}% 할인
                    </span>
                  </>
                ) : (
                  <span className="text-3xl font-bold text-gray-900 dark:text-white">
                    {apiUtils.formatPrice(product.selling_price)}
                  </span>
                )}
              </div>
              
              <div className="text-gray-600 dark:text-gray-400">
                {product.stock_quantity > 0 ? (
                  <span className="text-green-600 dark:text-green-400">
                    재고 {product.stock_quantity}개 남음
                  </span>
                ) : (
                  <span className="text-red-600 dark:text-red-400">품절</span>
                )}
              </div>
            </div>

            {/* 상품 설명 */}
            {product.description && (
              <div>
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                  {product.description}
                </p>
              </div>
            )}

            {/* 수량 선택 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                수량
              </label>
              <div className="flex items-center space-x-4">
                <div className="flex items-center border border-gray-300 dark:border-gray-600 rounded-lg">
                  <button
                    onClick={() => handleQuantityChange(quantity - 1)}
                    disabled={quantity <= 1}
                    className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <MinusIcon className="h-5 w-5" />
                  </button>
                  <span className="px-4 py-2 text-lg font-medium text-gray-900 dark:text-white">
                    {quantity}
                  </span>
                  <button
                    onClick={() => handleQuantityChange(quantity + 1)}
                    disabled={quantity >= product.stock_quantity}
                    className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <PlusIcon className="h-5 w-5" />
                  </button>
                </div>
                
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  총 {apiUtils.formatPrice((product.discount_price || product.selling_price) * quantity)}
                </div>
              </div>
            </div>

            {/* 액션 버튼들 */}
            <div className="space-y-4">
              <div className="flex space-x-4">
                <button
                  onClick={handleAddToCart}
                  disabled={product.stock_quantity === 0 || addToCartMutation.isPending}
                  className="flex-1 flex items-center justify-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ShoppingCartIcon className="h-5 w-5 mr-2" />
                  {addToCartMutation.isPending ? '추가 중...' : '장바구니 담기'}
                </button>
                
                <button
                  onClick={handleBuyNow}
                  disabled={product.stock_quantity === 0 || addToCartMutation.isPending}
                  className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  바로 구매
                </button>
              </div>
              
              <div className="flex space-x-4">
                <button
                  onClick={handleToggleWishlist}
                  disabled={toggleWishlistMutation.isPending}
                  className="flex-1 flex items-center justify-center px-6 py-3 border-2 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:border-red-500 hover:text-red-500 transition-colors"
                >
                  {isWished ? (
                    <HeartSolidIcon className="h-5 w-5 mr-2 text-red-500" />
                  ) : (
                    <HeartIcon className="h-5 w-5 mr-2" />
                  )}
                  {toggleWishlistMutation.isPending ? '처리 중...' : '찜하기'}
                </button>
                
                <button
                  onClick={handleShare}
                  className="px-6 py-3 border-2 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:border-blue-500 hover:text-blue-500 transition-colors"
                >
                  <ShareIcon className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* 배송 정보 */}
            <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 space-y-3">
              <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                <TruckIcon className="h-5 w-5 mr-2 text-blue-600 dark:text-blue-400" />
                무료배송 (5만원 이상 구매 시)
              </div>
              <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                <ShieldCheckIcon className="h-5 w-5 mr-2 text-green-600 dark:text-green-400" />
                100% 정품 보장
              </div>
            </div>
          </div>
        </div>

        {/* 상품 상세 정보 탭 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
          
          {/* 탭 헤더 */}
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="flex space-x-8">
              <button
                onClick={() => setSelectedTab('description')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === 'description'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                상품 상세
              </button>
              <button
                onClick={() => setSelectedTab('reviews')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === 'reviews'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                리뷰 (0)
              </button>
              <button
                onClick={() => setSelectedTab('shipping')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === 'shipping'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                배송/교환/반품
              </button>
            </nav>
          </div>

          {/* 탭 콘텐츠 */}
          <div className="p-8">
            {selectedTab === 'description' && (
              <div className="prose dark:prose-invert max-w-none">
                <h3 className="text-xl font-semibold mb-4">상품 상세 정보</h3>
                <div className="space-y-4">
                  {product.description ? (
                    <p className="text-gray-600 dark:text-gray-400 leading-relaxed whitespace-pre-line">
                      {product.description}
                    </p>
                  ) : (
                    <p className="text-gray-500 dark:text-gray-500 italic">
                      상세 정보가 제공되지 않았습니다.
                    </p>
                  )}
                  
                  {/* 상품 스펙 */}
                  <div className="mt-8">
                    <h4 className="text-lg font-medium mb-4">상품 정보</h4>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">상품코드</dt>
                          <dd className="text-sm text-gray-900 dark:text-white">{product.sku || product.id}</dd>
                        </div>
                        <div>
                          <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">브랜드</dt>
                          <dd className="text-sm text-gray-900 dark:text-white">{product.brand?.name || '-'}</dd>
                        </div>
                        <div>
                          <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">카테고리</dt>
                          <dd className="text-sm text-gray-900 dark:text-white">{product.category?.name || '-'}</dd>
                        </div>
                        <div>
                          <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">재고 수량</dt>
                          <dd className="text-sm text-gray-900 dark:text-white">{product.stock_quantity}개</dd>
                        </div>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {selectedTab === 'reviews' && (
              <div className="text-center py-12">
                <div className="text-gray-500 dark:text-gray-400 mb-4">
                  아직 리뷰가 없습니다
                </div>
                <p className="text-gray-400 dark:text-gray-500">
                  첫 번째 리뷰를 작성해보세요!
                </p>
              </div>
            )}
            
            {selectedTab === 'shipping' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold mb-3">배송 정보</h3>
                  <ul className="space-y-2 text-gray-600 dark:text-gray-400">
                    <li>• 5만원 이상 구매 시 무료배송</li>
                    <li>• 평일 오후 3시 이전 주문 시 당일 발송</li>
                    <li>• 주말/공휴일 제외 1-3일 소요</li>
                    <li>• 도서/산간지역 추가 배송료 발생</li>
                  </ul>
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold mb-3">교환/반품 안내</h3>
                  <ul className="space-y-2 text-gray-600 dark:text-gray-400">
                    <li>• 상품 수령 후 7일 이내 교환/반품 가능</li>
                    <li>• 단순 변심으로 인한 반품 시 배송비 고객 부담</li>
                    <li>• 상품 하자/오배송 시 무료 교환/반품</li>
                    <li>• 사용 또는 훼손된 상품은 교환/반품 불가</li>
                  </ul>
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold mb-3">A/S 안내</h3>
                  <ul className="space-y-2 text-gray-600 dark:text-gray-400">
                    <li>• 제조사 보증기간에 따른 A/S 제공</li>
                    <li>• A/S 접수: 고객센터 1588-0000</li>
                    <li>• 평일 09:00 - 18:00 (점심시간 12:00-13:00 제외)</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProductDetail