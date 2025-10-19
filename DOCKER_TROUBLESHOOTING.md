# 拆词鸭项目 Docker 故障排除指南

## 🔍 问题诊断

### 症状：`socket.gaierror: [Errno 11001] getaddrinfo failed`

这个错误表示应用程序无法解析数据库主机名，通常由以下原因导致：

1. **API容器未启动** - 主要原因
2. **网络配置错误** - 容器间无法通信
3. **环境变量配置错误** - 使用了错误的主机名

## 🛠️ 修复方案

### 方案1：完整Docker部署（推荐）

```bash
# 1. 使用修复后的配置文件
cp docker-compose.fixed.yml docker-compose.yml

# 2. 配置环境变量
cp backend/.env.example backend/.env.docker
# 编辑 backend/.env.docker，设置必要的API密钥

# 3. 一键部署
# Windows
scripts\deploy-docker.bat prod

# Linux/Mac
chmod +x scripts/deploy-docker.sh
./scripts/deploy-docker.sh prod
```

### 方案2：开发环境部署

```bash
# 1. 仅启动数据库和Redis
# Windows
scripts\deploy-docker.bat dev

# Linux/Mac
./scripts/deploy-docker.sh dev

# 2. 本地启动API服务
cd backend
pdm run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. 本地启动前端服务
cd frontend
npm run dev
```

### 方案3：手动修复现有环境

#### 3.1 检查容器状态
```bash
docker ps -a
```

#### 3.2 检查网络配置
```bash
# 查看项目网络
docker network ls | grep chaiword

# 查看网络详情
docker network inspect chaiwordduck_default
```

#### 3.3 测试容器间连接
```bash
# 从数据库容器测试网络
docker exec chaiword_db ping -c 2 chaiword_redis

# 测试端口连通性
docker exec chaiword_db nc -zv chaiword_redis 6379
```

#### 3.4 修复环境变量

确保API容器使用正确的数据库连接字符串：

```bash
# 正确的Docker环境配置
DATABASE_URL=postgresql+asyncpg://postgres:password@chaiword_db:5432/chaiword_duck
REDIS_URL=redis://chaiword_redis:6379/0
```

**错误配置**（会导致getaddrinfo错误）：
```bash
# 错误：使用localhost
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/chaiword_duck

# 错误：使用127.0.0.1
DATABASE_URL=postgresql+asyncpg://postgres:password@127.0.0.1:5432/chaiword_duck
```

## 🔧 常见问题解决

### 问题1：容器启动失败

**症状**：`docker ps` 显示容器状态为 `Exited`

**解决方法**：
```bash
# 查看容器日志
docker logs chaiword_api
docker logs chaiword_db

# 重新构建镜像
docker-compose build --no-cache api

# 清理并重新启动
docker-compose down
docker system prune -f
docker-compose up -d
```

### 问题2：数据库连接超时

**症状**：API日志显示数据库连接超时

**解决方法**：
```bash
# 1. 检查数据库是否完全启动
docker logs chaiword_db | grep "database system is ready"

# 2. 检查健康检查状态
docker inspect chaiword_db | grep Health -A 10

# 3. 等待数据库完全启动
docker-compose up -d db
sleep 15
docker-compose up -d api
```

### 问题3：网络隔离问题

**症状**：容器间无法ping通

**解决方法**：
```bash
# 1. 确保容器在同一网络
docker network inspect chaiwordduck_default

# 2. 重新创建网络
docker network rm chaiwordduck_default
docker-compose up -d

# 3. 手动连接网络
docker network connect chaiwordduck_default chaiword_api
```

### 问题4：端口冲突

**症状**：`Port already in use` 错误

**解决方法**：
```bash
# 1. 查找占用端口的进程
netstat -ano | findstr :5432  # Windows
lsof -i :5432                 # Linux/Mac

# 2. 停止冲突的服务或更改端口
# 编辑 docker-compose.yml，修改端口映射
ports:
  - "5433:5432"  # 使用5433端口映射到容器5432
```

## 📊 监控和调试

### 实时查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f api
docker-compose logs -f db
```

### 进入容器调试
```bash
# 进入API容器
docker exec -it chaiword_api /bin/bash

# 进入数据库容器
docker exec -it chaiword_db psql -U postgres -d chaiword_duck

# 测试数据库连接
docker exec -it chaiword_api python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
engine = create_async_engine('postgresql+asyncpg://postgres:password@chaiword_db:5432/chaiword_duck')
async def test():
    async with engine.connect() as conn:
        result = await conn.execute('SELECT 1')
        print('Database connection successful!')
asyncio.run(test())
"
```

### 性能监控
```bash
# 查看容器资源使用情况
docker stats

# 查看容器详细信息
docker inspect chaiword_api
```

## 🚀 快速部署检查清单

### 部署前检查
- [ ] Docker和Docker Compose已安装
- [ ] 项目代码已更新到最新版本
- [ ] 环境变量文件已配置
- [ ] 端口5432、6379、8000、3000未被占用

### 部署步骤
- [ ] 停止旧的容器：`docker-compose down`
- [ ] 拉取最新代码：`git pull`
- [ ] 构建镜像：`docker-compose build`
- [ ] 启动服务：`docker-compose up -d`
- [ ] 等待健康检查通过
- [ ] 验证服务可访问性

### 部署后验证
- [ ] 检查容器状态：`docker ps`
- [ ] 检查健康状态：`docker-compose ps`
- [ ] 测试API健康检查：`curl http://localhost:8000/health`
- [ ] 测试数据库连接：查看API日志
- [ ] 测试前端页面：访问 http://localhost:3000

## 🆘 紧急故障恢复

### 完全重置环境
```bash
# 1. 停止所有服务
docker-compose down --remove-orphans

# 2. 删除所有相关容器
docker rm -f chaiword_api chaiword_db chaiword_redis chaiword_db_test 2>/dev/null || true

# 3. 删除网络
docker network rm chaiwordduck_default chaiwordduck_chaiword_network 2>/dev/null || true

# 4. 清理镜像（可选）
docker system prune -f

# 5. 重新部署
./scripts/deploy-docker.sh prod
```

### 数据备份和恢复
```bash
# 备份数据库
docker exec chaiword_db pg_dump -U postgres chaiword_duck > backup.sql

# 恢复数据库
docker exec -i chaiword_db psql -U postgres chaiword_duck < backup.sql
```

---

**最后更新时间**: 2025-10-19
**维护人员**: Claude Code Debugging Specialist
**版本**: v1.0.0