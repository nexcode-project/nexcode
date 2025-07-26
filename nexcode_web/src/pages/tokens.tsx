import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import { api } from '../lib/api';
import { useAuthStore } from '../store/authStore';

interface APIKey {
  id: number;
  key_name: string;
  key_prefix: string;
  scopes: string[];
  rate_limit: number;
  usage_count: number;
  last_used: string | null;
  is_active: boolean;
  created_at: string;
  expires_at: string | null;
}

interface TokenScope {
  value: string;
  label: string;
  description: string;
}

interface ScopesResponse {
  scopes: TokenScope[];
  default_scopes: string[];
}

const PersonalAccessTokens: React.FC = () => {
  const [tokens, setTokens] = useState<APIKey[]>([]);
  const [availableScopes, setAvailableScopes] = useState<TokenScope[]>([]);
  const [defaultScopes, setDefaultScopes] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newToken, setNewToken] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    key_name: '',
    scopes: [] as string[],
    rate_limit: 1000,
    expires_at: ''
  });
  
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    
    loadTokens();
    loadAvailableScopes();
  }, [isAuthenticated]);

  const loadTokens = async () => {
    try {
      const response = await api.get('/v1/users/me/api-keys');
      setTokens(response.data);
    } catch (error) {
      console.error('Failed to load tokens:', error);
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
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateToken = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const createData = {
        ...formData,
        expires_at: formData.expires_at || null
      };
      
      const response = await api.post('/v1/users/me/api-keys', createData);
      setNewToken(response.data.token);
      setShowCreateForm(false);
      setFormData({
        key_name: '',
        scopes: defaultScopes,
        rate_limit: 1000,
        expires_at: ''
      });
      loadTokens();
    } catch (error) {
      console.error('Failed to create token:', error);
      alert('创建Token失败，请重试');
    }
  };

  const handleDeleteToken = async (tokenId: number) => {
    if (!confirm('确定要删除这个Token吗？此操作无法撤销。')) {
      return;
    }
    
    try {
      await api.delete(`/v1/users/me/api-keys/${tokenId}`);
      loadTokens();
    } catch (error) {
      console.error('Failed to delete token:', error);
      alert('删除Token失败，请重试');
    }
  };

  const handleScopeChange = (scope: string, checked: boolean) => {
    setFormData(prev => ({
      ...prev,
      scopes: checked 
        ? [...prev.scopes, scope]
        : prev.scopes.filter(s => s !== scope)
    }));
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Token已复制到剪贴板');
  };

  if (isLoading) {
    return (
      <Layout>
        <div className="container mx-auto px-4 py-8">
          <div className="text-center">加载中...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Personal Access Tokens</h1>
          <p className="text-gray-600">
            Personal access tokens用于CLI工具和API访问。它们类似于密码，请妥善保管。
          </p>
        </div>

        {/* 新Token显示 */}
        {newToken && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <h3 className="text-lg font-semibold text-green-800 mb-2">
              Token创建成功！
            </h3>
            <p className="text-green-700 mb-3">
              请立即复制您的新personal access token。出于安全考虑，它不会再次显示。
            </p>
            <div className="bg-gray-100 p-3 rounded font-mono text-sm break-all">
              {newToken}
            </div>
            <div className="mt-3 flex gap-2">
              <button
                onClick={() => copyToClipboard(newToken)}
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
              >
                复制Token
              </button>
              <button
                onClick={() => setNewToken(null)}
                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
              >
                完成
              </button>
            </div>
          </div>
        )}

        {/* 创建新Token按钮 */}
        <div className="mb-6">
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            生成新Token
          </button>
        </div>

        {/* 创建Token表单 */}
        {showCreateForm && (
          <div className="bg-white border rounded-lg p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">创建新的Personal Access Token</h3>
            
            <form onSubmit={handleCreateToken}>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">
                  Token名称 *
                </label>
                <input
                  type="text"
                  value={formData.key_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, key_name: e.target.value }))}
                  className="w-full p-2 border rounded"
                  placeholder="例如：我的CLI工具"
                  required
                />
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">
                  过期时间（可选）
                </label>
                <input
                  type="datetime-local"
                  value={formData.expires_at}
                  onChange={(e) => setFormData(prev => ({ ...prev, expires_at: e.target.value }))}
                  className="w-full p-2 border rounded"
                />
                <small className="text-gray-500">留空表示永不过期</small>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">
                  速率限制（每小时）
                </label>
                <input
                  type="number"
                  value={formData.rate_limit}
                  onChange={(e) => setFormData(prev => ({ ...prev, rate_limit: parseInt(e.target.value) }))}
                  className="w-full p-2 border rounded"
                  min="1"
                  max="10000"
                />
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium mb-3">
                  权限范围
                </label>
                <div className="space-y-2">
                  {availableScopes.map((scope) => (
                    <label key={scope.value} className="flex items-start gap-2">
                      <input
                        type="checkbox"
                        checked={formData.scopes.includes(scope.value)}
                        onChange={(e) => handleScopeChange(scope.value, e.target.checked)}
                        className="mt-1"
                      />
                      <div>
                        <div className="font-medium">{scope.value}</div>
                        <div className="text-sm text-gray-600">{scope.description}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  type="submit"
                  className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                >
                  生成Token
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
                >
                  取消
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Token列表 */}
        <div className="bg-white border rounded-lg">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-semibold">现有的Personal Access Tokens</h3>
          </div>
          
          <div className="divide-y">
            {tokens.length === 0 ? (
              <div className="px-6 py-8 text-center text-gray-500">
                您还没有任何personal access tokens。
              </div>
            ) : (
              tokens.map((token) => (
                <div key={token.id} className="px-6 py-4 flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="font-semibold">{token.key_name}</h4>
                      <span className="text-xs bg-gray-200 px-2 py-1 rounded">
                        {token.key_prefix}
                      </span>
                      {!token.is_active && (
                        <span className="text-xs bg-red-200 text-red-800 px-2 py-1 rounded">
                          已撤销
                        </span>
                      )}
                    </div>
                    
                    <div className="text-sm text-gray-600 space-y-1">
                      <div>权限: {token.scopes?.join(', ') || '无'}</div>
                      <div>使用次数: {token.usage_count}</div>
                      <div>最后使用: {token.last_used ? new Date(token.last_used).toLocaleString() : '从未使用'}</div>
                      <div>创建时间: {new Date(token.created_at).toLocaleString()}</div>
                      {token.expires_at && (
                        <div>过期时间: {new Date(token.expires_at).toLocaleString()}</div>
                      )}
                    </div>
                  </div>
                  
                  <div>
                    <button
                      onClick={() => handleDeleteToken(token.id)}
                      className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                    >
                      删除
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 使用说明 */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-800 mb-2">如何使用</h3>
          <div className="text-blue-700 space-y-2">
            <p>1. 在CLI工具中配置Token：</p>
            <code className="block bg-blue-100 p-2 rounded text-sm">
              nexcode config set auth.token "your_token_here"
            </code>
            <p>2. 或者设置环境变量：</p>
            <code className="block bg-blue-100 p-2 rounded text-sm">
              export NEXCODE_TOKEN="your_token_here"
            </code>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default PersonalAccessTokens; 