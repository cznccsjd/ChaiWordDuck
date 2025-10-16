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

### ✅ 核心功能已完成 (2025-10-16)

后端MVP核心功能已实现，包括：

#### 用户认证与授权
- ✅ 用户认证系统（注册、登录、JWT、密码重置）
- ✅ 可选认证机制（支持游客模式）

#### 单词查询系统
- ✅ 单词查询API（查询、获取详情、统计）
- ✅ 游客识别服务（IP + 设备指纹）
- ✅ 统一限流服务（游客10次/天，注册50次/天）
- ✅ 查询历史记录

#### 收藏系统
- ✅ 添加/删除收藏
- ✅ 获取收藏列表
- ✅ 检查收藏状态

#### 数据库设计
- ✅ 5张核心表（users、words、favorites、query_logs、guest_query_logs）
- ✅ 数据库迁移脚本（Alembic）
- ✅ 预置10个黄金手册单词

#### 测试
- ✅ 游客模式集成测试（10+用例）
- ✅ 单词查询集成测试（API端点测试）
- ✅ TDD开发模式（先写测试再实现）

### ⏳ 待完成功能

- ⏳ Redis缓存集成（已预留接口）
- ⏳ OpenAI API集成（AI生成单词手册）
- ⏳ 复习提醒系统（邮件服务）
- ⏳ 性能优化（CDN、数据库索引）

详细进度请查看：[任务跟踪文档](./docs/TODOS.md) | [架构设计](./DESIGN.md)

---

## 🚀 如何运行项目

### 前端开发环境

#### 1. 安装依赖
```bash
cd frontend
npm install
```

#### 2. 配置环境变量
创建 `.env.local` 文件：
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

#### 3. 启动开发服务器
```bash
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000)

#### 4. 构建生产版本
```bash
npm run build
npm run start
```

#### 5. 代码检查
```bash
# ESLint检查
npm run lint

# TypeScript类型检查
npm run type-check
```

---

### 后端开发环境

#### 1. 安装依赖
```bash
cd backend
pdm install
```

#### 2. 配置环境变量
创建 `.env` 文件：
```bash
# 数据库配置
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/chaiword_duck

# JWT配置
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Redis配置（可选）
REDIS_URL=redis://localhost:6379/0

# OpenAI配置（可选）
OPENAI_API_KEY=sk-...

# 日志级别
LOG_LEVEL=INFO
```

#### 3. 运行数据库迁移
```bash
pdm run alembic upgrade head
```

#### 4. 启动开发服务器
```bash
pdm run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 [http://localhost:8000/docs](http://localhost:8000/docs) 查看API文档

#### 5. 运行测试
```bash
# 运行所有测试
pdm run pytest

# 运行测试并生成覆盖率报告
pdm run pytest --cov=app --cov-report=html
```

**已实现的API端点**：
- POST /api/v1/words/query - 查询单词
- GET /api/v1/words/query-limit - 获取查询统计
- GET /api/v1/words/{word_id} - 根据ID获取单词
- GET /api/v1/words/search/{word_text} - 根据单词文本查询（支持游客）
- POST /api/v1/favorites - 添加收藏
- DELETE /api/v1/favorites/{word_id} - 删除收藏
- GET /api/v1/favorites - 获取收藏列表
- GET /api/v1/favorites/check/{word_id} - 检查收藏状态

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

### 后端（部分完成）
- **框架**: FastAPI 0.104+
- **语言**: Python 3.11+
- **ORM**: SQLAlchemy 2.0 (异步)
- **数据库**: PostgreSQL 15+
- **认证**: JWT (python-jose) + bcrypt
- **测试**: pytest + pytest-asyncio
- **包管理**: pdm
- **缓存**: Redis 7+ (待集成)
- **AI**: OpenAI GPT-3.5-turbo (待集成)

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
- [x] 后端核心API开发（已完成 2025-10-16）
  - [x] 用户认证系统
  - [x] 单词查询系统
  - [x] 收藏系统
  - [x] 游客模式与限流系统
  - [x] 数据库设计与迁移
  - [x] 集成测试（TDD模式）
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
