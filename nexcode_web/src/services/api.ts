import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { toast } from 'react-hot-toast';
import type {
  // 認證相關
  LoginRequest,
  RegisterRequest,
  LoginResponse,
  AuthStatus,
  User,
  // 文檔相關
  Document,
  DocumentCreateRequest,
  DocumentUpdateRequest,
  DocumentListResponse,
  DocumentVersion,
  DocumentVersionsResponse,
  VersionRestoreResponse,
  // ShareDB 相關
  DocumentState,
  ShareDBSyncResponse,
  // AI 聊天相關
  ChatCompletionRequest,
  ChatCompletionResponse,
  CodeAnalysisRequest,
  CommitMessageRequest,
  // AI模板相关
  AITemplate,
  AITemplateCreateRequest,
  AITemplateUpdateRequest,
  AIAssistRequest,
  // 通用類型
  ApiResponse
} from '@/types/api';

/**
 * 統一的 API 服務類
 * 管理所有與後端的 HTTP 通信
 */
class ApiService {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30秒超時
    });

    this.setupInterceptors();
  }

  /**
   * 設置請求和響應攔截器
   */
  private setupInterceptors() {
    // 請求攔截器 - 自動添加認證 token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        // 添加 X-Session-Token 頭部（兼容現有實現）
        const sessionToken = localStorage.getItem('session_token');
        if (sessionToken) {
          config.headers['X-Session-Token'] = sessionToken;
        }
        
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // 響應攔截器 - 統一錯誤處理
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      (error) => {
        this.handleError(error);
        return Promise.reject(error);
      }
    );
  }

  /**
   * 獲取存儲的認證 token
   */
  private getAuthToken(): string | null {
    return localStorage.getItem('session_token') || localStorage.getItem('auth_token');
  }

  /**
   * 統一錯誤處理
   */
  private handleError(error: any) {
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 401:
          toast.error('認證失敗，請重新登錄');
          // 清除本地認證信息
          localStorage.removeItem('session_token');
          localStorage.removeItem('auth_token');
          // 可以在這裡觸發重定向到登錄頁面
          break;
        case 403:
          toast.error(data?.detail || '權限不足');
          break;
        case 404:
          toast.error(data?.detail || '資源不存在');
          break;
        case 422:
          toast.error(data?.detail || '請求參數錯誤');
          break;
        case 500:
          toast.error('服務器內部錯誤');
          break;
        default:
          toast.error(data?.detail || `請求失敗 (${status})`);
      }
    } else if (error.request) {
      toast.error('網絡連接失敗，請檢查網絡設置');
    } else {
      toast.error('請求配置錯誤');
    }
  }

  // ===================== 認證相關 API =====================
  
  /**
   * 用戶登錄
   */
  async login(data: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/v1/auth/login', data);
    return response.data;
  }

  /**
   * 用戶註冊
   */
  async register(data: RegisterRequest): Promise<User> {
    const response = await this.client.post<User>('/v1/auth/register', data);
    return response.data;
  }

  /**
   * 獲取當前用戶信息
   */
  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/v1/auth/me');
    return response.data;
  }

  /**
   * 用戶登出
   */
  async logout(): Promise<void> {
    await this.client.post('/v1/auth/logout');
    localStorage.removeItem('session_token');
    localStorage.removeItem('auth_token');
  }

  /**
   * 獲取認證狀態
   */
  async getAuthStatus(): Promise<AuthStatus> {
    const response = await this.client.get<AuthStatus>('/v1/auth/status');
    return response.data;
  }

  /**
   * 獲取 CAS 登錄 URL
   */
  async getCASLoginUrl(): Promise<{ login_url: string }> {
    const response = await this.client.get<{ login_url: string }>('/v1/auth/cas/login');
    return response.data;
  }

  // ===================== 文檔相關 API =====================

  /**
   * 獲取文檔列表
   */
  async getDocuments(params: {
    skip?: number;
    limit?: number;
    search?: string;
    category?: string;
  } = {}): Promise<DocumentListResponse> {
    const response = await this.client.get<DocumentListResponse>('/v1/documents', { params });
    return response.data;
  }

  /**
   * 獲取文檔詳情
   */
  async getDocument(id: number): Promise<Document> {
    const response = await this.client.get<Document>(`/v1/documents/${id}`);
    return response.data;
  }

  /**
   * 創建文檔
   */
  async createDocument(data: DocumentCreateRequest): Promise<Document> {
    const response = await this.client.post<Document>('/v1/documents', data);
    return response.data;
  }

  /**
   * 更新文檔
   */
  async updateDocument(id: number, data: DocumentUpdateRequest): Promise<Document> {
    const response = await this.client.put<Document>(`/v1/documents/${id}`, data);
    return response.data;
  }

  /**
   * 刪除文檔
   */
  async deleteDocument(id: number): Promise<void> {
    await this.client.delete(`/v1/documents/${id}`);
  }

  /**
   * 獲取文檔版本歷史
   */
  async getDocumentVersions(id: number, limit: number = 10): Promise<DocumentVersionsResponse> {
    const response = await this.client.get<DocumentVersionsResponse>(
      `/v1/documents/${id}/versions`, 
      { params: { limit } }
    );
    return response.data;
  }

  /**
   * 恢復文檔版本
   */
  async restoreDocumentVersion(id: number, versionNumber: number): Promise<VersionRestoreResponse> {
    const response = await this.client.post<VersionRestoreResponse>(
      `/v1/documents/${id}/versions/${versionNumber}/restore`
    );
    return response.data;
  }

  // ===================== ShareDB 相關 API =====================

  /**
   * 獲取 ShareDB 文檔狀態
   */
  async getShareDBDocument(docId: string): Promise<DocumentState> {
    const response = await this.client.get<DocumentState>(`/v1/sharedb/documents/${docId}`);
    return response.data;
  }

  /**
   * 同步文檔到 ShareDB
   */
  async syncShareDBDocument(docId: string, data: {
    content: string;
    version?: number;
    user_id?: number;
  }): Promise<ShareDBSyncResponse> {
    const response = await this.client.post<ShareDBSyncResponse>(
      `/v1/sharedb/documents/${docId}/sync`, 
      data
    );
    return response.data;
  }

  /**
   * 應用 ShareDB 操作
   */
  async applyShareDBOperation(docId: string, operation: any): Promise<any> {
    const response = await this.client.post(
      `/v1/sharedb/documents/${docId}/operations`, 
      operation
    );
    return response.data;
  }

  // ===================== AI 聊天相關 API =====================

  /**
   * OpenAI 兼容的聊天完成接口
   */
  async chatCompletion(data: ChatCompletionRequest, apiKey?: string): Promise<ChatCompletionResponse> {
    const headers: any = {};
    if (apiKey) {
      headers['Authorization'] = `Bearer ${apiKey}`;
    }

    const response = await this.client.post<ChatCompletionResponse>(
      '/v1/chat/completions', 
      data, 
      { headers }
    );
    return response.data;
  }

  /**
   * OpenAI 兼容接口（使用服務器 token）
   */
  async openaiChatCompletion(data: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    const response = await this.client.post<ChatCompletionResponse>(
      '/v1/openai/chat/completions', 
      data
    );
    return response.data;
  }

  /**
   * 智能問答
   */
  async intelligentQA(data: { question: string; context?: string }): Promise<{ answer: string }> {
    const response = await this.client.post<{ answer: string }>('/v1/intelligent-qa', data);
    return response.data;
  }

  // ===================== AI 相關方法 =====================
  
  /**
   * OpenAI 兼容的聊天完成
   */
  async getChatCompletion(request: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    try {
      const response = await this.client.post<ChatCompletionResponse>('/v1/openai_compatible/chat/completions', request);
      return response.data;
    } catch (error) {
      console.error('Chat completion failed:', error);
      throw error;
    }
  }

  /**
   * 代碼質量分析
   */
  async analyzeCode(request: CodeAnalysisRequest): Promise<{ analysis: string }> {
    try {
      const response = await this.client.post<{ analysis: string }>('/v1/code_quality/', request);
      return response.data;
    } catch (error) {
      console.error('Code analysis failed:', error);
      throw error;
    }
  }

  /**
   * 代碼審查
   */
  async reviewCode(data: CodeAnalysisRequest): Promise<any> {
    const response = await this.client.post('/v1/code-review', data);
    return response.data;
  }

  /**
   * 生成提交信息
   */
  async generateCommitMessage(request: CommitMessageRequest): Promise<{ message: string }> {
    try {
      const response = await this.client.post<{ message: string }>('/v1/commit_message/', request);
      return response.data;
    } catch (error) {
      console.error('Commit message generation failed:', error);
      throw error;
    }
  }

  // AI模板管理方法
  async getAITemplates(): Promise<AITemplate[]> {
    try {
      const response = await this.client.get<AITemplate[]>('/v1/ai/templates');
      return response.data;
    } catch (error) {
      console.error('Failed to get AI templates:', error);
      throw error;
    }
  }

  async createAITemplate(template: AITemplateCreateRequest): Promise<AITemplate> {
    try {
      const response = await this.client.post<AITemplate>('/v1/ai/templates', template);
      return response.data;
    } catch (error) {
      console.error('Failed to create AI template:', error);
      throw error;
    }
  }

  async updateAITemplate(id: number, updates: AITemplateUpdateRequest): Promise<AITemplate> {
    try {
      const response = await this.client.put<AITemplate>(`/v1/ai/templates/${id}`, updates);
      return response.data;
    } catch (error) {
      console.error('Failed to update AI template:', error);
      throw error;
    }
  }

  async deleteAITemplate(id: number): Promise<void> {
    try {
      await this.client.delete(`/v1/ai/templates/${id}`);
    } catch (error) {
      console.error('Failed to delete AI template:', error);
      throw error;
    }
  }

  // AI辅助功能
  async aiAssist(request: AIAssistRequest): Promise<{ response: string }> {
    try {
      const response = await this.client.post<{ response: string }>('/v1/ai/assist', request);
      return response.data;
    } catch (error) {
      console.error('AI assist failed:', error);
      throw error;
    }
  }

  // ===================== 工具方法 =====================

  /**
   * 直接使用 fetch 進行請求（用於特殊情況）
   */
  async fetch(url: string, options: RequestInit = {}): Promise<Response> {
    const fullUrl = url.startsWith('http') ? url : `${this.baseURL}${url}`;
    
    const defaultHeaders: HeadersInit = {
      'Content-Type': 'application/json',
    };

    const token = this.getAuthToken();
    if (token) {
      defaultHeaders['Authorization'] = `Bearer ${token}`;
      defaultHeaders['X-Session-Token'] = token;
    }

    return fetch(fullUrl, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });
  }

  /**
   * 獲取完整的 API URL
   */
  getFullUrl(path: string): string {
    return `${this.baseURL}${path}`;
  }

  /**
   * 檢查網絡連接狀態
   */
  async checkConnection(): Promise<boolean> {
    try {
      await this.client.get('/health', { timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }
}

// 創建單例實例
export const apiService = new ApiService();

// 導出類型以供其他模塊使用
export type { ApiService };

// 為了向後兼容，保留原有的 api 導出
export const api = apiService['client']; 