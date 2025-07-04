# NexCode 文档

欢迎使用 NexCode 文档！这里包含了项目的完整文档。

## 📚 文档目录

### 核心组件
- [**Web 应用**](../nexcode_web/README.md) - 现代化的 React/Next.js Web 用户界面
- [**服务器文档**](README_Server.md) - NexCode 服务器的配置和部署指南
- [**CLI 文档**](README_CLI.md) - NexCode 命令行工具的使用指南
- [**数据库文档**](README_Database.md) - 数据库架构和迁移指南

### API 文档
- [**OpenAI 兼容 API**](README_OpenAI_API.md) - OpenAI 兼容接口的使用说明

## 🚀 快速开始

### 使用 Docker (推荐)

1. 确保已安装 Docker 和 Docker Compose
2. 克隆项目到本地
3. 进入项目目录并启动服务：

```bash
cd docker
docker-compose up -d
```

### 手动安装

1. **安装服务器**：
   ```bash
   cd nexcode_server
   pip install -r requirements_server.txt
   python scripts/init_db.py  # 初始化数据库
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **安装 CLI**：
   ```bash
   cd nexcode_cli
   pip install -e .
   nexcode --help
   ```

## 🔧 配置

### 环境变量

服务器支持以下环境变量：

- `OPENAI_API_BASE` - OpenAI API 基础 URL (默认: https://api.openai.com/v1)
- `OPENAI_MODEL` - 默认模型 (默认: gpt-3.5-turbo)
- `DATABASE_URL` - 数据库连接字符串
- `HOST` - 服务器监听地址 (默认: 0.0.0.0)
- `PORT` - 服务器端口 (默认: 8000)
- `REQUIRE_AUTH` - 是否需要认证 (默认: false)
- `API_TOKEN` - API 令牌

## 📖 功能特性

### 🤖 AI 辅助
- **提交消息生成** - 基于代码变更自动生成规范的提交消息
- **代码质量检查** - AI 驱动的代码质量分析
- **代码审查** - 智能代码审查建议
- **错误诊断** - Git 错误的智能分析和解决方案

### 🔐 认证系统
- **CAS 单点登录** - 企业级认证支持
- **JWT 令牌** - 安全的 API 访问
- **API 密钥** - 程序化访问支持
- **会话管理** - 完整的用户会话控制

### 📊 数据管理
- **提交历史** - 详细的提交信息记录
- **用户分析** - 代码提交统计和分析
- **反馈系统** - 用户反馈收集和处理

### 🔌 集成能力
- **OpenAI 兼容** - 完全兼容 OpenAI API 格式
- **Git 集成** - 无缝的 Git 工作流集成
- **CLI 工具** - 强大的命令行界面

## 🏗️ 架构概览

```
NexCode
├── nexcode_web/       # React/Next.js Web 应用
│   ├── src/          # 源代码
│   ├── public/       # 静态资源
│   └── package.json  # 依赖配置
├── nexcode_server/    # FastAPI 后端服务
│   ├── app/          # 应用核心代码
│   ├── alembic/      # 数据库迁移
│   ├── prompts/      # AI 提示模板
│   └── scripts/      # 部署脚本
├── nexcode_cli/      # Python CLI 工具
│   └── nexcode/      # CLI 核心代码
├── docker/          # Docker 配置
└── docs/           # 项目文档
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](../LICENSE) 文件了解详情。

## 🆘 支持

如果您遇到问题或有疑问：

1. 查看相关文档
2. 检查 [Issues](https://github.com/your-org/nexcode/issues)
3. 创建新的 Issue 描述问题

---

**注意**: 本文档会持续更新，请定期查看最新版本。 