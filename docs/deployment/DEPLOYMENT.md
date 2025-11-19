# 拆词鸭 ChaiWord Duck - 部署指南

## 1. 部署概述

### 1.1 支持的部署环境

| 环境 | 描述 | 推荐用于 |
|------|------|----------|
| **Docker Compose** | 本地开发和小规模部署 | 开发、测试、小规模生产 |
| **Kubernetes** | 容器编排和自动扩缩容 | 中到大规模生产环境 |
| **Vercel (前端) + Railway/Render (后端)** | 无服务器部署 | 快速原型和MVP |
| **云服务商托管** | AWS/GCP/Azure | 企业级部署 |

### 1.2 部署架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        生产环境架构                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CDN/WAF       │    │   Load Balancer │    │   Web Server    │
│  (Cloudflare)   │───▶│    (Nginx)      │───▶│   (Nginx/Caddy) │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                      │
                           ┌────────────────────────┴────────────────────────┐
                           │                                               │
                ┌─────────────────┐                          ┌─────────────────┐
                │  Frontend App   │                          │  Backend API    │
                │ (Next.js SPA)   │                          │   (FastAPI)     │
                │                 │                          │                 │
                └─────────────────┘                          └─────────────────┘
                                                                     │
                           ┌────────────────────────┬───────────────────┼──────────────────┬─────────────────┐
                           │                        │                   │                  │                 │
                ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
                │  PostgreSQL     │   │     Redis       │   │   OpenAI API   │ │  SendGrid      │ │   Sentry       │
                │   (Database)    │   │    (Cache)      │   │   (AI生成)     │ │   (邮件)       │ │   (监控)       │
                │                 │   │                 │   │                 │ │                 │ │                 │
                └─────────────────┘   └─────────────────┘   └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 1.3 技术要求

#### 最低配置要求

| 组件 | CPU | 内存 | 存储 | 带宽 |
|------|-----|------|------|------|
| **Frontend** | 1核 | 512MB | 10GB | 1Mbps |
| **Backend** | 2核 | 2GB | 20GB | 5Mbps |
| **PostgreSQL** | 2核 | 2GB | 50GB SSD | 10Mbps |
| **Redis** | 1核 | 1GB | 10GB SSD | 5Mbps |

#### 推荐生产配置

| 组件 | CPU | 内存 | 存储 | 带宽 |
|------|-----|------|------|------|
| **Frontend** | 2核 | 2GB | 20GB SSD | 10Mbps |
| **Backend** | 4核 | 8GB | 50GB SSD | 50Mbps |
| **PostgreSQL** | 4核 | 16GB | 200GB SSD | 100Mbps |
| **Redis** | 2核 | 4GB | 50GB SSD | 20Mbps |

---

## 2. 环境准备

### 2.1 系统要求

- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **容器运行时**: Docker 24.0+ / Docker Compose 2.0+
- **Kubernetes**: 1.25+ (如果使用K8s部署)
- **Node.js**: 18+ (前端构建)
- **Python**: 3.12+ (后端开发环境)

### 2.2 依赖服务配置

#### PostgreSQL 15+ 配置

```bash
# 1. 安装PostgreSQL 15
sudo apt update
sudo apt install -y postgresql-15 postgresql-contrib

# 2. 修改配置文件 /etc/postgresql/15/main/postgresql.conf
sudo nano /etc/postgresql/15/main/postgresql.conf

# 添加以下配置
# 内存配置
shared_buffers = 256MB                    # 根据服务器内存调整
effective_cache_size = 1GB               # 根据服务器内存调整
work_mem = 4MB                           # 提高JSONB查询性能
maintenance_work_mem = 64MB

# 连接配置
max_connections = 100                     # 并发连接数
listen_addresses = '*'                   # 监听所有地址

# 日志配置
log_statement = 'all'                    # 记录所有SQL语句
log_min_duration_statement = 1000         # 记录慢查询（1秒+）
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '

# 3. 修改pg_hba.conf允许连接
sudo nano /etc/postgresql/15/main/pg_hba.conf
# 添加
host    all             all             0.0.0.0/0               md5

# 4. 重启PostgreSQL
sudo systemctl restart postgresql
sudo systemctl enable postgresql
```

#### Redis 7+ 配置

