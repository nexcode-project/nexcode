# NexCode Web Application

一个现代化的 React/Next.js Web 应用，为 NexCode AI 助手提供用户界面。

## 🚀 功能特性

- **用户认证**: 支持 CAS 单点登录
- **智能对话**: 与 AI 助手进行实时对话
- **响应式设计**: 适配桌面和移动设备
- **现代 UI**: 使用 Tailwind CSS 和 Lucide Icons
- **状态管理**: 使用 Zustand 进行全局状态管理
- **动画效果**: 使用 Framer Motion 提供流畅动画

## 🛠️ 技术栈

- **框架**: Next.js 14
- **语言**: TypeScript
- **样式**: Tailwind CSS
- **状态管理**: Zustand
- **HTTP 客户端**: Axios
- **动画**: Framer Motion
- **图标**: Lucide React
- **通知**: React Hot Toast

## 📦 安装

1. 安装依赖：
```bash
npm install
```

2. 创建环境变量文件：
```bash
cp .env.local.example .env.local
```

3. 配置环境变量：
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🚀 运行

### 开发模式
```bash
npm run dev
```

### 生产构建
```bash
npm run build
npm start
```

## 📁 项目结构

```
nexcode_web/
├── src/
│   ├── components/         # React 组件
│   │   ├── Layout.tsx     # 布局组件
│   │   └── Chat.tsx       # 聊天组件
│   ├── lib/               # 工具库
│   │   └── api.ts         # API 客户端
│   ├── pages/             # Next.js 页面
│   │   ├── _app.tsx       # App 组件
│   │   ├── index.tsx      # 首页
│   │   ├── login.tsx      # 登录页
│   │   └── chat.tsx       # 聊天页
│   ├── store/             # 状态管理
│   │   └── authStore.ts   # 认证状态
│   └── styles/            # 样式文件
│       └── globals.css    # 全局样式
├── public/                # 静态资源
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── next.config.js
```

## 🔧 配置说明

### API 配置

应用通过 `NEXT_PUBLIC_API_URL` 环境变量连接到 NexCode 服务器。默认为 `http://localhost:8000`。

### 认证流程

1. 用户点击登录按钮
2. 重定向到 CAS 认证服务器
3. 认证成功后回调到应用
4. 获取用户信息并保存会话
5. 重定向到聊天页面

### 路由保护

- `/` - 公开页面，已认证用户自动重定向到 `/chat`
- `/login` - 登录页面，已认证用户自动重定向到 `/chat`
- `/chat` - 受保护页面，未认证用户重定向到 `/login`

## 🎨 UI 组件

### Layout 组件
- 导航栏
- 用户信息显示
- 登出功能

### Chat 组件
- 消息列表
- 实时消息发送
- 加载状态
- 滚动到底部

## 📱 响应式设计

应用采用移动优先的响应式设计：
- 移动设备：单列布局
- 平板设备：适中间距
- 桌面设备：最大宽度限制

## 🔍 开发说明

### 代码规范
- 使用 TypeScript 严格模式
- 遵循 React Hooks 最佳实践
- 使用 ESLint 进行代码检查

### 状态管理
- 使用 Zustand 进行全局状态管理
- 认证状态持久化到 Cookie
- 自动处理认证失效

### API 集成
- 自动添加认证头
- 统一错误处理
- 请求/响应拦截器

## 🚀 部署

### Docker 部署

1. 构建镜像：
```bash
docker build -t nexcode-web .
```

2. 运行容器：
```bash
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://your-api-server:8000 nexcode-web
```

### 传统部署

1. 构建应用：
```bash
npm run build
```

2. 启动应用：
```bash
npm start
```

## 📄 许可证

MIT License - 查看 [LICENSE](../LICENSE) 文件了解详情。 