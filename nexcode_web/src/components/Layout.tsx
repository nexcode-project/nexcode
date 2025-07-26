import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuthStore } from '../store/authStore';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, isAuthenticated, logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

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
                  <Link 
                    href="/tokens" 
                    className={`text-gray-700 hover:text-blue-600 ${
                      router.pathname === '/tokens' ? 'text-blue-600 font-medium' : ''
                    }`}
                  >
                    Personal Access Tokens
                  </Link>
                </div>
              )}
            </div>

            <div className="flex items-center space-x-4">
              {isAuthenticated ? (
                <div className="flex items-center space-x-3">
                  <span className="text-gray-700">
                    欢迎, {user?.username || user?.full_name}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                  >
                    登出
                  </button>
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