```bash
# 1. 安装Redis 7
sudo apt install -y redis

# 2. 修改配置 /etc/redis/redis.conf
sudo nano /etc/redis/redis.conf

# 添加以下配置
# 网络配置
bind 0.0.0.0                          # 允许外部连接
port 6379
protected-mode no                      # 生产环境应该开启并设置密码

# 内存配置
maxmemory 512mb                       # 根据服务器内存调整
maxmemory-policy allkeys-lru          # 内存满时的淘汰策略

# 持久化配置
save 900 1                            # 15分钟内有1个key变更就保存
save 300 10                           # 5分钟内有10个key变更就保存
save 60 10000                         # 1分钟内有10000个key变更就保存

# 安全配置
requirepass your-strong-password       # 设置密码
rename-command CONFIG ""               # 禁用CONFIG命令
rename-command FLUSHDB ""              # 禁用FLUSHDB命令
rename-command FLUSHALL ""             # 禁用FLUSHALL命令

# 日志配置
loglevel notice
logfile /var/log/redis/redis-server.log

# 3. 重启Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

---

## 3. 应用部署

### 3.1 Docker Compose 部署

#### 3.1.1 环境变量配置

创建 `.env.production` 文件：

```bash
# 环境标识
ENVIRONMENT=production
DEBUG=false

# 数据库配置
DATABASE_URL=postgresql+asyncpg://chaiword_user:your_db_password@postgres:5432/chaiword_duck
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0
REDIS_POOL_SIZE=20

# JWT配置
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080

# OpenAI配置
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000

# 多语言配置
DEFAULT_LANGUAGE_CODE=en
SUPPORTED_LANGUAGES=en,zh_CN,zh_TW,ja,ko,fr,de,es,it,ru
PROMPT_VERSION=v2.0

# 查询限制配置
GUEST_DAILY_LIMIT=10
FREE_USER_DAILY_LIMIT=50
PREMIUM_USER_DAILY_LIMIT=-1
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=1000

# 邮件配置
SENDGRID_API_KEY=SG.your-sendgrid-api-key
FROM_EMAIL=noreply@chaiwordduck.com

# 监控配置
SENTRY_DSN=https://your-sentry-dsn
LOG_LEVEL=INFO

# CORS配置
CORS_ORIGINS=https://chaiwordduck.com,https://www.chaiwordduck.com
CORS_ALLOW_CREDENTIALS=true

# 前端配置
NEXT_PUBLIC_API_URL=https://api.chaiwordduck.com/v1
NEXT_PUBLIC_APP_URL=https://chaiwordduck.com
```

#### 3.1.2 Docker Compose 配置

创建 `docker-compose.production.yml`：

```yaml
version: '3.9'

services:
  # PostgreSQL 数据库
  postgres:
    image: postgres:15-alpine
    container_name: chaiword-postgres
    environment:
      POSTGRES_USER: chaiword_user
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}
      POSTGRES_DB: chaiword_duck
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
      - ./backup:/backup
    ports:
      - "5432:5432"
    networks:
      - chaiword-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U chaiword_user"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: chaiword-redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf
    ports:
      - "6379:6379"
    networks:
      - chaiword-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # 后端 API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.production
    container_name: chaiword-backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://chaiword_user:${DATABASE_PASSWORD}@postgres:5432/chaiword_duck
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - SENDGRID_API_KEY=${SENDGRID_API_KEY}
      - SENTRY_DSN=${SENTRY_DSN}
      - ENVIRONMENT=production
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - chaiword-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # 前端应用
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.production
      args:
        - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
        - NEXT_PUBLIC_APP_URL=${NEXT_PUBLIC_APP_URL}
    container_name: chaiword-frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    networks:
      - chaiword-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    container_name: chaiword-nginx
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./ssl:/etc/ssl/certs
      - ./logs/nginx:/var/log/nginx
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - frontend
      - backend
    networks:
      - chaiword-network
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  chaiword-network:
    driver: bridge
```

#### 3.1.3 Nginx 配置

创建 `nginx/conf.d/chaiword.conf`：

```nginx
# 上游后端服务器
upstream backend {
    server backend:8000;
    keepalive 32;
}

# HTTP重定向到HTTPS
server {
    listen 80;
    server_name chaiwordduck.com www.chaiwordduck.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS主服务器
server {
    listen 443 ssl http2;
    server_name chaiwordduck.com www.chaiwordduck.com;

    # SSL配置
    ssl_certificate /etc/ssl/certs/chaiwordduck.com.crt;
    ssl_certificate_key /etc/ssl/certs/chaiwordduck.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 静态文件缓存
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        root /var/www/html;
    }

    # API代理
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # 限流
        limit_req zone=api burst=30 nodelay;
    }

    # 健康检查
    location /health {
        proxy_pass http://backend;
        access_log off;
    }

    # 前端应用
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # 限制请求区域定义
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;
}
```

#### 3.1.4 部署脚本

创建 `deploy.sh`：

```bash
#!/bin/bash

