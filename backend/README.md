# 拆词鸭后端 API

## 项目简介

拆词鸭项目的后端服务,基于 FastAPI 开发,提供用户认证、单词管理、AI生成等核心功能。

## 技术栈

- **框架**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0 (异步)
- **数据库**: PostgreSQL 15+ (生产) / SQLite (测试)
- **迁移**: Alembic
- **认证**: JWT (python-jose) + bcrypt
- **测试**: pytest + pytest-asyncio + pytest-cov
- **包管理**: pdm

## 快速开始

### 1. 安装依赖

```bash
cd backend
pdm install
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件,配置数据库连接等信息
```

### 3. 运行数据库迁移

```bash
pdm run alembic upgrade head
```

### 4. 启动开发服务器

```bash
pdm run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看API文档

### 5. 运行测试

```bash
# 运行所有测试
pdm run pytest

# 运行测试并生成覆盖率报告
pdm run pytest --cov=app --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

## 项目结构

```
backend/
├── app/                      # 应用代码
│   ├── main.py              # FastAPI应用入口
│   ├── core/                # 核心模块
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 数据库连接
│   │   ├── dependencies.py  # 依赖注入
│   │   ├── logging.py       # 日志配置
│   │   └── security.py      # 安全工具(JWT/bcrypt)
│   ├── models/              # 数据库模型
│   │   └── user.py          # 用户模型
│   ├── schemas/             # Pydantic模型
│   │   ├── common.py        # 通用响应模型
│   │   └── user.py          # 用户相关模型
│   └── api/                 # API路由
│       └── v1/
│           └── auth.py      # 认证相关API
├── tests/                   # 测试代码
│   ├── unit/                # 单元测试
│   └── integration/         # 集成测试
├── alembic/                 # 数据库迁移
│   └── versions/            # 迁移脚本
├── pyproject.toml           # 项目配置
├── pdm.lock                 # 依赖锁定文件
└── alembic.ini              # Alembic配置
```

## 已实现功能

### 用户认证模块 ✅

- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户信息
- `POST /api/v1/auth/password-reset` - 请求密码重置
- `POST /api/v1/auth/password-reset/confirm` - 确认密码重置

### 数据库模型 ✅

- `users` - 用户表
- `guest_sessions` - 游客会话表
- `password_reset_tokens` - 密码重置令牌表

### 测试覆盖 ✅

- 35个测试 (20个单元测试 + 15个集成测试)
- 测试通过率: 97.2%
- 代码覆盖率: 80%

## 开发规范

### Git 提交规范

遵循 Conventional Commits:

```bash
feat(auth): add user registration endpoint
fix(security): fix JWT token expiration handling
docs(readme): update installation guide
test(auth): add integration tests for login
```

### 代码质量

- 遵循 PEP 8 规范
- 完整的类型注解 (Type Hints)
- 文档字符串 (Docstring)
- 结构化日志记录

### 测试要求

- 单元测试覆盖率 ≥ 95%
- 集成测试覆盖率 ≥ 90%
- 所有API端点必须有集成测试
- Bug修复必须添加回归测试

## 环境变量

创建 `.env` 文件配置以下变量:

```bash
# 数据库配置
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/chaiword_duck

# JWT配置
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Redis配置 (可选)
REDIS_URL=redis://localhost:6379/0

# OpenAI配置 (可选)
OPENAI_API_KEY=sk-...

# 日志级别
LOG_LEVEL=INFO
```

## 部署

### Docker部署

```bash
# 构建镜像
docker build -t chaiword-duck-backend .

# 运行容器
docker run -d -p 8000:8000 --env-file .env chaiword-duck-backend
```

### 生产环境

```bash
# 使用 Gunicorn + Uvicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

## 常见问题

### 1. 数据库初始化（首次启动必读）

**问题**: 启动服务后访问API出现 `relation "words" does not exist` 错误

**原因**: 数据库迁移脚本未执行，数据库表尚未创建

**解决方案**:
```bash
# 步骤1: 确保PostgreSQL服务正在运行
# 步骤2: 确保.env文件中的DATABASE_URL配置正确
# 步骤3: 执行数据库迁移
pdm run alembic upgrade head

