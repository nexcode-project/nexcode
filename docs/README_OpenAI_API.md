# NexCode OpenAI 兼容 API

## 概述

NexCode 提供了完全兼容 OpenAI 的 API 接口，支持：
- `/v1/chat/completions` - Chat Completions API
- `/v1/completions` - Text Completions API

这些接口可以直接使用标准的 OpenAI 客户端库调用，并支持所有主要参数。

## 🚀 快速开始

### 1. 启动服务

```bash
# 启动后端服务
cd nexcode_server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动前端服务 (可选)
cd nexcode_web
npm run dev
```

### 2. 使用 Web 界面

访问 `http://localhost:3000`，登录后：

1. **默认模式** - 使用内置智能问答，无需额外配置
2. **OpenAI 模式** - 点击聊天界面右上角的设置按钮 ⚙️
   - 勾选"使用 OpenAI Chat Completion 接口"
   - 输入您的 OpenAI API Key
   - 选择模型（GPT-3.5/GPT-4/GPT-4 Turbo）
   - 调整温度参数（0-2）

### 3. 使用标准 OpenAI 客户端

NexCode 完全兼容 OpenAI API，可以直接替换 OpenAI 的 base_url：

```python
import openai

client = openai.OpenAI(
    api_key="your-openai-api-key",
    base_url="http://localhost:8000/v1"  # 指向 NexCode 服务器
)

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello"}]
)
```

## 📡 API 接口详情

### Chat Completions (`/v1/chat/completions`)

**请求格式:**
```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {"role": "system", "content": "你是一个助手"},
    {"role": "user", "content": "你好"}
  ],
  "temperature": 0.7,
  "max_tokens": 1500,
  "top_p": 1.0,
  "presence_penalty": 0.0,
  "frequency_penalty": 0.0,
  "stop": ["停止词"]
}
```

**响应格式:**
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-3.5-turbo",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "你好！有什么可以帮助你的吗？"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 15,
    "total_tokens": 25
  }
}
```

### Text Completions (`/v1/completions`)

**请求格式:**
```json
{
  "model": "gpt-3.5-turbo", 
  "prompt": "请解释 Python 的装饰器",
  "temperature": 0.7,
  "max_tokens": 1500,
  "top_p": 1.0,
  "presence_penalty": 0.0,
  "frequency_penalty": 0.0,
  "stop": ["停止词"]
}
```

## 💻 使用示例

### Python 客户端

```python
import openai

# 配置客户端
client = openai.OpenAI(
    api_key="your-openai-api-key",
    base_url="http://localhost:8000/v1"
)

# 聊天对话
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "你是一个专业的Python编程助手"},
        {"role": "user", "content": "如何创建一个简单的装饰器？"}
    ],
    temperature=0.7,
    max_tokens=1000
)

print(response.choices[0].message.content)
```

### JavaScript/Node.js

```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: 'your-openai-api-key',
  baseURL: 'http://localhost:8000/v1'
});

async function chat() {
  const completion = await openai.chat.completions.create({
    messages: [{ role: 'user', content: 'Hello!' }],
    model: 'gpt-3.5-turbo',
  });
  
  console.log(completion.choices[0].message.content);
}
```

### cURL

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-openai-api-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "你好"}
    ],
    "temperature": 0.7
  }'
```

## 🔧 配置选项

### 环境变量

```bash
# OpenAI 配置
OPENAI_API_BASE=https://api.openai.com/v1  # OpenAI API 基础URL
OPENAI_MODEL=gpt-3.5-turbo                 # 默认模型

# 模型参数
MAX_TOKENS=1500        # 最大 token 数
TEMPERATURE=0.7        # 默认温度
SOLUTION_TEMPERATURE=0.3  # 解决方案温度

# 服务配置
HOST=0.0.0.0          # 服务主机
PORT=8000             # 服务端口
DEBUG=false           # 调试模式

# 认证配置 (可选)
API_TOKEN=your-server-token  # 服务器 API 令牌
REQUIRE_AUTH=false           # 是否需要认证
```

### Web 界面设置

在聊天界面中，您可以通过设置面板配置：

- **接口选择**: 内置智能问答 vs OpenAI Chat Completion
- **API Key**: 您的 OpenAI API 密钥
- **模型选择**: 
  - `gpt-3.5-turbo` - 快速、经济
  - `gpt-4` - 更强能力
  - `gpt-4-turbo-preview` - 最新模型
- **温度参数**: 0-2，控制响应的创造性

## 🔐 认证说明

### API Key 认证

- **客户端 API Key**: 在 `Authorization: Bearer your-openai-api-key` 头中传递您的 OpenAI API Key
- **服务器令牌**: 如果启用了服务器认证，使用服务器的 API_TOKEN

### 认证优先级

1. 如果请求包含有效的 OpenAI API Key，直接使用该密钥
2. 如果启用了服务器认证（`REQUIRE_AUTH=true`），需要提供服务器 API_TOKEN
3. 否则使用服务器配置的 OpenAI 设置

## 🌟 特性

- **完全兼容**: 与 OpenAI API 100% 兼容
- **参数透传**: 支持所有 OpenAI 参数
- **双模式**: 支持内置智能问答和 OpenAI API
- **Web 界面**: 用户友好的聊天界面
- **灵活认证**: 支持客户端和服务器端认证
- **实时配置**: 在 Web 界面动态切换模型和参数

## 🔍 故障排除

### 常见问题

**1. "Connection error" 错误**
- 检查 OpenAI API Key 是否正确
- 确认网络连接正常
- 验证 OPENAI_API_BASE 设置

**2. "Authentication failed" 错误**
- 确认 API Key 格式正确（sk-...）
- 检查 API Key 是否有效且有余额
- 验证服务器认证配置

**3. Web 界面无法访问**
- 确认前端服务在 3000 端口运行
- 检查后端服务在 8000 端口运行
- 查看浏览器控制台错误信息

**4. 登录后无法跳转**
- 清除浏览器缓存和 localStorage
- 检查网络连接
- 确认认证服务正常

### 调试步骤

1. **检查服务状态**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **测试 API 接口**:
   ```bash
   curl -X POST http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your-api-key" \
     -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"test"}]}'
   ```

3. **查看日志**:
   ```bash
   # 后端日志
   cd nexcode_server && python -m uvicorn app.main:app --reload --log-level debug
   
   # 前端日志
   cd nexcode_web && npm run dev
   ```

## 📚 更多资源

- [NexCode CLI 工具文档](./CLI_Usage.md)
- [API 参考文档](./API_Reference.md)
- [部署指南](./Deployment.md)
- [开发指南](./Development.md)

## 🔄 版本更新

### v1.2.0 新增功能
- ✅ Web 界面集成 OpenAI Chat Completion 接口
- ✅ 动态模型和参数配置
- ✅ 双模式聊天支持（内置 + OpenAI）
- ✅ 改进的认证和错误处理
- ✅ 修复登录重定向问题 