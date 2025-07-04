import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  // Use localStorage instead of cookies since backend sets HTTPOnly cookies
  // Only access localStorage on client side to prevent SSR issues
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('session_token');
    if (token) {
      config.headers['X-Session-Token'] = token;
    }
  }
  return config;
});

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('session_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export interface User {
  id: number;
  username: string;
  full_name: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  session_token: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// OpenAI compatible message format
export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  presence_penalty?: number;
  frequency_penalty?: number;
  stop?: string | string[];
}

export interface ChatCompletionResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: ChatMessage;
    finish_reason: string;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface ChatRequest {
  message: string;
  context?: any;
}

export interface ChatResponse {
  message: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  email?: string;
  full_name?: string;
}

export const authAPI = {
  // 密码登录
  login: (data: LoginRequest) => api.post<LoginResponse>('/v1/auth/login', data),
  register: (data: RegisterRequest) => api.post<User>('/v1/auth/register', data),
  
  // CAS 登录
  getCASLoginUrl: () => api.get<{ login_url: string }>('/v1/auth/cas/login'),
  
  // 通用认证
  getCurrentUser: () => api.get<User>('/v1/auth/me'),
  logout: () => api.post('/v1/auth/logout'),
  getAuthStatus: () => api.get('/v1/auth/status'),
};

export const chatAPI = {
  // 使用标准 OpenAI Chat Completion 接口
  chatCompletion: (data: ChatCompletionRequest, apiKey?: string) => {
    const headers: any = { 'Content-Type': 'application/json' };
    if (apiKey) {
      headers['Authorization'] = `Bearer ${apiKey}`;
    }
    
    return api.post<ChatCompletionResponse>('/v1/chat/completions', data, { headers });
  },
  
  // 原有的智能问答接口
  sendMessage: (data: ChatRequest) => 
    api.post<ChatResponse>('/v1/intelligent-qa', data),
  
  generateCommitMessage: (data: {
    diff: string;
    style?: string;
    context?: any;
    api_key?: string;
    api_base_url?: string;
    model_name?: string;
  }) => api.post<{ message: string }>('/v1/commit-message', data),
  
  analyzeCode: (data: {
    code: string;
    language?: string;
    api_key?: string;
    api_base_url?: string;
    model_name?: string;
  }) => api.post('/v1/code-quality', data),
  
  reviewCode: (data: {
    code: string;
    language?: string;
    api_key?: string;
    api_base_url?: string;
    model_name?: string;
  }) => api.post('/v1/code-review', data),
}; 