# 步骤4: 验证迁移成功
pdm run alembic current  # 应显示: 004_guest_query_logs (head)
```

**验证数据**:
```bash
# 测试黄金手册单词查询
curl http://localhost:8000/api/v1/words/query/accommodation
```

### 2. AI服务配置（可选，用于AI生成单词）

**背景**: 当查询数据库中不存在的单词时，系统会调用AI服务实时生成单词学习手册。

**配置步骤**:

1. **获取OpenAI API Key**:
   - 访问 https://platform.openai.com/api-keys
   - 创建新的API Key
   - 复制API Key（格式：`sk-proj-...`）

2. **配置环境变量**:

   编辑 `backend/.env` 文件，添加：

   ```bash
   # AI服务选择
   AI_PROVIDER=openai  # 目前仅支持openai

   # OpenAI配置
   OPENAI_API_KEY=sk-proj-your-actual-key-here
   OPENAI_MODEL=gpt-4o-mini  # 或 gpt-3.5-turbo（更便宜）
   OPENAI_TEMPERATURE=0.7
   OPENAI_MAX_TOKENS=1000
   OPENAI_TIMEOUT=30

   # AI生成限额
   AI_GENERATION_LIMIT_GUEST=5   # 游客每天5次
   AI_GENERATION_LIMIT_USER=10   # 注册用户每天10次
   ```

3. **重启服务**:

   ```bash
   # Ctrl+C 停止当前服务
   pdm run uvicorn app.main:app --reload
   ```

4. **测试AI生成功能**:

   ```bash
   # 查询新单词（触发AI生成，耗时5-10秒）
   curl http://localhost:8000/api/v1/words/query/contribution

   # 预期返回：200 OK，包含AI生成的单词学习手册
   ```

5. **AI生成限额说明**:
   - **游客**（未登录）：5次/天/IP
   - **注册用户**：10次/天/用户
   - 超出限额后返回429错误：`AI_GENERATION_LIMIT_EXCEEDED`
   - AI生成的单词会缓存到数据库，避免重复生成

6. **成本控制**:
   - 使用 `gpt-4o-mini`：约 $0.01-0.03/次生成
   - 使用 `gpt-3.5-turbo`：约 $0.005-0.01/次生成
   - 首次生成后会缓存，后续查询不产生费用

**常见问题**:

- **Q: 如果没有配置OpenAI API Key会怎样？**
  - A: 查询新单词时会返回500错误（AI服务不可用）

- **Q: 如何查看AI生成日志？**
  - A: 查询数据库表 `ai_generation_logs`
    ```sql
    SELECT * FROM ai_generation_logs ORDER BY created_at DESC LIMIT 10;
    ```

- **Q: 如何重置AI生成限额？**
  - A: 限额按自然日计算（UTC时间0点重置），也可以手动清理：
    ```sql
    DELETE FROM ai_generation_logs WHERE created_at < CURRENT_DATE;
    ```

- **Q: OpenAI API调用超时怎么办？**
  - A: 调整`.env`中的`OPENAI_TIMEOUT`参数（默认30秒）

### 3. 数据库迁移失败

```bash
# 重置数据库
pdm run alembic downgrade base
pdm run alembic upgrade head
```

### 4. 测试失败

```bash
# 清理缓存
rm -rf .pytest_cache __pycache__
pdm run pytest
```

### 5. bcrypt版本问题

如果遇到bcrypt相关错误,确保使用bcrypt 4.1.2版本:

```bash
pdm add bcrypt==4.1.2
```

## 文档

- [完成报告](./COMPLETION_REPORT.md) - 开发完成情况和测试报告
- [测试覆盖报告](./TEST_COVERAGE_REVIEW_REPORT.md) - 测试覆盖率详细分析
- [API文档](http://localhost:8000/docs) - Swagger UI (开发服务器运行时)

## 许可证

MIT License

## 联系方式

项目地址: https://github.com/cznccsjd/ChaiWordDuck
