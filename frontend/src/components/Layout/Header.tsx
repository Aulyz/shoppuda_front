import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Bars3Icon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'

interface HeaderProps {
  onMenuClick: () => void
}

const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [showDropdown, setShowDropdown] = useState(false)
  const [searchResults, setSearchResults] = useState<any[]>([])

  const handleSearch = async (query: string) => {
    setSearchQuery(query)
    
    if (query.length >= 2) {
      // TODO: 실제 API 연동 시 구현
      // 임시 mock 데이터
      const mockResults = [
        { id: 1, name: `${query} 관련 상품 1`, type: 'product' },
        { id: 2, name: `${query} 관련 상품 2`, type: 'product' },
      ]
      setSearchResults(mockResults)
      setShowDropdown(true)
    } else {
      setSearchResults([])
      setShowDropdown(false)
    }
  }

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      // TODO: 검색 결과 페이지로 이동
      console.log('검색:', searchQuery)
      setShowDropdown(false)
    }
  }

  return (
    <div className="sticky top-0 z-30 bg-white/80 dark:bg-gray-800/80 backdrop-blur-lg border-b border-gray-200 dark:border-gray-700">
      <div className="flex h-16 items-center gap-x-4 px-4 sm:gap-x-6 sm:px-6 lg:px-8">
        {/* Mobile menu button */}
        <button
          type="button"
          onClick={onMenuClick}
          className="lg:hidden -m-2.5 p-2.5 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
        >
          <Bars3Icon className="w-5 h-5" />
        </button>

        {/* Breadcrumb - 추후 확장 */}
        <div className="flex-1 text-sm leading-6 text-gray-500 dark:text-gray-400 hidden sm:block">
          <div className="flex items-center space-x-2">
            <span>홈</span>
          </div>
        </div>

        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <form onSubmit={handleSearchSubmit}>
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                onFocus={() => searchResults.length > 0 && setShowDropdown(true)}
                onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                placeholder="상품 검색..."
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:ring-opacity-20 focus:outline-none transition-all"
              />
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
            </div>
          </form>

          {/* Search dropdown */}
          {showDropdown && searchResults.length > 0 && (
            <div className="absolute top-full mt-1 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50">
              <div className="py-2">
                {searchResults.map((result) => (
                  <button
                    key={result.id}
                    onClick={() => {
                      console.log('선택된 상품:', result)
                      setShowDropdown(false)
                    }}
                    className="w-full px-4 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-gray-200 dark:bg-gray-600 rounded-md flex-shrink-0" />
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {result.name}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          상품
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
              <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-2">
                <button
                  onClick={() => {
                    handleSearchSubmit(new Event('submit') as any)
                  }}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium"
                >
                  "{searchQuery}" 전체 검색 결과 보기
                </button>
              </div>
            </div>
          )}
        </div>

        {/* User menu */}
        <div className="flex items-center space-x-4">
          {/* 알림 아이콘 (추후 구현) */}
          <button className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </button>

          {/* 다크모드 토글 (추후 구현) */}
          <button className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          </button>

          {/* 사용자 메뉴 */}
          <div className="flex items-center space-x-3">
            <Link
              to="/login"
              className="text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              로그인
            </Link>
            <Link
              to="/signup"
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors shadow-sm"
            >
              회원가입
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Header