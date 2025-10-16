# AI服务架构设计总结报告

## 执行摘要

本报告为拆词鸭项目的AI生成单词手册功能提供完整的技术架构方案。核心目标是设计一个**可扩展、成本优化、高可用**的多AI提供商架构，支持OpenAI、Gemini等主流服务。

### 关键决策

| 决策项 | 选择 | 备选方案 | 决策理由 |
|--------|------|---------|---------|
| **主AI提供商** | Gemini (gemini-1.5-flash) | OpenAI, Claude | 成本最低（$0.0002/次），速度快（2-3秒） |
| **备用提供商** | OpenAI (gpt-4o-mini) | Claude | 稳定性最高（99.9%），成本可接受（$0.0004/次）|
| **架构模式** | 抽象工厂 + 策略模式 | 单一提供商 | 易于扩展，支持运行时切换，降低供应商锁定风险 |
| **并发控制** | Redis分布式锁 | 数据库唯一约束 | 防止重复生成，支持分布式部署 |
| **降级策略** | 自动切换备用服务 | 返回错误 | 提高系统可用性，用户无感知 |

### 成本对比（月成本，基于1000次生成）

```
Gemini:   $6   ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░ (基准)
OpenAI:   $12  ████████░░░░░░░░░░░░░░░░░░░░░░░░ (2倍)
Claude:   $270 ████████████████████████████████ (45倍)
```

**推荐配置**：Gemini（主） + OpenAI（备用） = **$6-12/月**

---

## 1. 架构设计概览

### 1.1 系统分层架构

```
┌─────────────────────────────────────────────────────────┐
│                    业务层 (API)                          │
│  /api/v1/words/query/{word}                             │
│  - 查询数据库                                            │
│  - 不存在 → 检查限额 → AI生成 → 存储                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│               AI服务抽象层 (Service)                      │
│  ┌────────────────────────────────────────────┐         │
│  │     BaseAIService (抽象基类)                │         │
│  │  + generate_word_handbook()                │         │
│  │  + check_availability()                    │         │
│  │  + get_estimated_cost()                    │         │
│  └─────────────┬──────────────┬────────────────┘        │
│         ┌──────┴──────┐  ┌────┴─────┐  ┌──────┴────┐   │
│         │ OpenAIService│  │Gemini    │  │Claude     │   │
│         │             │  │Service   │  │Service    │   │
│         └─────────────┘  └──────────┘  └───────────┘   │
│                                                          │
│  ┌────────────────────────────────────────────┐         │
│  │    AIServiceFactory (工厂类)                │         │
│  │  + create_service(provider)                │         │
│  │  + get_primary_service()                   │         │
│  │  + get_fallback_service()                  │         │
│  └────────────────────────────────────────────┘         │
│                                                          │
│  ┌────────────────────────────────────────────┐         │
│  │   AIGenerationManager (管理器)              │         │
│  │  + generate_word_handbook()                │         │
│  │  + 降级策略                                  │         │
│  │  + 分布式锁                                  │         │
│  └────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│              并发控制层 (Redis)                           │
│  - ai_generation:lock:{word}         (分布式锁)          │
│  - ai_generation:count:{user}:{date} (限额计数)          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│              外部AI API                                   │
│  Gemini API  |  OpenAI API  |  Claude API               │
└─────────────────────────────────────────────────────────┘
```

### 1.2 核心组件

#### 1.2.1 BaseAIService（抽象基类）

**职责**：
- 定义统一的AI服务接口
- 提供通用的错误处理、重试、超时机制
- 子类只需实现`_generate_raw()`和`_parse_response()`

**关键方法**：
```python
class BaseAIService(ABC):
    async def generate_word_handbook(word: str) -> WordHandbook:
        """生成单词手册（带重试和超时）"""

    @abstractmethod
    async def _generate_raw(word: str) -> Dict:
        """调用AI API（子类实现）"""

    @abstractmethod
    def _parse_response(raw: Dict, word: str) -> WordHandbook:
        """解析AI响应（子类实现）"""

    async def check_availability() -> bool:
        """健康检查"""

    def get_estimated_cost(word: str) -> float:
        """估算成本"""
```

