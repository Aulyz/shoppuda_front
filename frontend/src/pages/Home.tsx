import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  ChevronLeftIcon, 
  ChevronRightIcon,
  StarIcon,
  HeartIcon,
  ShoppingCartIcon,
  TagIcon, // Card 만들 때 사용할지도
  FireIcon
} from '@heroicons/react/24/outline'
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid'

// Mock 데이터 타입
interface Banner {
  id: number
  title: string
  subtitle: string
  image: string
  link: string
  buttonText: string
}

interface Product {
  id: number
  name: string
  price: number
  discountPrice?: number
  image: string
  rating: number
  reviewCount: number
  isNew: boolean
  isFeatured: boolean
  isWished: boolean
  discountPercentage?: number
}

interface Category {
  id: number
  name: string
  productCount: number
  icon: string
}

const Home: React.FC = () => {
  const [currentBanner, setCurrentBanner] = useState(0)
  const [wishlist, setWishlist] = useState<Set<number>>(new Set())

  // Mock 데이터
  const banners: Banner[] = [
    {
      id: 1,
      title: "신상품 특가 할인",
      subtitle: "최대 50% 할인된 가격으로 만나보세요",
      image: "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1200&h=600&fit=crop",
      link: "/products",
      buttonText: "지금 쇼핑하기"
    },
    {
      id: 2,
      title: "여름 컬렉션",
      subtitle: "시원한 여름을 위한 필수 아이템",
      image: "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=1200&h=600&fit=crop",
      link: "/products",
      buttonText: "컬렉션 보기"
    },
    {
      id: 3,
      title: "무료배송 이벤트",
      subtitle: "3만원 이상 구매 시 무료배송",
      image: "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=1200&h=600&fit=crop",
      link: "/products",
      buttonText: "자세히 보기"
    }
  ]

  const categories: Category[] = [
    { id: 1, name: "의류", productCount: 245, icon: "👕" },
    { id: 2, name: "전자제품", productCount: 156, icon: "📱" },
    { id: 3, name: "화장품", productCount: 89, icon: "💄" },
    { id: 4, name: "가전제품", productCount: 67, icon: "🏠" },
    { id: 5, name: "도서", productCount: 234, icon: "📚" },
    { id: 6, name: "스포츠", productCount: 123, icon: "⚽" },
  ]

  const featuredProducts: Product[] = [
    {
      id: 1,
      name: "프리미엄 무선 이어폰",
      price: 129000,
      discountPrice: 89000,
      image: "https://images.unsplash.com/photo-1572569511254-d8f925fe2cbb?w=400&h=400&fit=crop",
      rating: 4.8,
      reviewCount: 324,
      isNew: true,
      isFeatured: true,
      isWished: false,
      discountPercentage: 31
    },
    {
      id: 2,
      name: "스마트 워치 Pro",
      price: 299000,
      discountPrice: 249000,
      image: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop",
      rating: 4.9,
      reviewCount: 156,
      isNew: false,
      isFeatured: true,
      isWished: true,
      discountPercentage: 17
    },
    {
      id: 3,
      name: "노트북 백팩 15인치",
      price: 89000,
      image: "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&fit=crop",
      rating: 4.6,
      reviewCount: 89,
      isNew: false,
      isFeatured: true,
      isWished: false
    },
    {
      id: 4,
      name: "블루투스 스피커",
      price: 59000,
      discountPrice: 39000,
      image: "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&h=400&fit=crop",
      rating: 4.7,
      reviewCount: 201,
      isNew: true,
      isFeatured: true,
      isWished: false,
      discountPercentage: 34
    }
  ]

  const newProducts: Product[] = [
    {
      id: 5,
      name: "USB-C 충전 케이블",
      price: 15000,
      image: "https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=400&h=400&fit=crop",
      rating: 4.5,
      reviewCount: 45,
      isNew: true,
      isFeatured: false,
      isWished: false
    },
    {
      id: 6,
      name: "게이밍 마우스 패드",
      price: 25000,
      discountPrice: 19000,
      image: "https://images.unsplash.com/photo-1527814050087-3793815479db?w=400&h=400&fit=crop",
      rating: 4.3,
      reviewCount: 67,
      isNew: true,
      isFeatured: false,
      isWished: false,
      discountPercentage: 24
    }
  ]

  // 배너 자동 슬라이드
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentBanner((prev) => (prev + 1) % banners.length)
    }, 5000)
    return () => clearInterval(timer)
  }, [banners.length])

  const toggleWishlist = (productId: number) => {
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

  const ProductCard = ({ product }: { product: Product }) => (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 group overflow-hidden border border-gray-200 dark:border-gray-700">
      <div className="relative overflow-hidden">
        <img 
          src={product.image} 
          alt={product.name}
          className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300"
        />
        
        {/* 상품 뱃지 */}
        <div className="absolute top-3 left-3 flex flex-col space-y-1">
          {product.isNew && (
            <span className="px-2 py-1 bg-green-500 text-white text-xs font-bold rounded-md">
              NEW
            </span>
          )}
          {product.discountPercentage && (
            <span className="px-2 py-1 bg-red-500 text-white text-xs font-bold rounded-md">
              -{product.discountPercentage}%
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
          <button className="p-2 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-colors">
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
          {product.discountPrice ? (
            <>
              <span className="text-lg font-bold text-gray-900 dark:text-white">
                {product.discountPrice.toLocaleString()}원
              </span>
              <span className="text-sm text-gray-500 line-through">
                {product.price.toLocaleString()}원
              </span>
            </>
          ) : (
            <span className="text-lg font-bold text-gray-900 dark:text-white">
              {product.price.toLocaleString()}원
            </span>
          )}
        </div>

        {/* 평점 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-1">
            <StarIcon className="w-4 h-4 text-yellow-400 fill-current" />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {product.rating} ({product.reviewCount})
            </span>
          </div>
          {product.isFeatured && (
            <FireIcon className="w-4 h-4 text-orange-500" />
          )}
        </div>
      </div>
    </div>
  )

  return (
    <div className="space-y-12">
      {/* 메인 배너 */}
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
                  {banner.buttonText}
                </Link>
              </div>
            </div>
          ))}
        </div>

        {/* 배너 네비게이션 */}
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
      </section>

      {/* 카테고리 섹션 */}
      <section>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">카테고리</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          {categories.map((category) => (
            <Link
              key={category.id}
              to={`/products?category=${category.id}`}
              className="bg-white dark:bg-gray-800 rounded-xl p-6 text-center hover:shadow-lg transition-all duration-300 border border-gray-200 dark:border-gray-700 group"
            >
              <div className="text-3xl mb-3">{category.icon}</div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1 group-hover:text-blue-600 dark:group-hover:text-blue-400">
                {category.name}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {category.productCount}개 상품
              </p>
            </Link>
          ))}
        </div>
      </section>

      {/* 추천 상품 */}
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
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {featuredProducts.map((product) => (
            <Link key={product.id} to={`/products/${product.id}`}>
              <ProductCard product={product} />
            </Link>
          ))}
        </div>
      </section>

      {/* 신상품 */}
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
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-6">
          {newProducts.map((product) => (
            <Link key={product.id} to={`/products/${product.id}`}>
              <ProductCard product={product} />
            </Link>
          ))}
        </div>
      </section>

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
    </div>
  )
}

export default Home