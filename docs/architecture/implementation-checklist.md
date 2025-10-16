# 游客模式实施检查清单

## 文档信息

| 属性 | 内容 |
|------|------|
| **文档版本** | v1.0 |
| **创建日期** | 2025-10-16 |
| **文档作者** | 架构师 |
| **目标阶段** | MVP Phase 1 |
| **预计完成时间** | 2025-11-01 |

---

## 使用说明

**检查清单格式**：
- ✅ 已完成
- 🔄 进行中
- ⏳ 未开始
- ❌ 已阻塞

**责任人缩写**：
- BE: 后端工程师
- FE: 前端工程师
- ARC: 架构师
- QA: 测试专家
- PM: 产品经理
- PA: 项目助理

---

## Phase 1: 后端基础设施（Week 1）

### 1.1 Redis集成

| 任务 | 状态 | 责任人 | 预计工时 | 备注 |
|------|------|--------|---------|------|
| 安装Redis 7+ | ⏳ | BE | 0.5h | 本地开发环境 |
| 配置Redis连接池 | ⏳ | BE | 1h | app/core/redis.py |
| 创建RedisKeys管理类 | ✅ | ARC | 1h | app/core/redis_keys.py（已完成） |
| 编写Redis连接测试 | ⏳ | BE | 0.5h | 测试连接和基本操作 |
| 更新环境变量配置 | ⏳ | BE | 0.5h | .env.example, config.py |
| 更新Docker Compose | ⏳ | BE | 0.5h | 添加Redis服务 |

**验收标准**：
- [ ] Redis服务启动成功
- [ ] 应用能成功连接Redis
- [ ] 基本INCR/GET/SET操作正常
- [ ] 连接池配置正确（最大连接数、超时时间）

**交付物**：
- `backend/app/core/redis.py` - Redis连接管理
- `backend/app/core/redis_keys.py` - Redis键管理（已完成）
- `backend/docker-compose.yml` - 更新Redis服务
- `backend/.env.example` - Redis配置示例

---

### 1.2 游客识别服务

| 任务 | 状态 | 责任人 | 预计工时 | 备注 |
|------|------|--------|---------|------|
| 创建GuestIdentifier模型 | ⏳ | BE | 1h | app/schemas/guest.py |
| 实现IP提取逻辑 | ⏳ | BE | 1h | 支持X-Forwarded-For |
| 实现guest_id生成算法 | ⏳ | BE | 1h | SHA256(IP + UA) |
| 创建GuestSession数据模型 | ⏳ | BE | 1h | app/models/guest.py |
| 实现游客识别服务 | ⏳ | BE | 2h | app/services/guest_identifier.py |
| 编写单元测试 | ⏳ | BE | 2h | 覆盖率≥95% |

**验收标准**：
- [ ] 能正确提取客户端IP（包括代理场景）
- [ ] guest_id生成稳定且唯一
- [ ] GuestSession能正确创建和查询
- [ ] 单元测试覆盖率≥95%

**交付物**：
- `backend/app/schemas/guest.py` - 游客Schema
- `backend/app/models/guest.py` - GuestSession模型
- `backend/app/services/guest_identifier.py` - 游客识别服务
- `backend/tests/unit/test_guest_identifier.py` - 单元测试

---

### 1.3 限流服务实现

| 任务 | 状态 | 责任人 | 预计工时 | 备注 |
|------|------|--------|---------|------|
| 创建RateLimitService类 | ⏳ | BE | 1h | app/services/rate_limit.py |
| 实现游客限流逻辑 | ⏳ | BE | 3h | Redis计数器 + Set |
| 实现用户限流逻辑 | ⏳ | BE | 2h | 区分free/premium |
| 实现"重复查询不计次"逻辑 | ⏳ | BE | 2h | Redis SISMEMBER检查 |
| 实现Redis降级方案 | ⏳ | BE | 3h | 降级到PostgreSQL |
| 编写单元测试 | ⏳ | BE | 3h | Mock Redis和DB |

