import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  ChevronLeftIcon, 
  ChevronRightIcon,
  StarIcon,
  HeartIcon,
  ShoppingCartIcon,
  FireIcon
} from '@heroicons/react/24/outline'
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid'
import { 
  productService, 
  categoryService, 
  bannerService 
} from '../api/services'
import { Product, Category, Banner } from '../api/types'

const Home: React.FC = () => {
  const [currentBanner, setCurrentBanner] = useState(0)
  const [wishlist, setWishlist] = useState<Set<string>>(new Set())

  // API 데이터 fetch
  const { data: banners, isLoading: bannersLoading } = useQuery({
    queryKey: ['banners'],
    queryFn: bannerService.getMainBanners,
    staleTime: 10 * 60 * 1000, // 10분
  })

  const { data: categories, isLoading: categoriesLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: categoryService.getCategories,
    staleTime: 30 * 60 * 1000, // 30분
  })

  const { data: featuredProducts, isLoading: featuredLoading } = useQuery({
    queryKey: ['featuredProducts'],
    queryFn: () => productService.getFeaturedProducts(8),
    staleTime: 15 * 60 * 1000, // 15분
  })

  const { data: newProducts, isLoading: newProductsLoading } = useQuery({
    queryKey: ['newProducts'],
    queryFn: () => productService.getNewProducts(6),
    staleTime: 15 * 60 * 1000, // 15분
  })

  // 배너 자동 슬라이드
  useEffect(() => {
    if (banners && banners.length > 1) {
      const timer = setInterval(() => {
        setCurrentBanner((prev) => (prev + 1) % banners.length)
      }, 5000)
      return () => clearInterval(timer)
    }
  }, [banners])

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

  // 로딩 상태
  if (bannersLoading || categoriesLoading || featuredLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">페이지를 로딩 중입니다...</p>
        </div>
      </div>
    )
  }

  // 상품 카드 컴포넌트
  const ProductCard = ({ product }: { product: Product }) => {
    const discountPercentage = product.discount_price 
      ? Math.round(((product.selling_price - product.discount_price) / product.selling_price) * 100)
      : 0

    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 group overflow-hidden border border-gray-200 dark:border-gray-700">
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
          </div>

          {/* 찜하기 버튼 */}
          <button
            onClick={(e) => {
              e.preventDefault()
              toggleWishlist(product.id)
            }}
            className="absolute top-3 right-3 p-2 bg-white dark:bg-gray-800 rounded-full shadow-md hover:shadow-lg transition-all opacity-0 group-hover:opacity-100"
          >
            {wishlist.has(product.id) ? (
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
            {product.is_featured && (
              <FireIcon className="w-4 h-4 text-orange-500" />
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-12">
      {/* 메인 배너 */}
      {banners && banners.length > 0 && (
        <section className="relative rounded-2xl overflow-hidden">
          <div className="relative h-96 sm:h-[500px]">
            {banners.map((banner, index) => (
              <div
                key={banner.id}
                className={`absolute inset-0 transition-opacity duration-1000 ${
                  index === currentBanner ? 'opacity-100' : 'opacity-0'
                }`}
              >
                <img
                  src={banner.image}
                  alt={banner.title}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-black bg-opacity-40" />
                <div className="absolute bottom-8 left-8 text-white">
                  <h2 className="text-3xl sm:text-4xl font-bold mb-2">{banner.title}</h2>
                  <p className="text-lg mb-4 opacity-90">{banner.subtitle}</p>
                  <Link
                    to={banner.link}
                    className="inline-block px-6 py-3 bg-white text-gray-900 font-semibold rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    {banner.button_text}
                  </Link>
                </div>
              </div>
            ))}
          </div>

          {/* 배너 네비게이션 */}
          {banners.length > 1 && (
            <>
              <div className="absolute bottom-4 right-4 flex space-x-2">
                {banners.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentBanner(index)}
                    className={`w-3 h-3 rounded-full transition-colors ${
                      index === currentBanner ? 'bg-white' : 'bg-white bg-opacity-50'
                    }`}
                  />
                ))}
              </div>

              {/* 배너 화살표 */}
              <button
                onClick={() => setCurrentBanner((prev) => (prev - 1 + banners.length) % banners.length)}
                className="absolute left-4 top-1/2 transform -translate-y-1/2 p-2 bg-white bg-opacity-80 rounded-full hover:bg-opacity-100 transition-all"
              >
                <ChevronLeftIcon className="w-5 h-5 text-gray-900" />
              </button>
              <button
                onClick={() => setCurrentBanner((prev) => (prev + 1) % banners.length)}
                className="absolute right-4 top-1/2 transform -translate-y-1/2 p-2 bg-white bg-opacity-80 rounded-full hover:bg-opacity-100 transition-all"
              >
                <ChevronRightIcon className="w-5 h-5 text-gray-900" />
              </button>
            </>
          )}
        </section>
      )}

      {/* 카테고리 섹션 */}
      {categories && categories.length > 0 && (
        <section>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">카테고리</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {categories.slice(0, 6).map((category) => (
              <Link
                key={category.id}
                to={`/products?category=${category.id}`}
                className="bg-white dark:bg-gray-800 rounded-xl p-6 text-center hover:shadow-lg transition-all duration-300 border border-gray-200 dark:border-gray-700 group"
              >
                <div className="text-3xl mb-3">📦</div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1 group-hover:text-blue-600 dark:group-hover:text-blue-400">
                  {category.name}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {category.product_count || 0}개 상품
                </p>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* 추천 상품 */}
      {featuredProducts && featuredProducts.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">추천 상품</h2>
            <Link
              to="/products?featured=true"
              className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium"
            >
              전체보기 →
            </Link>
          </div>
          {featuredLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="bg-gray-200 dark:bg-gray-700 h-48 rounded-lg mb-4"></div>
                  <div className="space-y-2">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {featuredProducts.map((product) => (
                <Link key={product.id} to={`/products/${product.id}`}>
                  <ProductCard product={product} />
                </Link>
              ))}
            </div>
          )}
        </section>
      )}

      {/* 신상품 */}
      {newProducts && newProducts.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">신상품</h2>
            <Link
              to="/products?new=true"
              className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium"
            >
              전체보기 →
            </Link>
          </div>
          {newProductsLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="bg-gray-200 dark:bg-gray-700 h-32 rounded-lg mb-4"></div>
                  <div className="space-y-2">
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded"></div>
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-6">
              {newProducts.map((product) => (
                <Link key={product.id} to={`/products/${product.id}`}>
                  <ProductCard product={product} />
                </Link>
              ))}
            </div>
          )}
        </section>
      )}

      {/* 특가 이벤트 배너 */}
      <section className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl p-8 text-center text-white">
        <h2 className="text-3xl font-bold mb-4">특가 이벤트</h2>
        <p className="text-lg mb-6 opacity-90">
          선착순 100명! 전 상품 추가 20% 할인
        </p>
        <Link
          to="/products?sale=true"
          className="inline-block px-8 py-3 bg-white text-purple-600 font-semibold rounded-lg hover:bg-gray-100 transition-colors"
        >
          이벤트 참여하기
        </Link>
      </section>

      {/* 데이터가 없을 때 */}
      {!banners?.length && !categories?.length && !featuredProducts?.length && (
        <div className="text-center py-16">
          <div className="text-6xl mb-4">🏪</div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            준비 중입니다
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            곧 다양한 상품들을 만나보실 수 있습니다.
          </p>
        </div>
      )}
    </div>
  )
}

export default Home