#### 1.2.2 OpenAIService & GeminiService

**实现差异**：

| 方面 | OpenAI | Gemini |
|------|--------|--------|
| **SDK** | `openai.AsyncOpenAI` | `google.generativeai` |
| **模型** | gpt-4o-mini | gemini-1.5-flash |
| **JSON强制** | `response_format={"type": "json_object"}` | `response_mime_type="application/json"` |
| **调用方式** | `client.chat.completions.create()` | `model.generate_content_async()` |
| **成本** | $0.0004/次 | $0.0002/次 |
| **响应时间** | 3-5秒 | 2-3秒 |

**统一接口示例**：
```python
# 业务层调用（无需关心底层提供商）
service = AIServiceFactory.get_primary_service()
handbook = await service.generate_word_handbook("serendipitous")
```

#### 1.2.3 AIGenerationManager（生成管理器）

**核心功能**：

1. **自动降级**：
   ```python
   try:
       # 尝试主服务（Gemini）
       handbook = await self.primary_service.generate_word_handbook(word)
   except AIGenerationError:
       # 主服务失败，切换到备用服务（OpenAI）
       handbook = await self.fallback_service.generate_word_handbook(word)
   ```

2. **分布式锁（防重复生成）**：
   ```python
   lock_key = f"ai_generation:lock:{word}"
   async with self._distributed_lock(lock_key):
       # 同一时刻只有一个请求可以生成该单词
       handbook = await self.primary_service.generate_word_handbook(word)
   ```

3. **超时控制**：
   ```python
   handbook = await asyncio.wait_for(
       self._generate_raw(word),
       timeout=30  # 30秒超时
   )
   ```

---

## 2. 关键技术决策详解

### 决策1: 为什么选择Gemini作为主服务？

**对比分析**：

| 维度 | Gemini | OpenAI | Claude | 权重 |
|------|--------|--------|--------|------|
| **成本** | ⭐⭐⭐⭐⭐ ($0.0002) | ⭐⭐⭐⭐ ($0.0004) | ⭐ ($0.009) | 40% |
| **速度** | ⭐⭐⭐⭐⭐ (2-3秒) | ⭐⭐⭐⭐ (3-5秒) | ⭐⭐⭐ (4-6秒) | 30% |
| **质量** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 20% |
| **可用性** | ⭐⭐⭐⭐ (99.5%) | ⭐⭐⭐⭐⭐ (99.9%) | ⭐⭐⭐⭐ (99.7%) | 10% |
| **综合得分** | **4.55** | 4.4 | 2.6 | - |

**结论**：
- Gemini在成本和速度上优势明显
- 质量满足MVP需求（后续可根据用户反馈调整）
- 配合OpenAI备用服务，可用性可达99.95%+

**月成本估算（假设每日1000次生成）**：
```
Gemini:  $0.0002 × 1000 × 30 = $6/月
OpenAI:  $0.0004 × 1000 × 30 = $12/月（仅作为备用）
```

### 决策2: 为什么使用抽象工厂模式？

**备选方案对比**：

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **单一提供商** | 简单 | 供应商锁定，无法切换 | ❌ 不推荐 |
| **硬编码多提供商** | 中等复杂度 | 难以扩展，违反开闭原则 | ❌ 不推荐 |
| **抽象工厂模式** | 易扩展，支持运行时切换 | 代码略复杂 | ✅ **推荐** |
| **策略模式** | 运行时动态选择 | 与工厂模式类似 | ✅ 可结合使用 |

**选择抽象工厂的理由**：
1. **开闭原则**：新增提供商（如Claude）无需修改现有代码
2. **依赖倒置**：业务层依赖抽象接口，而非具体实现
3. **运行时切换**：通过配置文件切换AI提供商，无需重新部署

