import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { toast } from 'react-hot-toast';
import { 
  User, 
  Key, 
  Settings, 
  Save, 
  Eye, 
  EyeOff, 
  Copy, 
  Trash2, 
  Plus,
  ArrowLeft,
  Shield,
  Clock,
  Activity
} from 'lucide-react';
import { api } from '@/lib/api';
import { useAuthStore } from '@/store/authStore';

// 导入类型
import type { APIKey, TokenScope } from '@/types/api';

interface ScopesResponse {
  scopes: TokenScope[];
  default_scopes: string[];
}

export default function UserSettings() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [tokens, setTokens] = useState<APIKey[]>([]);
  const [availableScopes, setAvailableScopes] = useState<TokenScope[]>([]);
  const [defaultScopes, setDefaultScopes] = useState<string[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newToken, setNewToken] = useState<string | null>(null);
  const [showToken, setShowToken] = useState(false);
  const [formData, setFormData] = useState({
    key_name: '',
    scopes: [] as string[],
    rate_limit: 1000,
    expires_at: ''
  });

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    
    // 从URL参数获取要显示的标签页
    const tab = router.query.tab as string;
    if (tab && (tab === 'profile' || tab === 'tokens')) {
      setActiveTab(tab);
    }
    
    if (activeTab === 'tokens') {
      loadTokens();
      loadAvailableScopes();
    }
  }, [isAuthenticated, activeTab, router.query.tab]);

  const loadTokens = async () => {
    try {
      const response = await api.get('/v1/users/me/api-keys');
      setTokens(response.data);
    } catch (error) {
      console.error('Failed to load tokens:', error);
      toast.error('加载Personal Access Tokens失败');
    }
  };

  const loadAvailableScopes = async () => {
    try {
      const response = await api.get<ScopesResponse>('/v1/users/me/api-keys/scopes');
      setAvailableScopes(response.data.scopes);
      setDefaultScopes(response.data.default_scopes);
      setFormData(prev => ({ ...prev, scopes: response.data.default_scopes }));
    } catch (error) {
      console.error('Failed to load scopes:', error);
      toast.error('加载权限范围失败');
    }
  };

  const handleCreateToken = async () => {
    if (!formData.key_name.trim()) {
      toast.error('请输入Token名称');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/v1/users/me/api-keys', {
        key_name: formData.key_name,
        scopes: formData.scopes,
        rate_limit: formData.rate_limit,
        expires_at: formData.expires_at || null
      });
      
      setNewToken(response.data.token);
      setShowToken(true);
      setShowCreateForm(false);
      setFormData({
        key_name: '',
        scopes: defaultScopes,
        rate_limit: 1000,
        expires_at: ''
      });
      loadTokens();
      toast.success('Personal Access Token创建成功');
    } catch (error) {
      console.error('Failed to create token:', error);
      toast.error('创建Token失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteToken = async (tokenId: number) => {
    if (!confirm('确定要删除这个Token吗？删除后无法恢复。')) {
      return;
    }

    try {
      await api.delete(`/v1/users/me/api-keys/${tokenId}`);
      loadTokens();
      toast.success('Token删除成功');
    } catch (error) {
      console.error('Failed to delete token:', error);
      toast.error('删除Token失败');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('已复制到剪贴板');
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
            <div className="w-64 flex-shrink-0">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <nav className="space-y-2">
                  <button
                    onClick={() => setActiveTab('profile')}
                    className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-left transition-colors ${
                      activeTab === 'profile'
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <User className={`w-5 h-5 ${activeTab === 'profile' ? 'text-blue-600' : 'text-gray-400'}`} />
                    <span className="font-medium">个人资料</span>
                  </button>
                  <button
                    onClick={() => setActiveTab('tokens')}
                    className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-left transition-colors ${
                      activeTab === 'tokens'
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <Key className={`w-5 h-5 ${activeTab === 'tokens' ? 'text-blue-600' : 'text-gray-400'}`} />
                    <span className="font-medium">Personal Access Tokens</span>
                  </button>
                </nav>
              </div>
            </div>

            {/* 右侧内容区域 */}
            <div className="flex-1">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200">
                <div className="p-8">
                  {/* 个人资料标签页 */}
                  {activeTab === 'profile' && (
                    <div className="space-y-8">
                      <div className="flex items-center space-x-6">
                        <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full flex items-center justify-center">
                          <User className="w-10 h-10 text-blue-600" />
                        </div>
                        <div>
                          <h2 className="text-2xl font-bold text-gray-900">
                            {user?.full_name || user?.username}
                          </h2>
                          <p className="text-lg text-gray-500">{user?.email}</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        <div className="space-y-4">
                          <label className="block text-lg font-medium text-gray-700">
                            用户名
                          </label>
                          <input
                            type="text"
                            value={user?.username || ''}
                            disabled
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-50 text-gray-500 text-lg"
                          />
                        </div>
                        <div className="space-y-4">
                          <label className="block text-lg font-medium text-gray-700">
                            邮箱
                          </label>
                          <input
                            type="email"
                            value={user?.email || ''}
                            disabled
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-50 text-gray-500 text-lg"
                          />
                        </div>
                      </div>

                      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6">
                        <div className="flex items-start space-x-4">
                          <Shield className="w-6 h-6 text-blue-600 mt-1" />
                          <div>
                            <h4 className="text-lg font-semibold text-blue-900 mb-2">
                              账户安全提示
                            </h4>
                            <p className="text-blue-700 leading-relaxed">
                              如需修改密码或更新个人信息，请联系系统管理员。我们致力于保护您的账户安全。
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Personal Access Tokens标签页 */}
                  {activeTab === 'tokens' && (
                    <div className="space-y-8">
                      <div className="flex items-center justify-between">
                        <div>
                          <h2 className="text-2xl font-bold text-gray-900 mb-2">
                            Personal Access Tokens
                          </h2>
                          <p className="text-lg text-gray-600">
                            创建和管理用于API访问的Personal Access Tokens
                          </p>
                        </div>
                        <button
                          onClick={() => setShowCreateForm(true)}
                          className="flex items-center space-x-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-3 rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 shadow-lg hover:shadow-xl"
                        >
                          <Plus className="w-5 h-5" />
                          <span className="font-medium">新建Token</span>
                        </button>
                      </div>

                      {/* Token列表 */}
                      <div className="space-y-4">
                        {tokens.map((token) => (
                          <div
                            key={token.id}
                            className="border border-gray-200 rounded-xl p-6 hover:bg-gray-50 transition-colors"
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex-1">
                                <div className="flex items-center space-x-4">
                                  <div className="w-12 h-12 bg-gradient-to-br from-gray-100 to-gray-200 rounded-lg flex items-center justify-center">
                                    <Key className="w-6 h-6 text-gray-600" />
                                  </div>
                                  <div>
                                    <h4 className="text-xl font-semibold text-gray-900">
                                      {token.key_name}
                                    </h4>
                                    <p className="text-gray-500">
                                      创建于 {new Date(token.created_at).toLocaleDateString()}
                                    </p>
                                  </div>
                                </div>
                                <div className="mt-4 flex items-center space-x-6 text-sm text-gray-500">
                                  <div className="flex items-center space-x-2">
                                    <Activity className="w-4 h-4" />
                                    <span>使用次数: {token.usage_count || 0}</span>
                                  </div>
                                  {token.expires_at && (
                                    <div className="flex items-center space-x-2">
                                      <Clock className="w-4 h-4" />
                                      <span>
                                        过期时间: {new Date(token.expires_at).toLocaleDateString()}
                                      </span>
                                    </div>
                                  )}
                                </div>
                              </div>
                              <button
                                onClick={() => handleDeleteToken(token.id)}
                                className="p-3 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                                title="删除Token"
                              >
                                <Trash2 className="w-5 h-5" />
                              </button>
                            </div>
                          </div>
                        ))}
                        
                        {tokens.length === 0 && (
                          <div className="text-center py-12">
                            <div className="w-24 h-24 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center mx-auto mb-6">
                              <Key className="w-12 h-12 text-gray-400" />
                            </div>
                            <h3 className="text-xl font-semibold text-gray-900 mb-2">暂无Personal Access Tokens</h3>
                            <p className="text-gray-500 mb-6">点击"新建Token"创建您的第一个Token</p>
                            <button
                              onClick={() => setShowCreateForm(true)}
                              className="inline-flex items-center space-x-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
                            >
                              <Plus className="w-4 h-4" />
                              <span>创建第一个Token</span>
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 创建Token模态框 */}
        {showCreateForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-8 w-full max-w-lg mx-4 shadow-2xl">
              <h3 className="text-2xl font-bold text-gray-900 mb-6">
                创建Personal Access Token
              </h3>
              
              <div className="space-y-6">
                <div>
                  <label className="block text-lg font-medium text-gray-700 mb-3">
                    Token名称
                  </label>
                  <input
                    type="text"
                    value={formData.key_name}
                    onChange={(e) => setFormData(prev => ({ ...prev, key_name: e.target.value }))}
                    placeholder="例如: CLI工具"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                  />
                </div>

                <div>
                  <label className="block text-lg font-medium text-gray-700 mb-3">
                    权限范围
                  </label>
                  <div className="space-y-3">
                    {availableScopes.map((scope) => (
                      <label key={scope.name} className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.scopes.includes(scope.name)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFormData(prev => ({
                                ...prev,
                                scopes: [...prev.scopes, scope.name]
                              }));
                            } else {
                              setFormData(prev => ({
                                ...prev,
                                scopes: prev.scopes.filter(s => s !== scope.name)
                              }));
                            }
                          }}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 w-5 h-5"
                        />
                        <span className="ml-3 text-gray-700">
                          <span className="font-medium">{scope.name}</span> - {scope.description}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-lg font-medium text-gray-700 mb-3">
                    速率限制 (每分钟请求数)
                  </label>
                  <input
                    type="number"
                    value={formData.rate_limit}
                    onChange={(e) => setFormData(prev => ({ ...prev, rate_limit: parseInt(e.target.value) || 1000 }))}
                    min="1"
                    max="10000"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                  />
                </div>

                <div>
                  <label className="block text-lg font-medium text-gray-700 mb-3">
                    过期时间 (可选)
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.expires_at}
                    onChange={(e) => setFormData(prev => ({ ...prev, expires_at: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end space-x-4 mt-8">
                <button
                  onClick={() => setShowCreateForm(false)}
                  className="px-6 py-3 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors font-medium"
                >
                  取消
                </button>
                <button
                  onClick={handleCreateToken}
                  disabled={loading || !formData.key_name.trim()}
                  className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-500 transition-all duration-200 font-medium"
                >
                  {loading ? '创建中...' : '创建Token'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 显示新创建的Token */}
        {newToken && showToken && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-8 w-full max-w-lg mx-4 shadow-2xl">
              <h3 className="text-2xl font-bold text-gray-900 mb-6">
                Token创建成功
              </h3>
              
              <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-xl p-6 mb-6">
                <div className="flex items-start space-x-3">
                  <Shield className="w-6 h-6 text-yellow-600 mt-1" />
                  <div>
                    <h4 className="text-lg font-semibold text-yellow-900 mb-2">
                      重要提示
                    </h4>
                    <p className="text-yellow-800 leading-relaxed">
                      请立即复制并保存您的Token。出于安全考虑，Token只会显示一次。
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-lg font-medium text-gray-700 mb-3">
                    Personal Access Token
                  </label>
                  <div className="flex items-center space-x-3">
                    <input
                      type={showToken ? "text" : "password"}
                      value={newToken}
                      readOnly
                      className="flex-1 px-4 py-3 border border-gray-300 rounded-lg bg-gray-50 font-mono text-lg"
                    />
                    <button
                      onClick={() => setShowToken(!showToken)}
                      className="p-3 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      {showToken ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                    <button
                      onClick={() => copyToClipboard(newToken)}
                      className="p-3 text-blue-500 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
                    >
                      <Copy className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-end mt-8">
                <button
                  onClick={() => {
                    setNewToken(null);
                    setShowToken(false);
                  }}
                  className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 font-medium"
                >
                  确定
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
} 