**验收标准**：
- [ ] 游客10次/天限制正确执行
- [ ] 用户50次/天限制正确执行
- [ ] Premium用户无限制
- [ ] 重复查询不消耗次数
- [ ] Redis故障时能降级到PostgreSQL
- [ ] 单元测试覆盖率≥95%

**交付物**：
- `backend/app/services/rate_limit.py` - 限流服务
- `backend/tests/unit/test_rate_limit.py` - 单元测试

---

### 1.4 依赖注入改造

| 任务 | 状态 | 责任人 | 预计工时 | 备注 |
|------|------|--------|---------|------|
| 实现get_optional_user() | ⏳ | BE | 1h | app/core/dependencies.py |
| 实现get_user_or_guest() | ⏳ | BE | 2h | 统一认证入口 |
| 更新现有API依赖 | ⏳ | BE | 2h | 将强制认证改为可选 |
| 编写单元测试 | ⏳ | BE | 2h | 测试认证和游客场景 |

**验收标准**：
- [ ] 有token时正确返回User对象
- [ ] 无token时正确返回GuestIdentifier对象
- [ ] token无效时正确降级为游客
- [ ] 不影响现有需要认证的API

**交付物**：
- `backend/app/core/dependencies.py` - 更新依赖注入
- `backend/tests/unit/test_dependencies.py` - 单元测试

---

### 1.5 数据库迁移

| 任务 | 状态 | 责任人 | 预计工时 | 备注 |
|------|------|--------|---------|------|
| 创建guest_sessions表迁移 | ⏳ | BE | 1h | Alembic迁移脚本 |
| 更新query_logs表 | ⏳ | BE | 1h | 添加guest_session_id外键 |
| 创建数据库索引 | ⏳ | BE | 1h | 复合索引优化 |
| 测试迁移脚本 | ⏳ | BE | 1h | 本地和测试环境 |
| 准备回滚脚本 | ⏳ | BE | 0.5h | downgrade()函数 |

**验收标准**：
- [ ] 迁移脚本能成功执行
- [ ] 表结构符合设计（字段类型、约束、索引）
- [ ] 能正确回滚（downgrade）
- [ ] 现有数据不受影响

**交付物**：
- `backend/alembic/versions/xxx_add_guest_mode.py` - 迁移脚本
- 迁移测试报告

---

### 1.6 配置更新

| 任务 | 状态 | 责任人 | 预计工时 | 备注 |
|------|------|--------|---------|------|
| 更新Settings类 | ⏳ | BE | 0.5h | 添加限额配置 |
| 更新.env.example | ⏳ | BE | 0.5h | Redis和限额配置 |
| 更新README.md | ⏳ | PA | 1h | 环境搭建说明 |

**验收标准**：
- [ ] guest_daily_limit = 10
- [ ] free_user_daily_limit = 50
- [ ] premium_user_daily_limit = -1
- [ ] Redis配置完整

**交付物**：
- `backend/app/core/config.py` - 更新配置
- `backend/.env.example` - 配置示例
- `README.md` - 文档更新

---

## Phase 2: API改造与集成（Week 2）

### 2.1 单词查询API改造

| 任务 | 状态 | 责任人 | 预计工时 | 备注 |
|------|------|--------|---------|------|
| 更新GET /words/query/{word} | ⏳ | BE | 2h | 支持游客查询 |
| 更新POST /words/query | ⏳ | BE | 1h | 支持游客查询 |
| 更新响应格式 | ⏳ | BE | 1h | 添加user_type等字段 |
| 集成RateLimitService | ⏳ | BE | 2h | 限流检查逻辑 |
| 更新错误处理 | ⏳ | BE | 1h | 429错误详细信息 |
| 编写集成测试 | ⏳ | BE | 3h | 游客和用户场景 |

**验收标准**：
- [ ] 游客无需token可查询单词
- [ ] 注册用户使用token查询
- [ ] 限流逻辑正确执行
- [ ] 响应包含剩余次数信息
- [ ] 集成测试覆盖率≥90%