**扩展性示例**：
```python
# 未来新增Claude服务，只需：
# 1. 实现ClaudeService类（继承BaseAIService）
# 2. 在工厂中注册
# 3. 修改配置文件

class ClaudeService(BaseAIService):
    async def _generate_raw(self, word: str):
        # Claude特定实现
        pass

# 无需修改业务逻辑
```

### 决策3: 为什么使用Redis分布式锁？

**问题场景**：
```
时刻T0: 用户A查询"serendipitous"（数据库不存在）
时刻T1: 用户B查询"serendipitous"（数据库仍不存在）
问题：两个请求同时调用AI生成，浪费成本
```

**备选方案对比**：

| 方案 | 实现难度 | 分布式支持 | 性能 | 推荐度 |
|------|---------|-----------|------|--------|
| **数据库唯一约束** | 低 | ✅ 支持 | 中等 | ⭐⭐⭐ |
| **应用层锁（asyncio.Lock）** | 低 | ❌ 单机 | 高 | ❌ 不推荐 |
| **Redis分布式锁** | 中等 | ✅ 支持 | 高 | ⭐⭐⭐⭐⭐ **推荐** |
| **Zookeeper分布式锁** | 高 | ✅ 支持 | 高 | ⭐⭐⭐ 过重 |

**Redis分布式锁实现**：
```python
lock_key = f"ai_generation:lock:{word}"

# 尝试获取锁（SET NX EX）
lock_acquired = await redis.set(
    lock_key,
    "lock_value",
    nx=True,  # Only set if not exists
    ex=60,    # Expire after 60 seconds
)

if lock_acquired:
    # 获取锁成功，执行AI生成
    handbook = await ai_service.generate_word_handbook(word)
else:
    # 锁被占用，等待重试
    await asyncio.sleep(1)
```

**优势**：
- 支持分布式部署（多个后端实例）
- 性能高（Redis内存操作）
- 自动过期（避免死锁）

### 决策4: 为什么需要降级策略？

**可用性计算**：

假设单一提供商可用性99.5%：
```
单一提供商：  99.5% 可用性
             = 每月停机时间 3.6小时
```

引入备用服务后（假设独立失败）：
```
主+备用：    1 - (1 - 0.995) × (1 - 0.999)
           = 1 - 0.005 × 0.001
           = 99.9995% 可用性
           = 每月停机时间 0.02小时（1.2分钟）
```

**降级流程**：
```
1. 调用主服务（Gemini）
   ↓ 失败
2. 记录失败日志
   ↓
3. 调用备用服务（OpenAI）
   ↓ 成功
4. 返回结果（用户无感知）
```

**成本影响**：
- 正常情况：100%使用Gemini = $6/月
- 主服务故障（假设5%）：95% Gemini + 5% OpenAI = $6.3/月
- **成本增加仅5%，可用性提升100倍**

---

## 3. 限额和成本控制

### 3.1 限额策略

| 用户类型 | 查询限额 | AI生成限额 | 月成本估算 |
|---------|---------|-----------|-----------|
| **游客** | 10次/天 | 5次/天 | $0.001/天 × 30 = $0.03/月 |
| **免费用户** | 50次/天 | 20次/天 | $0.004/天 × 30 = $0.12/月 |
| **Premium用户** | 无限 | 无限 | 按实际使用计费 |

**限额检查逻辑**：
```python
# Redis键设计
count_key = f"ai_generation:count:{user_id}:{date}"

# 检查限额
current_count = await redis.get(count_key)
if current_count >= limit:
    raise HTTPException(429, "AI生成次数已用完")

# 递增计数
await redis.incr(count_key)
await redis.expire(count_key, 86400)  # 24小时过期
```

### 3.2 成本优化策略

**Phase 1（MVP）**：
1. 使用Gemini作为主服务（成本最低）
2. 仅在单词不存在时生成（避免重复）
3. 分布式锁防止并发重复生成

