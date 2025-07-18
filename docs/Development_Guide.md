# 协作文档平台开发指南

## 1. 开发环境搭建

### 1.1 前置要求
- Node.js 18+
- Python 3.9+
- MongoDB 5.0+
- Redis 6.0+

### 1.2 项目初始化
```bash
# 克隆项目
git clone <repository-url>
cd collaborative-docs

# 安装前端依赖
cd frontend
npm install

# 安装后端依赖
cd ../backend
pip install -r requirements.txt

# 启动数据库
docker-compose up -d mongodb redis
```

### 1.3 环境配置
```bash
# 后端环境变量
cp .env.example .env
# 配置数据库连接、OpenAI API Key等

# 前端环境变量
cp .env.local.example .env.local
# 配置API地址等
```

## 2. 开发规范

### 2.1 代码规范
- **前端**: ESLint + Prettier + TypeScript
- **后端**: Black + isort + mypy
- **提交**: Conventional Commits

### 2.2 分支策略
- `main`: 生产环境
- `develop`: 开发环境
- `feature/*`: 功能分支
- `hotfix/*`: 紧急修复

### 2.3 测试要求
- 单元测试覆盖率 > 80%
- 集成测试覆盖核心功能
- E2E测试覆盖主要用户流程

## 3. 核心功能开发

### 3.1 实时协作编辑器
```typescript
// 编辑器组件示例
import { useWebSocket } from '@/hooks/useWebSocket';
import { useEditor } from '@/hooks/useEditor';

export function CollaborativeEditor() {
  const { content, updateContent } = useEditor();
  const { sendMessage, onMessage } = useWebSocket();
  
  // 处理本地编辑
  const handleEdit = (change: Change) => {
    updateContent(change);
    sendMessage({
      type: 'content_change',
      change
    });
  };
  
  // 处理远程编辑
  onMessage((message) => {
    if (message.type === 'content_change') {
      applyRemoteChange(message.change);
    }
  });
  
  return <Editor content={content} onChange={handleEdit} />;
}
```

### 3.2 AI助手集成
```python
# AI服务示例
from openai import AsyncOpenAI

class AIAssistant:
    def __init__(self):
        self.client = AsyncOpenAI()
    
    async def generate_content(self, prompt: str, context: str) -> str:
        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的文档写作助手"},
                {"role": "user", "content": f"上下文: {context}\n\n请求: {prompt}"}
            ]
        )
        return response.choices[0].message.content
    
    async def optimize_text(self, text: str) -> str:
        # 文本优化逻辑
        pass
```

### 3.3 WebSocket处理
```python
# WebSocket管理器
from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, document_id: str):
        await websocket.accept()
        if document_id not in self.active_connections:
            self.active_connections[document_id] = []
        self.active_connections[document_id].append(websocket)
    
    async def broadcast(self, message: dict, document_id: str):
        if document_id in self.active_connections:
            for connection in self.active_connections[document_id]:
                await connection.send_json(message)
```

## 4. 数据库操作

### 4.1 MongoDB操作
```python
# 文档服务示例
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

class DocumentService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.documents
    
    async def create_document(self, document_data: dict) -> str:
        result = await self.collection.insert_one(document_data)
        return str(result.inserted_id)
    
    async def get_document(self, document_id: str) -> dict:
        return await self.collection.find_one({"_id": ObjectId(document_id)})
    
    async def update_document(self, document_id: str, update_data: dict):
        await self.collection.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": update_data}
        )
```

### 4.2 Redis缓存
```python
# 缓存服务示例
import redis.asyncio as redis
import json

class CacheService:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0)
    
    async def set_online_users(self, document_id: str, users: list):
        await self.redis.setex(
            f"online_users:{document_id}",
            300,  # 5分钟过期
            json.dumps(users)
        )
    
    async def get_online_users(self, document_id: str) -> list:
        data = await self.redis.get(f"online_users:{document_id}")
        return json.loads(data) if data else []
```

## 5. 测试指南

### 5.1 前端测试
```typescript
// 组件测试示例
import { render, screen } from '@testing-library/react';
import { CollaborativeEditor } from '@/components/Editor';

describe('CollaborativeEditor', () => {
  it('should render editor content', () => {
    render(<CollaborativeEditor initialContent="Hello World" />);
    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });
  
  it('should handle text changes', async () => {
    const onChangeMock = jest.fn();
    render(<CollaborativeEditor onChange={onChangeMock} />);
    
    // 模拟用户输入
    const editor = screen.getByRole('textbox');
    fireEvent.change(editor, { target: { value: 'New content' } });
    
    expect(onChangeMock).toHaveBeenCalledWith('New content');
  });
});
```

### 5.2 后端测试
```python
# API测试示例
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_document(client: AsyncClient):
    response = await client.post("/api/v1/documents", json={
        "title": "Test Document",
        "content": "# Hello World"
    })
    assert response.status_code == 201
    assert response.json()["title"] == "Test Document"

@pytest.mark.asyncio
async def test_websocket_connection():
    # WebSocket连接测试
    pass
```

## 6. 部署指南

### 6.1 Docker部署
```dockerfile
# Dockerfile示例
FROM node:18-alpine AS frontend
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.9-slim AS backend
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt
COPY backend/ ./

FROM nginx:alpine AS production
COPY --from=frontend /app/dist /usr/share/nginx/html
COPY --from=backend /app /app
```

### 6.2 环境配置
```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mongodb://mongodb:27017/collaborative_docs
      - REDIS_URL=redis://redis:6379
  
  mongodb:
    image: mongo:5.0
    ports:
      - "27017:27017"
  
  redis:
    image: redis:6.0-alpine
    ports:
      - "6379:6379"
```

## 7. 故障排查

### 7.1 常见问题
- **WebSocket连接失败**: 检查防火墙和代理配置
- **AI服务超时**: 检查OpenAI API配额和网络
- **数据库连接错误**: 验证连接字符串和权限

### 7.2 日志分析
```python
# 日志配置示例
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

## 8. 性能优化建议

### 8.1 前端优化
- 使用React.memo减少不必要渲染
- 实现虚拟滚动处理大文档
- 优化WebSocket消息频率

### 8.2 后端优化
- 数据库查询优化和索引
- 实现连接池管理
- 缓存热点数据

## 9. 安全最佳实践

### 9.1 输入验证
```python
from pydantic import BaseModel, validator

class DocumentCreate(BaseModel):
    title: str
    content: str
    
    @validator('title')
    def validate_title(cls, v):
        if len(v) > 200:
            raise ValueError('标题过长')
        return v.strip()
```

### 9.2 权限检查
```python
async def check_document_permission(user_id: str, document_id: str, required_permission: str):
    document = await get_document(document_id)
    if not document:
        raise HTTPException(404, "文档不存在")
    
    # 检查用户权限
    if document.owner_id == user_id:
        return True
    
    for collaborator in document.collaborators:
        if collaborator.user_id == user_id and collaborator.permission >= required_permission:
            return True
    
    raise HTTPException(403, "权限不足")
```