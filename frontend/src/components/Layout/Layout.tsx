import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  MagnifyingGlassIcon,
  HeartIcon,
  ShoppingCartIcon,
  UserIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [cartCount, setCartCount] = useState(0);
  const [wishlistCount, setWishlistCount] = useState(0);
  const location = useLocation();

  // 스크롤 이벤트 처리
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 100);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // 모바일 메뉴 토글
  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  // 검색 처리
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      // 검색 페이지로 이동
      window.location.href = `/products?search=${encodeURIComponent(searchQuery)}`;
    }
  };

  const navItems = [
    { name: '전체상품', path: '/products' },
    { name: '베스트', path: '/products?filter=best' },
    { name: '신상품', path: '/products?filter=new' },
    { name: '세일', path: '/products?filter=sale', className: 'text-red-600 hover:text-red-700' },
    { name: '이벤트', path: '/events' },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* 네비게이션 */}
      <nav className={`sticky top-0 z-50 transition-all duration-300 ${
        isScrolled 
          ? 'bg-white/95 backdrop-blur-md shadow-lg' 
          : 'bg-white shadow-sm'
      }`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* 로고 */}
            <div className="flex items-center">
              <Link 
                to="/" 
                className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent"
              >
                Shopuda
              </Link>
            </div>

            {/* 데스크톱 메뉴 */}
            <div className="hidden md:flex space-x-8">
              {navItems.map((item) => (
                <Link
                  key={item.name}
                  to={item.path}
                  className={`font-medium transition-colors ${
                    item.className || 'text-gray-700 hover:text-purple-600'
                  } ${
                    location.pathname === item.path ? 'text-purple-600' : ''
                  }`}
                >
                  {item.name}
                </Link>
              ))}
            </div>

            {/* 검색바 및 아이콘들 */}
            <div className="flex items-center space-x-4">
              {/* 데스크톱 검색바 */}
              <form onSubmit={handleSearch} className="relative hidden md:block">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="상품을 검색해보세요"
                  className="w-64 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <button
                  type="submit"
                  className="absolute right-3 top-1/2 transform -translate-y-1/2"
                >
                  <MagnifyingGlassIcon className="w-5 h-5 text-gray-400" />
                </button>
              </form>

              {/* 모바일 검색 버튼 */}
              <button className="md:hidden">
                <MagnifyingGlassIcon className="w-6 h-6 text-gray-600" />
              </button>

              {/* 찜하기 */}
              <Link to="/wishlist" className="relative">
                <HeartIcon className="w-6 h-6 text-gray-600 hover:text-red-500 transition-colors" />
                {wishlistCount > 0 && (
                  <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                    {wishlistCount}
                  </span>
                )}
              </Link>

              {/* 장바구니 */}
              <Link to="/cart" className="relative">
                <ShoppingCartIcon className="w-6 h-6 text-gray-600 hover:text-purple-600 transition-colors" />
                {cartCount > 0 && (
                  <span className="absolute -top-2 -right-2 bg-purple-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                    {cartCount}
                  </span>
                )}
              </Link>

              {/* 사용자 메뉴 */}
              <Link to="/login">
                <UserIcon className="w-6 h-6 text-gray-600 hover:text-purple-600 transition-colors" />
              </Link>

              {/* 모바일 메뉴 버튼 */}
              <button 
                className="md:hidden"
                onClick={toggleMenu}
              >
                {isMenuOpen ? (
                  <XMarkIcon className="w-6 h-6 text-gray-600" />
                ) : (
                  <Bars3Icon className="w-6 h-6 text-gray-600" />
                )}
              </button>
            </div>
          </div>

          {/* 모바일 메뉴 */}
          {isMenuOpen && (
            <div className="md:hidden border-t border-gray-200 pb-4">
              <div className="px-2 pt-2 pb-3 space-y-1">
                {/* 모바일 검색바 */}
                <form onSubmit={handleSearch} className="relative mb-4">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="상품을 검색해보세요"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </form>

                {/* 모바일 메뉴 아이템 */}
                {navItems.map((item) => (
                  <Link
                    key={item.name}
                    to={item.path}
                    className={`block px-3 py-2 text-base font-medium rounded-md transition-colors ${
                      item.className || 'text-gray-700 hover:bg-gray-100'
                    }`}
                    onClick={() => setIsMenuOpen(false)}
                  >
                    {item.name}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </nav>

      {/* 메인 컨텐츠 */}
      <main className="flex-1">
        {children}
      </main>

      {/* 푸터 */}
      <footer className="bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {/* 회사 정보 */}
            <div>
              <h3 className="text-2xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                Shopuda
              </h3>
              <p className="text-gray-400 mb-4">
                온라인 쇼핑의 새로운 경험
              </p>
              <div className="flex space-x-4">
                <a href="#" className="text-gray-400 hover:text-white transition-colors">
                  <i className="fab fa-facebook-f"></i>
                </a>
                <a href="#" className="text-gray-400 hover:text-white transition-colors">
                  <i className="fab fa-instagram"></i>
                </a>
                <a href="#" className="text-gray-400 hover:text-white transition-colors">
                  <i className="fab fa-youtube"></i>
                </a>
              </div>
            </div>

            {/* 고객센터 */}
            <div>
              <h4 className="font-semibold mb-4">고객센터</h4>
              <ul className="space-y-2 text-gray-400">
                <li>
                  <Link to="/notice" className="hover:text-white transition-colors">
                    공지사항
                  </Link>
                </li>
                <li>
                  <Link to="/faq" className="hover:text-white transition-colors">
                    자주 묻는 질문
                  </Link>
                </li>
                <li>
                  <Link to="/inquiry" className="hover:text-white transition-colors">
                    1:1 문의
                  </Link>
                </li>
                <li>
                  <Link to="/shipping" className="hover:text-white transition-colors">
                    배송 안내
                  </Link>
                </li>
              </ul>
            </div>

            {/* 회사 정보 */}
            <div>
              <h4 className="font-semibold mb-4">회사 정보</h4>
              <ul className="space-y-2 text-gray-400">
                <li>
                  <Link to="/about" className="hover:text-white transition-colors">
                    회사 소개
                  </Link>
                </li>
                <li>
                  <Link to="/terms" className="hover:text-white transition-colors">
                    이용약관
                  </Link>
                </li>
                <li>
                  <Link to="/privacy" className="hover:text-white transition-colors">
                    개인정보처리방침
                  </Link>
                </li>
                <li>
                  <Link to="/business" className="hover:text-white transition-colors">
                    사업자 정보
                  </Link>
                </li>
              </ul>
            </div>

            {/* 연락처 */}
            <div>
              <h4 className="font-semibold mb-4">연락처</h4>
              <div className="text-gray-400 space-y-2">
                <p>
                  <i className="fas fa-phone mr-2"></i>
                  010-2474-0413
                </p>
                <p>
                  <i className="fas fa-envelope mr-2"></i>
                  seri00413@naver.com
                </p>
                <p>
                  <i className="fas fa-clock mr-2"></i>
                  09:00 - 18:00
                </p>
              </div>
            </div>
          </div>

          {/* 카피라이트 */}
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 Shopuda. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;