**Phase 2（优化）**：
1. **预生成高频单词**：
   - 后台任务批量生成GRE/TOEFL核心词汇
   - 避免用户等待

2. **缓存策略**：
   - Redis缓存已生成单词（7天TTL）
   - 减少数据库查询

3. **智能降级**：
   - 监控成本，超过阈值时限制免费用户生成频率
   - Premium用户不受影响

**成本监控**：
```python
# 每日成本统计
SELECT
    DATE(created_at) as date,
    COUNT(*) as generation_count,
    COUNT(*) * 0.0002 as estimated_cost_usd
FROM words
WHERE source = 'ai'
GROUP BY DATE(created_at);
```

---

## 4. 并发处理和防雪崩

### 4.1 并发场景

**场景1：多用户查询同一新单词**

```
时刻T0: 100个用户同时查询"serendipitous"
问题：如果不加控制，会触发100次AI生成
解决：Redis分布式锁
```

```python
lock_key = f"ai_generation:lock:serendipitous"

# 只有一个请求获取锁，其他等待
async with distributed_lock(lock_key):
    # 再次检查数据库（可能已被其他请求生成）
    word = await db.get_word("serendipitous")
    if word:
        return word  # 已生成，直接返回

    # 调用AI生成
    handbook = await ai_manager.generate_word_handbook("serendipitous")
    await db.save_word(handbook)
```

**场景2：AI API限流**

```
OpenAI限流: 3500 RPM (requests per minute)
Gemini限流: 60 RPM（免费）, 1000 RPM（付费）

问题：高并发时可能被限流
解决：请求队列 + 速率限制
```

```python
# 使用Redis实现令牌桶算法
async def rate_limit_check(provider: str):
    key = f"ai_rate_limit:{provider}:minute"
    current = await redis.incr(key)

    if current == 1:
        await redis.expire(key, 60)  # 1分钟过期

    limit = 50 if provider == "gemini" else 500  # 保守限制

    if current > limit:
        raise HTTPException(429, "AI服务繁忙，请稍后重试")
```

### 4.2 防雪崩机制

**1. 超时控制**：
```python
# 每个AI请求30秒超时
handbook = await asyncio.wait_for(
    ai_service.generate_word_handbook(word),
    timeout=30
)
```

**2. 重试机制（指数退避）**：
```python
for attempt in range(max_retries):
    try:
        return await ai_service.generate_word_handbook(word)
    except Exception:
        await asyncio.sleep(2 ** attempt)  # 1秒, 2秒, 4秒...
```

**3. 熔断器（Circuit Breaker）**：
```python
# 如果错误率>50%，停止调用10分钟
if error_rate > 0.5:
    logger.error("AI服务熔断，停止调用10分钟")
    await asyncio.sleep(600)
```

**4. 优雅降级**：
```python
try:
    # 尝试AI生成
    handbook = await ai_manager.generate_word_handbook(word)
except AIGenerationError:
    # 返回简化版手册（仅基础信息）
    return {
        "word": word,
        "core_game": "暂无AI生成内容，请稍后重试",
        ...
    }
```

---

## 5. 监控和告警

### 5.1 关键指标

| 指标 | 阈值 | 告警级别 | 说明 |
|------|------|---------|------|
| **AI生成失败率** | >10% | Warning | 主服务可能不稳定 |
| **AI生成失败率** | >30% | Critical | 主服务严重故障 |
| **平均响应时间** | >10秒 | Warning | 性能下降 |
| **平均响应时间** | >30秒 | Critical | 严重性能问题 |
| **单日成本** | >$20 | Warning | 成本异常 |
| **单日成本** | >$50 | Critical | 可能遭受攻击 |
| **降级切换次数** | >100次/小时 | Warning | 主服务频繁故障 |

### 5.2 日志记录