**交付物**：
- `backend/app/api/v1/words.py` - 更新API
- `backend/app/schemas/word.py` - 更新Schema
- `backend/tests/integration/test_words_guest.py` - 集成测试

---

### 2.2 查询限制API

| 任务 | 状态 | 责任人 | 预计工时 | 备注 |
|------|------|--------|---------|------|
| 实现GET /words/query-limit | ⏳ | BE | 1h | 获取限额信息 |
| 支持游客查询限额 | ⏳ | BE | 1h | 无需认证 |
| 编写集成测试 | ⏳ | BE | 1h | 测试各用户类型 |

**验收标准**：
- [ ] 游客能查询剩余次数
- [ ] 注册用户能查询剩余次数
- [ ] 返回已查询单词列表

**交付物**：
- `backend/app/api/v1/words.py` - 新增API
- `backend/tests/integration/test_query_limit.py` - 集成测试

---

### 2.3 IP限流中间件

| 任务 | 状态 | 责任人 | 预计工时 | 备注 |
|------|------|--------|---------|------|
| 创建IPRateLimitMiddleware | ⏳ | BE | 2h | app/middleware/ip_rate_limit.py |
| 集成到FastAPI应用 | ⏳ | BE | 1h | main.py中注册 |
| 配置白名单 | ⏳ | BE | 0.5h | 开发环境IP白名单 |
| 编写单元测试 | ⏳ | BE | 1h | 测试限流逻辑 |

**验收标准**：
- [ ] 单个IP超过30次/分钟被拦截
- [ ] 返回429错误和重试时间
- [ ] 白名单IP不受限制
- [ ] 不影响正常用户请求

**交付物**：
- `backend/app/middleware/ip_rate_limit.py` - 中间件
- `backend/tests/unit/test_ip_rate_limit.py` - 单元测试

---

### 2.4 异常行为检测

| 任务 | 状态 | 责任人 | 预计工时 | 备注 |
|------|------|--------|---------|------|
| 创建AbuseDetectionService | ⏳ | BE | 3h | app/services/abuse_detection.py |
| 实现重复查询检测 | ⏳ | BE | 1h | 5秒内3次相同单词 |
| 实现爬虫模式检测 | ⏳ | BE | 2h | 字母顺序查询 |
| 实现Captcha标记逻辑 | ⏳ | BE | 1h | Redis记录 |
| 编写单元测试 | ⏳ | BE | 2h | Mock场景测试 |

**验收标准**：
- [ ] 能正确识别重复查询模式
- [ ] 能正确识别爬虫模式
- [ ] 可疑行为被标记
- [ ] 不误判正常用户

**交付物**：
- `backend/app/services/abuse_detection.py` - 检测服务
- `backend/tests/unit/test_abuse_detection.py` - 单元测试

---

### 2.5 AI生成限额控制

| 任务 | 状态 | 责任人 | 预计工时 | 备注 |
|------|------|--------|---------|------|
| 实现AI生成限额检查 | ⏳ | BE | 1h | 5次/天/IP |
| 集成到WordService | ⏳ | BE | 1h | 生成前检查 |
| 优先返回预生成手册 | ⏳ | BE | 1h | 查询逻辑优化 |
| 编写单元测试 | ⏳ | BE | 1h | 测试限额逻辑 |

**验收标准**：
- [ ] AI生成限额5次/天正确执行
- [ ] 超限时返回友好错误信息
- [ ] 优先返回预生成手册（减少AI调用）

**交付物**：
- `backend/app/services/word_generation.py` - 生成服务更新
- `backend/tests/unit/test_word_generation.py` - 单元测试

---

### 2.6 监控和日志

| 任务 | 状态 | 责任人 | 预计工时 | 备注 |
|------|------|--------|---------|------|
| 配置结构化日志 | ⏳ | BE | 1h | app/core/logging.py |
| 添加Prometheus指标 | ⏳ | BE | 2h | app/core/metrics.py |
| 配置Sentry错误追踪 | ⏳ | BE | 1h | main.py集成 |
| 创建Grafana面板 | ⏳ | BE | 2h | 监控仪表板 |
| 配置告警规则 | ⏳ | BE | 1h | Prometheus AlertManager |

