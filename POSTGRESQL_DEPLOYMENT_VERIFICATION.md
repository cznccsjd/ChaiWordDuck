# PostgreSQL 部署验证指南
## 拆词鸭项目 - Railway PostgreSQL 数据库验证

> **文档类型**: 部署验证指南
> **项目版本**: 拆词鸭 v1.0.0+
> **文档更新时间**: 2025-10-27
> **适用平台**: Railway Cloud Platform
> **数据库**: PostgreSQL 14-16
> **状态**: ✅ 已完成

本指南提供完整的验证步骤，确保 Railway 上的 PostgreSQL 数据库成功部署并正常运行。

---

## 🔍 验证清单概览

### ✅ 必须验证的项目

- [ ] Railway 控制台服务状态检查
- [ ] API 健康检查端点响应
- [ ] 数据库客户端连接测试
- [ ] 数据库表结构验证
- [ ] 多语言支持功能测试
- [ ] 数据库迁移脚本执行确认

---

## 🖥️ 方法一：通过 Railway 控制台验证

### 1.1 访问 Railway 控制台

1. 打开浏览器，访问 [Railway Dashboard](https://railway.app/dashboard)
2. 登录您的 Railway 账户
3. 选择您的拆词鸭项目

### 1.2 检查 PostgreSQL 服务状态

**查看服务状态指示器：**
- 🟢 绿色：服务正常运行
- 🟡 黄色：服务正在启动或重启中
- 🔴 红色：服务存在问题

**检查关键信息：**
```
服务名称：PostgreSQL
状态：Running（必须为运行状态）
启动时间：显示最近一次启动时间
资源使用：CPU 和内存使用情况
```

### 1.3 获取数据库连接信息

在 PostgreSQL 服务页面，点击 "Connect" 按钮：

**连接信息包含：**
```bash
# 示例格式（请使用您的实际连接信息）
Host: containers.railway.app
Port: 7652
Database: railway
Username: postgres
Password: [自动生成的密码]
URL: postgresql://postgres:[password]@containers.railway.app:7652/railway
```

### 1.4 查看部署日志

1. 在 PostgreSQL 服务页面，点击 "Logs" 标签
2. 查看最近的日志输出

**预期看到的关键日志：**
```
PostgreSQL init process complete; ready for start up.
database system is ready to accept connections
LOG: autovacuum launcher started
```

**警告信号（需要关注）：**
```
FATAL: database "railway" does not exist
LOG: could not bind IPv4 address
ERROR: connection to server failed
```

---

## 🌐 方法二：通过 API 连接验证

### 2.1 获取 API 服务 URL

在 Railway 控制台中找到您的后端 API 服务 URL，格式通常为：
```
https://your-app-name.railway.app
```

### 2.2 健康检查端点测试

**使用 curl 测试：**
```bash
# 基础健康检查
curl -X GET "https://your-app-name.railway.app/health"

# 预期响应：
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-XX..."
}
```

**详细健康检查：**
```bash
# 详细健康信息
curl -X GET "https://your-app-name.railway.app/health/detailed"

# 预期响应：
{
  "status": "healthy",
  "database": {
    "status": "connected",
    "type": "postgresql",
    "max_connections": 100,
    "active_connections": 2
  },
  "external_services": {
    "gemini": "connected"
  },
  "timestamp": "2024-01-XX..."
}
```

### 2.3 测试数据库相关 API

**测试多语言提示词 API：**
```bash
# 获取中文提示词
curl -X GET "https://your-app-name.railway.app/api/v1/prompts/zh/word_decomposition" \
  -H "accept: application/json"

# 预期响应：
{
  "language": "zh",
  "type": "word_decomposition",
  "content": "请将英文单词...",
  "variables": ["word", "difficulty_level"]
}
```

**测试用户语言偏好设置：**
```bash
# 设置用户语言偏好
curl -X POST "https://your-app-name.railway.app/api/v1/users/language-preference" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "preferred_language": "zh",
    "fallback_language": "en"
  }'

# 预期响应：
{
  "status": "success",
  "message": "语言偏好设置成功"
}
```

### 2.4 错误响应分析

**数据库连接失败时的响应：**
```json
{
  "detail": "Database connection failed",
  "error_code": "DB_CONNECTION_ERROR"
}
```

**服务不可用时的响应：**
```json
{
  "detail": "Service temporarily unavailable",
  "error_code": "SERVICE_UNAVAILABLE"
}
```

---

## 💻 方法三：通过数据库客户端验证

### 3.1 使用 psql 命令行工具

**连接数据库：**
```bash
# 使用连接字符串（请替换为您的实际连接信息）
psql "postgresql://postgres:[password]@containers.railway.app:7652/railway"

# 或者使用参数方式
psql -h containers.railway.app -p 7652 -U postgres -d railway
```

### 3.2 检查数据库基本信息

**连接成功后执行：**
```sql
-- 查看当前数据库
\c

-- 查看数据库版本
SELECT version();

-- 查看所有表
\dt

-- 查看所有表的大小
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 3.3 验证表结构

**检查多语言支持相关表：**
```sql
-- 查看语言偏好设置表
\d user_language_preferences

-- 预期输出：
Table "public.user_language_preferences"
      Column      |          Type          | Collation | Nullable | Default
------------------+------------------------+-----------+----------+---------
id                | integer                |           | not null |
user_id           | text                   |           | not null |
preferred_language| text                   |           | not null |
fallback_language | text                   |           |          |
created_at        | timestamp with time zone|           | not null | now()
updated_at        | timestamp with time zone|           | not null | now()

-- 查看多语言提示词表
\d multilingual_prompts

-- 预期输出：
Table "public.multilingual_prompts"
      Column      |          Type          | Collation | Nullable | Default
------------------+------------------------+-----------+----------+---------
id                | integer                |           | not null |
language          | text                   |           | not null |
prompt_type       | text                   |           | not null |
content           | text                   |           | not null |
variables         | jsonb                  |           |          |
is_active         | boolean                |           | not null | true
created_at        | timestamp with time zone|           | not null | now()
updated_at        | timestamp with time zone|           | not null | now()
```

### 3.4 验证数据内容

**检查多语言提示词数据：**
```sql
-- 查看所有支持的语言
SELECT DISTINCT language FROM multilingual_prompts ORDER BY language;

-- 预期输出：
 language
----------
 en
 zh
 ja
 es
(4 rows)

-- 查看单词拆解类型的提示词
SELECT language, prompt_type, LEFT(content, 50) as preview
FROM multilingual_prompts
WHERE prompt_type = 'word_decomposition'
AND is_active = true;

-- 检查 JSONB 字段内容
SELECT language, variables
FROM multilingual_prompts
WHERE prompt_type = 'word_decomposition'
LIMIT 1;

-- 预期输出：
 language |                      variables
----------+---------------------------------------------------
 en       | ["word", "difficulty_level", "context", "examples"]
```

### 3.5 使用 DBeaver 或其他 GUI 工具

**连接配置：**
```
Host: containers.railway.app
Port: 7652
Database: railway
Username: postgres
Password: [您的密码]
```

**验证步骤：**
1. 测试连接是否成功
2. 查看数据库列表
3. 浏览表结构
4. 查询数据内容

---

## 📊 方法四：检查数据库内容

### 4.1 验证迁移脚本执行状态

**检查迁移记录表：**
```sql
-- 查看 Alembic 迁移版本表
SELECT * FROM alembic_version;

-- 预期输出：
 version_num
-------------
 2024_01_xx_...
(1 row)
```

### 4.2 验证索引和约束

**检查索引：**
```sql
-- 查看用户语言偏好表的索引
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'user_language_preferences';

-- 预期看到类似输出：
 indexname |                     indexdef
-----------+----------------------------------------------------
 idx_user_language_preferences_user_id | CREATE UNIQUE INDEX idx_user_language_preferences_user_id ON public.user_language_preferences USING btree (user_id)
```

**检查约束：**
```sql
-- 查看表的约束
SELECT conname, contype
FROM pg_constraint
WHERE conrelid = 'multilingual_prompts'::regclass;

-- 预期输出：
 conname | contype
---------+---------
 multilingual_prompts_pkey | p
```

### 4.3 验证多语言功能数据完整性

**检查数据完整性：**
```sql
-- 检查每种语言是否都有必要的提示词类型
SELECT
    language,
    array_agg(DISTINCT prompt_type ORDER BY prompt_type) as available_types
FROM multilingual_prompts
WHERE is_active = true
GROUP BY language
ORDER BY language;

-- 预期每种语言都有基本的提示词类型：
-- word_decomposition, memory_assistance, example_sentences, pronunciation

-- 检查 JSONB 字段的有效性
SELECT
    language,
    prompt_type,
    CASE
        WHEN jsonb_typeof(variables) = 'array' THEN 'Valid array'
        ELSE 'Invalid JSONB'
    END as variables_status
FROM multilingual_prompts;
```

---

## ⚠️ 故障排除指南

### 5.1 常见问题及解决方案

**问题 1：连接被拒绝**
```
ERROR: could not connect to server
```
**解决方案：**
- 检查 PostgreSQL 服务是否在运行
- 确认端口和主机名正确
- 检查防火墙设置

**问题 2：认证失败**
```
FATAL: password authentication failed for user "postgres"
```
**解决方案：**
- 重新获取密码（在 Railway 控制台重置）
- 检查用户名拼写
- 确认没有额外的空格

**问题 3：数据库不存在**
```
FATAL: database "railway" does not exist
```
**解决方案：**
- 检查数据库名称是否正确
- 等待数据库初始化完成
- 重启 PostgreSQL 服务

**问题 4：连接超时**
```
Connection timeout expired
```
**解决方案：**
- 检查网络连接
- 确认服务正在运行
- 增加连接超时时间

### 5.2 API 响应错误分析

**500 内部服务器错误：**
```bash
# 查看详细错误信息
curl -v "https://your-app-name.railway.app/health"
```

**503 服务不可用：**
- 检查后端服务是否正在运行
- 查看后端服务日志

**404 未找到：**
- 确认 API 端点路径正确
- 检查 API 版本号

### 5.3 日志分析技巧

**查看应用日志：**
```bash
# 使用 Railway CLI（如果已安装）
railway logs

# 或在控制台查看实时日志
```

**关键日志信息：**
- 数据库连接成功/失败信息
- 迁移脚本执行结果
- API 请求处理日志

---

## 📋 验证完成清单

### ✅ 所有验证项目完成后，请确认：

- [ ] Railway 控制台显示 PostgreSQL 服务状态为 **Running**
- [ ] 健康检查 API 返回 `status: "healthy"` 和 `database: "connected"`
- [ ] 数据库客户端（psql/DBeaver）能够成功连接
- [ ] 所有必要的数据库表都已创建
- [ ] 多语言提示词数据已正确导入
- [ ] JSONB 字段内容格式正确
- [ ] 索引和约束已正确设置
- [ ] API 能够正确查询和更新多语言数据

### 🎯 成功标准

**完全成功的验证：**
- 所有验证步骤都通过
- 能够正常使用多语言功能
- 数据持久化工作正常
- 性能表现符合预期

**需要关注的情况：**
- 某些 API 响应较慢
- 部分功能需要重试才能正常工作
- 日志中有警告信息

**需要立即处理的情况：**
- 数据库连接完全失败
- 关键 API 端点返回 500 错误
- 数据库表结构不完整

---

## 📞 获取帮助

如果在验证过程中遇到问题：

1. **检查日志**：首先查看 Railway 控制台的详细日志
2. **查阅文档**：参考项目的 `README.md` 和 `DESIGN.md`
3. **重置服务**：尝试重启 PostgreSQL 或后端服务
4. **联系支持**：如问题持续，可联系 Railway 技术支持

---

**重要提醒：**
- 请勿在代码或公共文档中暴露数据库连接信息
- 定期更换数据库密码以确保安全
- 监控数据库使用情况，避免超出资源限制

**文档最后更新时间：** 2025-10-27
**适用版本：** 拆词鸭项目 v1.0.0+