**结构化日志示例**：
```python
logger.info(
    "AI生成单词手册成功",
    extra={
        "word": "serendipitous",
        "provider": "gemini",
        "duration_ms": 2500,
        "cost_usd": 0.0002,
        "user_id": 123,
        "user_type": "registered",
    }
)

logger.error(
    "AI生成失败，已切换到备用服务",
    extra={
        "word": "serendipitous",
        "primary_provider": "gemini",
        "fallback_provider": "openai",
        "primary_error": "API timeout",
        "attempt": 3,
    },
    exc_info=True
)
```

### 5.3 健康检查端点

```bash
# 检查AI服务健康状态
GET /api/health/ai

# 响应示例
{
  "status": "healthy",  # healthy | degraded | unhealthy
  "services": {
    "gemini": true,
    "openai": true
  },
  "timestamp": "2025-10-16T10:30:00Z"
}
```

---

## 6. 测试策略

### 6.1 测试层级

| 测试类型 | 覆盖率要求 | 测试内容 |
|---------|-----------|---------|
| **单元测试** | ≥95% | AI服务类方法（generate, parse, check）|
| **集成测试** | ≥90% | API + AI服务 + 数据库端到端流程 |
| **Mock测试** | 100% | AI API调用失败、超时、降级场景 |
| **负载测试** | - | 并发生成、分布式锁、限流机制 |

### 6.2 关键测试场景

**1. 正常生成流程**：
```python
@pytest.mark.asyncio
async def test_word_generation_success():
    """测试AI生成成功"""
    response = await client.get("/api/v1/words/query/serendipitous")

    assert response.status_code == 200
    assert response.json()["data"]["word"] == "serendipitous"
    assert response.json()["data"]["core_game"]
```

**2. 降级切换**：
```python
@pytest.mark.asyncio
async def test_fallback_mechanism(monkeypatch):
    """测试主服务失败时切换到备用服务"""
    # Mock主服务失败
    monkeypatch.setattr(GeminiService, "generate_word_handbook", mock_error)

    # 应自动切换到OpenAI
    response = await client.get("/api/v1/words/query/test")
    assert response.status_code == 200
```

**3. 并发防重复**：
```python
@pytest.mark.asyncio
async def test_concurrent_generation():
    """测试并发请求同一单词只生成一次"""
    # 100个并发请求
    tasks = [
        client.get("/api/v1/words/query/serendipitous")
        for _ in range(100)
    ]
    responses = await asyncio.gather(*tasks)

    # 验证数据库只有一条记录
    word_count = await db.execute(
        select(func.count()).where(Word.word == "serendipitous")
    )
    assert word_count == 1
```

**4. 限额控制**：
```python
@pytest.mark.asyncio
async def test_ai_generation_limit():
    """测试AI生成限额"""
    # 游客连续生成6个新单词（超出5次限额）
    for i in range(6):
        response = await client.get(f"/api/v1/words/query/testword{i}")

        if i < 5:
            assert response.status_code == 200
        else:
            assert response.status_code == 429
            assert "AI生成次数已用完" in response.json()["detail"]["message"]
```

---

## 7. 风险和缓解措施

### 7.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| **AI API故障** | 无法生成新单词 | 中 | 降级策略（备用服务） |
| **成本超预算** | 财务压力 | 低 | 限额控制 + 成本监控 |
| **生成质量差** | 用户体验差 | 中 | 人工审核 + Prompt优化 |
| **并发重复生成** | 成本浪费 | 中 | Redis分布式锁 |
| **API限流** | 服务不可用 | 中 | 速率限制 + 请求队列 |

### 7.2 业务风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| **滥用免费生成** | 成本激增 | 高 | 严格限额 + 验证码 |
| **AI生成内容侵权** | 法律风险 | 低 | 免责声明 + 人工审核 |
| **用户不满意生成内容** | 流失用户 | 中 | 反馈机制 + 重新生成 |

---

## 8. 实施路线图

### Phase 1: MVP（2周）

**目标**：基础AI生成功能，支持Gemini和OpenAI

