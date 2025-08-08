# NexCode 管理界面使用指南

## 概述

NexCode 管理界面是一个基于 React + TypeScript 的现代化Web应用，提供了完整的系统管理功能，包括用户管理、提交历史监控、API监控、系统设置等。

## 项目结构

```
nexcode_admin/
├── src/
│   ├── components/           # 公共组件
│   │   └── AdminLayout.tsx   # 管理界面布局
│   ├── contexts/             # React Context
│   │   └── AuthContext.tsx   # 认证上下文
│   ├── pages/                # 页面组件
│   │   ├── Login.tsx         # 登录页面
│   │   ├── Dashboard.tsx     # 控制台
│   │   ├── UserManagement.tsx # 用户管理
│   │   ├── CommitHistory.tsx # 提交历史
│   │   ├── APIMonitor.tsx    # API监控
│   │   └── SystemSettings.tsx # 系统设置
│   ├── services/             # API服务
│   │   └── api.ts            # API客户端
│   └── App.tsx               # 主应用
├── public/                   # 静态资源
│   └── logo.png              # 应用logo
└── package.json              # 依赖配置
```

## 功能特性

### 1. 认证系统

#### 支持的认证方式
- **密码认证**: 传统用户名/密码登录
- **CAS单点登录**: 企业级单点登录支持
- **JWT Token**: 安全的会话管理
- **自动刷新**: Token自动续期机制

#### 认证流程
1. 用户在登录页面选择认证方式
2. 密码认证: 直接验证用户名密码
3. CAS认证: 重定向到CAS服务器进行认证
4. 认证成功后获取JWT token和用户信息
5. 自动处理token过期和刷新

### 2. 控制台 (Dashboard)

#### 系统统计
- **用户统计**: 总用户数、活跃用户数
- **提交统计**: 今日提交数、总提交数
- **质量指标**: 平均评分、评分分布
- **API使用**: API调用次数统计

#### 系统监控
- **资源监控**: CPU、内存、磁盘使用率
- **实时指标**: 活跃连接数、每分钟请求数
- **健康状态**: 服务运行状态检查

#### 数据可视化
- **提交趋势**: 每日提交数量和评分趋势
- **风格分布**: 不同提交风格的使用比例
- **最近活动**: 实时显示最新提交记录

### 3. 用户管理

#### 用户操作
- **查看用户**: 列表显示所有用户信息
- **搜索用户**: 按用户名、邮箱等条件搜索
- **创建用户**: 添加新用户账户
- **编辑用户**: 修改用户信息和权限
- **删除用户**: 停用或删除用户账户

#### API密钥管理
- **查看密钥**: 显示用户的API密钥列表
- **创建密钥**: 为用户生成新的API密钥
- **管理权限**: 设置密钥的访问范围和限制
- **撤销密钥**: 删除或停用API密钥

### 4. 提交历史

#### 提交记录
- **全局视图**: 查看所有用户的提交记录
- **过滤搜索**: 按仓库、用户、时间等条件筛选
- **详细信息**: 查看提交的diff、消息、评分等
- **质量分析**: 提交质量统计和趋势分析

#### 数据统计
- **仓库排行**: 最活跃的代码仓库
- **用户排行**: 贡献最多的开发者
- **质量趋势**: 代码质量变化趋势
- **风格分析**: 提交消息风格分布

### 5. API监控

#### 监控指标
- **调用统计**: 总调用次数、成功率、失败率
- **性能指标**: 平均响应时间、延迟分布
- **端点分析**: 各API端点的使用情况
- **错误分析**: 错误类型和频率统计

#### 实时监控
- **活跃连接**: 当前活跃的API连接数
- **请求频率**: 每分钟API请求数量
- **系统负载**: 服务器CPU和内存使用情况
- **告警机制**: 异常情况自动告警

### 6. 系统设置

#### CAS配置
- **服务器设置**: CAS服务器URL配置
- **属性映射**: 用户属性字段映射
- **连接测试**: CAS服务器连通性测试
- **登出配置**: CAS登出回调设置

#### 系统参数
- **基础配置**: 系统名称、版本信息
- **安全设置**: 密码策略、会话超时
- **邮件配置**: SMTP服务器设置
- **日志配置**: 日志级别和存储设置

## 技术栈

### 前端技术
- **React 18**: 现代化前端框架
- **TypeScript**: 类型安全的JavaScript
- **Ant Design**: 企业级UI组件库
- **React Router**: 客户端路由管理
- **Recharts**: 数据可视化图表库
- **Axios**: HTTP客户端库

### 后端API
- **FastAPI**: 高性能Python web框架
- **SQLAlchemy**: 数据库ORM
- **JWT认证**: 安全的token认证
- **CAS集成**: 企业单点登录支持
- **异步处理**: 高并发请求处理

## 安装和配置

### 前置要求
- Node.js 16+ 
- npm 或 yarn
- NexCode后端服务 (端口8000)

### 安装步骤

1. **安装依赖**
```bash
cd nexcode_admin
npm install
```

2. **配置环境变量**
创建 `.env.local` 文件:
```bash
REACT_APP_API_BASE_URL=http://localhost:8000
```

3. **启动开发服务器**
```bash
npm run dev
```

4. **构建生产版本**
```bash
npm run build
```

