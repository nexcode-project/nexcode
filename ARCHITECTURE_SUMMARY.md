# NexCode 架构总结 - 统一API服务架构

## 架构概述

NexCode 现已完全重构为客户端-服务端架构，其中 CLI 的每个命令都通过专门的后端服务处理，完全不直接调用 OpenAI API。

## 核心架构原则

1. **CLI命令完全依赖后端服务** - 所有AI功能都通过服务端处理
2. **统一的API客户端管理** - 所有请求通过单一客户端类处理
3. **专门化的服务端点** - 每个功能有对应的专门API端点
4. **配置统一传递** - 客户端的API配置（密钥、URL、模型）自动传递给服务端

## 服务端架构

### API端点结构

```
/v1/
├── git-error/           # Git错误分析
├── code-review/         # 基础代码审查
├── code-quality/        # 代码质量检查（专门为check命令）
├── commit-message/      # 提交消息生成
├── commit-qa/           # 基础提交问答
├── intelligent-qa/      # 智能问答（专门为ask命令）
├── push-strategy/       # 推送策略（专门为push命令）
└── repository-analysis/ # 仓库分析
```

### 数据模型

- **APIConfigMixin**: 基础配置模型，包含API密钥、基础URL、模型名称
- **专门的请求/响应模型**: 每个服务都有对应的请求和响应数据模型
- **统一的错误处理**: 所有API都有一致的错误响应格式

### Prompt模板

```
prompts/
├── git_error.toml          # Git错误诊断
├── code_review.toml        # 代码审查
├── code_quality.toml       # 代码质量检查
├── commit_message.toml     # 提交消息生成
├── commit_qa.toml          # 提交问答
├── intelligent_qa.toml     # 智能问答
├── push_strategy.toml      # 推送策略
└── repository_analysis.toml # 仓库分析
```

## 客户端架构

### API客户端设计

```python
nexcode_cli/nexcode/api/
├── __init__.py         # 模块导出
├── endpoints.py        # API端点路径定义
└── client.py          # 统一API客户端
```

### CLI命令映射

| CLI命令 | 专门服务 | API端点 | 功能描述 |
|---------|---------|---------|----------|
| `nexcode check` | 代码质量检查 | `/v1/code-quality/` | 全面代码质量分析，包含评分和建议 |
| `nexcode ask` | 智能问答 | `/v1/intelligent-qa/` | 增强问答，包含相关主题和建议操作 |
| `nexcode diagnose` | Git错误分析 | `/v1/git-error/` | Git命令错误诊断和解决方案 |
| `nexcode commit` | 提交消息生成 | `/v1/commit-message/` | 生成提交消息 |
| `nexcode push` | 推送策略 | `/v1/push-strategy/` | 推送策略分析和提交消息生成 |
| `nexcode status` | 健康检查 | `/health` | 服务端状态检查和故障排除 |

### 配置传递机制

客户端自动将以下配置传递给服务端：
```json
{
  "api_key": "客户端OpenAI API密钥",
  "api_base_url": "客户端API基础URL", 
  "model_name": "客户端模型名称"
}
```

## 关键特性

### 1. 完全的服务端处理
- CLI不再直接调用OpenAI API
- 所有AI功能都通过服务端统一处理
- 客户端只负责用户交互和请求转发

### 2. 智能的错误处理
- 统一的连接错误处理
- 友好的错误信息提示
- 自动的故障排除建议

### 3. 配置集中管理
- 客户端配置自动传递
- 服务端使用客户端配置调用LLM
- 支持多种LLM提供商（通过配置）

### 4. 响应格式标准化
- 结构化的API响应
- 一致的错误响应格式
- 丰富的响应内容（评分、建议、相关主题等）

## 使用示例

### 代码质量检查
```bash
nexcode check --staged
# 输出：质量评分、问题列表、改进建议
```

### 智能问答
```bash
nexcode ask "如何解决合并冲突"
# 输出：详细回答、相关主题、建议操作
```

### 推送策略
```bash
nexcode push --new-branch feature/new-feature
# 输出：分析代码质量、生成提交消息、执行推送
```

## 配置示例

```bash
# 服务端配置
nexcode config set api_server.url "http://your-server:8000"
nexcode config set api_server.token "your-auth-token"

# 客户端LLM配置（自动传递给服务端）
nexcode config set api.key "your-openai-key"
nexcode config set api.base_url "https://api.openai.com/v1"
nexcode config set model.name "gpt-4"
```

## 部署架构

```
┌─────────────────┐    HTTP/JSON    ┌─────────────────┐    API调用    ┌─────────────────┐
│   NexCode CLI   │ ───────────────► │  NexCode Server │ ──────────── ► │   LLM Service   │
│                 │                  │                 │               │  (OpenAI/Other) │
│ • 用户交互      │                  │ • API端点       │               │                 │
│ • 命令解析      │                  │ • Prompt管理    │               │ • 客户端配置    │
│ • 配置管理      │                  │ • LLM客户端     │               │ • 模型调用      │
│ • 结果展示      │                  │ • 响应处理      │               │                 │
└─────────────────┘                  └─────────────────┘               └─────────────────┘
```

## 优势

1. **可扩展性**: 新功能只需添加新的API端点
2. **可维护性**: 清晰的职责分离，易于调试和维护
3. **灵活性**: 支持多种LLM提供商和部署方式
4. **一致性**: 统一的API设计和错误处理
5. **安全性**: API密钥在服务端统一管理
6. **性能**: 减少客户端复杂度，提高响应速度

## 未来扩展

- 添加新的AI服务（如代码生成、文档生成等）
- 支持流式响应
- 添加缓存机制
- 支持多用户和权限管理
- 添加API使用统计和监控 