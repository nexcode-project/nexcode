# NexCode CLI

NexCode 项目的命令行工具（客户端），负责与用户交互、数据采集，并通过 HTTP API 与 LLM 代理服务端通信。

## 功能特性

- 🚀 **智能 Git 助手**：自动分析 Git 错误并提供解决方案
- 🔍 **代码审查**：检测代码变更中的潜在问题和安全隐患
- 💬 **AI 问答**：回答 Git 和版本控制相关问题
- ⚙️ **灵活配置**：支持本地和全局配置
- 🔐 **GitHub风格认证**：使用Personal Access Token进行安全认证

## 快速开始

### 1. 安装依赖

```bash
cd nexcode_cli
pip install -r requirements.txt
```

### 2. 获取Personal Access Token

#### 方式一：Web界面创建（推荐）
1. 访问 NexCode Web 界面
2. 登录您的账户
3. 导航到 "Personal Access Tokens" 页面
4. 点击 "生成新Token"
5. 填写Token名称（如：CLI工具）
6. 选择所需权限范围
7. 点击创建并复制Token

#### 方式二：管理员后台创建
1. 管理员登录后台系统
2. 进入用户管理页面
3. 为用户创建API密钥

### 3. 配置认证

#### 方法一：交互式配置（推荐）
```bash
nexcode config
# 按照提示输入Personal Access Token
```

#### 方法二：直接配置
```bash
# 设置Personal Access Token
nexcode config set auth.token "nxc_your_token_here"

# 设置服务器地址（如果不是默认地址）
nexcode config set server.url "http://your-server:8000"
```

#### 方法三：环境变量
```bash
export NEXCODE_TOKEN="nxc_your_token_here"
export NEXCODE_SERVER_URL="http://your-server:8000"
```

### 4. 验证配置

```bash
# 检查配置状态
nexcode status

# 测试连接
nexcode ask "Hello"
```

## 使用示例

### Git 错误诊断
```bash
# 当 git 命令出错时自动获取解决方案
git push  # 失败
nexcode diagnose
```

### 代码审查
```bash
# 检查当前更改
nexcode check

# 检查特定提交的更改
nexcode check --commit HEAD~1
```

### AI 问答
```bash
# 询问 Git 相关问题
nexcode ask "如何撤销最后一次提交？"
nexcode ask "git rebase 和 git merge 的区别是什么？"
```

### 智能推送
```bash
nexcode push                          # 智能推送（根据仓库类型）
nexcode push --dry-run               # 预览推送命令
```

## 配置详解

### 全局配置文件

配置文件位置：`~/.config/nexcode/config.yaml`

```yaml
# 认证配置（推荐）
auth:
  token: "nxc_your_personal_access_token_here"

# 服务器配置
server:
  url: "http://localhost:8000"
  enabled: true

# 模型配置
model:
  name: "gpt-4o-mini"
  commit_temperature: 0.1
  solution_temperature: 0.1
  max_tokens_commit: 100
  max_tokens_solution: 2048

# 提交配置
commit:
  style: "conventional"
  check_bugs_by_default: true
```

### 认证方式优先级

CLI 工具支持多种认证方式，按以下优先级使用：

1. **Personal Access Token**（推荐）
   - 配置：`auth.token`
   - 环境变量：`NEXCODE_TOKEN`
   - 格式：`nxc_xxxxxxxxxx`

2. **Legacy API Token**（向后兼容）
   - 配置：`api_server.token`
   - 环境变量：`NEXCODE_API_TOKEN`

3. **Direct API Key**（仅用于直连模式）
   - 配置：`api.key`
   - 环境变量：`OPENAI_API_KEY`

## 故障排除

### 认证问题

#### 401 Unauthorized 错误
```bash
# 检查token是否正确配置
nexcode config get auth.token

# 验证token格式（应以nxc_开头）
# 在Web界面重新生成token

# 检查服务器连接
curl -H "Authorization: Bearer nxc_your_token" http://localhost:8000/v1/users/me
```

#### 403 Forbidden 错误
```bash
# 检查token权限范围
# 在Web界面查看token的权限设置
# 可能需要请求管理员分配更多权限
```

### 连接问题

#### 无法连接到服务端
```bash
# 检查服务端是否运行
curl http://localhost:8000/health

# 检查配置
nexcode config get server.url

# 尝试不同的服务器地址
nexcode config set server.url "http://your-server:8000"
```

### 权限问题

不同的API操作需要不同的权限范围：

- **user:read** - 基本用户信息查询
- **api:read** - 只读API调用（ask、diagnose等）
- **api:write** - 写入API调用（commit、push等）
- **repo:write** - 仓库相关操作
- **admin** - 管理员权限

## 安全建议

1. **定期轮换Token**：建议每3-6个月更换一次Personal Access Token
2. **最小权限原则**：只分配CLI工具所需的最小权限范围
3. **安全存储**：不要在代码或公共文件中硬编码Token
4. **监控使用**：定期检查Token的使用情况和最后使用时间

## 迁移指南

### 从旧版本升级

如果您之前使用的是 `api_server.token` 配置：

```bash
# 旧配置（仍然支持）
nexcode config get api_server.token

# 迁移到新配置
nexcode config set auth.token "$(nexcode config get api_server.token)"
nexcode config unset api_server.token
```

### Personal Access Token 优势

相比旧的API token方式，Personal Access Token提供：

- ✅ 更细粒度的权限控制
- ✅ 更好的安全性（GitHub标准格式）
- ✅ 用户自主管理能力
- ✅ 使用统计和审计功能
- ✅ 可设置过期时间

## 开发指南

### 添加新命令

1. 在 `commands/` 目录添加新的命令文件
2. 在 `cli.py` 中注册新命令
3. 如需LLM功能，确保使用正确的权限范围

### 自定义配置

直接编辑配置文件或使用 `nexcode config` 命令。 