set -e

echo "🚀 开始部署拆词鸭应用..."

# 1. 检查环境
echo "📋 检查部署环境..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

# 2. 加载环境变量
if [ ! -f .env.production ]; then
    echo "❌ .env.production 文件不存在"
    exit 1
fi

source .env.production

# 3. 创建必要的目录
echo "📁 创建目录结构..."
mkdir -p logs/nginx logs/app backup uploads ssl

# 4. 备份数据库
echo "💾 备份数据库..."
if docker ps | grep -q chaiword-postgres; then
    docker exec chaiword-postgres pg_dump -U chaiword_user -d chaiword_duck > "backup/backup_$(date +%Y%m%d_%H%M%S).sql"
    echo "✅ 数据库备份完成"
fi

# 5. 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin main

# 6. 构建和启动服务
echo "🔨 构建和启动服务..."
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d

# 7. 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 8. 运行数据库迁移
echo "🗃️ 运行数据库迁移..."
docker exec chaiword-backend pdm run alembic upgrade head

# 9. 健康检查
echo "🏥 执行健康检查..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ 后端服务健康"
else
    echo "❌ 后端服务不健康"
    exit 1
fi

if curl -f https://chaiwordduck.com > /dev/null 2>&1; then
    echo "✅ 前端服务健康"
else
    echo "❌ 前端服务不健康"
    exit 1
fi

# 10. 清理旧镜像
echo "🧹 清理旧镜像..."
docker image prune -f

echo "🎉 部署完成！"
echo "📍 前端地址: https://chaiwordduck.com"
echo "📍 API文档: https://chaiwordduck.com/docs"
echo "📍 健康检查: https://chaiwordduck.com/health"
```

### 3.2 Kubernetes 部署

#### 3.2.1 命名空间和配置

创建 `k8s/namespace.yaml`：

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: chaiword
  labels:
    name: chaiword
```

创建 `k8s/configmap.yaml`：

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: chaiword-config
  namespace: chaiword
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  DEFAULT_LANGUAGE_CODE: "en"
  SUPPORTED_LANGUAGES: "en,zh_CN,zh_TW,ja,ko,fr,de,es,it,ru"
  PROMPT_VERSION: "v2.0"
  GUEST_DAILY_LIMIT: "10"
  FREE_USER_DAILY_LIMIT: "50"
  PREMIUM_USER_DAILY_LIMIT: "-1"
  RATE_LIMIT_PER_MINUTE: "30"
  RATE_LIMIT_PER_HOUR: "1000"
  NEXT_PUBLIC_API_URL: "https://api.chaiwordduck.com/v1"
  NEXT_PUBLIC_APP_URL: "https://chaiwordduck.com"
```

#### 3.2.2 密钥管理

创建 `k8s/secrets.yaml`：

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: chaiword-secrets
  namespace: chaiword
type: Opaque
data:
  DATABASE_URL: <base64-encoded-database-url>
  JWT_SECRET_KEY: <base64-encoded-jwt-secret>
  OPENAI_API_KEY: <base64-encoded-openai-key>
  REDIS_PASSWORD: <base64-encoded-redis-password>
  SENDGRID_API_KEY: <base64-encoded-sendgrid-key>
  SENTRY_DSN: <base64-encoded-sentry-dsn>
```

#### 3.2.3 数据库部署

创建 `k8s/postgres.yaml`：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: chaiword
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: chaiword_duck
        - name: POSTGRES_USER
          value: chaiword_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: chaiword-secrets
              key: DATABASE_PASSWORD
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "1000m"
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: chaiword
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: chaiword
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: fast-ssd
```

#### 3.2.4 后端部署

创建 `k8s/backend.yaml`：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: chaiword
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: ghcr.io/chaiword/backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: chaiword-config
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: chaiword-secrets
              key: DATABASE_URL
        - name: REDIS_URL
          value: "redis://:$(REDIS_PASSWORD)@redis-service:6379/0"
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: chaiword-secrets
              key: REDIS_PASSWORD
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: chaiword-secrets
              key: JWT_SECRET_KEY
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: chaiword-secrets
              key: OPENAI_API_KEY
        - name: SENTRY_DSN
          valueFrom:
            secretKeyRef:
              name: chaiword-secrets
              key: SENTRY_DSN
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3

---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: chaiword
spec:
  selector:
    app: backend
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: chaiword
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 4. 数据库迁移

### 4.1 迁移前检查

```bash
# 1. 备份数据库
pg_dump -h localhost -U chaiword_user -d chaiword_duck > backup_before_migration.sql

