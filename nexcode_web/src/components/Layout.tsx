import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuthStore } from '../store/authStore';
import { User, Settings, LogOut, ChevronDown } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, isAuthenticated, logout } = useAuthStore();
  const router = useRouter();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  // 点击外部关闭用户菜单
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <Link href="/" className="text-xl font-bold text-blue-600">
                NexCode
              </Link>
              
              {isAuthenticated && (
                <div className="flex space-x-6">
                  <Link 
                    href="/documents" 
                    className={`text-gray-700 hover:text-blue-600 ${
                      router.pathname === '/documents' ? 'text-blue-600 font-medium' : ''
                    }`}
                  >
                    文档
                  </Link>
                  <Link 
                    href="/chat" 
                    className={`text-gray-700 hover:text-blue-600 ${
                      router.pathname === '/chat' ? 'text-blue-600 font-medium' : ''
                    }`}
                  >
                    AI助手
                  </Link>
                </div>
              )}
            </div>

            <div className="flex items-center space-x-4">
              {isAuthenticated ? (
                <div className="relative" ref={userMenuRef}>
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <User className="w-4 h-4 text-blue-600" />
                    </div>
                    <span className="text-gray-700 font-medium">
                      {user?.username || user?.full_name}
                    </span>
                    <ChevronDown className={`w-4 h-4 text-gray-500 transition-transform ${
                      showUserMenu ? 'rotate-180' : ''
                    }`} />
                  </button>

                  {/* 用户下拉菜单 */}
                  {showUserMenu && (
                    <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
                      {/* 用户信息 */}
                      <div className="px-4 py-3 border-b border-gray-100">
                        <p className="text-sm font-medium text-gray-900">
                          {user?.full_name || user?.username}
                        </p>
                        <p className="text-sm text-gray-500">
                          {user?.email}
                        </p>
                      </div>

                      {/* 菜单项 */}
                      <div className="py-1">
                        <Link
                          href="/settings"
                          onClick={() => setShowUserMenu(false)}
                          className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        >
                          <User className="w-4 h-4 mr-3" />
                          Profile
                        </Link>
                        <Link
                          href="/settings?tab=tokens"
                          onClick={() => setShowUserMenu(false)}
                          className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        >
                          <Settings className="w-4 h-4 mr-3" />
                          Personal Access Tokens
                        </Link>
                        <Link
                          href="/settings?tab=organizations"
                          onClick={() => setShowUserMenu(false)}
                          className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        >
                          <Settings className="w-4 h-4 mr-3" />
                         Organizations
                        </Link>
                      </div>

                      {/* 分割线 */}
                      <div className="border-t border-gray-100 my-1"></div>

                      {/* 登出 */}
                      <button
                        onClick={() => {
                          setShowUserMenu(false);
                          handleLogout();
                        }}
                        className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        <LogOut className="w-4 h-4 mr-3" />
                        退出登录
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <Link
                  href="/login"
                  className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                >
                  登录
                </Link>
              )}
            </div>
          </div>
        </div>
      </nav>

      <main className="flex-1">
        {children}
      </main>
    </div>
  );
};

export default Layout;
