import axios from 'axios';

// API基础配置 - 直接使用localhost地址避免环境变量问题
const API_BASE_URL = 'http://localhost:8000';

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加认证token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器 - 处理错误
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token过期，清除本地存储并重定向到登录页
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 类型定义
export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
  cas_user_id?: string;
  cas_attributes?: Record<string, any>;
}

export interface CommitInfo {
  id: number;
  user_id: number;
  repository_name: string;
  commit_hash?: string;
  branch_name: string;
  files_changed: string[];
  lines_added: number;
  lines_deleted: number;
  commit_style: string;
  generated_messages: string[];
  user_selected_message?: string;
  final_commit_message?: string;
  diff_content?: string;
  context_info?: Record<string, any>;
  ai_model: string;
  processing_time: number;
  user_rating?: number;
  user_feedback?: string;
  status: string;
  created_at: string;
  updated_at: string;
  committed_at?: string;
  user?: User;
}

export interface CommitAnalytics {
  user_stats: {
    total_commits: number;
    avg_rating: number;
    common_styles: string[];
    productivity_trend: Array<{ date: string; commits: number; }>;
  };
  recent_trends: Array<{
    period: string;
    commits: number;
    avg_rating: number;
  }>;
  top_repositories: Array<{
    name: string;
    commits: number;
    avg_rating: number;
  }>;
}

export interface APIKey {
  id: number;
  name: string;
  key_hash: string;
  is_active: boolean;
  created_at: string;
  last_used?: string;
  expires_at?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  session_token: string;
}

export interface CASConfig {
  enabled: boolean;
  server_url: string;
  service_url: string;
  logout_url: string;
  attributes_mapping: Record<string, string>;
}

export interface SystemStats {
  total_users: number;
  active_users: number;
  total_commits: number;
  commits_today: number;
  avg_rating: number;
  api_calls_today: number;
}

// Auth API
export const authAPI = {
  // 密码登录
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const response = await apiClient.post('/v1/auth/login', {
      username,
      password
    });
    return response.data;
  },

  // CAS登录URL
  getCASLoginURL: async (): Promise<{ login_url: string }> => {
    const response = await apiClient.get('/v1/auth/cas/login');
    return response.data;
  },

  // CAS ticket验证
  verifyCASTicket: async (ticket: string, serviceUrl: string): Promise<LoginResponse> => {
    const response = await apiClient.post('/v1/auth/cas/verify', {
      cas_ticket: ticket,
      service_url: serviceUrl
    });
    return response.data;
  },

  // 认证状态检查
  getAuthStatus: async (): Promise<{ authenticated: boolean; user?: User }> => {
    const response = await apiClient.get('/v1/auth/status');
    return response.data;
  },

  // 登出
  logout: async (): Promise<void> => {
    await apiClient.post('/v1/auth/logout');
  }
};

