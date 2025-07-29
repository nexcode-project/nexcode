import { useState, useEffect, useRef } from 'react';
import { toast } from 'react-hot-toast';
import {
  Building2,
  Plus,
  Users,
  Settings,
  Trash2,
  UserPlus,
  Crown,
  Shield,
  Eye,
  EyeOff,
  Search,
  X
} from 'lucide-react';
import { api } from '@/lib/api';

interface Organization {
  id: number;
  name: string;
  description: string | null;
  avatar_url: string | null;
  owner_id: number;
  is_public: boolean;
  allow_member_invite: boolean;
  require_admin_approval: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface OrganizationMember {
  id: number;
  organization_id: number;
  user_id: number;
  role: string;
  joined_at: string;
  invited_by: number | null;
  is_active: boolean;
  username: string;
  email: string;
  full_name: string | null;
}

interface UserSearchResult {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
}

export default function OrganizationsTab() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [showMembers, setShowMembers] = useState(false);
  const [showAddMember, setShowAddMember] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<UserSearchResult[]>([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const searchTimeoutRef = useRef<NodeJS.Timeout>();
  const searchInputRef = useRef<HTMLInputElement>(null);
  const searchContainerRef = useRef<HTMLDivElement>(null);
  
  // 分页相关状态
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [totalMembers, setTotalMembers] = useState(0);
  const [membersLoading, setMembersLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_public: false,
    allow_member_invite: true,
    require_admin_approval: false
  });
  const [memberFormData, setMemberFormData] = useState({
    user_email: '',
    role: 'member'
  });
  const [selectedUsers, setSelectedUsers] = useState<UserSearchResult[]>([]);

  useEffect(() => {
    loadOrganizations();
  }, []);

  // 点击外部关闭搜索结果
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
        setShowSearchResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // 用户搜索功能
  const searchUsers = async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      setShowSearchResults(false);
      return;
    }

    if (!selectedOrg) {
      setSearchResults([]);
      setShowSearchResults(false);
      return;
    }