**验收标准**：
- [ ] 关键操作有日志记录
- [ ] Prometheus指标正常收集
- [ ] Sentry能捕获异常
- [ ] Grafana面板正常展示
- [ ] 告警规则正确触发

**交付物**：
- `backend/app/core/logging.py` - 日志配置
- `backend/app/core/metrics.py` - Prometheus指标
- `monitoring/alerts.yml` - 告警规则
- `monitoring/grafana-dashboard.json` - Grafana面板

---

## Phase 3: 前端适配（Week 2）

### 3.1 游客模式UI

| 任务 | 状态 | 责任人 | 预计工时 | 备注 |
|------|------|--------|---------|------|
| 创建游客识别管理器 | ⏳ | FE | 1h | lib/guest-identifier.ts |
| 实现查询次数显示组件 | ⏳ | FE | 2h | components/QueryLimitBadge.tsx |
| 实现渐进式引导组件 | ⏳ | FE | 3h | components/GuestGuidance.tsx |
| 实现限额达到页面 | ⏳ | FE | 2h | components/QueryLimitReached.tsx |
| 适配API调用 | ⏳ | FE | 2h | 支持游客模式 |
| 编写E2E测试 | ⏳ | QA | 3h | Playwright测试 |

**验收标准**：
- [ ] 游客无需登录可查询单词
- [ ] 页面正确显示剩余次数
- [ ] 渐进式引导按阶段展示
- [ ] 限额达到后显示引导页面
- [ ] E2E测试覆盖关键流程

**交付物**：
- `frontend/lib/guest-identifier.ts` - 游客管理
- `frontend/components/QueryLimitBadge.tsx` - 限额展示
- `frontend/components/GuestGuidance.tsx` - 引导组件
- `frontend/tests/e2e/guest-mode.spec.ts` - E2E测试

---

### 3.2 A/B测试框架

| 任务 | 状态 | 责任人 | 预计工时 | 备注 |
|------|------|--------|---------|------|
| 创建A/B测试Hook | ⏳ | FE | 2h | hooks/useABTest.ts |
| 实现事件追踪 | ⏳ | FE | 1h | lib/analytics.ts |
| 配置测试变体 | ⏳ | PM | 1h | 定义3个变体 |
| 编写测试用例 | ⏳ | QA | 1h | 验证分流逻辑 |

**验收标准**：
- [ ] 用户能正确分配到不同变体
- [ ] 事件正确追踪到后端
- [ ] 变体数据可分析

**交付物**：
- `frontend/hooks/useABTest.ts` - A/B测试Hook
- `frontend/lib/analytics.ts` - 事件追踪
- A/B测试方案文档

---

## Phase 4: 测试与部署（Week 2末）

### 4.1 集成测试

| 任务 | 状态 | 责任人 | 预计工时 | 备注 |
|------|------|--------|---------|------|
| 游客查询流程测试 | ⏳ | QA | 2h | 完整流程 |
| 限流逻辑测试 | ⏳ | QA | 2h | 各种限额场景 |
| 降级方案测试 | ⏳ | QA | 2h | Redis故障模拟 |
| 性能压测 | ⏳ | QA | 3h | Locust 100并发 |
| 安全测试 | ⏳ | QA | 2h | SQL注入、XSS |

**验收标准**：
- [ ] 所有集成测试通过
- [ ] 性能指标达标（P95<500ms）
- [ ] 无严重安全漏洞

**交付物**：
- 集成测试报告
- 性能测试报告
- 安全测试报告

---

### 4.2 文档更新