# 2. 检查当前版本
pdm run alembic current
pdm run alembic history

# 3. 验证数据完整性
pdm run python -c "
import asyncio
from app.core.database import get_db_session
from app.models.word import Word

async def check_data():
    async with get_db_session() as db:
        result = await db.execute('SELECT COUNT(*) FROM words')
        total = result.scalar()
        print(f'总单词数: {total}')

        result = await db.execute('SELECT COUNT(*) FROM words WHERE is_golden = true')
        golden = result.scalar()
        print(f'黄金手册数: {golden}')

asyncio.run(check_data())
"
```

### 4.2 执行迁移

#### 4.2.1 单步迁移

```bash
# 检查待执行的迁移
pdm run alembic show head

# 执行迁移
pdm run alembic upgrade head

# 验证迁移结果
pdm run alembic current
```

#### 4.2.2 分步迁移（推荐）

```bash
# 1. 添加新字段（阶段1）
pdm run alembic upgrade 005_add_multilang_prompt_support

# 2. 验证字段添加成功
pdm run python -c "
import asyncio
from app.core.database import get_db_session
from sqlalchemy import text

async def verify_fields():
    async with get_db_session() as db:
        # 检查新字段是否存在
        result = await db.execute(text('''
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'words'
            AND column_name IN ('translation', 'language_code', 'core_game_new')
        '''))

        for row in result:
            print(f'字段: {row[0]}, 类型: {row[1]}')

asyncio.run(verify_fields())
"

# 3. 运行数据迁移脚本
pdm run python scripts/migrate_multilang_data.py

# 4. 验证数据迁移
pdm run python -c "
import asyncio
from app.core.database import get_db_session

async def verify_migration():
    async with get_db_session() as db:
        result = await db.execute('SELECT COUNT(*) FROM words WHERE is_legacy_format = false')
        new_format = result.scalar()

        result = await db.execute('SELECT COUNT(*) FROM words')
        total = result.scalar()

        print(f'新格式数据: {new_format}/{total} ({new_format/total*100:.1f}%)')

asyncio.run(verify_migration())
"
```

### 4.3 迁移后验证

```bash
# 1. 性能测试
pdm run python -c "
import asyncio
import time
from app.services.word import WordService
from app.core.database import get_db_session

async def performance_test():
    async with get_db_session() as db:
        service = WordService()

        # 测试查询性能
        start = time.time()
        word = await service.get_word_by_text(db, 'accountability')
        duration = time.time() - start

        print(f'单词查询耗时: {duration*1000:.1f}ms')

        # 测试JSONB字段访问
        start = time.time()
        if word and word.core_game_new:
            content = word.core_game_new.get('content', '')
        duration = time.time() - start

        print(f'JSONB字段访问耗时: {duration*1000:.1f}ms')

asyncio.run(performance_test())
"

# 2. API测试
curl -X GET "https://api.chaiwordduck.com/v1/words/query/accountability?language_code=zh_CN" \
  -H "Accept: application/json"

# 3. 索引效果验证
psql -h localhost -U chaiword_user -d chaiword_duck -c "
EXPLAIN ANALYZE
SELECT * FROM words
WHERE core_game_new->>'content' LIKE '%问责%'
AND language_code = 'zh_CN';
"
```

---

## 5. 回滚方案

### 5.1 应用回滚

#### 5.1.1 Docker Compose 回滚

```bash
# 1. 查看之前运行的镜像版本
docker images | grep chaiword

# 2. 回滚到指定版本
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d \
  --force-recreate \
  --image ghcr.io/chaiword/backend:v1.0.0 \
  --image ghcr.io/chaiword/frontend:v1.0.0

# 3. 验证回滚
curl -f https://chaiwordduck.com/health
```

#### 5.1.2 Kubernetes 回滚

```bash
# 1. 查看部署历史
kubectl rollout history deployment/backend -n chaiword

