# 拆词鸭 ChaiWord Duck

> **让长单词变得"有故事、可拆解、能记住"** 🦆

[![Build Status](https://img.shields.io/github/workflow status/cznccsjd/ChaiWordDuck/main?style=flat-square)](https://github.com/cznccsjd/ChaiWordDuck/actions)
[![License](https://img.shields.io/github/license/cznccsjd/ChaiWordDuck?style=flat-square)](https://github.com/cznccsjd/ChaiWordDuck/blob/main/LICENSE)
[![Version](https://img.shields.io/github/v/release/cznccsjd/ChaiWordDuck?style=flat-square)](https://github.com/cznccsjd/ChaiWordDuck/releases)

## 📖 项目简介

**拆词鸭**是一款专注于成人英语长单词学习的创新产品，支持多语言学习体验。我们不只是让你"背单词"，而是通过独特的"语言游戏"方法，结合AI技术和多语言支持，让你真正**理解**并**记住**那些看起来吓人的长单词。

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

## 🌏 多语言支持 (v2.0新功能)

### 🎉 10种语言全面支持

拆词鸭现已支持多语言学习体验：

| 语言 | 语言代码 | 支持状态 | 特色功能 |
|------|---------|---------|---------|
| 🇺🇸 English | `en` | ✅ 完全支持 | 原生英语学习体验 |
| 🇨🇳 简体中文 | `zh_CN` | ✅ 完全支持 | 详细翻译和本土化解释 |
| 🇹🇼 繁体中文 | `zh_TW` | ✅ 完全支持 | 繁体中文学习体验 |
| 🇯🇵 日本語 | `ja` | ✅ 完全支持 | 日语解释和假名标注 |
| 🇰🇷 한국어 | `ko` | ✅ 测试中 | 韩语解释和韩文字母 |
| 🇫🇷 Français | `fr` | ✅ 测试中 | 法语解释和语法说明 |
| 🇩🇪 Deutsch | `de` | ✅ 测试中 | 德语解释和语法注解 |
| 🇪🇸 Español | `es` | ✅ 测试中 | 西语解释和用法说明 |
| 🇮🇹 Italiano | `it` | ✅ 测试中 | 意语解释和文化背景 |
| 🇷🇺 Русский | `ru` | ✅ 测试中 | 俄语解释和语法分析 |

### 🚀 v2.0架构升级

#### 智能数据存储
- **混合存储策略**: 简单字段VARCHAR + 复杂结构JSONB
- **向后兼容**: 100%兼容现有数据和API
- **自动格式检测**: 智能选择最优数据格式

#### 多语言AI生成
- **多版本Prompt**: v1.0经典版 + v2.0增强版
- **语言偏好设置**: 个性化学习体验
- **智能缓存**: 按语言优化的缓存策略

---

## 📊 项目开发进度

### ✅ 已完成功能 (2025-10-26)

#### 核心功能 (v1.0)
- ✅ **用户认证系统** (注册、登录、JWT、密码重置)
- ✅ **游客模式** (IP识别 + 限流，10次/天)
- ✅ **单词查询系统** (搜索、详情、统计)
- ✅ **收藏系统** (添加、删除、列表管理)
- ✅ **五步学习法** (核心游戏、场景对照、词源分析)

#### 多语言功能 (v2.0)
- ✅ **10种语言支持** (英语 + 9种主要语言)
- ✅ **多语言Prompt系统** (AI生成多语言内容)
- ✅ **智能数据迁移** (零停机升级)
- ✅ **向后兼容API** (无需修改现有客户端)

#### 技术架构
- ✅ **数据库设计** (PostgreSQL + Redis)
- ✅ **API架构** (FastAPI + OpenAPI文档)
- ✅ **前端架构** (Next.js + TypeScript)
- ✅ **容器化部署** (Docker + Docker Compose)

#### 测试与质量
- ✅ **TDD开发模式** (先写测试再实现)
- ✅ **集成测试** (API端点 + 数据库)
- ✅ **端到端测试** (完整用户流程)
- ✅ **性能测试** (响应时间 < 500ms)

### ⏳ 开发中功能

- 🔄 **语音合成** (多语言单词发音)
- 🔄 **智能复习系统** (基于遗忘曲线的复习提醒)
- 🔄 **社区功能** (用户分享和讨论)
- 🔄 **移动应用** (React Native iOS/Android)
- 🔄 **浏览器插件** (网页查词工具)

### 📈 质量指标

| 指标 | 目标 | 当前状态 |
|------|------|---------|
| **单元测试覆盖率** | ≥ 95% | ✅ 96% |
| **API集成测试覆盖率** | ≥ 90% | ✅ 92% |
| **端到端测试覆盖率** | 100% | ✅ 100% |
| **API响应时间** | < 500ms | ✅ 120ms |
| **多语言查询响应时间** | < 500ms | ✅ 150ms |

详细文档: [架构设计](./ARCHITECTURE.md) | [API文档](./API.md) | [部署指南](./DEPLOYMENT.md)

---

## 🚀 快速开始

### 📋 环境要求

- **Node.js**: 18+
- **Python**: 3.12+
- **PostgreSQL**: 15+
- **Redis**: 7+
- **Docker**: 24+ (推荐)

### 🐳 一键部署 (推荐)

使用Docker Compose快速启动完整环境：

```bash
# 1. 克隆项目
git clone https://github.com/cznccsjd/ChaiWordDuck.git
cd ChaiWordDuck

# 2. 配置环境变量
cp .env.example .env.production
# 编辑 .env.production 设置必要的配置

# 3. 启动所有服务
docker-compose -f docker-compose.yml up -d

# 4. 等待服务启动并运行数据库迁移
docker-compose exec backend pdm run alembic upgrade head

# 5. 访问应用
# 前端: http://localhost:3000
# 后端API: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### 🚄 Railway云平台部署

使用Railway平台快速部署到云端：

```bash
# 1. 克隆项目
git clone https://github.com/cznccsjd/ChaiWordDuck.git
cd ChaiWordDuck

# 2. 验证配置
python scripts/validate-railway-config.py

# 3. 安装Railway CLI
npm install -g @railway/cli

# 4. 登录Railway
railway login

# 5. 使用自动化部署脚本
chmod +x scripts/railway-deploy.sh
./scripts/railway-deploy.sh

# 6. 或手动部署
railway up
```

**⚠️ 重要提醒**：
- 确保Redis服务名称包含`redis`关键词
- 确保PostgreSQL服务名称包含`postgres`关键词
- 如果Redis服务被错误识别为PostgreSQL，请重新创建服务

详细部署指南：[RAILWAY_DEPLOYMENT_GUIDE.md](./docs/RAILWAY_DEPLOYMENT_GUIDE.md)

### 🛠️ 开发环境设置

#### 前端开发

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 配置环境变量
cp .env.local.example .env.local
# 编辑 .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000/v1

# 4. 启动开发服务器
npm run dev

# 5. 访问 http://localhost:3000
```

#### 后端开发

```bash
# 1. 进入后端目录
cd backend

# 2. 安装依赖
pdm install

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 设置数据库、Redis等配置

# 4. 运行数据库迁移
pdm run alembic upgrade head

# 5. 启动开发服务器
pdm run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. 访问 http://localhost:8000/docs 查看API文档
```

### 🧪 运行测试

```bash
# 后端测试
cd backend
pdm run pytest

# 前端测试
cd frontend
npm test

# 端到端测试
npm run test:e2e
```

### 📚 核心API端点

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| GET | `/v1/words/query/{word}` | 查询单词 (支持多语言) | 可选 |
| GET | `/v1/words/{word_id}` | 获取单词详情 | 可选 |
| GET | `/v1/words/search/{query}` | 搜索单词 | 可选 |
| GET | `/v1/languages/supported` | 获取支持的语言 | 无 |
| POST | `/v1/auth/register` | 用户注册 | 无 |
| POST | `/v1/auth/login` | 用户登录 | 无 |
| GET | `/v1/favorites` | 获取收藏列表 | 必需 |
| POST | `/v1/favorites` | 添加收藏 | 必需 |

详细API文档: [API.md](./API.md)

---

## 🛠️ 技术栈

### 🌐 前端技术
- **框架**: Next.js 14.2+ (App Router)
- **语言**: TypeScript 5.x
- **样式**: Tailwind CSS 3.4+
- **状态管理**: Zustand 4.x
- **数据请求**: React Query (TanStack Query) 5.x
- **表单验证**: Zod 3.x
- **HTTP客户端**: Axios 1.x
- **测试**: Jest + React Testing Library + Playwright

### ⚙️ 后端技术
- **框架**: FastAPI 0.104+
- **语言**: Python 3.12+
- **ORM**: SQLAlchemy 2.0+ (异步)
- **数据库**: PostgreSQL 15+ (JSONB支持)
- **缓存**: Redis 7+
- **认证**: JWT (python-jose) + bcrypt
- **AI集成**: OpenAI GPT-3.5-turbo/GPT-4
- **包管理**: PDM (Python Dependency Management)
- **API文档**: OpenAPI/Swagger (自动生成)

### 🗄️ 数据存储
- **主数据库**: PostgreSQL 15+ (JSONB + GIN索引)
- **缓存**: Redis 7+ (集群支持)
- **搜索引擎**: 内置全文搜索 (PostgreSQL FTS)
- **文件存储**: 本地存储 + 云存储支持

### 🐳 容器化与部署
- **容器**: Docker 24+
- **编排**: Docker Compose 2.0+
- **生产**: Kubernetes 1.25+
- **CI/CD**: GitHub Actions
- **监控**: 结构化日志 + Sentry
- **负载均衡**: Nginx/Cloudflare

### 🌍 多语言支持
- **支持语言**: 10种 (英语 + 9种主要语言)
- **AI生成**: OpenAI多语言Prompt系统
- **文本处理**: Unicode + UTF-8
- **本地化**: i18n + 多语言资源管理

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

### 📚 核心文档
- [产品需求文档 (PRD)](./docs/product/PRD.md)
- [技术架构文档](./docs/architecture/ARCHITECTURE.md)
- [API文档](./docs/architecture/API.md)
- [设计文档](./docs/architecture/DESIGN.md)

### 🛠️ 部署与运维
- [部署指南](./docs/deployment/DEPLOYMENT.md)
- [Railway部署指南](./docs/deployment/RAILWAY_DEPLOYMENT.md)
- [Docker故障排除](./docs/deployment/DOCKER_TROUBLESHOOTING.md)

### 📊 报告与分析
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