### 后端配置

1. **安装后端依赖**
```bash
cd nexcode_server
pip install -r requirements_server.txt
```

2. **配置环境变量**
在 `.env` 文件中设置:
```bash
# CAS配置 (可选)
CAS_SERVER_URL=https://cas.your-domain.com
CAS_SERVICE_URL=http://localhost:8000/v1/auth/cas/callback
CAS_LOGOUT_URL=https://cas.your-domain.com/logout

# 数据库配置
DATABASE_URL=sqlite:///./app.db

# JWT配置
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

3. **初始化数据库**
```bash
cd nexcode_server
python scripts/init_db.py
```

4. **启动后端服务**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 使用说明

### 首次登录

1. **启动服务**
   - 确保后端服务运行在 `http://localhost:8000`
   - 启动前端服务 `http://localhost:5433`

2. **管理员登录**
   - 默认用户名: `admin`
   - 默认密码: `admin`
   - 或使用CAS单点登录

3. **访问管理界面**
   - 登录成功后自动跳转到控制台
   - 查看系统统计和健康状态

### CAS单点登录配置

1. **配置CAS服务器**
   ```bash
   # 在后端 .env 文件中设置
   CAS_SERVER_URL=https://your-cas-server.com
   CAS_SERVICE_URL=http://localhost:8000/v1/auth/cas/callback
   ```

2. **测试CAS连接**
   - 在系统设置页面点击"测试CAS连接"
   - 确认连接状态正常

3. **使用CAS登录**
   - 在登录页面点击"使用CAS单点登录"
   - 系统自动重定向到CAS服务器
   - 认证成功后返回管理界面

### 用户管理

1. **查看用户列表**
   - 导航到"用户管理"页面
   - 查看所有注册用户

2. **创建新用户**
   - 点击"添加用户"按钮
   - 填写用户信息并保存

3. **管理API密钥**
   - 选择用户后点击"API密钥"
   - 创建或撤销API密钥

### 系统监控

1. **查看系统状态**
   - 控制台页面显示实时系统状态
   - 监控CPU、内存、磁盘使用情况

2. **API监控**
   - 导航到"API监控"页面
   - 查看API调用统计和性能指标

3. **提交历史**
   - 查看所有用户的提交记录
   - 分析代码质量趋势

## 故障排除

### 常见问题

1. **无法连接到后端**
   - 检查后端服务是否启动 (端口8000)
   - 确认API_BASE_URL配置正确
   - 检查网络防火墙设置

2. **CAS登录失败**
   - 验证CAS服务器URL配置
   - 检查服务回调URL设置
   - 查看后端日志错误信息

3. **Token过期问题**
   - 系统会自动刷新过期token
   - 如果频繁登出，检查时钟同步
   - 调整token过期时间设置

### 日志调试

1. **前端调试**
   ```bash
   # 开启开发者工具
   F12 -> Console
   ```

2. **后端调试**
   ```bash
   # 查看后端日志
   uvicorn app.main:app --log-level debug
   ```

## API文档

### 认证API
- `POST /v1/auth/login` - 密码登录
- `GET /v1/auth/cas/login` - 获取CAS登录URL
- `POST /v1/auth/cas/verify` - 验证CAS ticket
- `GET /v1/auth/status` - 获取认证状态

### 用户管理API
- `GET /v1/users/` - 获取用户列表
- `POST /v1/users/admin/create` - 创建用户
- `PATCH /v1/users/{user_id}` - 更新用户
- `DELETE /v1/users/{user_id}` - 删除用户

### 系统管理API
- `GET /v1/admin/stats` - 系统统计
- `GET /v1/admin/system/health` - 健康检查
- `GET /v1/admin/cas/config` - CAS配置
- `GET /v1/admin/monitoring/api` - API监控

### 提交管理API
- `GET /v1/commits/admin/all` - 获取所有提交
- `GET /v1/commits/admin/search` - 搜索提交
- `GET /v1/commits/admin/user/{user_id}/analytics` - 用户分析

## 开发指南

### 代码结构

1. **组件开发**
   - 使用TypeScript进行类型安全开发
   - 遵循React Hooks最佳实践
   - 使用Ant Design组件保持一致性

2. **API集成**
   - 统一的API客户端封装
   - 自动错误处理和重试机制
   - 类型安全的数据接口

3. **状态管理**
   - 使用React Context进行全局状态管理
   - 本地状态使用useState和useEffect
   - 数据缓存和同步策略

### 扩展功能

1. **添加新页面**
   - 在 `src/pages/` 目录创建新组件
   - 在 `AdminLayout.tsx` 中添加菜单项
   - 配置路由映射

2. **集成新API**
   - 在 `src/services/api.ts` 中添加API方法
   - 定义TypeScript接口类型
   - 更新组件使用新API

3. **自定义样式**
   - 使用Ant Design主题定制
   - 在 `src/App.css` 中添加全局样式
   - 组件级样式使用CSS Modules

## 版本说明

- **当前版本**: v1.0.0
- **更新日期**: 2025-01-04
- **兼容性**: NexCode Server v2.0.0+

## 许可证

MIT License - 详见项目根目录 LICENSE 文件

## 支持

如有问题或建议，请联系开发团队或在项目仓库提交Issue。 