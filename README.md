# 拆词鸭 ChaiWord Duck

> **让长单词变得"有故事、可拆解、能记住"**

## 📖 项目简介

**拆词鸭**是一款专注于成人英语长单词学习的创新产品。我们不只是让你"背单词"，而是通过独特的"语言游戏"方法，让你真正**理解**并**记住**那些看起来吓人的长单词。

### 核心理念

基于维特根斯坦的"语言游戏"哲学：
- 不是给单词下定义，而是教你**如何使用**
- 不是机械重复，而是**理解语境**
- 不是孤立记忆，而是**建立连接**

---

## 🎯 为什么要做拆词鸭？

### 真实的痛点

- 你学了20年英语，四六级都过了，但看到 `accommodation`、`serendipitous` 这样的长单词还是记不住
- 你用了墨墨背单词、扇贝等APP，重复了无数次，过两天还是忘
- 你知道词根词缀，但工具书式的列表让你看了就头疼

**市场调研显示**：现有英语学习产品（Duolingo、Memrise、扇贝等）都是"通用词汇学习"，**没有专门深度解决"长单词记忆"痛点**。

---

## 💡 我们的解决方案

### 五步"语言游戏"学习法

以 `accommodation` 为例：

#### 1. 核心游戏：这是什么"局"？
> 这是一场**"双向调整以达成共处"的协商游戏**

#### 2. 游戏棋盘：双场景对照
- **思辨场**：商务谈判中的"妥协调和"
- **生活场**：旅行中的"住宿"

#### 3. 游戏溯源与拆解
```
ac-  +  -commod-  +  -ation
向着    使适合       名词化
```
**组装故事**：古罗马主人为客人调整房间和习惯，"使某物适合另一物"

#### 4. 犯规警告
⚠️ 最容易犯的错：拼写时漏掉一个 'm' 或一个 'c'
**口诀**："CC 看见 MM 住进房间"（两个c，两个m）

#### 5. 通关秘籍
💡 想象酒店房间有**两张床**（cc）和**两个枕头**（mm），这就是 **accommodation**！

---

## 🎨 产品特色

### 与现有产品的差异

| 维度 | 传统背单词APP | 拆词鸭 |
|------|--------------|--------|
| 学习方式 | 抽认卡 + 机械重复 | 故事化深度学习 + SRS |
| 词根拆解 | 列出词根（工具书式） | 讲"组装故事"（有趣） |
| 记忆技巧 | 简单联想或无 | 创意视觉化秘籍 |
| 语境展示 | 单一例句 | 双场景对照 |
| 防错机制 | 无 | 主动犯规警告 |
| 专注度 | 通用词汇 | 专注长单词（8字母+） |

---

## 📊 前端开发进度

### ✅ 已完成 (2025-10-14)

前端 MVP 核心功能已全部完成，包括：

- ✅ 项目初始化（Next.js 14 + TypeScript + Tailwind CSS）
- ✅ 用户认证（登录/注册）
- ✅ 首页和搜索功能
- ✅ 单词手册详情页（五步学习法）
- ✅ 收藏功能
- ✅ 查询次数限制和游客模式
- ✅ 响应式设计（移动端优先）

详细进度请查看：[前端开发进度报告](./docs/FRONTEND_PROGRESS.md)

---

## 📊 后端开发进度

### ✅ 已完成 (2025-10-15)

后端核心API和基础设施已实现，包括：

**核心功能**:
- ✅ 用户认证系统（注册、登录、JWT、密码重置）
- ✅ 单词查询系统（查询API、获取单词详情、查询统计）
- ✅ 收藏系统（添加/删除收藏、获取收藏列表、检查收藏状态）
- ✅ 查询限制系统（每日查询次数限制、查询历史记录）

**数据库架构**:
- ✅ PostgreSQL 数据库设计（4张表：users、words、favorites、query_logs）
- ✅ Docker Compose 统一环境（PostgreSQL + Redis + 测试数据库）
- ✅ Alembic 数据库迁移工具
- ✅ SQLAlchemy 异步ORM
- ✅ 预置10个黄金手册单词

