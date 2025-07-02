# NexCode CLI

NexCode 项目的命令行工具（客户端），负责与用户交互、数据采集，并通过 HTTP API 与 LLM 代理服务端通信。

## 功能特性

- 🚀 **智能 Git 助手**：自动分析 Git 错误并提供解决方案
- 🔍 **代码审查**：检测代码变更中的潜在问题和安全隐患
- 💬 **AI 问答**：回答 Git 和版本控制相关问题
- ⚙️ **灵活配置**：支持本地和全局配置
- 🔌 **双模式支持**：可直接调用 LLM 或通过代理服务端

## 工作模式

CLI 工具支持两种工作模式：

### 1. API 服务端模式（推荐）
- 通过 HTTP API 调用 FastAPI 服务端
- 服务端统一管理 LLM 交互和 Prompt 配置
- 支持多端口、多策略部署

### 2. 直连模式
- 直接调用 OpenAI API
- 适用于无法部署服务端的场景
- 保持与原版本的兼容性

## 快速开始

### 1. 安装依赖

```bash
cd nexcode_cli
pip install -r requirements.txt
```

### 2. 配置

#### 全局配置
```bash
# 如果使用 API 服务端模式（默认）
nexcode config set api_server.url "http://your-server:8000"
nexcode config set api_server.enabled true
nexcode config set api_server.token "your-api-token"  # 如果服务端启用了认证

# 如果使用直连模式
nexcode config set api_server.enabled false
nexcode config set api.key "your-openai-api-key"
nexcode config set model.name "gpt-3.5-turbo"
```

#### 本地仓库配置
```bash
# 在项目根目录初始化本地配置
nexcode init
```

### 3. 使用示例

#### Git 错误诊断
```bash
# 当 git 命令出错时自动获取解决方案
git push  # 失败
nexcode diagnose
```

#### 代码审查
```bash
# 检查当前更改
nexcode check

# 检查特定提交的更改
nexcode check --commit HEAD~1
```

#### AI 问答
```bash
# 询问 Git 相关问题
nexcode ask "如何撤销最后一次提交？"
nexcode ask "git rebase 和 git merge 的区别是什么？"
```

## 配置详解

### 全局配置文件

位置：`~/.config/nexcode/config.yaml`

```yaml
api:
  key: ""                    # OpenAI API 密钥（直连模式使用）
  base_url: ""              # OpenAI API 基础 URL

api_server:
  url: "http://localhost:8000"  # LLM 代理服务端 URL
  enabled: true                 # 是否启用服务端模式
  token: ""                     # API 访问令牌（如果服务端启用认证）

model:
  name: ""                  # 模型名称
  commit_temperature: 0.7   # 提交消息生成温度
  solution_temperature: 0.5 # 解决方案生成温度
  max_tokens_commit: 60     # 提交消息最大令牌数
  max_tokens_solution: 512  # 解决方案最大令牌数

commit:
  style: "conventional"           # 提交消息风格
  check_bugs_by_default: false   # 是否默认进行代码检查
```

### 本地配置文件

位置：`.nexcode/config.yaml`

```yaml
repository:
  type: github              # 仓库类型
  remote: origin           # 远程仓库名
  target_branch: main      # 目标分支
  push_command: "git push {remote} {branch}"  # 推送命令模板

commit:
  style: null              # 提交风格覆盖（null = 使用全局设置）
  check_bugs_by_default: null  # 代码检查覆盖
```

## 命令参考

### 配置管理
```bash
nexcode config list                    # 显示所有配置
nexcode config get api_server.url     # 获取特定配置
nexcode config set api_server.url "http://localhost:8001"  # 设置配置
nexcode config reset                   # 重置到默认配置
```

### 本地仓库初始化
```bash
nexcode init                          # 创建本地配置文件
```

### Git 操作
```bash
nexcode diagnose                      # 诊断最后的 Git 错误
nexcode check                         # 检查当前代码更改
nexcode check --commit HEAD~1        # 检查指定提交
nexcode ask "your question"          # AI 问答
```

### 推送操作
```bash
nexcode push                          # 智能推送（根据仓库类型）
nexcode push --dry-run               # 预览推送命令
```

## 故障排除

### 连接问题

如果无法连接到 API 服务端：

1. 检查服务端是否正在运行：
   ```bash
   curl http://localhost:8000/health
   ```

2. 检查配置：
   ```bash
   nexcode config get api_server.url
   ```

3. 切换到直连模式：
   ```bash
   nexcode config set api_server.enabled false
   nexcode config set api.key "your-openai-api-key"
   ```

### 权限问题

#### API 服务端认证问题

如果遇到 401 认证错误：

1. 检查服务端是否启用了认证：
   ```bash
   # 服务端日志中会显示 REQUIRE_AUTH 设置
   ```

2. 设置 API Token：
   ```bash
   nexcode config set api_server.token "your-secret-token"
   ```

3. 确保 token 与服务端配置一致

#### OpenAI API 密钥问题

如果遇到 API 密钥问题（直连模式）：

1. 设置环境变量：
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

2. 或通过配置文件设置：
   ```bash
   nexcode config set api.key "your-api-key"
   ```

## 迁移指南

### 从直连模式迁移到服务端模式

1. 部署 FastAPI 服务端
2. 更新 CLI 配置：
   ```bash
   nexcode config set api_server.url "http://your-server:8000"
   nexcode config set api_server.enabled true
   ```

### 从旧版本升级

旧版本的配置会自动兼容，无需手动迁移。

## 开发指南

### 添加新命令

1. 在 `commands/` 目录添加新的命令文件
2. 在 `cli.py` 中注册新命令
3. 如需 LLM 功能，在 `llm/services.py` 中添加相应函数

### 自定义配置

直接编辑配置文件或使用 `nexcode config` 命令。

## 许可证

[项目许可证信息] 