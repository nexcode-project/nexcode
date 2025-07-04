# NexCode 数据库和用户服务使用指南

## 概述

NexCode 现在支持完整的用户管理和数据持久化功能，包括：

- 用户认证和授权
- CAS 单点登录支持
- Commit 信息追踪和分析
- API 密钥管理
- 用户会话管理

## 数据库配置

### PostgreSQL 配置 (推荐生产环境)

默认配置使用 PostgreSQL：

```env
DATABASE_URL=postgresql+asyncpg://postgres:kangkang123@localhost:5432/nexcode
```


## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements_server.txt
```

### 2. 创建数据库

如果使用 PostgreSQL，先创建数据库：

```bash
psql -h localhost -U postgres -c "CREATE DATABASE nexcode;"
```

### 3. 运行数据库迁移

```bash
alembic upgrade head
```

### 4. 初始化基础数据

```bash
python scripts/init_db.py
```

这将创建：
- 管理员用户: `admin` / `admin@nexcode.local`
- 演示用户: `demo` / `demo@nexcode.local`
- 演示用户的 API 密钥

### 5. 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API 接口

### 认证相关

- `GET /v1/auth/cas/login` - 获取 CAS 登录 URL
- `GET /v1/auth/cas/callback` - CAS 登录回调
- `POST /v1/auth/cas/verify` - 验证 CAS ticket
- `POST /v1/auth/logout` - 用户登出
- `GET /v1/auth/me` - 获取当前用户信息
- `POST /v1/auth/refresh` - 刷新 JWT token

### 用户管理

- `GET /v1/users/me` - 获取当前用户信息
- `PATCH /v1/users/me` - 更新当前用户信息
- `GET /v1/users/me/sessions` - 获取用户会话列表
- `DELETE /v1/users/me/sessions/{session_id}` - 撤销用户会话
- `GET /v1/users/me/api-keys` - 获取用户 API 密钥列表
- `POST /v1/users/me/api-keys` - 创建用户 API 密钥
- `DELETE /v1/users/me/api-keys/{api_key_id}` - 撤销用户 API 密钥

#### 管理员接口

- `GET /v1/users/` - 获取用户列表
- `GET /v1/users/{user_id}` - 获取指定用户信息
- `PATCH /v1/users/{user_id}` - 更新指定用户信息
- `DELETE /v1/users/{user_id}` - 停用用户

### Commit 信息管理

- `POST /v1/commits/` - 创建 commit 信息记录
- `GET /v1/commits/` - 获取当前用户的 commit 列表
- `GET /v1/commits/search` - 搜索 commit 信息
- `GET /v1/commits/analytics` - 获取 commit 分析数据
- `GET /v1/commits/stats` - 获取 commit 统计信息
- `GET /v1/commits/{commit_id}` - 获取单个 commit 信息
- `PATCH /v1/commits/{commit_id}` - 更新 commit 信息
- `DELETE /v1/commits/{commit_id}` - 删除 commit 信息
- `POST /v1/commits/{commit_id}/commit` - 标记 commit 为已提交
- `POST /v1/commits/{commit_id}/feedback` - 添加 commit 反馈

## 认证方式

### 1. JWT Token 认证

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/v1/users/me
```

### 2. API Key 认证

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8000/v1/users/me
```

### 3. Session Token 认证

```bash
curl -H "X-Session-Token: YOUR_SESSION_TOKEN" \
     http://localhost:8000/v1/users/me
```

或通过 Cookie：

```bash
curl --cookie "session_token=YOUR_SESSION_TOKEN" \
     http://localhost:8000/v1/users/me
