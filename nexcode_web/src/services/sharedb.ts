import { api } from '@/lib/api';

export interface DocumentState {
  doc_id: string;
  content: string;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface Operation {
  type: 'insert' | 'delete' | 'replace' | 'full_update';
  position?: number;
  length?: number;
  text?: string;
  content?: string;
  version?: number;
}

export interface SyncResponse {
  success: boolean;
  version: number;
  content: string;
  operations: Array<{
    doc_id: string;
    version: number;
    operation: Operation;
    user_id: number;
    timestamp: string;
  }>;
  error?: string;
}

export interface OperationResponse {
  success: boolean;
  version?: number;
  content?: string;
  operation_id?: string;
  error?: string;
  current_version?: number;
  missing_operations?: Array<{
    doc_id: string;
    version: number;
    operation: Operation;
    user_id: number;
    timestamp: string;
  }>;
}

export class ShareDBClient {
  private docId: string;
  private currentVersion: number = 0;
  private currentContent: string = '';
  private syncTimeout: NodeJS.Timeout | null = null;
  private isOnline: boolean = true;
  private pendingOperations: Operation[] = [];
  private lastSyncTime: Date | null = null;
  private syncInProgress: boolean = false;

  constructor(docId: string) {
    this.docId = docId;
  }

  /**
   * 获取文档当前状态
   */
  async getDocument(): Promise<DocumentState> {
    try {
      const response = await api.get(`/v1/sharedb/documents/${this.docId}`);
      const docState = response.data as DocumentState;
      
      this.currentVersion = docState.version;
      this.currentContent = docState.content;
      this.lastSyncTime = new Date();
      this.isOnline = true;
      
      return docState;
    } catch (error) {
      console.error('Failed to get document:', error);
      this.isOnline = false;
      throw error;
    }
  }

  /**
   * 同步文档状态
   */
  async syncDocument(content: string): Promise<SyncResponse> {
    // 防止并发同步
    if (this.syncInProgress) {
      return {
        success: false,
        version: this.currentVersion,
        content: this.currentContent,
        operations: [],
        error: 'sync_in_progress'
      };
    }

    this.syncInProgress = true;

    try {
      const response = await api.post('/v1/sharedb/documents/sync', {
        doc_id: this.docId,
        version: this.currentVersion,
        content: content,
        create_version: false
      });
      
      const syncResult = response.data as SyncResponse;
      
      if (syncResult.success) {
        this.currentVersion = syncResult.version;
        this.currentContent = syncResult.content;
        this.lastSyncTime = new Date();
        this.isOnline = true;
        
        // 如果有缺失的操作，应用它们
        if (syncResult.operations && syncResult.operations.length > 0) {
          console.log('Received operations:', syncResult.operations);
          // TODO: 应用操作到本地内容
        }
      } else {
        console.warn('Sync failed:', syncResult.error);
      }
      
      return syncResult;
    } catch (error) {
      console.error('Failed to sync document:', error);
      this.isOnline = false;
      
      // 返回当前本地状态作为降级
      return {
        success: false,
        version: this.currentVersion,
        content: content, // 使用客户端内容
        operations: [],
        error: 'network_error'
      };
    } finally {
      this.syncInProgress = false;
    }
  }

  /**
   * 应用操作
   */
  async applyOperation(operation: Operation): Promise<OperationResponse> {
    try {
      const response = await api.post('/v1/sharedb/documents/operations', {
        doc_id: this.docId,
        operation: {
          ...operation,
          version: this.currentVersion
        }
      });
      
      const result = response.data as OperationResponse;
      
      if (result.success && result.version !== undefined) {
        this.currentVersion = result.version;
        if (result.content !== undefined) {
          this.currentContent = result.content;
        }
        this.lastSyncTime = new Date();
        this.isOnline = true;
      } else if (result.error === 'version_mismatch' && result.missing_operations) {
        // 处理版本冲突
        console.log('Version mismatch, applying missing operations:', result.missing_operations);
        // TODO: 应用缺失的操作
      }
      
      return result;
    } catch (error) {
      console.error('Failed to apply operation:', error);
      // 将操作添加到待处理队列
      this.pendingOperations.push(operation);
      this.isOnline = false;
      throw error;
    }
  }