| 任务 | 状态 | 责任人 | 预计工时 | 备注 |
|------|------|--------|---------|------|
| 更新DESIGN.md | ✅ | ARC | 4h | 技术设计文档（已完成） |
| 更新README.md | ⏳ | PA | 1h | 环境搭建和运行 |
| 编写API文档 | ⏳ | BE | 2h | OpenAPI规范 |
| 编写部署文档 | ⏳ | BE | 2h | Docker部署指南 |
| 更新TODOS.md | ⏳ | PA | 0.5h | 任务状态同步 |

**验收标准**：
- [ ] 文档完整准确
- [ ] 新开发者能根据文档搭建环境
- [ ] API文档与实际一致

**交付物**：
- `DESIGN.md` - 技术设计文档（已完成）
- `README.md` - 项目说明文档
- `docs/api/` - API文档
- `docs/deployment/` - 部署文档
- `TODOS.md` - 任务跟踪

---

### 4.3 部署准备

| 任务 | 状态 | 责任人 | 预计工时 | 备注 |
|------|------|--------|---------|------|
| 创建Dockerfile | ⏳ | BE | 1h | 后端镜像 |
| 创建docker-compose.yml | ⏳ | BE | 1h | 完整服务栈 |
| 配置CI/CD | ⏳ | BE | 2h | GitHub Actions |
| 准备生产环境变量 | ⏳ | BE | 1h | .env.production |
| 数据库备份策略 | ⏳ | BE | 1h | 自动备份脚本 |

**验收标准**：
- [ ] Docker镜像能正常构建
- [ ] docker-compose能启动所有服务
- [ ] CI/CD流水线正常运行
- [ ] 生产环境配置完整

**交付物**：
- `backend/Dockerfile` - Docker镜像
- `docker-compose.yml` - 服务编排
- `.github/workflows/deploy.yml` - CI/CD配置
- `.env.production.example` - 生产配置示例

---

## 关键里程碑

| 里程碑 | 日期 | 完成标准 | 状态 |
|-------|------|---------|------|
| M1: Redis和数据库就绪 | Week 1, Day 3 | Redis连接成功，数据库迁移完成 | ⏳ |
| M2: 后端API完成 | Week 1, Day 5 | 所有API实现并通过单元测试 | ⏳ |
| M3: 前端UI完成 | Week 2, Day 3 | 游客模式UI实现并通过E2E测试 | ⏳ |
| M4: 集成测试通过 | Week 2, Day 5 | 所有集成测试和性能测试通过 | ⏳ |
| M5: MVP上线 | Week 2, Day 7 | 生产环境部署完成，功能可用 | ⏳ |

---

## 风险跟踪

| 风险 | 当前状态 | 缓解措施 | 责任人 |
|------|---------|---------|--------|
| Redis故障 | ⏳ 待缓解 | 实现降级方案 | BE |
| IP识别不准 | ⏳ 待缓解 | Phase 1接受，Phase 2优化 | ARC |
| 性能瓶颈 | ⏳ 待验证 | 数据库索引优化 | BE |
| 转化率低 | ⏳ 待验证 | A/B测试优化 | PM + FE |

---

## 每日站会检查项

**后端团队**：
1. Redis集成进度？
2. 限流服务实现进度？
3. 遇到的技术难题？
4. 需要的支持？

**前端团队**：
1. 游客UI实现进度？
2. API对接是否顺利？
3. 是否有设计变更需求？
4. 需要的支持？

**测试团队**：
1. 测试用例编写进度？
2. 发现的Bug数量和严重程度？
3. 测试环境是否稳定？
4. 需要的支持？

---

## 验收标准汇总

### 功能验收

**游客模式核心功能**：
- [ ] 游客无需登录可查询10个单词/天
- [ ] 已查询单词可无限次复习（不计次数）
- [ ] 游客点击收藏跳转登录页
- [ ] 游客查询10次后显示注册引导
- [ ] 注册用户可查询50个单词/天
- [ ] Premium用户无限查询

**限流功能**：
- [ ] IP限流30次/分钟正确执行
- [ ] 游客日限额10次正确执行
- [ ] 用户日限额50次正确执行
- [ ] Redis故障时能降级到PostgreSQL
- [ ] 重复查询不消耗次数

