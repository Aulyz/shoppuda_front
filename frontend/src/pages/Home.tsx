import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowRightIcon } from '@heroicons/react/24/outline'
import { useFeaturedProducts, useProducts } from '../hooks/useApi'
import { apiUtils } from '../api/services'
import { Product } from '../types/api'

const ProductCard: React.FC<{ product: Product }> = ({ product }) => {
  const discountPercentage = product.discount_price 
    ? apiUtils.calculateDiscountPercentage(product.selling_price, product.discount_price)
    : 0

  return (
    <Link 
      to={`/products/${product.id}`}
      className="group block bg-white dark:bg-gray-800 rounded-xl shadow-sm hover:shadow-lg transition-all duration-200 overflow-hidden border border-gray-200 dark:border-gray-700"
    >
      <div className="aspect-square overflow-hidden bg-gray-100 dark:bg-gray-700">
        {product.primary_image ? (
          <img
            src={apiUtils.getImageUrl(product.primary_image.image)}
            alt={product.name}
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

const Home: React.FC = () => {
  // API를 통해 추천 상품 가져오기
  const { data: featuredProducts, isLoading: featuredLoading, error: featuredError } = useFeaturedProducts(8)
  
  // 신상품 가져오기 (최신 상품 6개)
  const { data: newProductsData, isLoading: newProductsLoading, error: newProductsError } = useProducts({
    page_size: 6,
    ordering: '-created_at'
  })
  
  const newProducts = newProductsData?.results || []

  return (
    <div className="min-h-screen">
      {/* Hero 섹션 */}
      <section className="relative bg-gradient-to-r from-blue-600 to-purple-700 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6">
              Shopuda와 함께하는
              <br />
              <span className="text-yellow-300">스마트 쇼핑</span>
            </h1>
            <p className="text-xl sm:text-2xl mb-8 text-blue-100">
              다양한 플랫폼의 상품을 한곳에서 비교하고 구매하세요
            </p>
            <Link
              to="/products"
              className="inline-flex items-center px-8 py-4 bg-white text-blue-600 rounded-full text-lg font-semibold hover:bg-blue-50 transition-colors duration-200"
            >
              쇼핑 시작하기
              <ArrowRightIcon className="ml-2 h-5 w-5" />
            </Link>
          </div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* 추천 상품 섹션 */}
        <section className="mb-16">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              추천 상품
            </h2>
            <Link 
              to="/products"
              className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium flex items-center"
            >
              더 보기
              <ArrowRightIcon className="ml-1 h-4 w-4" />
            </Link>
          </div>
          
          {featuredLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="aspect-square bg-gray-200 dark:bg-gray-700 rounded-lg mb-4"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
                  <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
                </div>
              ))}
            </div>
          ) : featuredError ? (
            <div className="text-center py-12">
              <div className="text-red-500 mb-2">상품을 불러오는 중 오류가 발생했습니다</div>
              <p className="text-gray-600 dark:text-gray-400">잠시 후 다시 시도해주세요</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {featuredProducts?.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}
        </section>

        {/* 신상품 섹션 */}
        <section className="mb-16">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              신상품
            </h2>
            <Link 
              to="/products?ordering=-created_at"
              className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium flex items-center"
            >
              더 보기
              <ArrowRightIcon className="ml-1 h-4 w-4" />
            </Link>
          </div>
          
          {newProductsLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="aspect-square bg-gray-200 dark:bg-gray-700 rounded-lg mb-4"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
                  <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
                </div>
              ))}
            </div>
          ) : newProductsError ? (
            <div className="text-center py-12">
              <div className="text-red-500 mb-2">신상품을 불러오는 중 오류가 발생했습니다</div>
              <p className="text-gray-600 dark:text-gray-400">잠시 후 다시 시도해주세요</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {newProducts.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}
        </section>

        {/* 특징 섹션 */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <div className="text-center p-6 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              검증된 판매자
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              신뢰할 수 있는 판매자들과만 거래하세요
            </p>
          </div>
          
          <div className="text-center p-6 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              최저가 보장
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              다양한 플랫폼의 가격을 비교하여 최저가를 제공합니다
            </p>
          </div>
          
          <div className="text-center p-6 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-purple-600 dark:text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              빠른 배송
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              전국 어디든 빠르고 안전한 배송 서비스
            </p>
          </div>
        </section>
      </div>
    </div>
  )
}

export default Home