  /**
   * 获取指定版本之后的操作
   */
  async getOperationsSince(sinceVersion: number): Promise<any> {
    try {
      const response = await api.get(`/v1/sharedb/documents/${this.docId}/operations?since_version=${sinceVersion}`);
      this.isOnline = true;
      return response.data;
    } catch (error) {
      console.error('Failed to get operations:', error);
      this.isOnline = false;
      throw error;
    }
  }

  /**
   * 创建文本插入操作
   */
  createInsertOperation(position: number, text: string): Operation {
    return {
      type: 'insert',
      position,
      text
    };
  }

  /**
   * 创建文本删除操作
   */
  createDeleteOperation(position: number, length: number): Operation {
    return {
      type: 'delete',
      position,
      length
    };
  }

  /**
   * 创建文本替换操作
   */
  createReplaceOperation(position: number, length: number, text: string): Operation {
    return {
      type: 'replace',
      position,
      length,
      text
    };
  }

  /**
   * 创建全量更新操作
   */
  createFullUpdateOperation(content: string): Operation {
    return {
      type: 'full_update',
      content
    };
  }

  /**
   * 防抖同步
   */
  debouncedSync(content: string, delay: number = 1000): Promise<SyncResponse> {
    return new Promise((resolve, reject) => {
      if (this.syncTimeout) {
        clearTimeout(this.syncTimeout);
      }
      
      this.syncTimeout = setTimeout(async () => {
        try {
          const result = await this.syncDocument(content);
          resolve(result);
        } catch (error) {
          reject(error);
        }
      }, delay);
    });
  }

  /**
   * 重试待处理的操作
   */
  async retryPendingOperations(): Promise<void> {
    if (!this.isOnline || this.pendingOperations.length === 0) {
      return;
    }

    const operations = [...this.pendingOperations];
    this.pendingOperations = [];

    for (const operation of operations) {
      try {
        await this.applyOperation(operation);
      } catch (error) {
        console.error('Failed to retry operation:', error);
        // 重新添加到待处理队列
        this.pendingOperations.push(operation);
      }
    }
  }

  /**
   * 检查连接状态
   */
  async checkConnection(): Promise<boolean> {
    try {
      // 简单的 ping 操作
      await api.get('/v1/sharedb/ping', { timeout: 5000 });
      this.isOnline = true;
      
      // 重试待处理的操作
      if (this.pendingOperations.length > 0) {
        await this.retryPendingOperations();
      }
      
      return true;
    } catch (error) {
      this.isOnline = false;
      return false;
    }
  }

  /**
   * 强制同步
   */
  async forceSyncWithServer(): Promise<SyncResponse> {
    try {
      // 获取服务器最新状态
      const serverDoc = await this.getDocument();
      
      // 如果本地有未同步的内容，尝试同步
      if (this.currentContent !== serverDoc.content) {
        return await this.syncDocument(this.currentContent);
      }
      
      return {
        success: true,
        version: serverDoc.version,
        content: serverDoc.content,
        operations: []
      };
    } catch (error) {
      console.error('Force sync failed:', error);
      throw error;
    }
  }

  /**
   * 获取同步状态
   */
  getSyncStatus() {
    return {
      isOnline: this.isOnline,
      lastSyncTime: this.lastSyncTime,
      syncInProgress: this.syncInProgress,
      hasPendingOperations: this.pendingOperations.length > 0,
      pendingOperationsCount: this.pendingOperations.length
    };
  }

  /**
   * 获取当前状态
   */
  getCurrentState() {
    return {
      docId: this.docId,
      version: this.currentVersion,
      content: this.currentContent,
      isOnline: this.isOnline,
      pendingOperations: this.pendingOperations.length,
      lastSyncTime: this.lastSyncTime,
      syncInProgress: this.syncInProgress
    };
  }

  /**
   * 清理资源
   */
  destroy() {
    if (this.syncTimeout) {
      clearTimeout(this.syncTimeout);
    }
    this.pendingOperations = [];
    this.syncInProgress = false;
  }
} 