    setSearchLoading(true);
    try {
      const response = await api.get('/v1/users/search', {
        params: { 
          q: query, 
          limit: 20  // 增加搜索数量，因为前端会过滤
        }
      });
      
      // 前端过滤：排除已经在组织中的用户
      const existingMemberIds = new Set(members.map(member => member.user_id));
      const filteredResults = response.data.filter((user: UserSearchResult) => 
        !existingMemberIds.has(user.id)
      );
      
      setSearchResults(filteredResults);
      setShowSearchResults(true);
    } catch (error) {
      console.error('Failed to search users:', error);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSearchInputChange = (value: string) => {
    setSearchQuery(value);
    
    // 清除之前的定时器
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    // 设置新的定时器，防抖搜索
    searchTimeoutRef.current = setTimeout(() => {
      searchUsers(value);
    }, 300);
  };

  const selectUser = (user: UserSearchResult) => {
    console.log('选择用户:', user);
    // 检查用户是否已经被选择
    const isAlreadySelected = selectedUsers.some(selectedUser => selectedUser.id === user.id);
    if (isAlreadySelected) {
      toast.error('该用户已被选择');
      return;
    }
    
    setSelectedUsers(prev => [...prev, user]);
    setSearchQuery('');
    setShowSearchResults(false);
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
    setShowSearchResults(false);
  };

  const removeSelectedUser = (userId: number) => {
    setSelectedUsers(prev => prev.filter(user => user.id !== userId));
  };

  const clearAllSelectedUsers = () => {
    setSelectedUsers([]);
  };

  const loadOrganizations = async () => {
    try {
      const response = await api.get('/v1/organizations');
      setOrganizations(response.data);
    } catch (error) {
      console.error('Failed to load organizations:', error);
      toast.error('加载组织列表失败');
    }
  };

  const handleCreateOrganization = async () => {
    if (!formData.name.trim()) {
      toast.error('请输入组织名称');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/v1/organizations', formData);
      setOrganizations(prev => [response.data, ...prev]);
      setShowCreateForm(false);
      setFormData({
        name: '',
        description: '',
        is_public: false,
        allow_member_invite: true,
        require_admin_approval: false
      });
      toast.success('组织创建成功');
    } catch (error) {
      console.error('Failed to create organization:', error);
      toast.error('创建组织失败');
    } finally {
      setLoading(false);
    }
  };

  const loadOrganizationMembers = async (orgId: number, page: number = 1, size: number = 10) => {
    setMembersLoading(true);
    try {
      const response = await api.get(`/v1/organizations/${orgId}/members`, {
        params: {
          skip: (page - 1) * size,
          limit: size
        }
      });
      setMembers(response.data.members || response.data);
      setTotalMembers(response.data.total || response.data.length);
      setCurrentPage(page);
    } catch (error) {
      console.error('Failed to load members:', error);
      toast.error('加载成员列表失败');
    } finally {
      setMembersLoading(false);
    }
  };

  const handleAddMembers = async () => {
    if (selectedUsers.length === 0) {
      toast.error('请至少选择一个用户');
      return;
    }

    if (!selectedOrg) return;

    setLoading(true);
    try {
      // 批量添加用户
      const promises = selectedUsers.map(user => 
        api.post(`/v1/organizations/${selectedOrg.id}/members`, {
          user_email: user.email,
          role: memberFormData.role
        })
      );
      
      await Promise.all(promises);
      loadOrganizationMembers(selectedOrg.id, currentPage, pageSize);
      setShowAddMember(false);
      setSelectedUsers([]);
      setMemberFormData({
        user_email: '',
        role: 'member'
      });
      toast.success(`成功添加 ${selectedUsers.length} 个成员`);
    } catch (error) {
      console.error('Failed to add members:', error);
      toast.error('添加成员失败');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateMemberRole = async (memberId: number, newRole: string) => {
    if (!selectedOrg) return;

    try {
      await api.put(`/v1/organizations/${selectedOrg.id}/members/${memberId}`, {
        role: newRole
      });
      loadOrganizationMembers(selectedOrg.id, currentPage, pageSize);
      toast.success('成员角色更新成功');
    } catch (error) {
      console.error('Failed to update member role:', error);
      toast.error('更新成员角色失败');
    }
  };

  const handleRemoveMember = async (memberId: number) => {
    if (!selectedOrg) return;

    if (!confirm('确定要移除这个成员吗？')) {
      return;
    }

    try {
      await api.delete(`/v1/organizations/${selectedOrg.id}/members/${memberId}`);
      loadOrganizationMembers(selectedOrg.id, currentPage, pageSize);
      toast.success('成员移除成功');
    } catch (error) {
      console.error('Failed to remove member:', error);
      toast.error('移除成员失败');
    }
  };

  const openMembersModal = (org: Organization) => {
    setSelectedOrg(org);
    setShowMembers(true);
    setCurrentPage(1);
    loadOrganizationMembers(org.id, 1, pageSize);
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            组织管理
          </h2>
          <p className="text-lg text-gray-600">
            创建和管理您的组织，实现文档的权限管理
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="flex items-center space-x-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-3 rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 shadow-lg hover:shadow-xl"
        >
          <Plus className="w-5 h-5" />
          <span className="font-medium">新建组织</span>
        </button>
      </div>

      {/* 组织列表 */}
      <div className="space-y-4">
        {organizations.map((org) => (
          <div
            key={org.id}
            className="border border-gray-200 rounded-xl p-6 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-100 to-blue-200 rounded-lg flex items-center justify-center">
                    <Building2 className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h4 className="text-xl font-semibold text-gray-900">
                      {org.name}
                    </h4>
                    <p className="text-gray-500">
                      {org.description || '暂无描述'}
                    </p>
                  </div>
                </div>
                <div className="mt-4 flex items-center space-x-6 text-sm text-gray-500">
                  <div className="flex items-center space-x-2">
                    {org.is_public ? (
                      <Eye className="w-4 h-4" />
                    ) : (
                      <EyeOff className="w-4 h-4" />
                    )}
                    <span>{org.is_public ? '公开组织' : '私有组织'}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Users className="w-4 h-4" />
                    <span>成员管理</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Crown className="w-4 h-4" />
                    <span>创建于 {new Date(org.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => openMembersModal(org)}
                  className="p-3 text-blue-500 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
                  title="管理成员"
                >
                  <Users className="w-5 h-5" />
                </button>
                <button
                  className="p-3 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  title="组织设置"
                >
                  <Settings className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        ))}

        {organizations.length === 0 && (
          <div className="text-center py-12">
            <div className="w-24 h-24 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center mx-auto mb-6">
              <Building2 className="w-12 h-12 text-gray-400" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">暂无组织</h3>
            <p className="text-gray-500 mb-6">点击"新建组织"创建您的第一个组织</p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="inline-flex items-center space-x-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>创建第一个组织</span>
            </button>
          </div>
        )}
      </div>

      {/* 创建组织模态框 */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-8 w-full max-w-lg mx-4 shadow-2xl">
            <h3 className="text-2xl font-bold text-gray-900 mb-6">
              创建组织
            </h3>

            <div className="space-y-6">
              <div>
                <label className="block text-lg font-medium text-gray-700 mb-3">
                  组织名称
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="例如: 我的团队"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                />
              </div>

              <div>
                <label className="block text-lg font-medium text-gray-700 mb-3">
                  组织描述
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="描述您的组织..."
                  rows={3}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                />
              </div>

              <div className="space-y-4">
                <label className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_public}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_public: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 w-5 h-5"
                  />
                  <span className="ml-3 text-gray-700">
                    <span className="font-medium">公开组织</span> - 其他用户可以搜索并申请加入
                  </span>
                </label>

                <label className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.allow_member_invite}
                    onChange={(e) => setFormData(prev => ({ ...prev, allow_member_invite: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 w-5 h-5"
                  />
                  <span className="ml-3 text-gray-700">
                    <span className="font-medium">允许成员邀请</span> - 成员可以邀请其他用户加入
                  </span>
                </label>

                <label className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.require_admin_approval}
                    onChange={(e) => setFormData(prev => ({ ...prev, require_admin_approval: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 w-5 h-5"
                  />
                  <span className="ml-3 text-gray-700">
                    <span className="font-medium">需要管理员审批</span> - 新成员加入需要管理员审批
                  </span>
                </label>
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
                onClick={handleCreateOrganization}
                disabled={loading || !formData.name.trim()}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-500 transition-all duration-200 font-medium"
              >
                {loading ? '创建中...' : '创建组织'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 成员管理模态框 */}
      {showMembers && selectedOrg && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-8 w-full max-w-4xl mx-4 shadow-2xl max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-bold text-gray-900">
                {selectedOrg.name} - 成员管理
              </h3>
              <button
                onClick={() => setShowMembers(false)}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <span className="sr-only">关闭</span>
                ×
              </button>
            </div>

            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-4">
                <p className="text-gray-600">
                  管理组织成员和权限
                </p>
                <div className="flex items-center space-x-2">
                  <label className="text-sm text-gray-600">每页显示:</label>
                  <select
                    value={pageSize}
                    onChange={(e) => {
                      const newSize = parseInt(e.target.value);
                      setPageSize(newSize);
                      setCurrentPage(1);
                      loadOrganizationMembers(selectedOrg.id, 1, newSize);
                    }}
                    className="px-2 py-1 border border-gray-300 rounded text-sm"
                  >
                    <option value={5}>5</option>
                    <option value={10}>10</option>
                    <option value={20}>20</option>
                    <option value={50}>50</option>
                  </select>
                </div>
              </div>
              <button
                onClick={() => setShowAddMember(true)}
                className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                <UserPlus className="w-4 h-4" />
                <span>添加成员</span>
              </button>
            </div>

            {/* 成员列表表格 */}
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              {membersLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-2 text-gray-600">加载中...</span>
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            用户
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            角色
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            加入时间
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            操作
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {members.map((member) => (
                          <tr key={member.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="w-10 h-10 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center">
                                  <span className="text-sm font-medium text-gray-600">
                                    {member.username.charAt(0).toUpperCase()}
                                  </span>
                                </div>
                                <div className="ml-4">
                                  <div className="text-sm font-medium text-gray-900">
                                    {member.full_name || member.username}
                                  </div>
                                  <div className="text-sm text-gray-500">
                                    {member.email}
                                  </div>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center space-x-2">
                                {member.role === 'owner' && <Crown className="w-4 h-4 text-yellow-500" />}
                                {member.role === 'admin' && <Shield className="w-4 h-4 text-blue-500" />}
                                <span className="text-sm font-medium text-gray-700 capitalize">
                                  {member.role}
                                </span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {new Date(member.joined_at).toLocaleDateString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                              <div className="flex items-center space-x-2">
                                <select
                                  value={member.role}
                                  onChange={(e) => handleUpdateMemberRole(member.id, e.target.value)}
                                  className="px-2 py-1 border border-gray-300 rounded text-xs"
                                  disabled={member.role === 'owner'}
                                >
                                  <option value="member">成员</option>
                                  <option value="admin">管理员</option>
                                  <option value="owner">所有者</option>
                                </select>
                                <button
                                  onClick={() => handleRemoveMember(member.id)}
                                  disabled={member.role === 'owner'}
                                  className="p-1 text-red-500 hover:text-red-700 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
                                  title="移除成员"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {members.length === 0 && (
                    <div className="text-center py-8">
                      <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500">暂无成员</p>
                    </div>
                  )}

                  {/* 分页组件 */}
                  {totalMembers > pageSize && (
                    <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
                      <div className="flex-1 flex justify-between sm:hidden">
                        <button
                          onClick={() => loadOrganizationMembers(selectedOrg.id, currentPage - 1, pageSize)}
                          disabled={currentPage === 1}
                          className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          上一页
                        </button>
                        <button
                          onClick={() => loadOrganizationMembers(selectedOrg.id, currentPage + 1, pageSize)}
                          disabled={currentPage >= Math.ceil(totalMembers / pageSize)}
                          className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          下一页
                        </button>
                      </div>
                      <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                        <div>
                          <p className="text-sm text-gray-700">
                            显示第 <span className="font-medium">{(currentPage - 1) * pageSize + 1}</span> 到{' '}
                            <span className="font-medium">
                              {Math.min(currentPage * pageSize, totalMembers)}
                            </span>{' '}
                            条，共 <span className="font-medium">{totalMembers}</span> 条记录
                          </p>
                        </div>
                        <div>
                          <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                            <button
                              onClick={() => loadOrganizationMembers(selectedOrg.id, currentPage - 1, pageSize)}
                              disabled={currentPage === 1}
                              className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              <span className="sr-only">上一页</span>
                              ←
                            </button>
                            {Array.from({ length: Math.min(5, Math.ceil(totalMembers / pageSize)) }, (_, i) => {
                              const page = i + 1;
                              return (
                                <button
                                  key={page}
                                  onClick={() => loadOrganizationMembers(selectedOrg.id, page, pageSize)}
                                  className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                                    currentPage === page
                                      ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                                      : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                                  }`}
                                >
                                  {page}
                                </button>
                              );
                            })}
                            <button
                              onClick={() => loadOrganizationMembers(selectedOrg.id, currentPage + 1, pageSize)}
                              disabled={currentPage >= Math.ceil(totalMembers / pageSize)}
                              className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              <span className="sr-only">下一页</span>
                              →
                            </button>
                          </nav>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* 添加成员模态框 */}
            {showAddMember && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-xl p-8 w-full max-w-lg mx-4 shadow-2xl max-h-[80vh] overflow-y-auto">
                  <h4 className="text-xl font-bold text-gray-900 mb-6">
                    添加成员
                  </h4>

                  <div className="space-y-4">
                    <div className="relative" ref={searchContainerRef}>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        搜索用户
                      </label>
                      <div className="relative">
                        <input
                          ref={searchInputRef}
                          type="text"
                          value={searchQuery}
                          onChange={(e) => handleSearchInputChange(e.target.value)}
                          placeholder="输入用户名、邮箱或姓名搜索..."
                          className="w-full px-3 py-2 pl-10 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                        <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                        {searchQuery && (
                          <button
                            onClick={clearSearch}
                            className="absolute right-3 top-2.5 w-4 h-4 text-gray-400 hover:text-gray-600"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        )}
                        
                        {/* 搜索结果下拉框 */}
                        {showSearchResults && (
                          <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-xl max-h-60 overflow-y-auto top-full">
                            {searchLoading ? (
                              <div className="p-4 text-center text-gray-500">
                                搜索中...
                              </div>
                            ) : searchResults.length > 0 ? (
                              searchResults.map((user) => (
                                <button
                                  key={user.id}
                                  onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    selectUser(user);
                                  }}
                                  className="w-full p-3 text-left hover:bg-gray-50 border-b border-gray-100 last:border-b-0 flex items-center space-x-3"
                                >
                                  <div className="w-8 h-8 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full flex items-center justify-center">
                                    <span className="text-sm font-medium text-blue-600">
                                      {user.username.charAt(0).toUpperCase()}
                                    </span>
                                  </div>
                                  <div className="flex-1">
                                    <div className="font-medium text-gray-900">
                                      {user.full_name || user.username}
                                    </div>
                                    <div className="text-sm text-gray-500">
                                      @{user.username} • {user.email}
                                    </div>
                                  </div>
                                </button>
                              ))
                            ) : searchQuery.trim() ? (
                              <div className="p-4 text-center text-gray-500">
                                未找到匹配的用户
                              </div>
                            ) : null}
                          </div>
                        )}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        角色
                      </label>
                      <select
                        value={memberFormData.role}
                        onChange={(e) => setMemberFormData(prev => ({ ...prev, role: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="member">成员</option>
                        <option value="admin">管理员</option>
                      </select>
                    </div>

                    {/* 已选择的用户列表 */}
                    {selectedUsers.length > 0 && (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <label className="block text-sm font-medium text-gray-700">
                            已选择的用户 ({selectedUsers.length})
                          </label>
                          <button
                            onClick={clearAllSelectedUsers}
                            className="text-sm text-red-600 hover:text-red-800 hover:bg-red-50 px-2 py-1 rounded"
                          >
                            清空全部
                          </button>
                        </div>
                        <div className="max-h-40 overflow-y-auto space-y-2">
                          {selectedUsers.map((user) => (
                            <div
                              key={user.id}
                              className="flex items-center justify-between p-3 bg-gray-50 border border-gray-200 rounded-lg"
                            >
                              <div className="flex items-center space-x-3">
                                <div className="w-8 h-8 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full flex items-center justify-center">
                                  <span className="text-sm font-medium text-blue-600">
                                    {user.username.charAt(0).toUpperCase()}
                                  </span>
                                </div>
                                <div>
                                  <div className="font-medium text-gray-900">
                                    {user.full_name || user.username}
                                  </div>
                                  <div className="text-sm text-gray-500">
                                    @{user.username} • {user.email}
                                  </div>
                                </div>
                              </div>
                              <button
                                onClick={() => removeSelectedUser(user.id)}
                                className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                                title="移除用户"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-end space-x-4 mt-6">
                    <button
                      onClick={() => {
                        setShowAddMember(false);
                        clearSearch();
                        setSelectedUsers([]);
                      }}
                      className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      取消
                    </button>
                    <button
                      onClick={handleAddMembers}
                      disabled={selectedUsers.length === 0}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                    >
                      {loading ? '添加中...' : `添加 ${selectedUsers.length} 个用户`}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
} 