import { useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { useAuthStore } from '@/store/authStore';
import { Bot, MessageSquare, Settings, Zap } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push('/chat');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    return null; // Will redirect to /chat
  }

  return (
    <>
      <Head>
        <title>NexCode - 智能AI编程助手</title>
      </Head>
      <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        {/* Hero Section */}
        <div className="text-center">
          <div className="flex justify-center mb-8">
            <img src="/logo.png" alt="NexCode" className="h-24 w-auto" />
          </div>
          <h1 className="text-4xl sm:text-6xl font-bold text-gray-900 mb-6">
            AI 助手
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            智能代码助手，帮助您提高开发效率。支持代码生成、审查、错误诊断和智能对话。
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => router.push('/login')}
              className="bg-primary-600 hover:bg-primary-700 text-white font-semibold py-3 px-8 rounded-lg text-lg transition-colors duration-200"
            >
              开始使用
            </button>
            <button
              onClick={() => router.push('/about')}
              className="bg-white hover:bg-gray-50 text-gray-700 font-semibold py-3 px-8 rounded-lg text-lg border border-gray-300 transition-colors duration-200"
            >
              了解更多
            </button>
          </div>
        </div>

        {/* Features */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center p-6">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <MessageSquare className="w-6 h-6 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">智能对话</h3>
            <p className="text-gray-600">
              与AI助手进行自然对话，获得编程问题的即时答案和建议。
            </p>
          </div>
          
          <div className="text-center p-6">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Settings className="w-6 h-6 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">开发工具</h3>
            <p className="text-gray-600">
              代码质量检查、审查建议、提交消息生成等实用开发工具。
            </p>
          </div>
          
          <div className="text-center p-6">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Zap className="w-6 h-6 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">高效便捷</h3>
            <p className="text-gray-600">
              集成现代开发工作流，提供无缝的用户体验和高效的开发支持。
            </p>
          </div>
        </div>

        {/* Call to Action */}
        <div className="mt-24 bg-white rounded-2xl shadow-lg p-8 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            准备开始您的AI编程之旅？
          </h2>
          <p className="text-gray-600 mb-6">
            立即登录，体验智能代码助手带来的便捷开发体验。
          </p>
          <button
            onClick={() => router.push('/login')}
            className="bg-primary-600 hover:bg-primary-700 text-white font-semibold py-3 px-8 rounded-lg text-lg transition-colors duration-200"
          >
            立即登录
          </button>
        </div>
      </div>
      </div>
    </>
  );
} 