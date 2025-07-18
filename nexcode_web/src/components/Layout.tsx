import React from 'react';
import { useRouter } from 'next/router';
import { useAuthStore } from '@/store/authStore';
import { FileText, MessageSquare, LogOut, User } from 'lucide-react';

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push('/');
  };

  if (!isAuthenticated) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 导航栏 */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-8">
              <div className="flex items-center">
                <img src="/logo.png" alt="NexCode" className="h-8 w-auto" />
                <span className="ml-2 text-xl font-bold text-gray-900">NexCode</span>
              </div>

              <div className="flex space-x-4">
                <button
                  onClick={() => router.push('/chat')}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium ${router.pathname === '/chat'
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                >
                  <MessageSquare className="h-4 w-4" />
                  <span>AI 对话</span>
                </button>

                <button
                  onClick={() => router.push('/documents')}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium ${router.pathname.startsWith('/documents')
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                >
                  <FileText className="h-4 w-4" />
                  <span>协作文档</span>
                </button>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <User className="h-5 w-5 text-gray-400" />
                <span className="text-sm text-gray-700">{user?.username}</span>
              </div>

              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 px-3 py-2 rounded-lg hover:bg-gray-100"
              >
                <LogOut className="h-4 w-4" />
                <span>退出</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* 主要内容 */}
      <main>{children}</main>
    </div>
  );
}
