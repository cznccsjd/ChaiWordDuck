# 拆词鸭项目Railway平台部署指南

## 🚨 重要警告：Redis服务配置问题

### 问题描述
在Railway平台创建Redis服务时，如果配置不当，可能导致：
- Redis服务被错误识别为PostgreSQL服务
- 生成错误的环境变量（DATABASE_URL而不是REDIS_URL）
- Source Image显示为PostgreSQL而不是Redis

### 📋 部署前检查清单

#### ✅ 必须检查的项目

1. **服务命名规范**
   - PostgreSQL服务名称必须包含：`postgres` 或 `database`
   - Redis服务名称必须包含：`redis`
   - 避免使用模糊名称如：`chaiword-duck-redis`（建议改为`chaiword-redis`）

2. **环境变量验证**
   - PostgreSQL服务应生成：`DATABASE_URL`
   - Redis服务应生成：`REDIS_URL`
   - ❌ 如果Redis服务生成`DATABASE_PUBLIC_URL`，说明配置错误

3. **Source Image验证**
   - PostgreSQL服务应显示：`ghcr.io/railwayapp-templates/postgres-ssl:17`
   - Redis服务应显示：`redis:7-alpine`或类似Redis镜像

#### 🛠️ 正确的部署步骤

### 步骤1：准备工作

```bash
# 1. 验证配置
python scripts/validate-railway-config.py

# 2. 安装Railway CLI
npm install -g @railway/cli

# 3. 登录Railway
railway login
```

### 步骤2：创建服务

```bash
# 方式1：使用CLI创建（推荐）
railway add postgresql --name chaiword-postgres
railway add redis --name chaiword-redis

# 方式2：使用控制台创建
# 1. 访问 https://railway.app
# 2. 创建新项目
# 3. 添加PostgreSQL服务（命名：chaiword-postgres）
# 4. 添加Redis服务（命名：chaiword-redis）
```

### 步骤3：验证服务配置

在Railway控制台中检查：

**PostgreSQL服务应显示：**
```
Variables:
- DATABASE_URL: postgresql://...
- DATABASE_PUBLIC_URL: postgresql://...
- POSTGRES_USER: ...
- POSTGRES_PASSWORD: ...
- POSTGRES_DB: ...

Source Image: ghcr.io/railwayapp-templates/postgres-ssl:17
```

**Redis服务应显示：**
```
Variables:
- REDIS_URL: redis://...
- REDIS_PASSWORD: ...

Source Image: redis:7-alpine
```

### 步骤4：配置应用环境变量

```bash
# 在主应用服务中设置
railway variables set DATABASE_URL="${{chaiword-postgres.DATABASE_URL}}"
railway variables set REDIS_URL="${{chaiword-redis.REDIS_URL}}"
railway variables set PORT=8000
```

### 步骤5：部署应用

```bash
# 使用提供的部署脚本
chmod +x scripts/railway-deploy.sh
./scripts/railway-deploy.sh

# 或手动部署
railway up
```

## 🐛 故障排除

### 问题1：Redis服务被识别为PostgreSQL

**症状：**
- Redis服务显示`DATABASE_URL`变量
- Source Image显示为PostgreSQL
- 无法连接到Redis

**解决方案：**
1. 删除错误的Redis服务
2. 重新创建，确保名称包含`redis`
3. 避免使用可能混淆的名称

### 问题2：环境变量配置错误

**症状：**
- 应用无法连接数据库
- 应用无法连接Redis
- 启动失败

**解决方案：**
1. 检查环境变量名称是否正确
2. 验证变量引用语法：`${{service-name.VARIABLE_NAME}}`
3. 使用配置验证脚本检查

### 问题3：服务连接超时

**症状：**
- 数据库连接超时
- Redis连接超时

**解决方案：**
1. 检查服务是否完全启动
2. 验证网络连接
3. 检查防火墙设置

## 📝 最佳实践

### 1. 服务命名规范

```bash
# ✅ 推荐的命名方式
- chaiword-postgres
- chaiword-redis
- chaiword-api

# ❌ 避免的命名方式
- chaiword-duck-redis（过于复杂）
- database（过于通用）
- cache（不够明确）
```

### 2. 环境变量管理

```bash
# ✅ 使用明确的服务引用
DATABASE_URL="${{chaiword-postgres.DATABASE_URL}}"
REDIS_URL="${{chaiword-redis.REDIS_URL}}"

# ❌ 避免硬编码
DATABASE_URL="postgresql://..."
REDIS_URL="redis://..."
```

### 3. 配置验证

```bash
# 部署前必须运行验证
python scripts/validate-railway-config.py

# 检查服务状态
railway status

# 查看环境变量
railway variables get
```

## 🔄 CI/CD集成

### GitHub Actions配置示例

```yaml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Validate Railway Config
        run: python scripts/validate-railway-config.py

      - name: Install Railway CLI
        run: npm install -g @railway/cli

      - name: Deploy to Railway
        run: railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

## 📞 支持和帮助

如果在部署过程中遇到问题：

1. 首先运行配置验证脚本
2. 检查Railway控制台的服务配置
3. 查看应用日志：`railway logs`
4. 参考Railway官方文档
5. 联系项目维护者

## 📚 相关资源

- [Railway官方文档](https://docs.railway.app/)
- [Railway服务类型](https://docs.railway.app/reference/services)
- [项目配置验证工具](scripts/validate-railway-config.py)
- [自动化部署脚本](scripts/railway-deploy.sh)

---

**最后更新：2025-11-17**
**版本：v1.0.0**