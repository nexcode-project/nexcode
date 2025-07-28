import { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import {
  Key,
  Plus,
  Trash2,
  Activity,
  Clock,
  Eye,
  EyeOff,
  Copy,
  Shield
} from 'lucide-react';
import { api } from '@/lib/api';
import type { APIKey, TokenScope } from '@/types/api';

interface ScopesResponse {
  scopes: TokenScope[];
  default_scopes: string[];
}

export default function TokensTab() {
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
    loadTokens();
    loadAvailableScopes();
  }, []);

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

  return (
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
  );
} 