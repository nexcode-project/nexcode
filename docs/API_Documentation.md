# 协作文档平台 API 文档

## 1. 认证

### 1.1 登录
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password"
}
```

**响应**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user_id",
    "username": "user@example.com",
    "full_name": "User Name"
  }
}
```

### 1.2 刷新Token
```http
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

## 2. 文档管理

### 2.1 创建文档
```http
POST /api/v1/documents
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "新文档",
  "content": "# 标题\n\n内容",
  "category": "工作",
  "tags": ["重要", "项目"]
}
```

### 2.2 获取文档列表
```http
GET /api/v1/documents?page=1&limit=20&category=工作&search=关键词
Authorization: Bearer <access_token>
```

### 2.3 获取文档详情
```http
GET /api/v1/documents/{document_id}
Authorization: Bearer <access_token>
```

### 2.4 更新文档
```http
PUT /api/v1/documents/{document_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "更新的标题",
  "content": "更新的内容"
}
```

### 2.5 删除文档
```http
DELETE /api/v1/documents/{document_id}
Authorization: Bearer <access_token>
```

## 3. 协作管理

### 3.1 添加协作者
```http
POST /api/v1/documents/{document_id}/collaborators
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_email": "collaborator@example.com",
  "permission": "editor"
}
```

### 3.2 更新协作者权限
```http
PUT /api/v1/documents/{document_id}/collaborators/{user_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "permission": "reader"
}
```

### 3.3 移除协作者
```http
DELETE /api/v1/documents/{document_id}/collaborators/{user_id}
Authorization: Bearer <access_token>
```

## 4. AI助手

### 4.1 生成内容
```http
POST /api/v1/ai/generate
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "prompt": "写一个关于项目管理的段落",
  "context": "这是一个技术文档",
  "max_tokens": 500
}
```

### 4.2 优化文本
```http
POST /api/v1/ai/optimize
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "text": "需要优化的文本内容",
  "optimization_type": "grammar"
}
```

### 4.3 获取建议
```http
POST /api/v1/ai/suggest
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "content": "当前文档内容",
  "cursor_position": 150
}
```

## 5. 版本管理

### 5.1 获取版本历史
```http
GET /api/v1/documents/{document_id}/versions?page=1&limit=10
Authorization: Bearer <access_token>
```

### 5.2 获取特定版本
```http
GET /api/v1/documents/{document_id}/versions/{version_number}
Authorization: Bearer <access_token>
```

### 5.3 回滚到指定版本
```http
POST /api/v1/documents/{document_id}/revert/{version_number}
Authorization: Bearer <access_token>
```

### 5.4 版本对比
```http
GET /api/v1/documents/{document_id}/compare?from={version1}&to={version2}
Authorization: Bearer <access_token>
```

## 6. WebSocket 实时通信

### 6.1 连接
```
ws://localhost:8000/api/v1/documents/{document_id}/ws?token={access_token}
```

### 6.2 消息格式

#### 用户加入
```json
{
  "type": "user_joined",
  "user_id": "user_id",
  "username": "用户名",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 内容变更
```json
{
  "type": "content_change",
  "user_id": "user_id",
  "operation": "insert",
  "position": {
    "line": 5,
    "column": 10
  },
  "content": "插入的文本",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 光标移动
```json
{
  "type": "cursor_move",
  "user_id": "user_id",
  "position": {
    "line": 5,
    "column": 10
  },
  "selection": {
    "start": {"line": 5, "column": 10},
    "end": {"line": 5, "column": 20}
  }
}
```

## 7. 错误码

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 429 | 请求频率限制 |
| 500 | 服务器内部错误 |

## 8. 响应格式

### 8.1 成功响应
```json
{
  "success": true,
  "data": {
    // 响应数据
  },
  "message": "操作成功"
}
```

### 8.2 错误响应
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数验证失败",
    "details": {
      "field": "title",
      "reason": "标题不能为空"
    }
  }
}
```

## 9. 限制说明

- API请求频率限制：100次/分钟
- 文档大小限制：10MB
- 协作者数量限制：50人/文档
- WebSocket连接超时：30分钟无活动自动断开