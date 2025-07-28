// ===================== 基礎類型 =====================
export interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface UserInfo {
  id: number;
  username: string;
  email: string | null;
}

// ===================== 認證相關 =====================
export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: User;
  expires_at: string;
}

export interface AuthStatus {
  authenticated: boolean;
  user?: User;
}

// ===================== 文檔相關 =====================
export interface Document {
  id: number;
  title: string;
  content: string;
  category?: string;
  tags?: string[];
  status: DocumentStatus;
  version: number;
  created_at: string;
  updated_at: string;
  owner: UserInfo;
  collaborators?: DocumentCollaborator[];
  user_permission?: PermissionLevel;
}

export interface DocumentCreateRequest {
  title: string;
  content?: string;
  category?: string;
  tags?: string[];
}

export interface DocumentUpdateRequest {
  title?: string;
  content?: string;
  category?: string;
  tags?: string[];
  change_description?: string;
  create_version?: boolean;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  page: number;
  size: number;
}

export interface DocumentVersion {
  id: number;
  version_number: number;
  title: string;
  content: string;
  change_description: string;
  created_at: string;
  changed_by: UserInfo;
}

export interface DocumentVersionsResponse {
  versions: DocumentVersion[];
}

export interface VersionRestoreResponse {
  success: boolean;
  content: string;
  version_number: number;
  message: string;
}

export interface DocumentCollaborator {
  id: number;
  user: UserInfo;
  permission: PermissionLevel;
  added_at: string;
}

export enum DocumentStatus {
  ACTIVE = 'active',
  ARCHIVED = 'archived',
  DELETED = 'deleted'
}

export enum PermissionLevel {
  READER = 'reader',
  EDITOR = 'editor',
  OWNER = 'owner'
}

// ===================== ShareDB 相關 =====================
export interface DocumentState {
  doc_id: string;
  content: string;
  version: number;
  created_at: string;
  updated_at: string;
  last_editor_id?: string | null;
}

export interface ShareDBSyncResponse {
  success: boolean;
  content: string;
  version: number;
  error?: string;
}

export interface ShareDBOperation {
  type: 'insert' | 'delete' | 'retain';
  position: number;
  content?: string;
  length?: number;
}

// ===================== AI 聊天相關 =====================
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
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

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// ===================== 代碼分析相關 =====================
export interface CodeAnalysisRequest {
  code: string;
  language?: string;
  api_key?: string;
  api_base_url?: string;
  model_name?: string;
}

export interface CommitMessageRequest {
  diff: string;
  style?: string;
  context?: any;
  api_key?: string;
  api_base_url?: string;
  model_name?: string;
}

// ===================== 通用響應類型 =====================
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success?: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  skip: number;
  limit: number;
}

export interface ErrorResponse {
  error: string;
  detail?: string;
  status_code?: number;
}

// ===================== Personal Access Token 相關 =====================
export interface APIKey {
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

export interface TokenScope {
  name: string;
  description: string;
}

export interface ScopesResponse {
  scopes: TokenScope[];
  default_scopes: string[];
} 