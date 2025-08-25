import React from 'react';
import { Link } from 'react-router-dom';
import { 
  HeartIcon, 
  StarIcon, 
  GiftIcon, 
  TruckIcon, 
  TagIcon,
  ArrowUpIcon 
} from '@heroicons/react/24/outline';
import { 
  HeartIcon as HeartSolidIcon,
  StarIcon as StarSolidIcon 
} from '@heroicons/react/24/solid';

// 타입 정의
interface Product {
  id: number;
  name: string;
  price: number;
  originalPrice?: number;
  image: string;
  rating: number;
  reviewCount: number;
  badge?: 'BEST' | 'NEW' | 'SALE';
  isLiked?: boolean;
}

interface Category {
  id: number;
  name: string;
  icon: string;
  color: string;
}

const Home: React.FC = () => {
  // 샘플 데이터
  const categories: Category[] = [
    { id: 1, name: '의류', icon: 'fas fa-tshirt', color: 'from-purple-400 to-purple-600' },
    { id: 2, name: '디지털', icon: 'fas fa-mobile-alt', color: 'from-blue-400 to-blue-600' },
    { id: 3, name: '생활용품', icon: 'fas fa-home', color: 'from-green-400 to-green-600' },
    { id: 4, name: '뷰티', icon: 'fas fa-gem', color: 'from-pink-400 to-pink-600' },
    { id: 5, name: '주방용품', icon: 'fas fa-utensils', color: 'from-orange-400 to-orange-600' },
    { id: 6, name: '스포츠', icon: 'fas fa-dumbbell', color: 'from-red-400 to-red-600' },
  ];

  const bestProducts: Product[] = [
    {
      id: 1,
      name: '클라리엘 스니커즈',
      price: 89000,
      image: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=300&h=300&fit=crop',
      rating: 4.8,
      reviewCount: 24,
      badge: 'BEST',
    },
    {
      id: 2,
      name: '클라리엘 딥클린 세탁세제',
      price: 12000,
      image: 'https://images.unsplash.com/photo-1556742400-b0abe8276b57?w=300&h=300&fit=crop',
      rating: 4.6,
      reviewCount: 18,
      badge: 'NEW',
    },
    {
      id: 3,
      name: '클리어린 주방세제',
      price: 8900,
      originalPrice: 12000,
      image: 'https://images.unsplash.com/photo-1556909114-4b729e2b4d65?w=300&h=300&fit=crop',
      rating: 4.9,
      reviewCount: 31,
      badge: 'SALE',
    },
    {
      id: 4,
      name: '우드 수납함 세트',
      price: 25000,
      image: 'https://images.unsplash.com/photo-1586823633818-cbf8e6c9c85c?w=300&h=300&fit=crop',
      rating: 4.7,
      reviewCount: 15,
    },
  ];

  const formatPrice = (price: number): string => {
    return new Intl.NumberFormat('ko-KR').format(price) + '원';
  };

  const getBadgeColor = (badge: string): string => {
    switch (badge) {
      case 'BEST': return 'bg-red-500';
      case 'NEW': return 'bg-green-500';
      case 'SALE': return 'bg-orange-500';
      default: return 'bg-gray-500';
    }
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 상단 공지 배너 */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white text-center py-2 text-sm">
        <GiftIcon className="inline w-4 h-4 mr-2" />
        첫 구매 고객을 위한 3,000원 할인 쿠폰 증정!
        <button className="ml-4 text-xs underline hover:no-underline">
          자세히보기
        </button>
      </div>

      {/* 히어로 섹션 */}
      <section className="relative h-96 bg-gradient-to-r from-purple-600 to-blue-600 flex items-center justify-center text-white overflow-hidden">
        <div className="text-center z-10">
          <h1 className="text-5xl font-bold mb-4 animate-fade-in-up">
            새로운 쇼핑 경험
          </h1>
          <p className="text-xl mb-8">
            Shopuda에서 만나는 특별한 상품들
          </p>
          <Link
            to="/products"
            className="inline-block bg-white text-purple-600 px-8 py-3 rounded-full font-semibold hover:bg-gray-100 transition-all duration-300 transform hover:-translate-y-1 hover:shadow-lg"
          >
            지금 쇼핑하기
          </Link>
        </div>
        
        {/* 플로팅 요소들 */}
        <div className="absolute top-20 left-10 animate-bounce">
          <div className="w-16 h-16 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
            <StarSolidIcon className="w-8 h-8 text-yellow-300" />
          </div>
        </div>
        <div className="absolute bottom-20 right-10 animate-bounce delay-1000">
          <div className="w-20 h-20 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
            <GiftIcon className="w-8 h-8 text-pink-300" />
          </div>
        </div>
      </section>

      {/* 카테고리 섹션 */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12 text-gray-800">
            카테고리
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
            {categories.map((category) => (
              <Link
                key={category.id}
                to={`/products?category=${category.id}`}
                className="text-center group cursor-pointer p-4 rounded-lg transition-all duration-300 hover:-translate-y-2 hover:shadow-lg"
              >
                <div className={`w-16 h-16 bg-gradient-to-br ${category.color} rounded-full mx-auto mb-3 flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                  <i className={`${category.icon} text-white text-2xl`}></i>
                </div>
                <span className="text-sm font-medium text-gray-700 group-hover:text-purple-600 transition-colors">
                  {category.name}
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* 베스트 상품 섹션 */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-800 mb-4">
              베스트 셀러
            </h2>
            <p className="text-gray-600">
              가장 많이 팔린 인기 상품들을 만나보세요
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {bestProducts.map((product) => (
              <div
                key={product.id}
                className="bg-white rounded-lg shadow-md overflow-hidden transition-all duration-300 hover:-translate-y-2 hover:shadow-xl group"
              >
                <div className="relative">
                  <img
                    src={product.image}
                    alt={product.name}
                    className="w-full aspect-square object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  
                  {/* 배지 */}
                  {product.badge && (
                    <div className={`absolute top-2 left-2 ${getBadgeColor(product.badge)} text-white px-2 py-1 rounded text-xs font-bold`}>
                      {product.badge}
                    </div>
                  )}
                  
                  {/* 찜하기 버튼 */}
                  <button className="absolute top-2 right-2 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-md hover:bg-gray-100 transition-colors">
                    {product.isLiked ? (
                      <HeartSolidIcon className="w-5 h-5 text-red-500" />
                    ) : (
                      <HeartIcon className="w-5 h-5 text-gray-400 hover:text-red-500" />
                    )}
                  </button>
                </div>
                
                <div className="p-4">
                  <Link to={`/products/${product.id}`}>
                    <h3 className="font-semibold text-gray-800 mb-2 text-sm hover:text-purple-600 transition-colors">
                      {product.name}
                    </h3>
                  </Link>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex flex-col">
                      <span className="text-lg font-bold text-purple-600">
                        {formatPrice(product.price)}
                      </span>
                      {product.originalPrice && (
                        <span className="text-sm text-gray-400 line-through">
                          {formatPrice(product.originalPrice)}
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center text-xs">
                      <StarSolidIcon className="w-4 h-4 text-yellow-400" />
                      <span className="ml-1 text-gray-600">
                        {product.rating} ({product.reviewCount})
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="text-center mt-12">
            <Link
              to="/products"
              className="inline-block bg-gradient-to-r from-purple-600 to-blue-600 text-white px-8 py-3 rounded-full font-semibold hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1"
            >
              더 많은 상품 보기
            </Link>
          </div>
        </div>
      </section>

      {/* 특별 이벤트 섹션 */}
      <section className="py-16 bg-gradient-to-r from-purple-600 to-blue-600 text-white">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">특별 이벤트</h2>
          <p className="text-xl mb-8">
            지금 진행 중인 다양한 이벤트 쿠폰을 만나보세요
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white bg-opacity-20 backdrop-blur-sm rounded-lg p-6 transition-all duration-300 hover:-translate-y-2 hover:bg-opacity-30">
              <GiftIcon className="w-12 h-12 mx-auto mb-4" />
              <h3 className="text-xl font-bold mb-2">첫 구매 할인</h3>
              <p className="mb-4">신규 회원 3,000원 할인</p>
              <button className="bg-white text-purple-600 px-4 py-2 rounded-full font-semibold hover:bg-gray-100 transition-colors">
                쿠폰 받기
              </button>
            </div>
            
            <div className="bg-white bg-opacity-20 backdrop-blur-sm rounded-lg p-6 transition-all duration-300 hover:-translate-y-2 hover:bg-opacity-30">
              <TruckIcon className="w-12 h-12 mx-auto mb-4" />
              <h3 className="text-xl font-bold mb-2">무료 배송</h3>
              <p className="mb-4">5만원 이상 구매 시</p>
              <button className="bg-white text-purple-600 px-4 py-2 rounded-full font-semibold hover:bg-gray-100 transition-colors">
                자세히보기
              </button>
            </div>
            
            <div className="bg-white bg-opacity-20 backdrop-blur-sm rounded-lg p-6 transition-all duration-300 hover:-translate-y-2 hover:bg-opacity-30">
              <TagIcon className="w-12 h-12 mx-auto mb-4" />
              <h3 className="text-xl font-bold mb-2">계절 세일</h3>
              <p className="mb-4">선택 상품 최대 50% 할인</p>
              <button className="bg-white text-purple-600 px-4 py-2 rounded-full font-semibold hover:bg-gray-100 transition-colors">
                세일 보기
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 플로팅 버튼 */}
      <div className="fixed bottom-6 right-6 space-y-3 z-50">
        <button className="w-12 h-12 bg-green-500 text-white rounded-full shadow-lg hover:bg-green-600 transition-colors flex items-center justify-center">
          <i className="fab fa-whatsapp text-xl"></i>
        </button>
        <button
          onClick={scrollToTop}
          className="w-12 h-12 bg-purple-500 text-white rounded-full shadow-lg hover:bg-purple-600 transition-colors flex items-center justify-center"
        >
          <ArrowUpIcon className="w-6 h-6" />
        </button>
      </div>
    </div>
  );
};

export default Home;