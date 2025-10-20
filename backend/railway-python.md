# Railway 直接Python部署指南（无Docker）

如果你不想使用Dockerfile，可以使用Railway的原生Python部署方式。

## 🚀 Railway配置设置

### 1. Builder 设置
```
Builder: Nixpacks
```

### 2. Build Command
```bash
pip install --upgrade pip && pip install -r requirements-core.txt
```

### 3. Start Command
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## ⚠️ 潜在问题和解决方案

### 问题1：PostgreSQL客户端缺失
如果遇到 `psycopg2` 或 `asyncpg` 连接问题，需要：

**解决方案**：在 requirements-core.txt 中添加：
```txt
# 替换 asyncpg 为 psycopg2-binary
psycopg2-binary==2.9.7
# 注释掉 asyncpg==0.29.0
```

### 问题2：系统依赖缺失
如果遇到系统库缺失错误，可以尝试：

**解决方案**：使用 Nixpacks 配置文件
创建 `nixpacks.toml`：
```toml
[phases.setup]
nixPkgs = ["postgresql", "libpq"]

[phases.build]
cmds = ["pip install --upgrade pip", "pip install -r requirements-core.txt"]
```

## 🔧 完整的Railway原生部署步骤

### 步骤1：修改 requirements-core.txt
将 `asyncpg==0.29.0` 替换为 `psycopg2-binary==2.9.7`

### 步骤2：Railway控制台设置
```
Project Settings → Your Service → Settings
↓
Builder: Nixpacks
Build Command: pip install --upgrade pip && pip install -r requirements-core.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Root Directory: backend
```

### 步骤3：环境变量配置
确保在Railway中设置所有必需的环境变量：
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- `OPENAI_API_KEY`
- 等等...

## 📊 两种方式对比

| 特性 | Dockerfile | Nixpacks（无Docker） |
|------|------------|---------------------|
| **设置复杂度** | 中等 | 简单 |
| **构建速度** | 快（有缓存） | 慢（每次重新安装） |
| **环境控制** | 完全控制 | 受限 |
| **调试便利性** | 优秀 | 一般 |
| **冷启动** | 快 | 慢 |
| **推荐场景** | 生产环境 | 简单项目 |

## 🎯 建议

对于拆词鸭项目，我建议继续使用Dockerfile，原因：

1. **PostgreSQL依赖**：我们需要`libpq5`库来确保数据库连接稳定
2. **健康检查**：Dockerfile中包含了健康检查配置
3. **生产稳定性**：Docker提供更一致的生产环境

但是，如果你确实想避免Docker，使用上面的Nixpacks配置也是可行的！