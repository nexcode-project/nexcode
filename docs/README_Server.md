# NexCode LLM Proxy Server

NexCode 项目的 FastAPI LLM 代理服务端，负责处理来自命令行工具的请求并与大语言模型交互。

## 功能特性

- 🚀 **FastAPI 框架**：高性能异步 Web 框架
- 🧠 **多 LLM 支持**：支持 OpenAI、Azure OpenAI 等
- 📝 **灵活 Prompt 配置**：基于 TOML 文件的 Prompt 管理
- 🔧 **模块化设计**：每个接口独立文件，易于维护
- 📊 **自动 API 文档**：内置 Swagger UI 和 ReDoc
- 🔍 **健康检查**：内置服务状态监控
- 🔑 **灵活密钥管理**：支持客户端传递API密钥或服务端统一管理

## 架构设计

NexCode 采用客户端密钥架构：
- **客户端负责**：用户交互、数据收集、API密钥管理
- **服务端负责**：Prompt管理、LLM调用代理、结果处理
- **密钥传递**：CLI 将本地配置的 OpenAI API 密钥传递给服务端使用
- **账单隔离**：每个用户使用自己的 API 配额，无需担心费用分摊
- **部署简化**：服务端无需配置 OpenAI API 密钥，降低部署复杂度

## API 接口

### 1. Git 错误处理
- **POST** `/v1/git-error/`
- 分析 Git 命令错误并提供解决方案

### 2. 代码审查
- **POST** `/v1/code-review/`
- 分析 Git diff 并检测潜在问题

### 3. Commit 问答
- **POST** `/v1/commit-qa/`
- 回答 Git 和版本控制相关问题

## 快速开始

### 1. 环境要求

- Python 3.8+
- OpenAI API Key（或其他支持的 LLM 服务）

### 2. 安装依赖

```bash
cd nexcode_server
pip install -r requirements.txt
```

### 3. 环境配置

创建 `.env` 文件或设置环境变量：

```bash
# 基础配置
export OPENAI_API_BASE="https://api.openai.com/v1"  # 可选
export OPENAI_MODEL="gpt-3.5-turbo"  # 可选
export HOST="0.0.0.0"  # 可选
export PORT="8000"  # 可选
export DEBUG="true"  # 可选，开发环境使用

# 认证配置（可选）
export REQUIRE_AUTH="true"           # 启用认证
export API_TOKEN="your-secret-token" # 设置访问令牌
```

**注意**：不需要设置 `OPENAI_API_KEY`，因为 API 密钥由客户端提供。

### 4. 启动服务

#### 开发环境
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 生产环境
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

#### 使用 Python 直接运行
```bash
python app/main.py
```

### 5. 访问文档

启动后访问以下地址：

- **API 文档（Swagger UI）**: http://localhost:8000/docs
- **API 文档（ReDoc）**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 | 是否必需 |
|--------|------|---------|----------|
| `OPENAI_API_BASE` | OpenAI API 基础 URL | `https://api.openai.com/v1` | 否 |
| `OPENAI_MODEL` | 使用的模型名称 | `gpt-3.5-turbo` | 否 |
| `MAX_TOKENS` | 最大输出令牌数 | `1500` | 否 |
| `TEMPERATURE` | 模型温度参数 | `0.7` | 否 |
| `SOLUTION_TEMPERATURE` | 解决方案温度参数 | `0.3` | 否 |
| `HOST` | 服务监听地址 | `0.0.0.0` | 否 |
| `PORT` | 服务监听端口 | `8000` | 否 |
| `DEBUG` | 调试模式 | `False` | 否 |
| `API_TOKEN` | API 访问令牌 | - | 否 |
| `REQUIRE_AUTH` | 是否需要认证 | `False` | 否 |

**说明**：OpenAI API 密钥由客户端在请求中提供，服务端无需配置。

### Prompt 配置

Prompt 配置文件位于 `prompts/` 目录，采用 TOML 格式：

```toml
[system]
content = "系统提示词"

[user]
template = """
用户提示词模板
{{ variable_name }}
"""
```

支持的变量：
- **git_error**: `{{ command }}`, `{{ error_message }}`
- **code_review**: `{{ diff }}`
- **commit_qa**: `{{ question }}`

## API 使用示例

### Git 错误处理

```bash
curl -X POST "http://localhost:8000/v1/git-error/" \
  -H "Content-Type: application/json" \
  -d '{
    "command": ["git", "push"],
    "error_message": "error: failed to push some refs to origin/main",
    "api_key": "your-openai-api-key"
  }'
```

如果启用了认证，需要添加认证头：
```bash
curl -X POST "http://localhost:8000/v1/git-error/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-access-token" \
  -d '{
    "command": ["git", "push"],
    "error_message": "error: failed to push some refs to origin/main",
    "api_key": "your-openai-api-key"
  }'
```

### 代码审查

```bash
curl -X POST "http://localhost:8000/v1/code-review/" \
  -H "Content-Type: application/json" \
  -d '{
    "diff": "--- a/file.py\n+++ b/file.py\n@@ -1,3 +1,4 @@\n def func():\n+    password = \"123456\"\n     return True",
    "api_key": "your-openai-api-key"
  }'
```

### Commit 问答

```bash
curl -X POST "http://localhost:8000/v1/commit-qa/" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "如何撤销最后一次提交？",
    "api_key": "your-openai-api-key"
  }'
```

## 部署

### Docker 部署

1. 创建 Dockerfile：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. 构建和运行：

```bash
docker build -t nexcode-server .
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key nexcode-server
```

### 多端口部署

可以启动多个实例监听不同端口，使用不同的配置：

```bash
# 端口 8000 - 默认配置
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 端口 8001 - 不同模型配置
OPENAI_MODEL=gpt-4 uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## 项目结构

```
nexcode_server/
├── app/
│   ├── main.py                   # FastAPI 入口
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py       # 路由聚合
│   │       ├── git_error.py      # Git 错误处理
│   │       ├── code_review.py    # 代码审查
│   │       └── commit_qa.py      # Commit 问答
│   ├── core/
│   │   ├── config.py             # 配置管理
│   │   ├── llm_client.py         # LLM 客户端
│   │   └── prompt_loader.py      # Prompt 加载器
│   └── models/
│       └── schemas.py            # 数据模型
├── prompts/                      # Prompt 配置
│   ├── git_error.toml
│   ├── code_review.toml
│   └── commit_qa.toml
├── requirements.txt
└── README.md
```

## 开发指南

### 添加新接口

1. 在 `app/models/schemas.py` 中添加请求/响应模型
2. 在 `prompts/` 中创建对应的 TOML 配置文件
3. 在 `app/api/v1/` 中创建新的路由文件
4. 在 `app/api/v1/__init__.py` 中注册新路由

### 自定义 Prompt

直接编辑 `prompts/` 目录下的 TOML 文件，支持模板变量替换。

### 支持新的 LLM

在 `app/core/llm_client.py` 中添加新的客户端实现。

## 许可证

[项目许可证信息] 