**防滥用功能**：
- [ ] 异常行为能被检测
- [ ] 可疑用户被标记
- [ ] AI生成限额5次/天

### 性能验收

- [ ] 100并发用户：P95响应时间<500ms
- [ ] 数据库查询：95%查询<100ms
- [ ] Redis操作：99%操作<10ms
- [ ] API整体可用性≥99.5%

### 质量验收

- [ ] 单元测试覆盖率≥95%
- [ ] 集成测试覆盖率≥90%
- [ ] E2E测试覆盖关键流程100%
- [ ] 无严重安全漏洞
- [ ] 代码符合规范（Ruff, Black, Prettier）

---

## 上线前最终检查

**技术检查**：
- [ ] 所有测试通过
- [ ] 性能指标达标
- [ ] 监控和告警配置完成
- [ ] 降级方案已验证
- [ ] 数据库备份策略就绪

**文档检查**：
- [ ] DESIGN.md更新完整
- [ ] README.md更新完整
- [ ] API文档与实际一致
- [ ] 部署文档完整可执行
- [ ] TODOS.md状态同步

**运维检查**：
- [ ] 生产环境配置正确
- [ ] SSL证书配置完成
- [ ] 日志收集正常
- [ ] 监控面板正常
- [ ] 告警通知渠道测试通过

**业务检查**：
- [ ] PRD需求全部实现
- [ ] 产品经理验收通过
- [ ] 设计师UI走查通过
- [ ] 内测用户反馈收集

---

## 上线后监控

**第1天（关键期）**：
- 每小时检查监控指标
- 实时关注错误日志
- 收集用户反馈
- 准备快速回滚

**第1周（稳定期）**：
- 每天检查关键指标
- 分析转化率数据
- 优化性能瓶颈
- 修复非关键Bug

**第1月（优化期）**：
- 每周数据分析会议
- 根据数据优化引导策略
- 规划Phase 2功能
- 总结经验教训

---

## 附录：快速参考

### 关键配置

```bash
# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 查询限额
GUEST_DAILY_LIMIT=10
FREE_USER_DAILY_LIMIT=50
PREMIUM_USER_DAILY_LIMIT=-1

# IP限流
RATE_LIMIT_PER_MINUTE=30
```

### 关键命令

```bash
# 启动开发环境
docker-compose up -d

# 运行数据库迁移
alembic upgrade head

# 运行测试
pytest tests/ --cov=app

# 运行性能测试
locust -f tests/performance/test_load.py --headless -u 100

# 查看Redis数据
redis-cli
> KEYS query_limit:guest:*
> GET query_limit:guest:abc123:2025-10-16
```

### 关键文件路径

```
backend/
├── app/
│   ├── core/
│   │   ├── redis.py              # Redis连接
│   │   ├── redis_keys.py         # Redis键管理
│   │   └── dependencies.py       # 依赖注入
│   ├── services/
│   │   ├── guest_identifier.py   # 游客识别
│   │   ├── rate_limit.py         # 限流服务
│   │   └── abuse_detection.py    # 滥用检测
│   ├── api/v1/
│   │   └── words.py              # 单词API
│   └── models/
│       └── guest.py              # 游客模型
├── tests/
│   ├── unit/                     # 单元测试
│   ├── integration/              # 集成测试
│   └── performance/              # 性能测试
└── alembic/versions/             # 数据库迁移

frontend/
├── lib/
│   ├── guest-identifier.ts       # 游客管理
│   └── api-client.ts             # API客户端
├── components/
│   ├── QueryLimitBadge.tsx       # 限额展示
│   ├── GuestGuidance.tsx         # 引导组件
│   └── QueryLimitReached.tsx     # 限额达到页面
└── tests/e2e/
    └── guest-mode.spec.ts        # E2E测试
```

---

**文档结束**

**版本**：v1.0
**最后更新**：2025-10-16
**维护责任人**：架构师 + 项目助理
**每日更新**：由各团队成员更新任务状态
