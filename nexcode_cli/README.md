# 🚀 NexCode - AI-Powered Git Assistant with Microservices Architecture

NexCode 是一个基于大语言模型的智能 Git 助手，采用微服务架构设计，将功能解耦为命令行工具和LLM代理服务端，提供更好的可维护性和扩展性。

## 🏗️ 项目架构

```
NexCode 项目
├── nexcode_cli/          # 命令行工具（客户端）
│   ├── 数据采集          # Git 操作、错误信息收集
│   ├── 用户交互          # CLI 命令和界面
│   └── HTTP 客户端       # 与服务端通信
├── nexcode_server/       # FastAPI LLM 代理服务端
│   ├── API 接口          # RESTful API 服务
│   ├── Prompt 管理       # TOML 配置文件
│   ├── LLM 调用          # 多模型支持
│   └── 策略配置          # 多端口、多策略
└── 文档/                 # 设计文档和说明
```

## ✨ 核心特性

### 🔧 命令行工具 (CLI)
- **智能 Git 助手**：自动分析 Git 错误并提供解决方案
- **代码审查**：检测代码变更中的潜在问题和安全隐患
- **AI 问答**：回答 Git 和版本控制相关问题
- **双模式支持**：可直接调用 LLM 或通过代理服务端
- **灵活配置**：支持本地和全局配置

### 🚀 LLM 代理服务端
- **FastAPI 框架**：高性能异步 Web 服务
- **模块化设计**：每个接口独立文件，易于维护
- **Prompt 配置化**：基于 TOML 文件的灵活 Prompt 管理
- **多模型支持**：OpenAI、Azure OpenAI、Qwen 等
- **多端口部署**：支持不同策略和配置的多实例部署
- **灵活密钥管理**：支持客户端传递API密钥或服务端统一管理

## 🔑 架构设计

NexCode 采用客户端密钥架构，实现清晰的职责分离：

- **CLI 端（客户端）**：
  - 用户交互和命令处理
  - Git 数据收集和分析
  - OpenAI API 密钥管理
  - HTTP 请求发送

- **服务端**：
  - Prompt 模板管理
  - LLM 调用代理
  - 多模型支持
  - 结果格式化

**密钥流程**：CLI 将本地配置的 OpenAI API 密钥随请求发送给服务端，服务端代为调用 LLM API，实现了用户账单隔离和服务端部署简化。

## 🚀 快速开始

### 1. 部署 LLM 代理服务端

```bash
cd nexcode_server

# 安装依赖
pip install -r requirements.txt

# 服务端无需配置 OpenAI API 密钥

# 启动服务端
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. 配置并使用 CLI 工具

```bash
cd nexcode_cli

# 安装依赖
pip install -r requirements.txt

# 配置服务端地址和 OpenAI API 密钥
nexcode config set api_server.url "http://localhost:8000"
nexcode config set api.key "your-openai-api-key"

# 使用示例
nexcode check                    # 代码审查
nexcode ask "如何撤销提交？"      # AI 问答
```

## 📚 详细文档

### 设计文档
- [**LLM_SERVER_DESIGN.md**](LLM_SERVER_DESIGN.md) - 完整的架构设计和技术方案

### 子项目文档
- [**nexcode_server/README.md**](nexcode_server/README.md) - 服务端部署和 API 文档
- [**nexcode_cli/README.md**](nexcode_cli/README.md) - CLI 工具使用指南

## 🔧 API 接口

### Git 错误处理
```bash
POST /v1/git-error/
Content-Type: application/json

{
  "command": ["git", "push"],
  "error_message": "error: failed to push some refs"
}
```

### 代码审查
```bash
POST /v1/code-review/
Content-Type: application/json

{
  "diff": "--- a/file.py\n+++ b/file.py\n..."
}
```

### Commit 问答
```bash
POST /v1/commit-qa/
Content-Type: application/json

{
  "question": "如何撤销最后一次提交？"
}
```

## ⚙️ 配置管理

### 服务端配置（环境变量）
```bash
# 无需配置 OPENAI_API_KEY，由客户端提供
OPENAI_API_BASE=https://api.openai.com/v1  # API 基础 URL
OPENAI_MODEL=gpt-3.5-turbo           # 模型名称
MAX_TOKENS=1500                      # 最大令牌数
HOST=0.0.0.0                         # 监听地址
PORT=8000                            # 监听端口
```

### CLI 配置
```yaml
# ~/.config/nexcode/config.yaml
api_server:
  url: "http://localhost:8000"       # 服务端 URL

api:
  key: ""                            # OpenAI API 密钥
  
commit:
  style: "conventional"              # 提交消息风格
  check_bugs_by_default: false      # 默认代码检查
```

## 🎯 使用场景

### 开发者个人使用
```bash
# 启动本地服务端
cd nexcode_server && uvicorn app.main:app --port 8000

# 使用 CLI 工具
cd your-project && nexcode check
```

### 团队/企业部署
```bash
# 服务端部署到云服务器
docker run -p 8000:8000 nexcode-server

# 团队成员配置 CLI
nexcode config set api_server.url "http://your-server:8000"
```

### 多策略部署
```bash
# 不同端口使用不同模型/策略
OPENAI_MODEL=gpt-3.5-turbo uvicorn app.main:app --port 8000
OPENAI_MODEL=gpt-4 uvicorn app.main:app --port 8001
```

## 🔄 工作流程

1. **用户操作**：在 CLI 中执行 Git 相关命令
2. **数据采集**：CLI 收集 Git 状态、错误信息、代码变更
3. **API 调用**：通过 HTTP 发送请求到服务端
4. **Prompt 渲染**：服务端加载 TOML 配置，渲染提示词
5. **LLM 交互**：调用大语言模型获取响应
6. **结果返回**：格式化结果返回给 CLI
7. **用户展示**：CLI 展示结果给用户

## 🚢 部署选项

### Docker 部署
```bash
# 构建服务端镜像
cd nexcode_server
docker build -t nexcode-server .

# 运行容器
docker run -p 8000:8000 nexcode-server
```

### 多实例部署
```bash
# 负载均衡配置（Nginx）
upstream nexcode_backend {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}
```

## 🔍 监控和运维

### 健康检查
```bash
curl http://localhost:8000/health
```

### API 文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 贡献指南

1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 开发环境设置
```bash
# 克隆仓库
git clone https://github.com/yourusername/nexcode.git
cd nexcode

# 设置服务端开发环境
cd nexcode_server
pip install -r requirements.txt

# 设置 CLI 开发环境
cd ../nexcode_cli
pip install -r requirements.txt
```

## 📝 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- OpenAI 提供强大的 GPT 模型
- FastAPI 社区提供优秀的 Web 框架
- 所有为 NexCode 贡献代码的开发者

---

**用 AI 助力，让 Git 操作更智能！🚀✨**