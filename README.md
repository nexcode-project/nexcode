# NexCode

一个基于大语言模型的智能代码辅助工具，提供代码审查、自动提交消息生成、问答等功能。

## 🌟 主要特性

- **🔧 CLI 工具** - 强大的命令行工具，支持代码审查、提交消息生成等
- **🌐 Web 界面** - 现代化的聊天界面，支持双模式 AI 对话
- **🔗 OpenAI 兼容** - 完全兼容 OpenAI API，可直接替换使用
- **🔐 多重认证** - 支持用户名/密码和 CAS 统一认证
- **📊 数据管理** - 完整的用户和会话管理系统

## 项目架构

NexCode 采用现代化的全栈架构：

- **nexcode_cli**: 命令行客户端，负责用户交互和 Git 操作
- **nexcode_server**: FastAPI 后端服务，提供 AI 功能和 API 接口
- **nexcode_web**: Next.js 前端应用，提供 Web 聊天界面

### 架构特点

- **统一的客户端密钥架构**: CLI 传递 OpenAI API 密钥给服务端
- **双模式 AI 支持**: 内置智能问答 + 标准 OpenAI Chat Completion
- **Token 认证**: 支持 Bearer Token 认证保护 API 接口
- **自动 Git 根目录**: CLI 可在任意子目录中自动找到 Git 根目录执行操作
- **职责分离**: CLI 负责用户交互，服务端负责 Prompt 管理，前端负责 Web 体验

## 🚀 快速开始

### 方式一：Docker Compose (推荐)

```bash
# 克隆项目
git clone <repository-url>
cd nexcode

# 使用 Docker Compose 启动所有服务
docker-compose up -d

# 访问 Web 界面
open http://localhost:3000
```

### 方式二：本地开发

#### 1. 启动后端服务

```bash
cd nexcode_server
pip install -r requirements.txt

# 创建 .env 文件
echo "OPENAI_API_KEY=your-openai-api-key" > .env

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. 启动前端服务 (可选)

```bash
cd nexcode_web
npm install
npm run dev

# 访问 http://localhost:3000
```

#### 3. 安装 CLI 工具

```bash
cd nexcode_cli
pip install -e .

# 配置 CLI
nexcode config set api_server.base_url "http://localhost:8000"
nexcode config set openai.api_key "your-openai-api-key"
```

## 💻 使用方式

### 1. Web 界面 (推荐新用户)

访问 `http://localhost:3000`，使用以下账号登录：

- **演示账号**: `demo` / `demo123`
- **管理员账号**: `admin` / `admin123`

功能特性：
- 🎯 **双模式 AI** - 内置智能问答 vs OpenAI GPT 模型
- ⚙️ **动态设置** - 实时切换模型、调整参数
- 💬 **流畅对话** - 自动维护上下文，支持多轮对话
- 📱 **响应式设计** - 完美支持桌面和移动设备

### 2. 标准 OpenAI API

完全兼容 OpenAI API，可以直接替换：

```python
import openai

client = openai.OpenAI(
    api_key="your-openai-api-key",
    base_url="http://localhost:8000/v1"  # 指向 NexCode
)

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### 3. CLI 工具 (开发者推荐)

```bash
# 代码检查和审查
nexcode check
nexcode check --files src/main.py

# 自动生成提交消息
nexcode commit
nexcode commit --dry-run

# 代码问答
nexcode ask "这个文件的主要功能是什么？" --files src/main.py

# 智能推送
nexcode push
```

## 📚 详细文档

- **[Web 界面使用指南](./docs/Web_Interface.md)** - 前端功能详细说明
- **[OpenAI API 兼容文档](./docs/README_OpenAI_API.md)** - API 接口使用指南
- **[CLI 工具文档](./docs/CLI_Usage.md)** - 命令行工具使用说明
- **[部署指南](./docs/Deployment.md)** - 生产环境部署
- **[开发指南](./docs/Development.md)** - 开发环境配置

## 🔧 配置选项

### 环境变量

```bash
# OpenAI 配置
OPENAI_API_KEY=sk-...                    # OpenAI API 密钥
OPENAI_API_BASE=https://api.openai.com/v1  # API 基础 URL
OPENAI_MODEL=gpt-3.5-turbo              # 默认模型

# 数据库配置 (自动创建 SQLite)
DATABASE_URL=sqlite:///./nexcode.db

# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=false

# 认证配置 (可选)
REQUIRE_AUTH=false
API_TOKEN=your-server-token
```

### CLI 配置

```bash
# 查看所有配置
nexcode config list

# 设置配置
nexcode config set openai.api_key "sk-..."
nexcode config set api_server.base_url "http://localhost:8000"

# 删除配置
nexcode config unset api_server.token
```

## 🌐 API 端点

### OpenAI 兼容接口
- `POST /v1/chat/completions` - Chat Completions API
- `POST /v1/completions` - Text Completions API

### NexCode 专用接口
- `POST /v1/code-review` - 代码审查
- `POST /v1/commit-message` - 提交消息生成
- `POST /v1/intelligent-qa` - 智能问答
- `POST /v1/auth/login` - 用户登录

### 认证接口
- `POST /v1/auth/login` - 密码登录
- `GET /v1/auth/cas/login` - CAS 登录
- `GET /v1/auth/me` - 获取用户信息
- `POST /v1/auth/logout` - 退出登录

## 📊 技术栈

### 后端
- **FastAPI** - 现代化的 Python Web 框架
- **SQLAlchemy** - SQL 工具包和 ORM
- **Alembic** - 数据库迁移工具
- **Pydantic** - 数据验证和设置管理
- **PostgreSQL/SQLite** - 数据库支持

### 前端
- **Next.js 14** - React 全栈框架
- **TypeScript** - 类型安全的 JavaScript
- **Tailwind CSS** - 实用优先的 CSS 框架
- **Zustand** - 轻量级状态管理
- **Framer Motion** - 动画库

### CLI
- **Click** - Python 命令行界面库
- **GitPython** - Git 仓库操作
- **Rich** - 丰富的终端输出

## 🚀 部署

### Docker 部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 手动部署

```bash
# 后端
cd nexcode_server
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端
cd nexcode_web
npm install && npm run build
npm start
```

## 🔄 更新日志

### v1.2.0 (当前版本)
- ✅ 新增现代化 Web 聊天界面
- ✅ 完整 OpenAI API 兼容支持
- ✅ 双模式 AI 对话 (内置 + OpenAI)
- ✅ 用户认证和会话管理
- ✅ 响应式设计和动画效果
- ✅ 修复登录重定向问题

### v1.1.0
- ✅ CLI 工具完整功能
- ✅ 代码审查和提交消息生成
- ✅ FastAPI 后端架构
- ✅ 基础 API 接口

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[MIT License](LICENSE)

## 开发指南

### 项目结构

```