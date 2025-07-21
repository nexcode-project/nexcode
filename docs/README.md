# NexCode

<div align="center">
  <img src="images/logo.png" alt="NexCode Logo" width="200">
  <h3>智能 AI 代码助手平台</h3>
  <p>基于大语言模型的全栈开发辅助工具，提供代码审查、智能问答、自动化工作流等功能</p>
</div>

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Node.js](https://img.shields.io/badge/node.js-16+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![React](https://img.shields.io/badge/React-18+-blue.svg)

</div>

## 🌟 核心特性

### 🤖 AI 驱动的代码辅助
- **智能代码审查** - 自动检测潜在bug、安全漏洞、性能问题
- **自动提交消息生成** - 基于代码变更生成规范的提交消息
- **Git 错误诊断** - 智能分析Git错误并提供解决方案
- **代码质量检查** - 全面的代码质量评估和改进建议
- **智能问答系统** - 回答开发相关问题，支持上下文理解

### 🔧 多端协同体验
- **命令行工具 (CLI)** - 强大的终端工具，集成Git工作流
- **Web 聊天界面** - 现代化的浏览器界面，支持实时对话
- **管理后台** - 完整的系统管理和监控功能
- **OpenAI API 兼容** - 完全兼容OpenAI接口，可直接替换使用

### 🔐 企业级特性
- **多重认证支持** - 用户名/密码、CAS单点登录、JWT令牌
- **用户权限管理** - 细粒度的权限控制和用户管理
- **数据统计分析** - 详细的使用统计和趋势分析
- **系统监控** - 实时的系统健康状态监控

## 🏗️ 系统架构

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   nexcode_cli   │  │   nexcode_web   │  │  nexcode_admin  │
│  (命令行工具)    │  │   (Web界面)     │  │   (管理后台)     │
└─────────┬───────┘  └─────────┬───────┘  └─────────┬───────┘
          │                    │                    │
          └────────────────────┼────────────────────┘
                               │
                    ┌─────────────────┐
                    │ nexcode_server  │
                    │ (FastAPI 后端)  │
                    └─────────┬───────┘
                              │
                    ┌─────────────────┐
                    │   数据库 & LLM   │
                    │ (SQLite/OpenAI) │
                    └─────────────────┘
```

### 架构特点
- **微服务设计** - 各组件职责分离，易于扩展维护
- **统一API网关** - 所有AI功能通过统一的FastAPI服务提供
- **客户端密钥架构** - 用户使用自己的OpenAI密钥，成本透明
- **实时数据同步** - 多端数据实时同步，体验一致

## 🚀 快速开始

### 方式一：Docker Compose (推荐)

```bash
# 1. 克隆项目
git clone https://github.com/your-org/nexcode.git
cd nexcode

# 2. 启动所有服务
cd docker
docker-compose up -d

# 3. 访问服务
# Web界面: http://localhost:3000
# 管理后台: http://localhost:5174
# API文档: http://localhost:8000/docs
```

### 方式二：本地开发

<details>
<summary>展开查看详细步骤</summary>

#### 1. 后端服务
```bash
cd nexcode_server
pip install -r requirements_server.txt

# 初始化数据库
python scripts/init_db.py

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Web界面 (可选)
```bash
cd nexcode_web
npm install
npm run dev
# 访问: http://localhost:3000
```

#### 3. 管理后台 (可选)
```bash
cd nexcode_admin
npm install
npm run dev
# 访问: http://localhost:5174
```

#### 4. CLI工具
```bash
cd nexcode_cli
pip install -e .

# 配置CLI
nexcode config set api_server.url "http://localhost:8000"
nexcode config set openai.api_key "your-openai-api-key"
```

</details>

## 💻 使用指南

### 🖥️ 命令行工具 (开发者推荐)

```bash
# 代码质量检查
nexcode check                           # 检查当前更改
nexcode check --files src/main.py       # 检查指定文件

# 智能提交
nexcode commit                          # 生成并提交
nexcode commit --dry-run                # 预览提交消息

# 智能问答
nexcode ask "如何优化这个函数？" --files src/utils.py
nexcode ask "Git rebase 和 merge 的区别？"

# Git错误诊断
nexcode diagnose                        # 诊断最后的Git错误

# 推送策略
nexcode push                            # 智能推送建议
nexcode push --dry-run                  # 预览推送策略

# 仓库分析
nexcode analyze --type overview         # 项目概览
nexcode analyze --type structure        # 结构分析
nexcode analyze --type dependencies     # 依赖分析
```

### 🌐 Web界面 (用户友好)

访问 `http://localhost:3000`，默认账号：
- **演示账号**: `demo` / `demo123`
- **管理员账号**: `admin` / `admin123`

**主要功能：**
- 🎯 **双模式AI对话** - 内置智能问答 + OpenAI GPT模型
- ⚙️ **实时参数调整** - 动态切换模型、温度、最大长度
- 💬 **上下文对话** - 自动维护对话历史，支持多轮交互
- 📱 **响应式设计** - 完美适配桌面和移动设备

### 🛠️ 管理后台 (管理员专用)

访问 `http://localhost:5174`，管理员账号：`admin` / `admin`

**核心功能：**
- 📊 **系统监控面板** - 实时状态、性能指标、资源使用
- 👥 **用户管理** - 账户管理、权限控制、API密钥管理
- 📈 **数据分析** - 提交统计、代码质量趋势、用户活跃度
- 🔧 **系统配置** - 全局设置、CAS配置、安全选项
- 🔍 **API监控** - 接口调用统计、性能监控、错误追踪

### 🔌 OpenAI API 兼容

完全兼容OpenAI接口，可直接替换：

```python
import openai

# 使用NexCode作为OpenAI的替代
client = openai.OpenAI(
    api_key="your-openai-api-key",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello, NexCode!"}]
)
```

## 📋 当前功能清单

### ✅ 已实现功能

#### 核心AI功能
- [x] **代码审查** - 基于Git diff的智能代码审查
- [x] **提交消息生成** - 自动生成符合规范的提交消息
- [x] **Git错误分析** - 智能诊断Git命令错误
- [x] **代码质量检查** - 全面的代码质量评估
- [x] **智能问答** - 支持Git、代码、工作流相关问题
- [x] **推送策略分析** - 智能推送建议和预检查
- [x] **仓库分析** - 项目结构和依赖分析

#### 用户界面
- [x] **CLI工具** - 完整的命令行界面
- [x] **Web聊天界面** - 现代化的浏览器界面
- [x] **管理后台** - 系统管理和监控面板
- [x] **响应式设计** - 多设备适配

#### 系统功能
- [x] **用户认证** - 多种认证方式支持
- [x] **权限管理** - 基于角色的访问控制
- [x] **数据统计** - 详细的使用统计和分析
- [x] **OpenAI兼容** - 完整的OpenAI API兼容层
- [x] **Docker部署** - 容器化部署支持

### 🔧 配置管理
- [x] **环境变量配置** - 灵活的环境配置
- [x] **CLI配置系统** - 本地和全局配置管理
- [x] **Prompt模板管理** - 基于TOML的提示词管理
- [x] **多模型支持** - OpenAI、Azure OpenAI等

## 🚧 规划功能

### 🎯 近期规划 (v1.3.0)

#### 增强的AI能力
- [ ] **真正的仓库分析** - 实际读取和分析代码文件结构
- [ ] **RAG智能问答** - 基于代码库内容的检索增强问答
- [ ] **上下文感知代码审查** - 结合项目历史和上下文的深度审查
- [ ] **智能代码补全** - 基于项目上下文的代码建议

#### 代码生成功能
- [ ] **单元测试生成** (`nexcode test`) - 自动生成单元测试代码
- [ ] **文档生成** (`nexcode doc`) - 自动生成函数和类的文档
- [ ] **代码脚手架** (`nexcode generate`) - 通过自然语言生成代码模板
- [ ] **代码重构助手** (`nexcode refactor`) - 智能代码重构建议

#### 安全与质量
- [ ] **依赖漏洞扫描** - 实际解析依赖文件，检查已知漏洞
- [ ] **敏感信息扫描** (`nexcode scan:secrets`) - 检测硬编码密钥等敏感信息
- [ ] **代码覆盖率分析** - 集成测试覆盖率报告
- [ ] **性能分析** - 代码性能瓶颈检测

### 🔮 中期规划 (v1.4.0)

#### CI/CD集成
- [ ] **GitHub App** - 自动PR代码审查
- [ ] **GitLab集成** - Webhook触发自动检查
- [ ] **Jenkins插件** - CI/CD流水线集成
- [ ] **自动化工作流** - 基于规则的自动化操作

#### 团队协作
- [ ] **代码审查协作** - 团队成员协作审查
- [ ] **知识库构建** - 团队知识沉淀和共享
- [ ] **代码规范检查** - 团队代码风格统一
- [ ] **技术债务跟踪** - 技术债务识别和管理

#### 高级分析
- [ ] **代码复杂度分析** - 圈复杂度、认知复杂度等指标
- [ ] **架构依赖分析** - 模块依赖关系可视化
- [ ] **代码演化分析** - 代码变更趋势和热点分析
- [ ] **开发者效率分析** - 个人和团队效率指标

### 🌟 长期愿景 (v2.0.0)

#### 智能化升级
- [ ] **多模态理解** - 支持图片、架构图等多媒体输入
- [ ] **自然语言编程** - 通过自然语言描述生成复杂功能
- [ ] **智能调试助手** - 基于错误信息的智能调试建议
- [ ] **自动化重构** - 基于最佳实践的自动代码重构

#### 生态系统
- [ ] **插件系统** - 支持第三方插件扩展
- [ ] **IDE集成** - VSCode、JetBrains等IDE插件
- [ ] **云服务版本** - SaaS版本提供
- [ ] **企业级部署** - 大规模企业部署支持

## 📊 技术栈

### 后端技术
- **FastAPI** - 高性能异步Web框架
- **SQLAlchemy** - 强大的Python ORM
- **Alembic** - 数据库版本管理
- **Pydantic** - 数据验证和序列化
- **PostgreSQL/SQLite** - 关系型数据库

### 前端技术
- **Next.js 14** - React全栈框架
- **TypeScript** - 类型安全的JavaScript
- **Tailwind CSS** - 原子化CSS框架
- **Zustand** - 轻量级状态管理
- **Framer Motion** - 动画库

### CLI工具
- **Click** - Python命令行框架
- **GitPython** - Git操作库
- **Rich** - 终端美化库
- **PyYAML** - 配置文件处理

### AI与集成
- **OpenAI API** - 大语言模型服务
- **LangChain** - LLM应用开发框架
- **Tiktoken** - Token计数工具
- **Jinja2** - 模板引擎

## 🔧 配置说明

### 环境变量配置

```bash
# OpenAI配置
OPENAI_API_KEY=sk-...                    # OpenAI API密钥
OPENAI_API_BASE=https://api.openai.com/v1  # API基础URL
OPENAI_MODEL=gpt-3.5-turbo              # 默认模型

# 数据库配置
DATABASE_URL=sqlite:///./nexcode.db      # 数据库连接字符串

# 服务配置
HOST=0.0.0.0                            # 服务监听地址
PORT=8000                               # 服务端口
DEBUG=false                             # 调试模式

# 认证配置
REQUIRE_AUTH=false                      # 是否需要认证
JWT_SECRET_KEY=your-secret-key          # JWT密钥
CAS_SERVER_URL=https://cas.example.com  # CAS服务器地址
```

### CLI配置管理

```bash
# 查看配置
nexcode config list                     # 显示所有配置
nexcode config get openai.api_key      # 获取特定配置

# 设置配置
nexcode config set openai.api_key "sk-..."
nexcode config set api_server.url "http://localhost:8000"
nexcode config set model.temperature 0.7

# 重置配置
nexcode config reset                    # 重置所有配置
```

## 🌐 API文档

### OpenAI兼容接口
- `POST /v1/chat/completions` - 聊天完成接口
- `POST /v1/completions` - 文本完成接口
- `GET /v1/models` - 模型列表接口

### NexCode专用接口
- `POST /v1/code-review` - 代码审查
- `POST /v1/commit-message` - 提交消息生成
- `POST /v1/intelligent-qa` - 智能问答
- `POST /v1/git-error-analysis` - Git错误分析
- `POST /v1/code-quality-check` - 代码质量检查
- `POST /v1/push-strategy` - 推送策略分析
- `POST /v1/repository-analysis` - 仓库分析

### 管理接口
- `POST /v1/auth/login` - 用户登录
- `GET /v1/auth/me` - 获取用户信息
- `GET /v1/users` - 用户列表
- `GET /v1/commits` - 提交历史
- `GET /v1/admin/stats` - 系统统计

## 🚀 部署指南

### Docker部署 (推荐)

```bash
# 1. 克隆项目
git clone https://github.com/your-org/nexcode.git
cd nexcode

# 2. 配置环境变量
cp docker/.env.example docker/.env
# 编辑 docker/.env 文件

# 3. 启动服务
cd docker
docker-compose up -d

# 4. 查看状态
docker-compose ps
docker-compose logs -f
```

### 手动部署

<details>
<summary>展开查看详细步骤</summary>

#### 后端部署
```bash
cd nexcode_server
pip install -r requirements_server.txt

# 配置环境变量
export OPENAI_API_KEY="your-key"
export DATABASE_URL="postgresql://user:pass@localhost/nexcode"

# 初始化数据库
python scripts/init_db.py

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 前端部署
```bash
cd nexcode_web
npm install
npm run build

# 使用nginx或其他静态服务器托管dist目录
```

#### 管理后台部署
```bash
cd nexcode_admin
npm install
npm run build

# 部署到静态服务器
```

</details>

## 🔍 监控与日志

### 健康检查
```bash
# 检查服务状态
curl http://localhost:8000/health

# 检查各组件状态
curl http://localhost:8000/health/detailed
```

### 日志管理
```bash
# 查看服务日志
docker-compose logs -f nexcode_server

# 查看特定时间范围的日志
docker-compose logs --since="2024-01-01" nexcode_server
```

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 开发流程
1. **Fork项目** - 点击右上角Fork按钮
2. **创建分支** - `git checkout -b feature/amazing-feature`
3. **提交代码** - `git commit -m 'Add amazing feature'`
4. **推送分支** - `git push origin feature/amazing-feature`
5. **创建PR** - 提交Pull Request

### 开发规范
- 遵循现有的代码风格
- 添加适当的测试用例
- 更新相关文档
- 提交信息使用[Conventional Commits](https://conventionalcommits.org/)格式

### 问题反馈
- 🐛 **Bug报告** - 使用Issue模板报告问题
- 💡 **功能建议** - 提出新功能想法
- 📚 **文档改进** - 帮助完善文档

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。

## 🙏 致谢

感谢以下开源项目和社区：
- [OpenAI](https://openai.com/) - 强大的AI能力支持
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能Web框架
- [Next.js](https://nextjs.org/) - 优秀的React框架
- [Click](https://click.palletsprojects.com/) - Python CLI框架
- [Ant Design](https://ant.design/) - 企业级UI组件

## 📞 联系我们

- **项目主页**: https://github.com/your-org/nexcode
- **文档站点**: https://nexcode.dev
- **问题反馈**: https://github.com/your-org/nexcode/issues
- **讨论区**: https://github.com/your-org/nexcode/discussions

---

<div align="center">
  <p><strong>NexCode Team</strong> - 让AI赋能每一行代码</p>
  <p>⭐ 如果这个项目对你有帮助，请给我们一个星标支持！</p>
</div>