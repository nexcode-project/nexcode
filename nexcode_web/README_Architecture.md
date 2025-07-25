# NexCode 前端架構說明

## 項目結構

```
nexcode_web/
├── src/
│   ├── components/           # 可復用組件
│   │   ├── AIAssistant.tsx   # AI助手組件
│   │   ├── Chat.tsx          # 聊天組件
│   │   ├── CollaborativeLexicalEditor.tsx  # 協作編輯器
│   │   └── ...
│   ├── pages/                # Next.js 頁面
│   │   ├── documents/        # 文檔相關頁面
│   │   ├── login.tsx         # 登錄頁面
│   │   └── ...
│   ├── services/             # 服務層（新增）
│   │   ├── api.ts            # 統一 API 服務
│   │   └── sharedb.ts        # ShareDB 服務
│   ├── types/                # TypeScript 類型定義（新增）
│   │   └── api.ts            # API 相關類型
│   ├── store/                # 狀態管理
│   │   └── authStore.ts      # 認證狀態
│   ├── hooks/                # 自定義 Hooks
│   │   └── useWebSocket.ts   # WebSocket Hook
│   ├── lib/                  # 工具庫
│   │   └── api.ts            # 原有 API 配置（兼容）
│   └── styles/               # 樣式文件
└── ...
```

## 架構改進

### 1. 統一 API 管理

#### 問題
- API 調用分散在各個組件中
- 使用不同的請求方式（fetch、axios）
- 錯誤處理不統一
- 類型定義重複

#### 解決方案
- 創建統一的 `ApiService` 類
- 集中管理所有 API 調用
- 統一錯誤處理和認證
- 完整的 TypeScript 類型支持

#### 核心文件

**`src/types/api.ts`** - 所有 API 相關的類型定義
```typescript
export interface Document { ... }
export interface LoginRequest { ... }
export interface ChatCompletionRequest { ... }
// ... 其他類型
```

**`src/services/api.ts`** - 統一的 API 服務類
```typescript
class ApiService {
  // 認證相關
  async login(data: LoginRequest): Promise<LoginResponse>
  async getCurrentUser(): Promise<User>
  
  // 文檔相關
  async getDocuments(): Promise<DocumentListResponse>
  async createDocument(data: DocumentCreateRequest): Promise<Document>
  
  // AI 聊天相關
  async chatCompletion(data: ChatCompletionRequest): Promise<ChatCompletionResponse>
  
  // ... 其他方法
}
```

### 2. 自動化功能

#### 請求攔截器
- 自動添加認證 token
- 統一請求頭設置
- 請求日志記錄

#### 響應攔截器
- 統一錯誤處理
- 自動 token 刷新
- 網絡狀態管理

#### 錯誤處理
```typescript
private handleError(error: any) {
  switch (status) {
    case 401: // 認證失敗
    case 403: // 權限不足
    case 404: // 資源不存在
    case 422: // 參數錯誤
    case 500: // 服務器錯誤
  }
}
```

### 3. 類型安全

#### 完整的 TypeScript 支持
- 所有 API 請求和響應都有類型定義
- 編譯時類型檢查
- 智能代碼提示

#### 類型組織
```typescript
// 基礎類型
interface User { ... }
interface UserInfo { ... }

// 請求類型
interface LoginRequest { ... }
interface DocumentCreateRequest { ... }

// 響應類型
interface LoginResponse { ... }
interface DocumentListResponse { ... }

// 枚舉類型
enum DocumentStatus { ... }
enum PermissionLevel { ... }
```

### 4. 服務分層

#### API 層（`services/api.ts`）
- HTTP 請求封裝
- 認證管理
- 錯誤處理

#### 業務邏輯層（`services/sharedb.ts`）
- ShareDB 實時協作
- 文檔同步邏輯
- 操作轉換

#### 狀態管理層（`store/`）
- 全局狀態管理
- 認證狀態
- 用戶偏好設置

### 5. 組件架構

#### 智能組件與展示組件分離
- 智能組件：處理邏輯和狀態
- 展示組件：純 UI 渲染

#### Hooks 封裝
- 複用邏輯抽取到自定義 Hooks
- 狀態管理邏輯封裝
- 副作用處理

## 使用指南

### 1. API 調用

**舊方式（不推薦）：**
```typescript
import { api } from '@/lib/api';

const response = await api.get('/v1/documents');
const documents = response.data.documents;
```

**新方式（推薦）：**
```typescript
import { apiService } from '@/services/api';

const response = await apiService.getDocuments();
const documents = response.documents; // 自動類型推斷
```

### 2. 錯誤處理

API 服務會自動處理常見錯誤並顯示用戶友好的錯誤消息。特殊情況下可以捕獲錯誤進行自定義處理：

```typescript
try {
  const document = await apiService.getDocument(id);
  setDocument(document);
} catch (error) {
  // 自定義錯誤處理
  console.error('Failed to load document:', error);
}
```

### 3. 類型使用

```typescript
import type { Document, DocumentCreateRequest } from '@/types/api';

const createDocument = async (data: DocumentCreateRequest): Promise<Document> => {
  return await apiService.createDocument(data);
};
```

## 遷移指南

### 現有組件遷移步驟

1. **更新導入**
   ```typescript
   // 舊
   import { api } from '@/lib/api';
   
   // 新
   import { apiService } from '@/services/api';
   import type { Document } from '@/types/api';
   ```

2. **替換 API 調用**
   ```typescript
   // 舊
   const response = await api.get('/v1/documents');
   const documents = response.data.documents;
   
   // 新
   const response = await apiService.getDocuments();
   const documents = response.documents;
   ```

3. **添加類型定義**
   ```typescript
   // 舊
   const [documents, setDocuments] = useState([]);
   
   // 新
   const [documents, setDocuments] = useState<Document[]>([]);
   ```

### 向後兼容

為了平滑遷移，保留了原有的 `api` 導出：

```typescript
// 仍然可用，但不推薦
import { api } from '@/services/api';
```

## 最佳實踐

### 1. API 設計
- 遵循 RESTful 設計原則
- 統一的響應格式
- 清晰的錯誤碼和消息

### 2. 類型定義
- 使用 interface 而不是 type（除非必要）
- 合理使用可選屬性和聯合類型
- 避免 `any` 類型

### 3. 錯誤處理
- 在適當的層級處理錯誤
- 提供有意義的錯誤消息
- 優雅的降級處理

### 4. 性能優化
- 合理使用緩存
- 避免不必要的重複請求
- 實現請求防抖和節流

## 未來規劃

1. **離線支持**
   - 實現離線緩存
   - 同步衝突解決

2. **實時協作優化**
   - 改進 ShareDB 集成
   - 用戶在線狀態顯示

3. **監控和分析**
   - API 性能監控
   - 用戶行為分析

4. **測試覆蓋**
   - 單元測試
   - 集成測試
   - E2E 測試 