# 拆词鸭前端 - 开发指南

## 🚀 快速开始

### 环境要求
- Node.js >= 18.x
- npm >= 9.x

### 安装依赖
```bash
npm install
```

### 开发模式
```bash
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000) 查看应用

### 构建生产版本
```bash
npm run build
npm run start
```

### 代码检查
```bash
npm run lint
```

## 📁 项目结构

```
ChaiWordDuck-frontend/
├── app/                          # Next.js 14 App Router
│   ├── (auth)/                  # 认证路由组
│   │   ├── login/              # 登录页
│   │   └── register/           # 注册页
│   ├── favorites/              # 收藏页
│   ├── word/[id]/              # 单词详情页（动态路由）
│   ├── layout.tsx              # 根布局
│   └── page.tsx                # 首页
│
├── components/                  # React 组件
│   ├── ui/                     # 基础 UI 组件
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   └── Toast.tsx
│   ├── layout/                 # 布局组件
│   │   └── Navbar.tsx
│   └── features/               # 功能组件
│       └── SearchBox.tsx
│
├── lib/                        # 工具库
│   ├── api/                    # API 客户端
│   │   ├── client.ts           # Axios 配置
│   │   ├── auth.ts             # 认证 API
│   │   ├── words.ts            # 单词 API
│   │   └── favorites.ts        # 收藏 API
│   ├── store/                  # 状态管理
│   │   └── auth.ts             # 认证 Store (Zustand)
│   ├── hooks/                  # 自定义 Hooks
│   │   └── useQueryLimit.ts    # 查询限制 Hook
│   └── utils/                  # 工具函数
│       └── index.ts
│
├── types/                      # TypeScript 类型定义
│   └── index.ts
│
├── public/                     # 静态资源
├── docs/                       # 项目文档
│   └── FRONTEND_PROGRESS.md    # 开发进度
│
├── .eslintrc.json             # ESLint 配置
├── .gitignore                 # Git 忽略文件
├── next.config.js             # Next.js 配置
├── package.json               # 项目依赖
├── tailwind.config.ts         # Tailwind CSS 配置
└── tsconfig.json              # TypeScript 配置
```

## 🛠️ 技术栈

### 核心框架
- **Next.js 14.2.33** - React 框架（App Router）
- **React 18** - UI 库
- **TypeScript 5.x** - 类型安全

### 样式
- **Tailwind CSS 3.x** - 实用优先的 CSS 框架

### 状态管理
- **Zustand 4.x** - 轻量级状态管理

### HTTP 请求
- **Axios** - Promise based HTTP client

### 开发工具
- **ESLint** - 代码检查
- **Git Flow** - 分支管理策略

## 🎨 设计规范

### 色彩系统
- **主色调**：黄色 (`#FFD93D`)
- **辅助色**：紫色 (`#6C63FF`)、橙色 (`#FF8A3D`)
- **中性色**：灰度系统

### 组件规范
- 所有组件使用 TypeScript
- 函数式组件 + Hooks
- Props 类型必须明确定义
- 组件文件名使用 PascalCase

### 代码风格
- 遵循 ESLint 配置
- 使用 2 空格缩进
- 单引号字符串
- 末尾不加分号（除非必要）

## 📱 响应式断点

```typescript
// Tailwind 默认断点
sm: 640px   // 小屏幕（手机横屏）
md: 768px   // 平板
lg: 1024px  // 桌面
xl: 1280px  // 大桌面
2xl: 1536px // 超大桌面
```

## 🔌 API 集成

### 环境变量
在项目根目录创建 `.env.local` 文件：

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### API 调用示例

```typescript
import { queryWord } from '@/lib/api/words';

// 查询单词
const wordData = await queryWord('accommodation');
```

## 📝 开发规范

### Git 提交规范
遵循 Conventional Commits：

```bash
feat(scope): 新功能
fix(scope): Bug 修复
docs(scope): 文档更新
style(scope): 代码格式化
refactor(scope): 重构
test(scope): 测试
chore(scope): 构建/工具变更
```

### 分支管理
```bash
main              # 主分支
develop           # 开发主分支
feature/*         # 功能分支
bugfix/*          # Bug 修复分支
hotfix/*          # 紧急修复分支
```

## 🧪 测试

### 运行测试（待实现）
```bash
npm run test        # 运行所有测试
npm run test:watch  # 监听模式
npm run test:cov    # 生成覆盖率报告
```

## 🚢 部署

### Vercel（推荐）
1. 连接 GitHub 仓库
2. 配置环境变量
3. 自动部署

### 手动部署
```bash
npm run build
npm run start
```

## 📚 相关文档

- [Next.js 官方文档](https://nextjs.org/docs)
- [Tailwind CSS 官方文档](https://tailwindcss.com/docs)
- [TypeScript 官方文档](https://www.typescriptlang.org/docs)
- [开发进度报告](./docs/FRONTEND_PROGRESS.md)

## 🐛 已知问题

1. Toast 功能使用浏览器 alert（待优化）
2. API 集成需要后端启动
3. 部分 ESLint 警告（React Hook 依赖）

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📧 联系方式

有问题或建议？欢迎提 Issue！

---

**前端负责人**：[待补充]
**最后更新**：2025-10-14
