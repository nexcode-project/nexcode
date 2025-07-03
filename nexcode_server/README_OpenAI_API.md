# NexCode OpenAI 兼容 API

## 概述

NexCode 现在提供了 OpenAI 兼容的 API 接口，支持：
- `/v1/chat/completions` - Chat Completions API
- `/v1/completions` - Text Completions API

这些接口内部调用 OpenAI 的服务，但提供了统一的访问入口和参数控制。

## 支持的参数

### Chat Completions (`/v1/chat/completions`)

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

### Text Completions (`/v1/completions`)

```json
{
  "model": "gpt-3.5-turbo", 
  "prompt": "请解释",
  "temperature": 0.7,
  "max_tokens": 1500,
  "top_p": 1.0,
  "presence_penalty": 0.0,
  "frequency_penalty": 0.0,
  "stop": ["停止词"]
}
```

## 使用方法

### 1. 使用 OpenAI Python 库

```python
import openai

# 配置客户端
client = openai.OpenAI(
    api_key="your-openai-api-key",
    base_url="http://localhost:8000/v1"
)

# 调用 Chat Completions
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "你好"}
    ],
    temperature=0.7
)

print(response.choices[0].message.content)
```

### 2. 使用 curl

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-openai-api-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "你好"}],
    "temperature": 0.7
  }'
```

## 认证

- 将您的 OpenAI API key 放在 `Authorization: Bearer your-api-key` 头中
- 如果服务器启用了认证，请使用服务器的 API token

## 特性

- **完全兼容**: 与 OpenAI API 完全兼容
- **参数透传**: 支持所有 OpenAI 参数
- **统一入口**: 通过 NexCode 服务器统一管理
- **扩展性**: 可以添加自定义逻辑和缓存

## 示例

查看 `examples/simple_openai_usage.py` 获取完整示例。

## 配置

通过环境变量配置：

```bash
# OpenAI 配置
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# 服务器配置  
HOST=0.0.0.0
PORT=8000

# 认证配置（可选）
REQUIRE_AUTH=false
API_TOKEN=your-server-token
```

## 错误处理

API 返回标准的 HTTP 状态码和错误信息，与 OpenAI API 保持一致。 