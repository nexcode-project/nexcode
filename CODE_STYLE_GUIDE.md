# NexCode 项目代码规范指南

## 概述

本文档规定了 NexCode 项目的代码规范和最佳实践，确保代码的一致性、可读性和可维护性。

## Python 代码规范

### 1. 导入顺序 (PEP8)

导入应按以下顺序排列，每组之间用空行分隔：

1. **标准库导入**
2. **第三方库导入**
3. **本地应用/库导入**

```python
# 正确示例
import os
import subprocess

import click
import requests

from ..api.client import api_client
from ..config import config as app_config
```

### 2. 类型注解

所有公共函数和方法应包含类型注解：

```python
# 正确示例
def get_repository_info() -> tuple[str | None, str | None]:
    """获取当前Git仓库的信息"""
    # ...

async def generate_commit_message(
    request: CommitMessageRequest, 
    current_user: OptionalUser,
    db: DatabaseSession
) -> CommitMessageResponse:
    """生成提交消息，并记录到数据库"""
    # ...
```

### 3. 文档字符串

所有公共函数、类和方法必须包含文档字符串：

```python
def clean_commit_message(message: str) -> str:
    """
    清理和优化AI生成的提交消息
    
    Args:
        message: 原始提交消息
        
    Returns:
        str: 清理后的提交消息
        
    Raises:
        ValueError: 当消息格式无效时
    """
    # ...
```

### 4. 异常处理

避免使用裸露的 `except:` 语句，应指定具体的异常类型：

```python
# 错误示例
try:
    data = json.loads(text)
except:
    pass

# 正确示例
try:
    data = json.loads(text)
except (json.JSONDecodeError, KeyError, TypeError):
    pass
```

### 5. 代码重复

提取公共函数避免代码重复：

```python
# 公共工具函数
def get_repository_info() -> tuple[str | None, str | None]:
    """获取当前Git仓库的信息"""
    try:
        result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'], 
            capture_output=True, text=True, check=True
        )
        repository_url = result.stdout.strip()
        
        # 提取仓库名
        repo_name_match = re.search(r'([^/]+?)(?:\.git)?$', repository_url)
        repository_name = repo_name_match.group(1) if repo_name_match else os.path.basename(repository_url)
        
        return repository_url, repository_name
    except subprocess.CalledProcessError:
        return None, None
```

## TypeScript/JavaScript 代码规范

### 1. 导入顺序

```typescript
// 正确示例
import React from 'react';
import { NextPage } from 'next';

import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
```

### 2. 接口定义

```typescript
interface UserProfile {
  id: number;
  username: string;
  email: string;
  created_at: string;
}

interface ApiResponse<T> {
  data: T;
  error?: string;
  success: boolean;
}
```

## 项目结构规范

### 1. 文件命名

- **Python**: 使用 snake_case (例如: `commit_message.py`)
- **TypeScript**: 使用 PascalCase 组件文件 (例如: `UserProfile.tsx`)
- **配置文件**: 使用 kebab-case (例如: `docker-compose.yml`)

### 2. 目录结构

```
nexcode/
├── nexcode_cli/          # CLI 客户端
│   ├── nexcode/
│   │   ├── api/          # API 客户端
│   │   ├── commands/     # 命令实现
│   │   ├── utils/        # 工具函数
│   │   └── config.py     # 配置管理
├── nexcode_server/       # FastAPI 服务端
│   ├── app/
│   │   ├── api/v1/       # API 路由
│   │   ├── core/         # 核心功能
│   │   ├── models/       # 数据模型
│   │   └── services/     # 业务逻辑
│   └── prompts/          # LLM 提示词
└── nexcode_web/          # Next.js 前端
    ├── src/
    │   ├── components/   # React 组件
    │   ├── pages/        # 页面路由
    │   └── lib/          # 工具库
```

## Git 提交规范

### 1. 提交消息格式

使用 Conventional Commits 规范：

```
type(scope): description

feat: add user authentication module
fix: resolve null pointer in login validator
docs: update API endpoint documentation
style: format code according to PEP8
refactor: extract common utility functions
test: add unit tests for auth service
chore: update dependencies
```

### 2. 提交类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 代码重构
- `perf`: 性能优化
- `test`: 测试相关
- `build`: 构建系统
- `ci`: CI/CD 配置
- `chore`: 杂项任务

## 代码质量工具

### 1. Python

```bash
# 代码格式化
black nexcode_server/
black nexcode_cli/

# 导入排序
isort nexcode_server/
isort nexcode_cli/

# 代码检查
flake8 nexcode_server/
flake8 nexcode_cli/

# 类型检查
mypy nexcode_server/
mypy nexcode_cli/
```

### 2. TypeScript

```bash
# 代码格式化
npm run format

# 代码检查
npm run lint

# 类型检查
npm run type-check
```

## 最佳实践

### 1. 错误处理

- 使用具体的异常类型
- 提供有意义的错误消息
- 记录错误日志
- 优雅地处理失败情况

### 2. 函数设计

- 单一职责原则
- 避免过长的函数（建议 < 50 行）
- 使用描述性的函数名
- 减少函数参数数量

### 3. 配置管理

- 使用环境变量管理敏感信息
- 提供默认配置值
- 支持多环境配置
- 配置文档化

### 4. 测试

- 编写单元测试
- 测试覆盖关键业务逻辑
- 使用描述性的测试名称
- 保持测试简洁和独立

## 代码审查清单

### Python

- [ ] 导入顺序符合 PEP8
- [ ] 包含类型注解
- [ ] 有文档字符串
- [ ] 异常处理规范
- [ ] 无代码重复
- [ ] 函数长度合理
- [ ] 变量命名清晰

### TypeScript

- [ ] 使用 TypeScript 严格模式
- [ ] 接口定义完整
- [ ] 组件有适当的类型
- [ ] 避免 `any` 类型
- [ ] 错误处理完善

### 通用

- [ ] 提交消息规范
- [ ] 代码格式一致
- [ ] 无调试代码
- [ ] 文档更新
- [ ] 测试通过

## 持续改进

1. **定期代码审查**: 每个 PR 都需要代码审查
2. **自动化检查**: 使用 CI/CD 自动运行代码质量检查
3. **团队讨论**: 定期讨论和更新编码标准
4. **工具更新**: 及时更新代码质量工具和规则

---

本文档会根据项目发展和团队反馈持续更新。如有建议或问题，请提交 Issue 或 PR。 