**任务清单**：
- [x] 架构设计（本文档）
- [ ] 环境配置和依赖安装（0.5天）
- [ ] AI服务模块开发（2天）
  - [ ] BaseAIService抽象基类
  - [ ] GeminiService实现
  - [ ] OpenAIService实现
  - [ ] AIServiceFactory工厂
  - [ ] AIGenerationManager管理器
- [ ] API集成（1天）
  - [ ] 修改单词查询逻辑
  - [ ] 增加AI生成限额检查
- [ ] 单元测试和集成测试（2天）
- [ ] 手动测试和调试（1天）
- [ ] 文档更新（0.5天）

**交付物**：
- 可用的AI生成功能
- 测试覆盖率≥90%
- 完整的API文档

### Phase 2: 优化（4周）

**目标**：性能优化、成本控制、监控告警

**任务清单**：
- [ ] 预生成高频单词（后台任务）
- [ ] Redis缓存优化
- [ ] 监控和告警系统
- [ ] 成本统计和报表
- [ ] 用户反馈机制
- [ ] Prompt优化（根据用户反馈）

### Phase 3: 扩展（未来）

**目标**：支持更多AI提供商、本地模型

**可选功能**：
- [ ] Claude服务支持
- [ ] 流式生成（SSE）
- [ ] 本地模型（Llama 3）
- [ ] 自定义Prompt模板
- [ ] 批量生成API

---

## 9. 附录

### 9.1 完整文件清单

```
backend/app/services/ai/
├── __init__.py                        # 模块导出
├── base.py                            # 抽象基类（300行）
├── openai_service.py                  # OpenAI实现（200行）
├── gemini_service.py                  # Gemini实现（200行）
├── factory.py                         # 服务工厂（150行）
└── manager.py                         # 生成管理器（250行）

backend/app/core/
├── config.py                          # 配置扩展（+30行）
└── redis_keys.py                      # Redis键定义（+20行）

backend/app/api/v1/
└── words.py                           # API集成（+100行）

docs/architecture/
├── AI_SERVICE_ARCHITECTURE.md         # 完整架构文档（2000行）
├── AI_SERVICE_IMPLEMENTATION_GUIDE.md # 实施指南（800行）
└── AI_SERVICE_SUMMARY.md              # 本文档（1200行）
```

### 9.2 配置模板

```bash
# .env.example

# ===== AI服务配置 =====

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

### 9.3 参考资料

**官方文档**：
- Gemini API: https://ai.google.dev/docs
- OpenAI API: https://platform.openai.com/docs
- Redis分布式锁: https://redis.io/docs/manual/patterns/distributed-locks/

**最佳实践**：
- FastAPI异步编程: https://fastapi.tiangolo.com/async/
- Python异步模式: https://docs.python.org/3/library/asyncio.html

---

## 10. 总结

本架构设计为拆词鸭项目提供了一个**健壮、可扩展、成本优化**的AI服务方案。核心亮点包括：

1. **多提供商支持**：抽象工厂模式支持OpenAI、Gemini等，易于扩展
2. **自动降级**：主服务故障时自动切换备用服务，用户无感知
3. **成本优化**：Gemini作为主服务，成本仅OpenAI的50%
4. **高可用性**：降级策略使可用性从99.5%提升到99.9995%
5. **并发控制**：Redis分布式锁防止重复生成，节省成本
6. **完善监控**：结构化日志、健康检查、成本统计

**预期成果**：
- 月成本：$6-12（基于1000次生成）
- 响应时间：2-5秒
- 可用性：99.99%+
- 开发周期：2周MVP + 4周优化

**下一步**：
交由后端开发工程师实施（参考`AI_SERVICE_IMPLEMENTATION_GUIDE.md`）

---

**文档版本**: v1.0
**创建日期**: 2025-10-16
**作者**: 架构师
**审批状态**: 待评审
**相关文档**:
- AI_SERVICE_ARCHITECTURE.md（完整技术设计）
- AI_SERVICE_IMPLEMENTATION_GUIDE.md（快速实施指南）
