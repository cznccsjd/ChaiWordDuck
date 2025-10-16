# AI服务架构文档导航

## 文档概览

本目录包含拆词鸭项目AI生成单词手册功能的完整技术架构设计。

## 文档清单

### 1. AI_SERVICE_SUMMARY.md（推荐首读）
**类型**：执行摘要
**阅读时间**：15分钟
**适用角色**：产品经理、技术经理、架构师

**内容**：
- 关键技术决策总结
- 成本对比分析（Gemini vs OpenAI vs Claude）
- 风险评估和缓解措施
- 实施路线图

**适合场景**：
- 快速了解架构设计核心决策
- 向管理层汇报技术方案
- 评估技术可行性和成本

### 2. AI_SERVICE_ARCHITECTURE.md（技术详设）
**类型**：完整技术设计文档
**阅读时间**：60分钟
**适用角色**：架构师、后端开发工程师

**内容**（12个章节）：
1. 架构概述（设计目标、系统架构图）
2. AI服务接口设计（抽象基类、统一接口）
3. AI服务工厂和管理（工厂模式、生成管理器）
4. 配置管理（环境变量、配置类）
5. Redis键设计（并发控制）
6. API集成示例（单词查询API改造）
7. 依赖项和安装（PDM命令）
8. 成本和性能对比（详细对比表）
9. 监控和告警（指标、日志、健康检查）
10. 测试策略（单元测试、集成测试）
11. 部署和运维（Docker、健康检查）
12. 未来扩展（Phase 2功能）

**适合场景**：
- 深入理解技术实现细节
- 代码Review参考
- 系统设计培训

### 3. AI_SERVICE_IMPLEMENTATION_GUIDE.md（快速上手）
**类型**：实施指南
**阅读时间**：30分钟
**适用角色**：后端开发工程师

**内容**（8个章节）：
1. 核心设计决策总结
2. 实施步骤（5步走）
   - 安装依赖
   - 配置环境变量
   - 更新配置类
   - 创建AI服务模块
   - 更新Redis键定义
3. API集成（核心逻辑）
4. 测试验证（单元测试、集成测试、手动测试）
5. 监控和运维（健康检查、日志监控、成本监控）
6. 常见问题（FAQ）
7. 下一步（实施任务清单）
8. 参考资料

**适合场景**：
- 开始编码前的快速参考
- 实施过程中查阅
- 问题排查

## 阅读路径推荐

### 路径1：产品经理/技术经理
```
AI_SERVICE_SUMMARY.md（执行摘要）
↓
第1节：执行摘要
第2节：关键技术决策
第8节：实施路线图
```
**阅读时间**：15分钟

### 路径2：架构师（评审架构）
```
AI_SERVICE_SUMMARY.md（执行摘要）
↓
AI_SERVICE_ARCHITECTURE.md（完整技术设计）
↓
第1节：架构概述
第2节：AI服务接口设计
第3节：AI服务工厂和管理
第7节：依赖项和安装
```
**阅读时间**：60分钟

### 路径3：后端开发工程师（开始实施）
```
AI_SERVICE_IMPLEMENTATION_GUIDE.md（快速上手）
↓
第2节：实施步骤（5步走）
第3节：API集成
第4节：测试验证
↓
AI_SERVICE_ARCHITECTURE.md（查阅具体技术细节）
```
**阅读时间**：30分钟（快速开始）+ 60分钟（深入学习）

### 路径4：测试工程师（编写测试）
```
AI_SERVICE_IMPLEMENTATION_GUIDE.md
↓
第4节：测试验证
↓
AI_SERVICE_ARCHITECTURE.md
↓
第10节：测试策略
```
**阅读时间**：20分钟

## 核心概念速查

### 抽象基类（BaseAIService）
- 定义统一的AI服务接口
- 提供通用的错误处理、重试、超时机制
- 子类只需实现`_generate_raw()`和`_parse_response()`

### 服务工厂（AIServiceFactory）
- 根据配置创建AI服务实例（OpenAI/Gemini/Claude）
- 管理多提供商的优先级
- 支持运行时切换

### 生成管理器（AIGenerationManager）
- 统一管理AI生成流程
- 实现降级策略（主服务失败时切换到备用服务）
- 防止并发重复生成（Redis分布式锁）

### 降级策略
```
主服务（Gemini）失败
↓
自动切换到备用服务（OpenAI）
↓
用户无感知
```

### 分布式锁
```python
lock_key = f"ai_generation:lock:{word}"
async with distributed_lock(lock_key):
    # 同一时刻只有一个请求可以生成该单词
    handbook = await ai_service.generate_word_handbook(word)
```

