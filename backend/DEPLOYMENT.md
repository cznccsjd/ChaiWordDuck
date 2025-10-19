# 拆词鸭后端部署指南

## 📦 pip包依赖部署说明

本项目现在支持使用传统的 pip 包管理进行部署，无需安装 PDM。我们提供了多种依赖文件以适应不同的部署场景。

### 🎯 推荐方案概览

| 部署环境 | 推荐文件 | 说明 |
|---------|----------|------|
| **生产环境** | `requirements-core.txt` | 精简核心依赖，最小化安装 |
| **完整生产环境** | `requirements.txt` | 包含所有传递依赖 |
| **开发环境** | `requirements-dev.txt` | 包含开发和测试工具 |
| **测试环境** | `requirements-core.txt` + `requirements-test.txt` | 分离安装，便于管理 |

## 🚀 快速部署

### 生产环境部署

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 2. 安装核心依赖
pip install -r requirements-core.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 4. 运行数据库迁移
alembic upgrade head

# 5. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 开发环境部署

```bash
# 1. 安装所有依赖（包含开发工具）
pip install -r requirements-dev.txt

# 2. 运行测试
pytest

# 3. 代码格式化
black .
ruff check .

# 4. 启动开发服务器
uvicorn app.main:app --reload
```

## 📋 依赖文件详细说明

### 1. requirements-core.txt
**用途**：生产环境核心依赖
**特点**：
- 仅包含必需的运行时依赖
- 精简安装，减少安全风险
- 适合 Docker 容器部署
- 安装速度快

**核心依赖包**：
- Web框架：FastAPI, Uvicorn
- 数据库：SQLAlchemy, AsyncPG, Alembic
- AI服务：OpenAI, Google GenerativeAI
- 认证：python-jose, passlib
- 缓存：Redis

### 2. requirements.txt
**用途**：完整生产环境
**特点**：
- 包含所有传递依赖
- 版本锁定，确保一致性
- 适合传统部署环境
- PDM 自动生成，无需手动维护

### 3. requirements-dev.txt
**用途**：开发和测试环境
**特点**：
- 包含所有生产依赖
- 额外包含开发工具
- 适合本地开发环境

**额外工具**：
- 测试：pytest, pytest-asyncio
- 代码质量：black, ruff, mypy
- 测试数据：faker
- HTTP测试：httpx

### 4. requirements-test.txt
**用途**：测试工具补充
**特点**：
- 仅包含测试相关工具
- 需要配合 requirements-core.txt 使用
- 便于CI/CD环境分离安装

## 🔧 平台特定部署指南

### Railway 部署

```bash
# Railway 设置
Build Command: pip install -r requirements-core.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Render 部署

```bash
# Render 设置
Build Command: pip install -r requirements-core.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 复制依赖文件
COPY requirements-core.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements-core.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 传统服务器部署

```bash
# 1. 系统依赖安装
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip postgresql-client

# 2. 项目部署
git clone https://github.com/cznccsjd/ChaiWordDuck.git
cd ChaiWordDuck/backend

# 3. 虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 4. 安装依赖
pip install --upgrade pip
pip install -r requirements-core.txt

# 5. 配置和启动
cp .env.example .env
# 编辑 .env
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🔍 验证部署

### 健康检查

```bash
# 检查API服务
curl http://localhost:8000/health

# 检查数据库连接
curl http://localhost:8000/health | jq '.services.database'
```

### 功能测试

```bash
# 运行基础测试（如果安装了测试依赖）
pytest tests/test_health.py -v

# 测试API端点
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "TestPass123"}'
```

## 🛠️ 常见问题解决

### 1. 依赖安装失败

```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements-core.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 清理缓存重试
pip cache purge
pip install -r requirements-core.txt --no-cache-dir
```

### 2. 数据库连接问题

```bash
# 检查环境变量
echo $DATABASE_URL

# 测试数据库连接
python -c "
import asyncpg
import asyncio

async def test():
    try:
        conn = await asyncpg.connect('$DATABASE_URL')
        print('Database connection successful!')
        await conn.close()
    except Exception as e:
        print(f'Database connection failed: {e}')

asyncio.run(test())
"
```

### 3. Redis 连接问题

```bash
# 测试Redis连接
python -c "
import redis
try:
    r = redis.from_url('$REDIS_URL')
    r.ping()
    print('Redis connection successful!')
except Exception as e:
    print(f'Redis connection failed: {e}')
"
```

## 📈 性能优化建议

### 1. 生产环境优化

```bash
# 使用 gunicorn（多进程）
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# 或直接使用 uvicorn 多进程
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. 内存优化

```bash
# 调整连接池大小
export DATABASE_POOL_SIZE=20
export DATABASE_MAX_OVERFLOW=10
```

## 🔄 依赖更新

### 更新生产依赖

```bash
# 1. 在 PDM 环境中更新
pdm update

# 2. 重新导出依赖
cd backend
pdm export -f requirements --without-hashes --prod -o requirements.txt

# 3. 手动更新核心依赖（可选）
# 编辑 requirements-core.txt
```

### 安全更新

```bash
# 检查已知漏洞
pip install safety
safety check -r requirements-core.txt

# 更新有漏洞的包
pip install --upgrade package-name
```

## 📋 部署检查清单

### 部署前检查
- [ ] Python 3.11+ 已安装
- [ ] 虚拟环境已创建
- [ ] 环境变量已配置
- [ ] 数据库服务可用
- [ ] Redis 服务可用
- [ ] 防火墙端口已开放

### 部署后验证
- [ ] API 健康检查通过
- [ ] 数据库连接正常
- [ ] Redis 连接正常
- [ ] 用户注册功能正常
- [ ] 单词查询功能正常
- [ ] 日志无错误信息

---

**注意**：
- 生产环境建议使用 `requirements-core.txt` 以减少攻击面
- 定期检查依赖包的安全更新
- 建议使用虚拟环境隔离依赖
- 监控依赖包的大小和性能影响