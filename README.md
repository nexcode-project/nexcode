# NexCode

一个基于大语言模型的智能代码辅助工具，提供代码审查、自动提交消息生成、问答等功能。

## 项目架构

NexCode 采用客户端-服务端架构：

- **nexcode_cli**: 命令行客户端，负责用户交互和 Git 操作
- **nexcode_server**: 后端服务，负责 Prompt 管理和 LLM 交互

### 架构特点

- **统一的客户端密钥架构**: CLI 传递 OpenAI API 密钥给服务端
- **Token 认证**: 支持 Bearer Token 认证保护 API 接口
- **自动 Git 根目录**: CLI 可在任意子目录中自动找到 Git 根目录执行操作
- **职责分离**: CLI 负责用户交互，服务端负责 Prompt 管理

## 快速开始

### 1. 安装服务端

```bash
cd nexcode_server
pip install -r requirements.txt
```

### 2. 配置服务端

创建 `.env` 文件：

```bash
# API 认证 Token（可选）
API_TOKEN=your-secret-token
REQUIRE_AUTH=true

# 服务配置
HOST=0.0.0.0
PORT=8000
```
test

### 3. 启动服务端

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. 安装 CLI

```bash
cd nexcode_cli
pip install -e .
```

### 5. 配置 CLI

```bash
# 配置服务端地址
nexcode config set api_server.base_url "http://localhost:8000"

# 配置认证 Token（如果服务端启用了认证）
nexcode config set api_server.token "your-secret-token"

# 配置 OpenAI API Key
nexcode config set openai.api_key "your-openai-api-key"
```

## 使用指南

### 代码检查和审查

```bash
# 检查当前分支的变更
nexcode check

# 检查指定文件
nexcode check --files src/main.py

# 检查特定 commit
nexcode check --commit abc123
```

### 自动生成提交消息

```bash
# 生成并提交（会提示确认）
nexcode commit

# 直接提交不确认
nexcode commit --no-confirm

# 只生成消息不提交
nexcode commit --dry-run
```

### 代码问答

```bash
# 询问代码相关问题
nexcode ask "如何优化这个函数的性能？"

# 询问特定文件
nexcode ask "这个文件的主要功能是什么？" --files src/main.py
```

### 智能推送

```bash
# 推送前自动检查和生成提交消息
nexcode push

# 推送到指定分支
nexcode push --branch feature/new-feature
```

## 配置管理

### 查看配置

```bash
# 查看所有配置
nexcode config list

# 查看特定配置
nexcode config get openai.api_key
```

### 设置配置

```bash
# 设置 OpenAI API Key
nexcode config set openai.api_key "sk-..."

# 设置服务端地址
nexcode config set api_server.base_url "https://your-server.com"

# 设置认证 Token
nexcode config set api_server.token "your-token"
```

### 删除配置

```bash
nexcode config unset api_server.token
```

## API 文档

服务端启动后，可以访问：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API 端点

### 代码审查
- `POST /api/v1/code-review` - 代码审查
- `POST /api/v1/git-error` - Git 错误分析

### 提交辅助
- `POST /api/v1/commit-qa` - 提交相关问答

## 开发指南

### 项目结构

```
nexcode/
├── nexcode_cli/          # CLI 客户端
│   ├── nexcode/
│   │   ├── commands/     # 命令实现
│   │   ├── config.py     # 配置管理
│   │   ├── llm/         # LLM 服务
│   │   └── utils/       # 工具函数
│   └── README.md
├── nexcode_server/       # 后端服务
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── core/        # 核心功能
│   │   ├── models/      # 数据模型
│   │   └── services/    # 业务逻辑
│   └── README.md
└── README.md            # 项目总览
```

### 开发环境设置

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd nexcode
   ```

2. **设置虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # 或
   venv\Scripts\activate     # Windows
   ```

3. **安装依赖**
   ```bash
   # 安装服务端依赖
   cd nexcode_server
   pip install -r requirements.txt
   
   # 安装 CLI 依赖
   cd ../nexcode_cli
   pip install -e .
   ```

4. **运行测试**
   ```bash
   # 在对应目录下运行测试
   pytest
   ```

## 特性

- ✅ **智能代码审查**: 基于 LLM 的代码质量分析
- ✅ **自动提交消息**: 根据代码变更自动生成规范的提交消息
- ✅ **代码问答**: 针对代码库的智能问答
- ✅ **Git 集成**: 深度集成 Git 工作流
- ✅ **配置管理**: 灵活的配置系统
- ✅ **Token 认证**: 安全的 API 访问控制
- ✅ **自动目录定位**: 在任意子目录中自动找到 Git 根目录

## 环境要求

- Python 3.8+
- Git
- OpenAI API Key

## 许可证

[添加许可证信息]

## 贡献

欢迎提交 Issue 和 Pull Request！

## 支持

如有问题，请提交 Issue 或联系维护者。 