**测试架构**:
- ✅ 单元测试框架（SQLite内存数据库）
- ✅ 集成测试框架（PostgreSQL测试数据库）
- ✅ 测试数据隔离机制
- ✅ pytest + pytest-asyncio 配置

### ⏳ 待完成功能

- ⏳ Redis缓存集成（已配置Docker服务，待实现缓存逻辑）
- ⏳ OpenAI API集成（AI生成单词手册）
- ⏳ 游客识别和限制（IP + Cookie）
- ⏳ 完整的单元测试和集成测试覆盖
- ⏳ API性能优化和监控

详细进度请查看：[任务跟踪文档](./docs/TODOS.md)

---

## 🚀 如何运行项目

### 开发环境要求

- Node.js 18+ (前端)
- Python 3.12+ (后端)
- **PDM** (Python依赖管理) - **强制使用，不使用 pip** - [安装指南](https://pdm-project.org/)
- Docker Desktop (数据库和缓存)
- Git

### 快速开始

#### 1. 克隆项目

```bash
git clone https://github.com/cznccsjd/ChaiWordDuck.git
cd ChaiWordDuck
```

#### 2. 启动 Docker 服务

```bash
# 启动 PostgreSQL + Redis + 测试数据库
docker-compose up -d

# 验证容器运行状态
docker-compose ps
```

#### 3. 配置后端环境

```bash
cd backend

# 复制环境变量文件
cp .env.example .env

# 安装依赖（使用 PDM，不要使用 pip！）
pdm install

# ⚠️ 注意：不要使用 pip install -r requirements.txt
# ⚠️ 项目使用 PDM 管理依赖，请使用上述 pdm install 命令

# (可选) 运行数据库迁移
# 注意: 如果遇到编码问题，应用启动时会自动创建表结构
pdm run alembic upgrade head
```

#### 4. 配置前端环境

```bash
cd frontend

# 安装依赖
npm install

# 创建环境变量文件
# 创建 .env.local 文件，内容如下:
# NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

#### 5. 启动开发服务器

在两个独立的终端窗口中：

```bash
# 终端1: 启动后端
cd backend
pdm run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# 终端2: 启动前端
cd frontend
npm run dev
```

#### 6. 访问应用

- 前端应用: http://localhost:3001
- 后端API文档: http://localhost:8000/docs
- 后端API: http://localhost:8000

---

### Docker Compose 使用

#### 服务说明

项目使用 Docker Compose 提供统一的数据库和缓存环境：

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| PostgreSQL | chaiword_db | 5432 | 开发数据库 |
| Redis | chaiword_redis | 6379 | 缓存服务 |
| PostgreSQL测试 | chaiword_db_test | 5433 | 集成测试专用 |

#### 常用命令

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f db

# 停止所有服务
docker-compose down

# 停止并删除所有数据 (慎用！)
docker-compose down -v

# 重启服务
docker-compose restart db
```

#### 数据持久化

- PostgreSQL 数据存储在 Docker volume: `postgres_data`
- Redis 数据存储在 Docker volume: `redis_data`
- 测试数据库使用内存存储 (tmpfs)，测试结束后自动清除

---

### 开发工作流

#### 日常开发

```bash
# 1. 确保 Docker 服务运行
docker-compose ps

# 2. 启动后端 (开发模式，自动重载)
cd backend
pdm run uvicorn app.main:app --reload

# 3. 启动前端 (开发模式，自动重载)
cd frontend
npm run dev
```

#### 运行测试

```bash
# 后端测试
cd backend

# 运行所有测试
pdm run pytest

# 运行单元测试 (使用SQLite内存数据库)
pdm run pytest -m unit

# 运行集成测试 (使用PostgreSQL测试数据库)
pdm run pytest -m integration

# 生成测试覆盖率报告
pdm run pytest --cov=app --cov-report=html
```

#### 数据库操作

```bash
# 创建新的迁移文件
cd backend
pdm run alembic revision --autogenerate -m "描述变更内容"

# 应用迁移
pdm run alembic upgrade head

# 回滚迁移
pdm run alembic downgrade -1

# 查看迁移历史
pdm run alembic history
```

---

### 故障排查

#### Docker 相关问题

**问题: docker-compose 命令失败**
```bash
# 解决方案: 确保 Docker Desktop 正在运行
# Windows: 启动 Docker Desktop 应用
# Mac/Linux: 检查 Docker 服务状态
docker ps
```

**问题: 端口被占用**
```bash
# Windows: 查看端口占用
netstat -ano | findstr :5432
netstat -ano | findstr :8000

# 停止占用端口的进程或更改配置
```

#### 数据库连接问题

**问题: 后端无法连接数据库**
```bash
# 1. 检查 Docker 容器状态
docker-compose ps

# 2. 查看数据库日志
docker-compose logs db

# 3. 验证数据库连接
docker exec -it chaiword_db psql -U postgres -d chaiword_duck
```

#### 前端问题

**问题: 前端运行在 3001 端口而非 3000**
- 这是正常的，Next.js 会自动选择可用端口
- 确保在 `backend/.env` 中的 CORS 配置包含 3001 端口:
  ```
  CORS_ORIGINS=http://localhost:3000,http://localhost:3001
  ```

#### Alembic 编码问题 (Windows)

**问题: alembic upgrade head 报编码错误**
- 这是 Windows 系统编码问题
- **临时解决方案**: 应用启动时会自动创建表结构
- **长期解决方案**: 确保所有 Python 文件使用 UTF-8 编码

```bash
# 设置环境变量
set PYTHONUTF8=1
pdm run alembic upgrade head
```

---

## 🚀 生产环境部署

### 部署架构说明

本项目采用前后端分离的部署策略，推荐使用以下免费/低成本的托管服务：

| 组件 | 推荐平台 | 成本 | 说明 |
|------|---------|------|------|
| 前端 | Vercel | 免费 | Next.js 官方推荐，支持 SSR/ISR |
| 后端 | Render.com | $21/月 | 原生支持 Python FastAPI + Docker |
| 数据库 | Render PostgreSQL | 包含在上述 | 托管 PostgreSQL，自动备份 |
| 缓存 | Render Redis | 包含在上述 | 托管 Redis，256MB 内存 |

**为什么不用 Supabase？**
- Supabase Edge Functions 只支持 Deno/TypeScript，不支持 Python
- 如果用 Supabase，需要完全重写后端（约 3000+ 行代码）
- Render.com 原生支持 FastAPI，无需任何改写
- 详细分析请查看架构文档

### 部署到 Render.com（后端）

#### 步骤 1: 准备 Render 账号

1. 注册账号：https://render.com
2. 连接 GitHub 账号
3. 选择 ChaiWordDuck 仓库

#### 步骤 2: 创建 Blueprint 部署

项目根目录已提供 `render.yaml` 配置文件，包含：
- FastAPI Web 服务
- PostgreSQL 数据库
- Redis 缓存

**使用 Blueprint 一键部署**：

1. 在 Render 控制台选择 "New" → "Blueprint"
2. 连接 GitHub 仓库
3. Render 会自动读取 `render.yaml` 配置
4. 点击 "Apply" 开始部署

#### 步骤 3: 配置环境变量

以下环境变量需要在 Render 控制台手动设置：

**必需设置**：
```bash
# OpenAI API（核心功能）
OPENAI_API_KEY=sk-your-openai-api-key

# CORS配置（前端域名）
CORS_ORIGINS=https://your-frontend-domain.vercel.app,https://chaiwordduck.com
```

**可选设置**：
```bash
# SendGrid邮件服务
SENDGRID_API_KEY=your-sendgrid-api-key

# Sentry错误监控
SENTRY_DSN=your-sentry-dsn
```

其他环境变量（DATABASE_URL、REDIS_URL、JWT_SECRET_KEY）会自动生成。

#### 步骤 4: 验证部署

部署完成后，访问以下 URL 验证：

```bash
# 健康检查
https://your-app.onrender.com/health

# API 文档
https://your-app.onrender.com/docs

# 测试查询单词
curl -X POST https://your-app.onrender.com/api/v1/words/query \
  -H "Content-Type: application/json" \
  -d '{"text": "accommodation"}'
```

#### 成本估算

**MVP 阶段（Starter 计划）**：
- Web 服务：$7/月（512MB RAM，无冷启动）
- PostgreSQL：$7/月（1GB 存储）
- Redis：$7/月（256MB 内存）
- **总计**：**$21/月（约 ¥150/月）**

**扩展阶段（1000-5000 用户）**：
- Web 服务：$25/月（更多资源）
- PostgreSQL Pro：$25/月（10GB 存储）
- Redis Pro：$25/月（更大缓存）
- **总计**：**$75/月（约 ¥540/月）**

### 部署到 Vercel（前端）

#### 步骤 1: 准备 Vercel 账号

1. 注册账号：https://vercel.com
2. 连接 GitHub 账号

#### 步骤 2: 导入项目

1. 在 Vercel 控制台选择 "New Project"
2. 导入 ChaiWordDuck 仓库
3. **重要**：设置 Root Directory 为 `frontend`
4. Framework Preset 会自动识别为 Next.js

#### 步骤 3: 配置环境变量

在 Vercel 项目设置中添加：

```bash
# 后端 API 地址
NEXT_PUBLIC_API_URL=https://your-app.onrender.com/api/v1
```

#### 步骤 4: 部署

1. 点击 "Deploy" 开始首次部署
2. 等待构建完成（约 2-3 分钟）
3. 访问 Vercel 提供的预览 URL

#### 步骤 5: 配置自定义域名（可选）

1. 在 Vercel 项目设置中添加域名
2. 按照提示配置 DNS 记录
3. Vercel 会自动配置 SSL 证书

#### 成本

- **Hobby 计划**：完全免费
- 支持 100GB 带宽/月
- 适合 MVP 阶段使用

### 部署后配置

#### 1. 更新后端 CORS 配置

在 Render 后端环境变量中更新：

```bash
CORS_ORIGINS=https://your-actual-domain.vercel.app
```

#### 2. 配置自动备份（推荐）

Render PostgreSQL 每日自动备份，保留 7 天。

**手动备份**：
```bash
# 在 Render 控制台执行
pg_dump $DATABASE_URL > backup.sql
```

#### 3. 配置监控告警

**Render 内置监控**：
- CPU/内存使用率
- 错误日志追踪
- 自动健康检查

**推荐集成 Sentry**（可选）：
```bash
# 在 Render 环境变量中设置
SENTRY_DSN=your-sentry-dsn
```

### 持续部署

#### 自动部署流程

```
开发者 Push 代码到 GitHub
         ↓
GitHub 触发 Webhook
         ↓
    ┌────┴────┐
    ↓         ↓
Render     Vercel
自动构建    自动构建
    ↓         ↓
后端部署    前端部署
    ↓         ↓
  完成       完成
```

#### 部署分支策略

- `main` 分支 → 生产环境自动部署
- `develop` 分支 → 可配置预览环境
- 功能分支 → Vercel 自动生成预览 URL

### 部署清单

部署前确认以下事项：

**后端（Render.com）**：
- [ ] `render.yaml` 配置文件已创建
- [ ] GitHub 仓库已连接
- [ ] 环境变量已设置（OPENAI_API_KEY、CORS_ORIGINS）
- [ ] 健康检查通过（/health 端点）
- [ ] API 文档可访问（/docs 端点）
- [ ] 数据库连接正常

**前端（Vercel）**：
- [ ] Root Directory 设置为 `frontend`
- [ ] 环境变量已设置（NEXT_PUBLIC_API_URL）
- [ ] 首次部署成功
- [ ] 前端可正常访问后端 API
- [ ] CORS 配置正确

**整体验证**：
- [ ] 用户注册/登录功能正常
- [ ] 单词查询功能正常
- [ ] 收藏功能正常
- [ ] 查询次数限制生效
- [ ] 错误日志正常记录

### 常见部署问题

#### 问题 1: Render 构建失败

**错误信息**：`ModuleNotFoundError: No module named 'app'`

**解决方案**：
```bash
# 检查 render.yaml 中的 buildCommand
buildCommand: "pip install pdm && pdm install --prod"

# 确保 pyproject.toml 在正确位置
```

#### 问题 2: 数据库连接超时

**错误信息**：`asyncpg.exceptions.ConnectionTimeoutError`

**解决方案**：
1. 检查 DATABASE_URL 环境变量是否正确
2. 确认数据库服务已启动
3. 检查网络安全组配置

#### 问题 3: CORS 错误

**错误信息**：`Access-Control-Allow-Origin header is missing`

**解决方案**：
```bash
# 在 Render 后端环境变量中设置
CORS_ORIGINS=https://your-frontend-domain.vercel.app

# 注意：不要包含尾部斜杠
```

#### 问题 4: Vercel 构建失败

**错误信息**：`MODULE_NOT_FOUND`

**解决方案**：
1. 检查 Root Directory 是否设置为 `frontend`
2. 确认 `package.json` 存在于 frontend 目录
3. 清除 Vercel 构建缓存后重试

---

### 已实现的API端点

**单词相关**:
- POST /api/v1/words/query - 查询单词
- GET /api/v1/words/query-limit - 获取查询统计
- GET /api/v1/words/{word_id} - 根据ID获取单词

**收藏相关**:
- POST /api/v1/favorites - 添加收藏
- DELETE /api/v1/favorites/{word_id} - 删除收藏
- GET /api/v1/favorites - 获取收藏列表
- GET /api/v1/favorites/check/{word_id} - 检查收藏状态

**用户认证**:
- POST /api/v1/auth/register - 用户注册
- POST /api/v1/auth/login - 用户登录
- POST /api/v1/auth/refresh - 刷新令牌
- POST /api/v1/auth/logout - 用户登出

---

## 🛠️ 技术栈

### 前端
- **框架**: Next.js 14.2.33 (App Router)
- **语言**: TypeScript 5.x
- **样式**: Tailwind CSS 3.4.0
- **状态管理**: Zustand 4.5.0
- **数据请求**: React Query 5.28.0
- **表单验证**: Zod 3.22.0
- **HTTP 客户端**: Axios 1.6.0

### 后端
- **框架**: FastAPI 0.104+
- **语言**: Python 3.12+
- **ORM**: SQLAlchemy 2.0 (异步)
- **数据库**:
  - 生产/开发: PostgreSQL 15+ (Docker)
  - 单元测试: SQLite (内存模式)
  - 集成测试: PostgreSQL (Docker, 独立测试库)
- **缓存**: Redis 7+ (Docker)
- **认证**: JWT (python-jose) + bcrypt
- **测试**: pytest + pytest-asyncio
- **包管理**: PDM
- **数据库迁移**: Alembic
- **AI**: OpenAI GPT-3.5-turbo (待集成)

### 基础设施
- **容器化**: Docker + Docker Compose
- **数据库**: PostgreSQL 15 Alpine (生产 + 测试环境)
- **缓存**: Redis 7 Alpine
- **数据持久化**: Docker Volumes
- **测试隔离**: 独立测试数据库 (端口5433)

---

## 🚀 发展规划

### 第一阶段：验证（已完成）
- [x] 制作 20 个高质量长单词"游戏手册"
- [x] 产品可行性分析
- [x] 市场调研验证

### 第二阶段：MVP 开发（进行中）
- [x] 前端应用开发（已完成 2025-10-14）
  - [x] 用户输入单词 → 展示"游戏手册"
  - [x] 收藏夹功能
  - [x] 查询次数限制
- [x] 后端核心API开发（部分完成 2025-10-15）
  - [x] 用户认证系统
  - [x] 单词查询系统
  - [x] 收藏系统
  - [x] 查询限制系统
  - [ ] Redis缓存集成（待完成）
  - [ ] OpenAI AI生成（待完成）
- [ ] 前后端联调和测试（下一步）
- [ ] 小范围推广（100-500用户）

### 第三阶段：完整产品（3-6个月）
- [ ] 智能复习系统（多维度测试）
- [ ] 游戏化机制（成就、排行榜）
- [ ] 社区功能（用户分享记忆技巧）
- [ ] iOS/Android App
- [ ] 浏览器插件

---

## 🎯 目标用户

1. **考试备考群体**（大学生、考研、托福/雅思）
2. **职场人士**（阅读英文文献、商务邮件）
3. **终身学习者**（有英语基础，想攻克长单词）

**市场规模**：
- 中国市场：大学生约4000万，考研人数年均400万+
- 全球市场：非英语母语国家学习者数以亿计

---

## 💰 商业模式

### 免费 + 增值

**免费版**：
- 每天学习 3 个长单词
- 基础复习功能

**高级版**（¥9.9/月 或 ¥99/年）：
- 无限学习单词
- 高级复习模式
- AI 个性化推荐
- 导出学习报告
- 无广告

**企业版**（¥299/年）：
- 培训机构、企业英语培训
- 批量账号管理
- 学习数据分析

---

## 📁 项目结构

```
ChaiWordDuck/
├── README.md                           # 项目说明
├── CLAUDE.md                          # AI 助手指南
├── .gitignore                         # Git 忽略规则
├── .claude/                           # Claude 配置目录
│
├── docs/                              # 文档目录
│   ├── product/                       # 产品文档
│   │   ├── PRD.md                     # 产品需求文档
│   │   ├── 01-产品可行性分析.md
│   │   ├── 02-品牌命名策略分析.md
│   │   └── 全球成人英語學習平台與長單詞記憶產品市場調研報告.md
│   │
│   ├── design/                        # 设计文档
│   │   └── DESIGN.md                  # UI/UX 设计文档
│   │
│   ├── architecture/                  # 架构文档
│   │   └── ARCHITECTURE.md            # 技术架构文档
│   │
│   └── project/                       # 项目管理文档
│
├── backend/                           # 后端服务 (FastAPI)
│   ├── app/                           # 应用代码
│   │   ├── main.py                    # FastAPI 入口
│   │   ├── api/                       # API 路由
│   │   ├── core/                      # 核心模块
│   │   ├── models/                    # 数据库模型
│   │   └── schemas/                   # Pydantic 模型
│   ├── tests/                         # 后端测试
│   │   ├── unit/                      # 单元测试
│   │   └── integration/               # 集成测试
│   ├── alembic/                       # 数据库迁移
│   ├── pyproject.toml                 # 后端依赖 (pdm)
│   └── README.md                      # 后端开发指南
│
└── frontend/                          # 前端应用 (Next.js)
    ├── app/                           # Next.js 页面
    ├── components/                    # React 组件
    ├── lib/                           # 工具函数
    ├── types/                         # TypeScript 类型
    ├── package.json                   # 前端依赖 (npm)
    └── README.md                      # 前端开发指南
```

## 📁 项目文档

### 产品文档
- [产品可行性分析](./docs/product/01-产品可行性分析.md)
- [品牌命名策略分析](./docs/product/02-品牌命名策略分析.md)
- [市场调研报告](./docs/product/全球成人英語學習平台與長單詞記憶產品市場調研報告.md)

---

## 🤝 团队协作

### 当前状态
- ✅ 完成产品构思和可行性分析
- ✅ 完成品牌命名和定位
- ✅ 完成技术架构设计
- ✅ 完成用户认证模块开发 (后端)
- ✅ 完成前端MVP开发 (前端)
- ✅ 完成后端核心API开发 (后端)
- 🔄 进行中：前后端联调和测试
- 📋 待办：Redis缓存集成、OpenAI AI生成、完整测试、部署上线

### 如何参与

如果你对这个项目感兴趣，无论是：
- 产品设计师
- 前端/后端开发
- UI/UX 设计师
- 英语教育专家
- 市场运营

都欢迎加入我们！

---

## 📞 联系方式

**项目发起人**：[待补充]
**项目地址**：https://github.com/cznccsjd/ChaiWordDuck

---

## 🎊 愿景

**让全球数百万英语学习者不再害怕长单词！**

我们相信，通过科学的方法和有趣的呈现，每个人都能轻松掌握那些看起来"很难"的长单词。

**拆词鸭，让学习变得简单而有趣！** 🦆

---

**项目启动日期**：2025-10-14
**当前版本**：v0.1.0-alpha (MVP 开发中)