## 成本速算

| 提供商 | 单次成本 | 1000次/月 |
|--------|---------|----------|
| Gemini | $0.0002 | $6/月 |
| OpenAI | $0.0004 | $12/月 |
| Claude | $0.009  | $270/月 |

**推荐配置**：Gemini（主） + OpenAI（备用） = **$6-12/月**

## 限额配置

| 用户类型 | 查询限额 | AI生成限额 |
|---------|---------|-----------|
| 游客 | 10次/天 | 5次/天 |
| 免费用户 | 50次/天 | 20次/天 |
| Premium | 无限 | 无限 |

## 技术栈

| 组件 | 技术选型 | 版本 |
|------|---------|------|
| AI SDK (OpenAI) | openai | ≥1.0.0 |
| AI SDK (Gemini) | google-generativeai | ≥0.3.0 |
| 并发控制 | Redis | 7+ |
| 包管理工具 | PDM | - |

## 安装命令（快速参考）

```bash
# 使用PDM安装依赖
cd backend
pdm add openai
pdm add google-generativeai

# 配置环境变量
cp .env.example .env
# 编辑.env，添加API Key

# 运行测试
pdm run pytest tests/unit/test_ai_services.py -v
pdm run pytest tests/integration/test_ai_generation.py -v

# 启动服务
pdm run uvicorn app.main:app --reload
```

## 配置模板（快速参考）

```bash
# .env

# 主AI提供商（推荐gemini）
AI_PRIMARY_PROVIDER=gemini
AI_FALLBACK_PROVIDER=openai

# Gemini配置
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXX
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TIMEOUT=30

# OpenAI配置
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXX
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT=30

# AI生成限额
GUEST_AI_GENERATION_LIMIT=5
FREE_USER_AI_GENERATION_LIMIT=20
PREMIUM_USER_AI_GENERATION_LIMIT=-1
```

## 健康检查（快速参考）

```bash
# 检查AI服务健康状态
curl http://localhost:8000/api/health/ai

# 预期响应
{
  "status": "healthy",
  "services": {
    "gemini": true,
    "openai": true
  },
  "timestamp": "2025-10-16T10:30:00Z"
}
```

## 实施任务清单（快速参考）

- [ ] 安装依赖（openai, google-generativeai）
- [ ] 配置环境变量（.env）
- [ ] 更新配置类（app/core/config.py）
- [ ] 创建AI服务模块（app/services/ai/）
  - [ ] base.py（抽象基类）
  - [ ] openai_service.py（OpenAI实现）
  - [ ] gemini_service.py（Gemini实现）
  - [ ] factory.py（服务工厂）
  - [ ] manager.py（生成管理器）
- [ ] 更新Redis键定义（app/core/redis_keys.py）
- [ ] 修改单词查询API（app/api/v1/words.py）
- [ ] 编写单元测试（tests/unit/test_ai_services.py）
- [ ] 编写集成测试（tests/integration/test_ai_generation.py）
- [ ] 手动测试验证
- [ ] 添加健康检查端点（app/api/endpoints/health.py）
- [ ] 文档更新（README.md, API文档）

**预估工作量**：12.5小时

## 常见问题（FAQ）

### Q1: 为什么选择Gemini作为主服务？
**A**: 成本最低（比OpenAI便宜50%），速度快（2-3秒），质量满足MVP需求。

### Q2: 如果Gemini API故障怎么办？
**A**: 自动切换到备用服务（OpenAI），确保系统可用性。

### Q3: 如何防止多用户同时查询同一新单词导致重复生成？
**A**: 使用Redis分布式锁，同一时刻只允许一个请求生成。

### Q4: 如何估算AI成本？
**A**: Gemini: $0.0002/次 × 每日生成次数 × 30天
示例：100次/天 × 30 = $6/月

## 参考资料

### 官方文档
- Gemini API: https://ai.google.dev/docs
- OpenAI API: https://platform.openai.com/docs
- Redis分布式锁: https://redis.io/docs/manual/patterns/distributed-locks/

### 项目文档
- CLAUDE.md（包管理工具、Git规范）
- PRD.md（产品需求）
- DESIGN.md（技术设计）

## 联系方式

- **架构师**：负责架构设计和Review
- **后端开发工程师**：负责具体实施
- **项目经理**：负责协调和进度跟踪

---

**文档版本**: v1.0
**创建日期**: 2025-10-16
**最后更新**: 2025-10-16
**维护者**: 架构师
