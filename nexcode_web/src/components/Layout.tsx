import React from 'react';
import { useAuthStore } from '@/store/authStore';
import { LogOut, MessageSquare, User, Settings } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout, isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-xl font-bold text-primary-600">NexCode</h1>
              </div>
              <div className="hidden md:block ml-10">
                <div className="flex space-x-8">
                  <a
                    href="/chat"
                    className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium flex items-center"
                  >
                    <MessageSquare className="w-4 h-4 mr-2" />
                    智能对话
                  </a>
                  <a
                    href="/tools"
                    className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium flex items-center"
                  >
                    <Settings className="w-4 h-4 mr-2" />
                    开发工具
                  </a>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <User className="w-5 h-5 text-gray-400" />
                <span className="text-sm text-gray-700">{user?.full_name || user?.username}</span>
              </div>
              <button
                onClick={logout}
                className="text-gray-400 hover:text-gray-600 p-2 rounded-md"
                title="退出登录"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
} 