# 2. 回滚到上一个版本
kubectl rollout undo deployment/backend -n chaiword

# 3. 回滚到指定版本
kubectl rollout undo deployment/backend --to-revision=2 -n chaiword

# 4. 验证回滚状态
kubectl rollout status deployment/backend -n chaiword
```

### 5.2 数据库回滚

#### 5.2.1 Alembic 回滚

```bash
# 1. 查看当前迁移版本
pdm run alembic current

# 2. 回滚一个版本
pdm run alembic downgrade -1

# 3. 回滚到指定版本
pdm run alembic downgrade 004_add_guest_query_logs

# 4. 回滚到基础版本
pdm run alembic downgrade base

# 5. 验证回滚
pdm run alembic current
```

#### 5.2.2 数据库备份恢复

```bash
# 1. 停止应用服务
docker-compose -f docker-compose.production.yml stop backend

# 2. 恢复数据库备份
psql -h localhost -U chaiword_user -d chaiword_duck < backup_20251026_100000.sql

# 3. 验证数据完整性
pdm run python scripts/verify_data_integrity.py

# 4. 重启应用服务
docker-compose -f docker-compose.production.yml start backend
```

### 5.3 紧急回滚脚本

创建 `rollback.sh`：

```bash
#!/bin/bash

set -e

ROLLBACK_TYPE=${1:-"app"}
BACKUP_FILE=${2:-"latest"}

echo "🚨 开始紧急回滚..."