// Users API
export const usersAPI = {
  // 获取所有用户(管理员)
  getAllUsers: async (skip = 0, limit = 100): Promise<User[]> => {
    const response = await apiClient.get(`/v1/users/admin/all?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // 搜索用户
  searchUsers: async (query: string): Promise<User[]> => {
    const response = await apiClient.get(`/v1/users/admin/search?query=${encodeURIComponent(query)}`);
    return response.data;
  },

  // 创建用户
  createUser: async (userData: Partial<User>): Promise<User> => {
    const response = await apiClient.post('/v1/users/admin/create', userData);
    return response.data;
  },

  // 更新用户
  updateUser: async (userId: number, userData: Partial<User>): Promise<User> => {
    const response = await apiClient.patch(`/v1/users/admin/${userId}`, userData);
    return response.data;
  },

  // 删除用户
  deleteUser: async (userId: number): Promise<void> => {
    await apiClient.delete(`/v1/users/admin/${userId}`);
  },

  // 获取用户的API密钥
  getUserAPIKeys: async (userId: number): Promise<APIKey[]> => {
    const response = await apiClient.get(`/v1/users/admin/${userId}/api-keys`);
    return response.data;
  },

  // 创建API密钥
  createAPIKey: async (userId: number, name: string): Promise<{ key: string; api_key: APIKey }> => {
    const response = await apiClient.post(`/v1/users/admin/${userId}/api-keys`, { name });
    return response.data;
  },

  // 删除API密钥
  deleteAPIKey: async (userId: number, keyId: number): Promise<void> => {
    await apiClient.delete(`/v1/users/admin/${userId}/api-keys/${keyId}`);
  }
};

// Commits API
export const commitsAPI = {
  // 获取所有提交记录(管理员)
  getAllCommits: async (params?: {
    skip?: number;
    limit?: number;
    repository_name?: string;
    username?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<{
    commits: Array<{
      id: number;
      user_id: number;
      username: string;
      repository_name: string;
      repository_url?: string;
      branch_name: string;
      commit_hash?: string;
      ai_generated_message?: string;
      final_commit_message: string;
      commit_style: string;
      lines_added: number;
      lines_deleted: number;
      files_changed: string[];
      ai_model_used?: string;
      generation_time_ms?: number;
      user_rating?: number;
      status: string;
      created_at: string;
      committed_at?: string;
    }>;
    total: number;
    skip: number;
    limit: number;
  }> => {
    const searchParams = new URLSearchParams();
    if (params?.skip !== undefined) searchParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) searchParams.append('limit', params.limit.toString());
    if (params?.repository_name) searchParams.append('repository_name', params.repository_name);
    if (params?.username) searchParams.append('username', params.username);
    if (params?.start_date) searchParams.append('start_date', params.start_date);
    if (params?.end_date) searchParams.append('end_date', params.end_date);
    
    const response = await apiClient.get(`/v1/admin/commits?${searchParams}`);
    return response.data;
  },

  // 获取提交分析数据
  getCommitAnalytics: async (days: number = 30): Promise<{
    daily_trends: Array<{ date: string; commit_count: number }>;
    user_activity: Array<{ username: string; commit_count: number }>;
    repository_activity: Array<{ repository_name: string; commit_count: number }>;
    model_usage: Array<{ model_name: string; usage_count: number }>;
    period_days: number;
    start_date: string;
    end_date: string;
  }> => {
    const response = await apiClient.get(`/v1/admin/commits/analytics?days=${days}`);
    return response.data;
  },

  // 搜索提交记录（保持原有的用户接口）
  searchCommits: async (params: {
    query?: string;
    repository_name?: string;
    commit_style?: string;
    min_rating?: number;
    skip?: number;
    limit?: number;
  }): Promise<CommitInfo[]> => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value.toString());
      }
    });
    
    const response = await apiClient.get(`/v1/commits/admin/search?${searchParams}`);
    return response.data;
  },

  // 获取用户提交分析
  getUserCommitAnalytics: async (userId: number): Promise<CommitAnalytics> => {
    const response = await apiClient.get(`/v1/commits/admin/user/${userId}/analytics`);
    return response.data;
  },

  // 获取单个提交详情
  getCommitDetail: async (commitId: number): Promise<CommitInfo> => {
    const response = await apiClient.get(`/v1/commits/${commitId}`);
    return response.data;
  },

  // 更新提交
  updateCommit: async (commitId: number, data: {
    final_commit_message?: string;
    user_rating?: number;
    user_feedback?: string;
    status?: string;
  }): Promise<CommitInfo> => {
    const response = await apiClient.patch(`/v1/commits/${commitId}`, data);
    return response.data;
  },

  // 删除提交
  deleteCommit: async (commitId: number): Promise<void> => {
    await apiClient.delete(`/v1/commits/${commitId}`);
  }
};

// System API
export const systemAPI = {
  // 获取系统统计
  getSystemStats: async (): Promise<SystemStats> => {
    const response = await apiClient.get('/v1/admin/stats');
    return response.data;
  },

  // 获取系统健康状态
  getHealthCheck: async (): Promise<{ status: string; version: string; services: Record<string, string> }> => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  // 获取CAS配置
  getCASConfig: async (): Promise<CASConfig> => {
    const response = await apiClient.get('/v1/admin/cas/config');
    return response.data;
  },

  // 更新CAS配置
  updateCASConfig: async (config: Partial<CASConfig>): Promise<CASConfig> => {
    const response = await apiClient.put('/v1/admin/cas/config', config);
    return response.data;
  },

  // 测试CAS连接
  testCASConnection: async (): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post('/v1/admin/cas/test');
    return response.data;
  }
};

// API监控
export const monitoringAPI = {
  // 获取API调用统计
  getAPIStats: async (timeRange = '24h'): Promise<{
    total_calls: number;
    successful_calls: number;
    failed_calls: number;
    avg_response_time: number;
    endpoints: Array<{
      path: string;
      calls: number;
      avg_response_time: number;
      success_rate: number;
    }>;
  }> => {
    const response = await apiClient.get(`/v1/admin/monitoring/api?time_range=${timeRange}`);
    return response.data;
  },

  // 获取实时监控数据
  getRealtimeMetrics: async (): Promise<{
    active_connections: number;
    requests_per_minute: number;
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
  }> => {
    const response = await apiClient.get('/v1/admin/monitoring/realtime');
    return response.data;
  }
};

export default {
  authAPI,
  usersAPI,
  commitsAPI,
  systemAPI,
  monitoringAPI
}; 