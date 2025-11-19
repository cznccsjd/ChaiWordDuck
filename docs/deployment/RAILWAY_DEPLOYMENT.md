# 拆词鸭 Railway 部署指南

## 🚀 部署概述

本指南详细说明如何将拆词鸭后端API部署到Railway平台。

## 📋 部署前准备

### 1. 代码准备
- ✅ develop分支已推送到远程
- ✅ requirements-railway.txt已生成（仅生产依赖）
- ✅ Dockerfile已优化支持Railway
- ✅ railway.json配置为DOCKERFILE模式
- ✅ 数据库迁移脚本已准备

### 2. Railway账户准备
- Railway账户已创建
- 支持PostgreSQL数据库
- 支持Redis缓存（可选）

## ⚙️ Railway配置

### 1. 项目设置
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "backend/Dockerfile"
  }
}
```

### 2. 必需环境变量

#### 核心配置
```bash
# 应用配置
APP_NAME=ChaiWord Duck API
APP_ENV=production
DEBUG=false

# 数据库配置（Railway自动提供）
DATABASE_URL=${{RAILWAY_DATABASE_URL}}

# JWT配置
JWT_SECRET_KEY=your-production-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

#### AI服务配置
```bash
# 主AI服务配置
AI_PRIMARY_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TIMEOUT=30

# 备用AI服务配置
AI_FALLBACK_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT=30
```

#### 业务配置
```bash
# 用户限制
GUEST_AI_GENERATION_LIMIT=5
FREE_USER_AI_GENERATION_LIMIT=20
PREMIUM_USER_AI_GENERATION_LIMIT=-1

GUEST_DAILY_LIMIT=10
FREE_USER_DAILY_LIMIT=50
PREMIUM_USER_DAILY_LIMIT=-1

FREE_USER_FAVORITE_LIMIT=10
PREMIUM_USER_FAVORITE_LIMIT=999999
```

#### 安全配置
```bash
# CORS配置（替换为实际域名）
CORS_ORIGINS=https://your-frontend-domain.com,https://your-domain.com
CORS_ALLOW_CREDENTIALS=true

# 限流配置
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=1000
```

## 🗄️ 数据库设置

### 1. PostgreSQL数据库
Railway自动创建PostgreSQL数据库，连接URL通过`${{RAILWAY_DATABASE_URL}}`环境变量提供。

### 2. 数据库迁移
应用启动时自动运行Alembic迁移：
- 自动执行`alembic upgrade head`
- 迁移包括多语言支持和JSONB字段
- 自动创建必要的索引和约束

### 3. 迁移内容
- 多语言支持字段（language_code, translation）
- JSONB结构化数据字段
- 用户语言偏好设置
- 优化索引和唯一约束

## 🚢 部署步骤

### 1. 创建Railway项目
1. 登录Railway控制台
2. 点击"New Project"
3. 连接GitHub仓库
4. 选择develop分支

### 2. 配置服务
1. Service Type: Dockerfile
2. Root Directory: backend
3. Dockerfile路径: backend/Dockerfile
4. Port: 8000

### 3. 设置环境变量
在Railway控制台中添加上述所有必需的环境变量。

### 4. 添加数据库
1. 点击"New Service"
2. 选择"PostgreSQL"
3. 数据库会自动连接到主应用

### 5. 部署
1. 点击"Deploy"按钮
2. Railway会自动构建Docker镜像
3. 启动时自动运行数据库迁移
4. 验证服务健康状态

## 🔍 验证部署

### 1. 健康检查
访问以下端点验证服务状态：
```bash
# 基础健康检查
GET https://your-app.railway.app/health

# 详细健康检查
GET https://your-app.railway.app/health/detailed

# API文档
GET https://your-app.railway.app/docs
```

### 2. 数据库验证
```bash
# 检查数据库连接
GET https://your-app.railway.app/api/v1/health/database

# 验证迁移状态
# 检查words表是否包含新字段
```

### 3. 功能测试
```bash
# 测试单词查询（支持多语言）
GET https://your-app.railway.app/api/v1/words/accommodation?language=zh_CN

# 测试AI生成功能
POST https://your-app.railway.app/api/v1/words/generate
```

## 🚨 故障排除

### 常见问题

#### 1. 数据库连接失败
```bash
# 检查DATABASE_URL环境变量
echo $DATABASE_URL

# 验证数据库连接状态
curl https://your-app.railway.app/api/v1/health/database
```

#### 2. AI服务配置错误
```bash
# 检查API密钥配置
curl https://your-app.railway.app/api/v1/health/ai-service

# 查看AI服务状态
```

#### 3. 迁移失败
检查Railway部署日志，查找迁移错误信息。

#### 4. 内存不足
在Railway控制台中增加服务内存配置。

### 日志查看
在Railway控制台中查看实时日志：
- 应用启动日志
- 数据库迁移日志
- API请求日志
- 错误日志

## 📈 监控和维护

### 1. 性能监控
- Railway提供基础监控指标
- 可集成第三方监控服务（如Sentry）

### 2. 数据库备份
Railway自动进行PostgreSQL备份。

### 3. 更新部署
- 推送代码到develop分支
- Railway自动触发重新部署
- 数据库迁移自动执行

## 🎯 生产环境优化建议

### 1. 性能优化
- 启用Redis缓存（添加Redis服务）
- 配置CDN加速静态资源
- 优化数据库查询

### 2. 安全配置
- 使用强密码和JWT密钥
- 配置HTTPS（Railway自动提供）
- 限制CORS源

### 3. 成本控制
- 监控API使用量
- 设置适当的用户限制
- 优化AI服务调用

## 📞 支持

如遇到部署问题：
1. 检查Railway部署日志
2. 验证环境变量配置
3. 确认数据库连接
4. 联系开发团队

---

**部署完成后，请更新前端API配置以指向新的Railway URL。**