```

### 4. CAS 登录认证

1. 获取 CAS 登录 URL：
```bash
curl http://localhost:8000/v1/auth/cas/login
```

2. 使用返回的 URL 进行 CAS 登录

3. 登录成功后获得 JWT token 和 session token

## 数据库模型

### User (用户表)

- `id` - 主键
- `username` - 用户名 (唯一)
- `email` - 邮箱 (唯一)
- `full_name` - 全名
- `cas_user_id` - CAS 用户ID
- `cas_attributes` - CAS 用户属性 (JSON)
- `is_active` - 是否激活
- `is_superuser` - 是否超级用户
- `created_at` - 创建时间
- `updated_at` - 更新时间
- `last_login` - 最后登录时间

### CommitInfo (Commit信息表)

- `id` - 主键
- `user_id` - 用户ID (外键)
- `repository_url` - 仓库URL
- `repository_name` - 仓库名称
- `branch_name` - 分支名称
- `commit_hash` - Commit哈希
- `user_selected_message` - 用户选择的commit信息
- `ai_generated_message` - AI生成的commit信息
- `final_commit_message` - 最终使用的commit信息
- `diff_content` - Git diff内容
- `files_changed` - 变更文件列表 (JSON)
- `lines_added` - 新增行数
- `lines_deleted` - 删除行数
- `ai_model_used` - 使用的AI模型
- `ai_parameters` - AI调用参数 (JSON)
- `generation_time_ms` - AI生成耗时(毫秒)
- `user_rating` - 用户评分 (1-5)
- `user_feedback` - 用户反馈
- `commit_style` - Commit风格
- `status` - 状态 (draft/committed/failed)
- `tags` - 自定义标签 (JSON)
- `created_at` - 创建时间
- `updated_at` - 更新时间
- `committed_at` - 提交时间

### UserSession (用户会话表)

- `id` - 主键
- `user_id` - 用户ID (外键)
- `session_token` - 会话令牌
- `cas_ticket` - CAS票据
- `ip_address` - IP地址
- `user_agent` - 用户代理
- `created_at` - 创建时间
- `expires_at` - 过期时间
- `last_activity` - 最后活动时间
- `is_active` - 是否激活

### APIKey (API密钥表)

- `id` - 主键
- `user_id` - 用户ID (外键)
- `key_name` - 密钥名称
- `key_hash` - 密钥哈希
- `key_prefix` - 密钥前缀
- `scopes` - 权限范围 (JSON)
- `rate_limit` - 速率限制
- `usage_count` - 使用次数
- `last_used` - 最后使用时间
- `is_active` - 是否激活
- `created_at` - 创建时间
- `expires_at` - 过期时间

## 示例用法

### 创建 API 密钥

```bash
curl -X POST "http://localhost:8000/v1/users/me/api-keys" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "key_name": "My API Key",
       "scopes": ["read", "write"],
       "rate_limit": 1000
     }'
```

### 使用 commit 信息接口

```bash
# 生成 commit 信息 (自动保存到数据库)
curl -X POST "http://localhost:8000/v1/commit-message" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "diff": "your git diff content",
       "style": "conventional",
       "context": {
         "repository_name": "my-project",
         "branch_name": "feature/new-feature"
       }
     }'

# 获取用户的 commit 统计
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "http://localhost:8000/v1/commits/stats"

# 获取 commit 分析数据
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "http://localhost:8000/v1/commits/analytics"
```

## 环境变量配置

创建 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:kangkang123@localhost:5432/nexcode

# JWT配置
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CAS配置
CAS_SERVER_URL=https://cas.example.com
CAS_SERVICE_URL=http://localhost:8000/v1/auth/cas/callback

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

## 数据库迁移

### 创建新迁移

```bash
alembic revision --autogenerate -m "Description of changes"
```

### 应用迁移

```bash
alembic upgrade head
```

### 回滚迁移

```bash
alembic downgrade -1
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查 PostgreSQL 服务是否运行
   - 验证数据库连接参数
   - 确保数据库存在

2. **CAS 认证失败**
   - 检查 CAS 服务器 URL 配置
   - 验证回调 URL 配置
   - 确保网络连通性

3. **API 密钥验证失败**
   - 检查密钥是否已过期
   - 验证密钥格式正确
   - 确保密钥未被撤销

### 日志调试

开启调试模式查看详细日志：

```bash
export DEBUG=true
uvicorn app.main:app --log-level debug
``` 