case $ROLLBACK_TYPE in
    "app")
        echo "📦 回滚应用..."
        # 回滚到上一个稳定版本
        git checkout HEAD~1

        # 重新构建和部署
        docker-compose -f docker-compose.production.yml down
        docker-compose -f docker-compose.production.yml build --no-cache
        docker-compose -f docker-compose.production.yml up -d

        # 等待服务启动
        sleep 30

        # 健康检查
        if curl -f https://chaiwordduck.com/health > /dev/null 2>&1; then
            echo "✅ 应用回滚成功"
        else
            echo "❌ 应用回滚失败"
            exit 1
        fi
        ;;

    "db")
        echo "💾 回滚数据库..."

        # 选择备份文件
        if [ "$BACKUP_FILE" = "latest" ]; then
            BACKUP_FILE=$(ls -t backup/*.sql | head -1)
        fi

        echo "使用备份文件: $BACKUP_FILE"

        # 停止应用
        docker-compose -f docker-compose.production.yml stop backend

        # 恢复数据库
        psql -h localhost -U chaiword_user -d chaiword_duck < "$BACKUP_FILE"

        # 验证数据
        if pdm run python scripts/verify_data_integrity.py; then
            echo "✅ 数据库回滚成功"
        else
            echo "❌ 数据库回滚失败"
            exit 1
        fi

        # 重启应用
        docker-compose -f docker-compose.production.yml start backend
        ;;

    "full")
        echo "🔄 完整回滚（应用+数据库）..."

        # 应用回滚
        $0 app

        # 数据库回滚
        $0 db "$BACKUP_FILE"
        ;;

    *)
        echo "用法: $0 {app|db|full} [backup_file]"
        echo "  app - 回滚应用代码"
        echo "  db  - 回滚数据库"
        echo "  full - 完整回滚"
        exit 1
        ;;
esac

echo "🎉 回滚完成！"
```

---

## 6. 监控和维护

### 6.1 健康检查

#### 6.1.1 应用健康检查

```bash
# 后端健康检查
curl -f https://api.chaiwordduck.com/health

# 数据库连接检查
curl -f https://api.chaiwordduck.com/health/database

# Redis连接检查
curl -f https://api.chaiwordduck.com/health/redis

# 综合健康检查
curl -f https://api.chaiwordduck.com/health/all
```

#### 6.1.2 创建健康检查脚本

创建 `scripts/health_check.sh`：

```bash
#!/bin/bash

# 健康检查脚本
API_URL="https://api.chaiwordduck.com"
WEB_URL="https://chaiwordduck.com"

# 检查函数
check_endpoint() {
    local url=$1
    local name=$2

    if curl -f -s "$url" > /dev/null; then
        echo "✅ $name: 正常"
        return 0
    else
        echo "❌ $name: 异常"
        return 1
    fi
}

# 执行检查
echo "🏥 开始健康检查..."
echo ""

overall_status=0

check_endpoint "$API_URL/health" "后端API" || overall_status=1
check_endpoint "$WEB_URL" "前端网站" || overall_status=1
check_endpoint "$API_URL/v1/words/query/hello" "单词查询API" || overall_status=1
check_endpoint "$API_URL/docs" "API文档" || overall_status=1

echo ""
if [ $overall_status -eq 0 ]; then
    echo "🎉 所有服务正常"
else
    echo "🚨 发现服务异常"
    exit 1
fi
```

### 6.2 日志监控

#### 6.2.1 应用日志查看

```bash
# 查看应用日志
docker logs -f chaiword-backend

# 查看Nginx日志
docker logs -f chaiword-nginx

# 查看错误日志
tail -f logs/app/error.log

# 查看访问日志
tail -f logs/nginx/access.log
```

#### 6.2.2 日志分析脚本

创建 `scripts/analyze_logs.sh`：

```bash
#!/bin/bash

LOG_DIR="./logs"
ERROR_LOG="$LOG_DIR/app/error.log"
ACCESS_LOG="$LOG_DIR/nginx/access.log"

echo "📊 分析应用日志..."

if [ -f "$ERROR_LOG" ]; then
    echo "🔍 最近的错误:"
    tail -20 "$ERROR_LOG"
    echo ""

    echo "📈 今日错误统计:"
    grep "$(date +%Y-%m-%d)" "$ERROR_LOG" | wc -l
    echo ""
fi

if [ -f "$ACCESS_LOG" ]; then
    echo "🌐 访问统计 (今日):"
    grep "$(date +%d/%b/%Y)" "$ACCESS_LOG" | awk '{print $1}' | sort | uniq -c | sort -nr | head -10
    echo ""

    echo "📱 用户代理统计:"
    grep "$(date +%d/%b/%Y)" "$ACCESS_LOG" | awk -F'"' '{print $6}' | sort | uniq -c | sort -nr | head -5
fi
```

### 6.3 性能监控

#### 6.3.1 资源使用监控

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
df -h

# 查看内存使用
free -h

# 查看CPU使用
top
```

#### 6.3.2 数据库性能监控

```sql
-- 查看慢查询
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC
LIMIT 10;

-- 查看连接数
SELECT count(*) FROM pg_stat_activity;

-- 查看数据库大小
SELECT pg_size_pretty(pg_database_size('chaiword_duck'));

-- 查看表大小
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 7. 故障排除

### 7.1 常见问题

#### 7.1.1 应用启动失败

**问题**: 容器启动后立即退出

**诊断步骤**:
```bash
# 1. 查看容器日志
docker logs chaiword-backend

# 2. 检查环境变量
docker exec chaiword-backend env | grep -E "(DATABASE|REDIS|JWT)"

# 3. 验证数据库连接
docker exec chaiword-backend pdm run python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def test_db():
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as conn:
        result = await conn.execute('SELECT 1')
        print('数据库连接正常')

asyncio.run(test_db())
"
```

**常见解决方案**:
1. 检查数据库连接字符串
2. 验证环境变量配置
3. 检查端口冲突
4. 确认依赖服务运行状态

#### 7.1.2 数据库迁移失败

**问题**: Alembic迁移失败

**诊断步骤**:
```bash
# 1. 查看迁移状态
pdm run alembic current
pdm run alembic history

# 2. 检查迁移脚本语法
pdm run alembic check

# 3. 手动执行迁移SQL
pdm run alembic upgrade head --sql
```

**解决方案**:
1. 检查数据库连接权限
2. 验证SQL语法正确性
3. 处理冲突的约束或索引
4. 手动执行迁移步骤

#### 7.1.3 性能问题

**问题**: API响应缓慢

**诊断步骤**:
```bash
# 1. 响应时间测试
curl -w "@curl-format.txt" -s -o /dev/null https://api.chaiwordduck.com/v1/words/query/hello

# 2. 数据库查询分析
psql -h localhost -U chaiword_user -d chaiword_duck -c "
EXPLAIN ANALYZE SELECT * FROM words WHERE word = 'hello';
"

# 3. Redis连接测试
docker exec chaiword-redis redis-cli ping
```

**解决方案**:
1. 添加数据库索引
2. 优化查询语句
3. 调整连接池大小
4. 启用查询缓存

### 7.2 紧急响应流程

#### 7.2.1 服务中断

**响应流程**:
1. **立即响应 (0-5分钟)**
   ```bash
   # 快速健康检查
   ./scripts/health_check.sh

   # 查看服务状态
   docker ps

   # 查看错误日志
   docker logs --tail 50 chaiword-backend
   ```

2. **临时修复 (5-30分钟)**
   ```bash
   # 重启服务
   docker-compose -f docker-compose.production.yml restart

   # 如果重启无效，回滚
   ./rollback.sh app
   ```

3. **根本原因分析 (30分钟-2小时)**
   ```bash
   # 详细日志分析
   ./scripts/analyze_logs.sh

   # 系统资源检查
   top
   df -h
   free -h
   ```

#### 7.2.2 数据丢失

**应急响应**:
```bash
# 1. 立即停止写入
docker-compose -f docker-compose.production.yml stop backend

# 2. 评估数据损坏程度
pdm run python scripts/data_integrity_check.py

# 3. 从最新备份恢复
psql -h localhost -U chaiword_user -d chaiword_duck < backup_latest.sql

# 4. 验证恢复结果
pdm run python scripts/verify_data_recovery.py
```

---

## 8. 安全配置

### 8.1 SSL/TLS 配置

#### 8.1.1 证书申请 (Let's Encrypt)

```bash
# 1. 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 2. 申请证书
sudo certbot --nginx -d chaiwordduck.com -d www.chaiwordduck.com

# 3. 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### 8.1.2 Nginx SSL 强化

```nginx
# 在nginx配置中添加
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;

# HSTS (HTTP严格传输安全)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# 其他安全头
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
```

### 8.2 防火墙配置

```bash
# 1. 配置UFW防火墙
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 2. 允许必要端口
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 3. 限制SSH访问 (可选)
sudo ufw limit ssh

# 4. 查看防火墙状态
sudo ufw status verbose
```

### 8.3 访问控制

```nginx
# 限制管理页面访问
location /admin {
    allow 192.168.1.0/24;  # 允许内网
    deny all;

    auth_basic "Admin Area";
    auth_basic_user_file /etc/nginx/.htpasswd;
}

# 限制API访问频率
location /api/ {
    limit_req zone=api burst=30 nodelay;
    limit_req_status 429;
}

# 阻止恶意请求
location ~* \.(php|asp|aspx|jsp)$ {
    deny all;
}
```

---

## 9. 备份和恢复

### 9.1 数据备份策略

#### 9.1.1 自动备份脚本

创建 `scripts/backup.sh`：

```bash
#!/bin/bash

BACKUP_DIR="/backup/chaiword"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# 创建备份目录
mkdir -p "$BACKUP_DIR"

echo "🗄️ 开始数据备份..."

# 1. 数据库备份
echo "💾 备份数据库..."
docker exec chaiword-postgres pg_dump -U chaiword_user -d chaiword_duck | gzip > "$BACKUP_DIR/db_backup_$DATE.sql.gz"

# 2. 应用文件备份
echo "📁 备份应用文件..."
tar -czf "$BACKUP_DIR/app_backup_$DATE.tar.gz" \
    --exclude=node_modules \
    --exclude=.git \
    --exclude=logs \
    --exclude=uploads \
    ./backend ./frontend

# 3. 配置文件备份
echo "⚙️ 备份配置文件..."
tar -czf "$BACKUP_DIR/config_backup_$DATE.tar.gz" \
    .env.production \
    docker-compose.production.yml \
    nginx/ \
    k8s/

# 4. 清理旧备份
echo "🧹 清理旧备份..."
find "$BACKUP_DIR" -name "*backup_*.gz" -mtime +$RETENTION_DAYS -delete

# 5. 上传到云存储 (可选)
if command -v aws &> /dev/null; then
    echo "☁️ 上传到AWS S3..."
    aws s3 sync "$BACKUP_DIR" s3://chaiword-backups/
fi

echo "✅ 备份完成: $BACKUP_DIR"
```

#### 9.1.2 定时备份配置

```bash
# 添加到crontab
sudo crontab -e

# 每日凌晨2点执行备份
0 2 * * * /path/to/chaiword/scripts/backup.sh

# 每周日凌晨3点执行完整备份
0 3 * * 0 /path/to/chaiword/scripts/full_backup.sh
```

### 9.2 数据恢复

#### 9.2.1 恢复脚本

创建 `scripts/restore.sh`：

```bash
#!/bin/bash

BACKUP_FILE=$1
RESTORE_TYPE=${2:-"db"}

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: $0 <backup_file> [db|app|config|full]"
    echo "  db     - 恢复数据库"
    echo "  app    - 恢复应用文件"
    echo "  config - 恢复配置文件"
    echo "  full   - 完整恢复"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

echo "🔄 开始恢复..."

case $RESTORE_TYPE in
    "db")
        echo "💾 恢复数据库..."

        # 停止应用
        docker-compose -f docker-compose.production.yml stop backend

        # 解压并恢复
        if [[ "$BACKUP_FILE" == *.gz ]]; then
            gunzip -c "$BACKUP_FILE" | psql -h localhost -U chaiword_user -d chaiword_duck
        else
            psql -h localhost -U chaiword_user -d chaiword_duck < "$BACKUP_FILE"
        fi

        # 重启应用
        docker-compose -f docker-compose.production.yml start backend
        ;;

    "app")
        echo "📁 恢复应用文件..."
        tar -xzf "$BACKUP_FILE" -C /
        ;;

    "config")
        echo "⚙️ 恢复配置文件..."
        tar -xzf "$BACKUP_FILE" -C /

        # 重启服务以应用新配置
        docker-compose -f docker-compose.production.yml down
        docker-compose -f docker-compose.production.yml up -d
        ;;

    "full")
        echo "🔄 完整恢复..."

        # 恢复应用和配置
        tar -xzf "$BACKUP_FILE" -C /

        # 查找数据库备份文件
        DB_BACKUP=$(tar -tzf "$BACKUP_FILE" | grep "db_backup_" | head -1)

        # 恢复数据库
        $0 "$DB_BACKUP" "db"
        ;;

    *)
        echo "❌ 无效的恢复类型: $RESTORE_TYPE"
        exit 1
        ;;
esac

echo "✅ 恢复完成"
```

---

## 10. 部署清单

### 10.1 部署前检查

- [ ] **环境准备**
  - [ ] 服务器规格满足要求
  - [ ] Docker和Docker Compose已安装
  - [ ] SSL证书已申请
  - [ ] 域名DNS已配置
  - [ ] 防火墙规则已设置

- [ ] **服务配置**
  - [ ] PostgreSQL已安装并配置
  - [ ] Redis已安装并配置
  - [ ] 环境变量已配置
  - [ ] 数据库备份已创建
  - [ ] 监控系统已配置

- [ ] **应用准备**
  - [ ] 代码已拉取到最新版本
  - [ ] 依赖已构建
  - [ ] 配置文件已准备
  - [ ] 健康检查已验证
  - [ ] 性能测试已通过

### 10.2 部署步骤

1. **准备阶段** (5分钟)
   ```bash
   # 检查环境
   ./scripts/pre_deploy_check.sh

   # 备份当前数据
   ./scripts/backup.sh
   ```

2. **代码部署** (10分钟)
   ```bash
   # 拉取最新代码
   git pull origin main

   # 构建新镜像
   docker-compose -f docker-compose.production.yml build --no-cache
   ```

3. **数据库迁移** (5-30分钟)
   ```bash
   # 执行迁移
   pdm run alembic upgrade head

   # 验证迁移
   ./scripts/verify_migration.sh
   ```

4. **服务重启** (5分钟)
   ```bash
   # 滚动更新
   docker-compose -f docker-compose.production.yml up -d --no-deps backend

   # 健康检查
   ./scripts/health_check.sh
   ```

5. **验证阶段** (10分钟)
   ```bash
   # 功能测试
   ./scripts/smoke_test.sh

   # 性能测试
   ./scripts/performance_test.sh
   ```

### 10.3 部署后验证

- [ ] **功能验证**
  - [ ] 前端页面正常访问
  - [ ] API接口正常响应
  - [ ] 用户注册登录正常
  - [ ] 单词查询功能正常
  - [ ] 多语言支持正常

- [ ] **性能验证**
  - [ ] 页面加载时间 < 2秒
  - [ ] API响应时间 < 500ms
  - [ ] 数据库查询优化有效
  - [ ] Redis缓存命中正常

- [ ] **安全验证**
  - [ ] HTTPS证书有效
  - [ ] 安全头配置正确
  - [ ] 防火墙规则生效
  - [ ] 访问控制正常

- [ ] **监控验证**
  - [ ] 健康检查正常
  - [ ] 日志收集正常
  - [ ] 错误监控正常
  - [ ] 告警配置生效

---

**文档结束**

**版本**: v1.0
**最后更新**: 2025-10-26
**维护者**: DevOps Team