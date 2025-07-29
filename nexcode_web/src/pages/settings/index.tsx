import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { ArrowLeft, User, Key, Building2 } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import SettingsNavigation from './SettingsNavigation';
import ProfileTab from './ProfileTab';
import TokensTab from './TokensTab';
import OrganizationsTab from './OrganizationsTab';

export default function UserSettings() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [activeTab, setActiveTab] = useState('profile');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    // 从URL参数获取要显示的标签页
    const tab = router.query.tab as string;
    if (tab && (tab === 'profile' || tab === 'tokens' || tab === 'organizations')) {
      setActiveTab(tab);
    }
  }, [isAuthenticated, router.query.tab]);

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    // 更新URL参数
    router.push(`/settings?tab=${tab}`, undefined, { shallow: true });
  };

  const handleBack = () => {
    router.push('/');
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <>
      <Head>
        <title>用户设置 - NexCode</title>
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* 主要内容区域 */}
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          {/* 头部 */}
          <div className="mb-8">
            <div className="flex items-center space-x-4 mb-4">
              <button
                onClick={handleBack}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">用户设置</h1>
                <p className="text-lg text-gray-600 mt-1">管理您的账户信息和Personal Access Tokens</p>
              </div>
            </div>
          </div>

          {/* 主要内容区域 */}
          <div className="flex gap-8">
            {/* 左侧导航 */}
            <SettingsNavigation activeTab={activeTab} onTabChange={handleTabChange} />

            {/* 右侧内容区域 */}
            <div className="flex-1">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200">
                <div className="p-8">
                  {activeTab === 'profile' && user && (
                    <ProfileTab user={{
                      ...user,
                      created_at: user.created_at || '',    
                      updated_at: user.updated_at || ''
                    }} />
                  )}
                  {activeTab === 'tokens' && <TokensTab />}
                  {activeTab === 'organizations' && <OrganizationsTab />}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
} 