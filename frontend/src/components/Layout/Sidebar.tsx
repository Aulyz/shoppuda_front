import { Link, useLocation } from 'react-router-dom'
import { XMarkIcon } from '@heroicons/react/24/outline'
import {
  HomeIcon,
  ShoppingBagIcon,
  ShoppingCartIcon,
  UserIcon,
  HeartIcon,
  ClockIcon
} from '@heroicons/react/24/outline'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const location = useLocation()

  const navigation = [
    { name: '홈', href: '/', icon: HomeIcon },
    { name: '상품', href: '/products', icon: ShoppingBagIcon },
    { name: '장바구니', href: '/cart', icon: ShoppingCartIcon },
    { name: '찜목록', href: '/wishlist', icon: HeartIcon },
    { name: '주문내역', href: '/orders', icon: ClockIcon },
    { name: '마이페이지', href: '/mypage', icon: UserIcon },
  ]

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(path)
  }

  const SidebarContent = () => (
    <div className="flex flex-col h-full bg-white dark:bg-gray-800">
      {/* Logo */}
      <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center shadow-sm">
            <span className="text-white font-bold text-sm">S</span>
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-bold text-gray-900 dark:text-white">Shopuda</span>
            <span className="text-xs text-gray-500 dark:text-gray-400">온라인 쇼핑몰</span>
          </div>
        </div>
        
        {/* Mobile close button */}
        <button
          onClick={onClose}
          className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 lg:hidden transition-colors"
        >
          <XMarkIcon className="w-5 h-5" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 mt-8 px-4 space-y-2 overflow-y-auto">
        {navigation.map((item) => {
          const Icon = item.icon
          return (
            <Link
              key={item.name}
              to={item.href}
              onClick={() => onClose()}
              className={`
                group flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ease-in-out
                ${isActive(item.href)
                  ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 shadow-sm border-r-2 border-blue-500'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white'
                }
              `}
            >
              <Icon className={`
                w-5 h-5 transition-colors
                ${isActive(item.href) 
                  ? 'text-blue-600 dark:text-blue-400' 
                  : 'text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-300'
                }
              `} />
              <span className="font-medium">{item.name}</span>
              
              {/* Active indicator */}
              {isActive(item.href) && (
                <div className="ml-auto w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              )}
            </Link>
          )
        })}
      </nav>

      {/* Quick Actions */}
      <div className="px-4 py-4 border-t border-gray-200 dark:border-gray-700">
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            빠른 메뉴
          </h3>
          <div className="grid grid-cols-2 gap-2">
            <button className="flex flex-col items-center p-3 rounded-lg bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
              <ShoppingCartIcon className="w-5 h-5 text-gray-600 dark:text-gray-400 mb-1" />
              <span className="text-xs text-gray-600 dark:text-gray-400">장바구니</span>
            </button>
            <button className="flex flex-col items-center p-3 rounded-lg bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
              <HeartIcon className="w-5 h-5 text-gray-600 dark:text-gray-400 mb-1" />
              <span className="text-xs text-gray-600 dark:text-gray-400">찜목록</span>
            </button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>v1.0.0</span>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span>온라인</span>
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 lg:hidden"
          onClick={onClose}
        >
          <div className="absolute inset-0 bg-gray-600 opacity-75" />
        </div>
      )}

      {/* Mobile sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300 ease-in-out lg:hidden
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <SidebarContent />
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:z-40 lg:w-64 lg:flex lg:flex-col">
        <SidebarContent />
      </div>
    </>
  )
}

export default Sidebar