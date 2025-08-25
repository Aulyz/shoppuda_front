import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  HeartIcon, 
  StarIcon, 
  ShoppingCartIcon,
  EyeIcon 
} from '@heroicons/react/24/outline';
import { 
  HeartIcon as HeartSolidIcon,
  StarIcon as StarSolidIcon 
} from '@heroicons/react/24/solid';
import { Product } from '../../types/api';
import { formatPrice, calculateDiscountPercentage } from '../../utils/helpers';

interface ProductCardProps {
  product: Product;
  showQuickView?: boolean;
  showWishlist?: boolean;
  showCompare?: boolean;
  className?: string;
  onAddToCart?: (productId: number) => void;
  onToggleWishlist?: (productId: number) => void;
  onQuickView?: (productId: number) => void;
}

const ProductCard: React.FC<ProductCardProps> = ({
  product,
  showQuickView = true,
  showWishlist = true,
  showCompare = false,
  className = '',
  onAddToCart,
  onToggleWishlist,
  onQuickView,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isLiked, setIsLiked] = useState(false);
  const [imageError, setImageError] = useState(false);

  const primaryImage = product.images?.find(img => img.is_primary) || product.images?.[0];
  const hasDiscount = product.discount_price && product.discount_price < product.selling_price;
  const discountPercentage = hasDiscount ? calculateDiscountPercentage(product.selling_price, product.discount_price!) : 0;

  const handleAddToCart = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (isLoading) return;
    
    setIsLoading(true);
    try {
      if (onAddToCart) {
        await onAddToCart(parseInt(product.id));
      }
    } catch (error) {
      console.error('장바구니 추가 오류:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleWishlist = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    setIsLiked(!isLiked);
    
    if (onToggleWishlist) {
      try {
        await onToggleWishlist(parseInt(product.id));
      } catch (error) {
        setIsLiked(isLiked); // 실패 시 원상복구
        console.error('찜하기 오류:', error);
      }
    }
  };

  const handleQuickView = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (onQuickView) {
      onQuickView(parseInt(product.id));
    }
  };

  const handleImageError = () => {
    setImageError(true);
  };

  const getBadgeInfo = () => {
    if (product.is_featured) {
      return { text: 'BEST', className: 'badge-best' };
    }
    if (hasDiscount) {
      return { text: 'SALE', className: 'badge-sale' };
    }
    if (new Date(product.created_at) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)) {
      return { text: 'NEW', className: 'badge-new' };
    }
    return null;
  };

  const renderStars = (rating: number) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;

    for (let i = 0; i < fullStars; i++) {
      stars.push(<StarSolidIcon key={i} className="w-4 h-4 text-yellow-400" />);
    }

    if (hasHalfStar) {
      stars.push(
        <div key="half" className="relative w-4 h-4">
          <StarIcon className="w-4 h-4 text-yellow-400 absolute" />
          <StarSolidIcon 
            className="w-4 h-4 text-yellow-400 absolute" 
            style={{ clipPath: 'inset(0 50% 0 0)' }}
          />
        </div>
      );
    }

    const emptyStars = 5 - Math.ceil(rating);
    for (let i = 0; i < emptyStars; i++) {
      stars.push(<StarIcon key={`empty-${i}`} className="w-4 h-4 text-gray-300" />);
    }

    return stars;
  };

  const badge = getBadgeInfo();

  return (
    <div className={`card card-hover group relative ${className}`}>
      <Link to={`/products/${product.id}`} className="block">
        {/* 상품 이미지 */}
        <div className="relative overflow-hidden bg-gray-100">
          {imageError ? (
            <div className="aspect-square flex items-center justify-center text-gray-400">
              <svg className="w-12 h-12" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
              </svg>
            </div>
          ) : (
            <img
              src={primaryImage?.image || '/placeholder-image.jpg'}
              alt={primaryImage?.alt_text || product.name}
              className="aspect-square w-full object-cover group-hover:scale-105 transition-transform duration-300"
              onError={handleImageError}
              loading="lazy"
            />
          )}

          {/* 배지 */}
          {badge && (
            <div className={`absolute top-2 left-2 ${badge.className}`}>
              {badge.text}
            </div>
          )}

          {/* 할인 퍼센트 */}
          {hasDiscount && discountPercentage > 0 && (
            <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded-full text-xs font-bold">
              -{discountPercentage}%
            </div>
          )}

          {/* 호버 액션 버튼들 */}
          <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-300 flex items-center justify-center opacity-0 group-hover:opacity-100">
            <div className="flex space-x-2">
              {showQuickView && (
                <button
                  onClick={handleQuickView}
                  className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-md hover:bg-gray-100 transition-colors"
                  title="빠른 보기"
                >
                  <EyeIcon className="w-5 h-5 text-gray-600" />
                </button>
              )}
              
              <button
                onClick={handleAddToCart}
                disabled={isLoading || product.stock_quantity === 0}
                className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center shadow-md hover:bg-purple-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                title="장바구니에 추가"
              >
                {isLoading ? (
                  <div className="spinner w-4 h-4 border-white"></div>
                ) : (
                  <ShoppingCartIcon className="w-5 h-5 text-white" />
                )}
              </button>
            </div>
          </div>

          {/* 찜하기 버튼 */}
          {showWishlist && (
            <button
              onClick={handleToggleWishlist}
              className="absolute top-2 right-2 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-md hover:bg-gray-100 transition-colors opacity-0 group-hover:opacity-100"
              title={isLiked ? "찜 해제" : "찜하기"}
            >
              {isLiked ? (
                <HeartSolidIcon className="w-5 h-5 text-red-500" />
              ) : (
                <HeartIcon className="w-5 h-5 text-gray-400 hover:text-red-500" />
              )}
            </button>
          )}

          {/* 재고 없음 오버레이 */}
          {product.stock_quantity === 0 && (
            <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
              <span className="text-white font-semibold">품절</span>
            </div>
          )}
        </div>

        {/* 상품 정보 */}
        <div className="p-4">
          {/* 브랜드 */}
          {product.brand && (
            <p className="text-xs text-gray-500 mb-1">{product.brand.name}</p>
          )}

          {/* 상품명 */}
          <h3 className="font-semibold text-gray-800 mb-2 text-sm line-clamp-2 group-hover:text-purple-600 transition-colors">
            {product.name}
          </h3>

          {/* 평점 및 리뷰 수 */}
          {(product.review_count && product.review_count > 0) && (
            <div className="flex items-center mb-2">
              <div className="flex items-center">
                {renderStars(product.average_rating || 0)}
              </div>
              <span className="text-xs text-gray-500 ml-2">
                ({product.review_count})
              </span>
            </div>
          )}

          {/* 가격 정보 */}
          <div className="flex items-center justify-between">
            <div className="flex flex-col">
              {hasDiscount ? (
                <>
                  <span className="text-lg font-bold text-purple-600">
                    {formatPrice(product.discount_price!)}
                  </span>
                  <span className="text-sm text-gray-400 line-through">
                    {formatPrice(product.selling_price)}
                  </span>
                </>
              ) : (
                <span className="text-lg font-bold text-purple-600">
                  {formatPrice(product.selling_price)}
                </span>
              )}
            </div>

            {/* 무료배송 표시 */}
            {product.selling_price >= 50000 && (
              <span className="text-xs text-green-600 font-medium">
                무료배송
              </span>
            )}
          </div>

          {/* 태그 */}
          {product.tags && product.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {product.tags.slice(0, 2).map((tag, index) => (
                <span
                  key={index}
                  className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </Link>
    </div>
  );
};

export default ProductCard;