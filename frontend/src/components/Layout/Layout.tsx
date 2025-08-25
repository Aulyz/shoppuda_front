// frontend/src/components/Layout/Layout.tsx
import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { 
  Bars3Icon, 
  XMarkIcon, 
  MagnifyingGlassIcon,
  ShoppingCartIcon,
  HeartIcon,
  UserIcon
} from '@heroicons/react/24/outline'

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const navItems = [
    { name: '홈', path: '/' },
    { name: '상품', path: '/products' },
    { name: '장바구니', path: '/cart' },
    { name: '마이페이지', path: '/mypage' },
  ]

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      window.location.href = `/products?search=${encodeURIComponent(searchQuery)}`
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {/* 헤더 */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            
            {/* 로고 */}
            <div className="flex items-center">
              <Link to="/" className="flex items-center">
                <span className="text-2xl font-bold text-blue-600">Shopuda</span>
              </Link>
            </div>

            {/* 데스크탑 검색바 */}
            <div className="hidden md:flex flex-1 max-w-lg mx-8">
              <form onSubmit={handleSearch} className="w-full relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="상품을 검색해보세요"
                  className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <MagnifyingGlassIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
              </form>
            </div>

            {/* 데스크탑 메뉴 */}
            <div className="hidden md:flex items-center space-x-8">
              {navItems.map((item) => (
                <Link
                  key={item.name}
                  to={item.path}
                  className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition-colors"
                >
                  {item.name}
                </Link>
              ))}
              
              {/* 사용자 메뉴 */}
              <div className="flex items-center space-x-4">
                <Link to="/cart" className="p-2 text-gray-600 hover:text-blue-600">
                  <ShoppingCartIcon className="h-6 w-6" />
                </Link>
                <Link to="/wishlist" className="p-2 text-gray-600 hover:text-blue-600">
                  <HeartIcon className="h-6 w-6" />
                </Link>
                <Link to="/login" className="p-2 text-gray-600 hover:text-blue-600">
                  <UserIcon className="h-6 w-6" />
                </Link>
              </div>
            </div>

            {/* 모바일 메뉴 버튼 */}
            <div className="md:hidden">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="p-2 text-gray-600 hover:text-gray-900"
              >
                {isMenuOpen ? (
                  <XMarkIcon className="w-6 h-6" />
                ) : (
                  <Bars3Icon className="w-6 h-6" />
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
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </form>

                {/* 모바일 메뉴 아이템 */}
                {navItems.map((item) => (
                  <Link
                    key={item.name}
                    to={item.path}
                    className="block px-3 py-2 text-base font-medium text-gray-700 hover:bg-gray-100 rounded-md"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    {item.name}
                  </Link>
                ))}
                
                <Link
                  to="/login"
                  className="block px-3 py-2 text-base font-medium text-gray-700 hover:bg-gray-100 rounded-md"
                  onClick={() => setIsMenuOpen(false)}
                >
                  로그인
                </Link>
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
              <h3 className="text-2xl font-bold mb-4 text-blue-400">
                Shopuda
              </h3>
              <p className="text-gray-400 mb-4">
                온라인 쇼핑의 새로운 경험
              </p>
              <div className="flex space-x-4">
                <a href="#" className="text-gray-400 hover:text-white transition-colors">
                  Facebook
                </a>
                <a href="#" className="text-gray-400 hover:text-white transition-colors">
                  Instagram
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
              </ul>
            </div>

            {/* 쇼핑 정보 */}
            <div>
              <h4 className="font-semibold mb-4">쇼핑 정보</h4>
              <ul className="space-y-2 text-gray-400">
                <li>
                  <Link to="/delivery" className="hover:text-white transition-colors">
                    배송 안내
                  </Link>
                </li>
                <li>
                  <Link to="/returns" className="hover:text-white transition-colors">
                    교환/반품
                  </Link>
                </li>
                <li>
                  <Link to="/payment" className="hover:text-white transition-colors">
                    결제 방법
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
              </ul>
            </div>
          </div>

          {/* 카피라이트 */}
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 Shopuda. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Layout