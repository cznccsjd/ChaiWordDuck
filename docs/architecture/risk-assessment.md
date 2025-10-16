# 游客模式技术风险评估报告

## 文档信息

| 属性 | 内容 |
|------|------|
| **文档版本** | v1.0 |
| **创建日期** | 2025-10-16 |
| **文档作者** | 架构师 |
| **风险评估周期** | MVP阶段（2025-10-16 至 2025-11-01） |
| **关联文档** | [DESIGN.md](../../DESIGN.md), [PRD.md](../product/PRD.md) |

---

## 1. 风险评估总览

### 1.1 风险矩阵

```
┌───────────────────────────────────────────────────────────────┐
│              风险等级 = 影响程度 × 发生概率                    │
└───────────────────────────────────────────────────────────────┘

影响程度：
- 高（5分）：系统完全不可用或数据丢失
- 中（3分）：部分功能受影响，用户体验下降
- 低（1分）：轻微影响，不影响核心功能

发生概率：
- 高（5分）：几乎确定发生（>60%）
- 中（3分）：可能发生（20-60%）
- 低（1分）：不太可能发生（<20%）

风险等级：
- 严重（15-25分）：立即处理，阻塞上线
- 高（9-12分）：优先处理，MVP前必须解决
- 中（5-8分）：计划处理，Phase 2解决
- 低（1-4分）：可接受，持续监控
```

### 1.2 风险汇总

| 风险ID | 风险描述 | 影响 | 概率 | 等级 | 状态 |
|-------|---------|------|------|------|------|
| R-001 | Redis故障导致限流失效 | 5 | 3 | 15（严重） | ✅ 已缓解 |
| R-002 | IP识别不准确（NAT/代理） | 3 | 5 | 15（严重） | ⚠️ 部分缓解 |
| R-003 | 恶意用户频繁切换IP | 3 | 3 | 9（高） | ✅ 已缓解 |
| R-004 | 高并发下Redis压力过大 | 5 | 1 | 5（中） | ✅ 已规划 |
| R-005 | PostgreSQL查询性能瓶颈 | 3 | 3 | 9（高） | ✅ 已优化 |
| R-006 | OpenAI API故障 | 3 | 1 | 3（低） | ✅ 已缓解 |
| R-007 | 前端localStorage被清除 | 1 | 3 | 3（低） | ✅ 可接受 |
| R-008 | 数据库连接池耗尽 | 5 | 1 | 5（中） | ✅ 已配置 |
| R-009 | AI成本暴增 | 3 | 2 | 6（中） | ✅ 已控制 |
| R-010 | 游客转化率低于预期 | 3 | 3 | 9（高） | ⏳ 待验证 |

---

## 2. 严重风险详细分析

### R-001: Redis故障导致限流失效

**风险描述**：
Redis服务故障或网络中断，导致无法进行限流检查，可能产生两种后果：
1. 系统完全拒绝所有请求（失败关闭）
2. 系统不做限流检查（失败开放），可能被滥用

**影响评估**：
- **用户影响**：所有用户无法查询单词（失败关闭）或限流失效导致滥用（失败开放）
- **业务影响**：核心功能不可用，用户流失
- **成本影响**：失败开放可能导致AI成本暴增
- **数据影响**：查询日志可能不准确

**发生概率**：中（3分）
- 单点Redis故障率约2-3%/年
- 网络抖动导致短暂不可用约1次/月

**缓解措施**：

**1. 降级方案（必须实施）**

```python
# app/services/rate_limit.py

async def check_query_limit_with_fallback(
    self,
    user_or_guest: Union[User, GuestIdentifier],
    word_id: int
) -> Tuple[bool, int, int, str]:
    """
    带降级的限流检查

    降级策略：
    1. 尝试Redis（主方案）
    2. Redis失败 → PostgreSQL（降级方案）
    3. PostgreSQL失败 → 失败关闭（拒绝请求）
    """
    try:
        # 尝试Redis限流（高性能）
        return await self._check_with_redis(user_or_guest, word_id)
    except (RedisConnectionError, RedisTimeoutError) as e:
        # Redis不可用，降级到PostgreSQL
        logger.error(
            "Redis unavailable, fallback to PostgreSQL",
            error=str(e),
            identifier=self._get_identifier(user_or_guest)
        )
        # 触发告警
        await self.alert_service.send_alert(
            level="CRITICAL",
            message="Redis限流服务不可用，已降级到PostgreSQL"
        )

        try:
            # 使用PostgreSQL限流（低性能但可用）
            return await self._check_with_postgres(user_or_guest, word_id)
        except Exception as pg_error:
            # PostgreSQL也失败，失败关闭
            logger.critical(
                "Both Redis and PostgreSQL unavailable",
                redis_error=str(e),
                postgres_error=str(pg_error)
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="限流服务暂时不可用，请稍后再试"
            )
```

**2. Redis高可用（Phase 2实施）**

```yaml
# docker-compose.yml (Redis Sentinel高可用配置)

version: '3.9'

services:
  redis-master:
    image: redis:7-alpine
    command: redis-server --requirepass yourpassword
    ports:
      - "6379:6379"

  redis-replica-1:
    image: redis:7-alpine
    command: redis-server --replicaof redis-master 6379 --requirepass yourpassword
    depends_on:
      - redis-master

  redis-sentinel-1:
    image: redis:7-alpine
    command: redis-sentinel /etc/redis/sentinel.conf
    volumes:
      - ./sentinel.conf:/etc/redis/sentinel.conf
    depends_on:
      - redis-master
      - redis-replica-1
```

**3. 监控告警（必须实施）**

```python
# app/core/monitoring.py

from prometheus_client import Counter, Gauge

# 指标定义
redis_connection_failures = Counter(
    'redis_connection_failures_total',
    'Redis连接失败次数'
)

redis_fallback_to_postgres = Counter(
    'redis_fallback_to_postgres_total',
    'Redis降级到PostgreSQL次数'
)

rate_limit_check_duration = Histogram(
    'rate_limit_check_duration_seconds',
    '限流检查耗时',
    ['source']  # redis/postgres
)

# 告警规则（Prometheus AlertManager）
# 规则：Redis连接失败超过5次/分钟 → 立即告警
```

**残余风险**：
- PostgreSQL也故障（极低概率，<0.1%）
- 降级期间性能下降（可接受）

**责任人**：后端工程师
**截止日期**：MVP上线前
**验收标准**：
- ✅ 降级方案实现并测试通过
- ✅ 监控告警配置完成
- ✅ 告警响应流程文档化

---

### R-002: IP识别不准确（NAT/代理）

**风险描述**：
在企业网络、校园网、公共WiFi等场景下，多个用户共享同一个公网IP，导致：
1. 一个用户用完10次，其他用户无法使用
2. 恶意用户消耗限额，影响正常用户

**影响评估**：
- **用户影响**：同一网络下的用户体验差，投诉增加
- **业务影响**：用户流失，口碑下降
- **转化影响**：游客无法充分体验产品，转化率降低

**发生概率**：高（5分）
- 校园网、公司网络场景占用户20-30%
- NAT识别误判率约15-20%

**缓解措施**：

**Phase 1 (MVP)：接受风险，提供申诉渠道**

```typescript
// frontend/components/LimitReachedAppeal.tsx

export function LimitReachedAppeal() {
  return (
    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
      <p className="text-sm text-gray-600 mb-2">
        💡 如果您认为限额异常（例如与他人共享网络），请点击申诉
      </p>
      <button
        onClick={handleAppeal}
        className="text-sm text-blue-600 underline"
      >
        申诉限额异常
      </button>
    </div>
  );
}

// 申诉逻辑：
// 1. 记录申诉（日志）
// 2. 临时提升限额（20次/天）
// 3. 人工审核（后续）
```

**Phase 2：引入设备指纹识别**

```typescript
// frontend/lib/fingerprint.ts

import FingerprintJS from '@fingerprintjs/fingerprintjs';

export async function getDeviceFingerprint(): Promise<string> {
  const fp = await FingerprintJS.load();
  const result = await fp.get();
  return result.visitorId;  // 唯一设备标识
}

// 后端验证
// app/services/guest_identifier.py

def generate_guest_id_v2(
    ip: str,
    user_agent: str,
    device_fingerprint: Optional[str]
) -> str:
    """
    Phase 2: 使用设备指纹增强识别

    准确率：95%+ （vs Phase 1的85%）
    """
    if device_fingerprint:
        # 使用设备指纹（优先）
        combined = f"{device_fingerprint}:{ip[:10]}"  # IP仅作为辅助
    else:
        # 降级到IP+UA（兼容旧客户端）
        combined = f"{ip}:{user_agent}"

    return hashlib.sha256(combined.encode()).hexdigest()
```

**Phase 3：动态限额调整**

```python
# 根据识别可信度动态调整限额

def get_dynamic_guest_limit(confidence: float) -> int:
    """
    根据识别可信度调整限额

    Args:
        confidence: 识别可信度（0.0-1.0）

    Returns:
        动态限额
    """
    if confidence > 0.95:
        # 高可信度（设备指纹）：10次
        return 10
    elif confidence > 0.85:
        # 中可信度（IP+UA）：8次
        return 8
    else:
        # 低可信度（仅IP）：5次
        return 5
```

**残余风险**：
- 设备指纹仍可能被绕过（VPN + 隐私浏览器）
- 隐私合规风险（需明确告知用户）

**责任人**：架构师 + 前端工程师
**截止日期**：Phase 2（MVP后2周）
**验收标准**：
- ✅ Phase 1申诉渠道上线
- ⏳ Phase 2设备指纹集成（准确率≥95%）
- ⏳ 隐私政策更新

---

## 3. 高风险详细分析

### R-003: 恶意用户频繁切换IP

**风险描述**：
技术能力较强的恶意用户通过以下方式绕过限流：
1. 使用VPN频繁切换IP
2. 使用代理池（数百个IP）
3. 分布式爬虫

**影响评估**：
- **成本影响**：AI生成成本增加
- **性能影响**：数据库和Redis压力增加
- **公平性影响**：正常用户资源被占用

**发生概率**：中（3分）
- MVP阶段用户量小，被攻击概率低
- 但一旦发生，影响较大

**缓解措施**：

**1. 行为检测（必须实施）**

```python
# app/services/abuse_detection.py

class AbuseDetectionService:
    """滥用行为检测"""

    async def detect_suspicious_pattern(
        self,
        identifier: str,
        word: str,
    ) -> Optional[str]:
        """
        检测可疑查询模式

        检测模式：
        1. 短时间重复查询同一单词（<5秒/次）
        2. 按字母顺序查询（爬虫特征）
        3. 查询罕见单词（非热门词汇）
        4. 查询速度过快（人类平均15秒/次）
        """
        recent_queries_key = f"abuse:recent:{identifier}"

        # 获取最近10次查询
        recent = await self.redis.lrange(recent_queries_key, 0, 9)

        # 检测1：重复查询
        if recent.count(word.encode()) >= 3:
            logger.warning(
                "Suspicious pattern detected: repeated query",
                identifier=identifier,
                word=word
            )
            return "REPEATED_QUERY"

        # 检测2：字母顺序（爬虫）
        if len(recent) >= 5:
            words = [w.decode() for w in recent[:5]]
            if self._is_alphabetical_sequence(words):
                logger.warning(
                    "Suspicious pattern detected: alphabetical crawling",
                    identifier=identifier,
                    words=words
                )
                return "ALPHABETICAL_CRAWLING"

        # 检测3：查询速度过快
        if len(recent) >= 3:
            # 检查最近3次查询的时间戳
            timestamps = await self._get_query_timestamps(identifier, 3)
            if timestamps and (timestamps[-1] - timestamps[0]) < 10:
                # 10秒内查询3次，疑似机器人
                logger.warning(
                    "Suspicious pattern detected: too fast",
                    identifier=identifier,
                    interval=timestamps[-1] - timestamps[0]
                )
                return "TOO_FAST"

        # 记录本次查询
        await self.redis.lpush(recent_queries_key, word)
        await self.redis.ltrim(recent_queries_key, 0, 9)
        await self.redis.expire(recent_queries_key, 300)

        return None

    @staticmethod
    def _is_alphabetical_sequence(words: list[str]) -> bool:
        """检测是否为字母顺序"""
        first_chars = [w[0].lower() for w in words if w]
        return first_chars == sorted(first_chars)
```

**2. Captcha验证（可选实施）**

```python
# app/middleware/captcha.py

async def check_captcha_required(request: Request):
    """
    检查是否需要Captcha验证

    触发条件：
    - 行为检测标记为可疑
    - IP在短时间内创建多个游客会话
    """
    identifier = get_identifier(request)

    captcha_key = f"captcha:required:{identifier}"
    if await redis.get(captcha_key):
        # 需要Captcha验证
        captcha_token = request.headers.get("X-Captcha-Token")
        if not captcha_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "CAPTCHA_REQUIRED",
                    "message": "需要完成人机验证",
                    "captcha_site_key": settings.captcha_site_key
                }
            )

        # 验证Captcha
        is_valid = await captcha_service.verify(captcha_token)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Captcha验证失败"
            )

        # 验证通过，清除标记
        await redis.delete(captcha_key)
```

**3. AI生成限额控制（必须实施）**

```python
# app/services/word_generation.py

async def check_ai_generation_limit(identifier: str) -> bool:
    """
    检查AI生成限额

    限制：每个IP/游客每天最多生成5个新单词
    目的：防止滥用导致成本暴增
    """
    generation_key = f"ai:generation:{identifier}:{date.today()}"
    count = await redis.get(generation_key)

    if count and int(count) >= settings.ai_generation_daily_limit:
        logger.warning(
            "AI generation limit exceeded",
            identifier=identifier,
            count=count
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "AI_GENERATION_LIMIT_EXCEEDED",
                "message": "AI生成限额已用完（5次/天），请查询已有单词或明日再试"
            }
        )

    return True
```

**残余风险**：
- 高级爬虫仍可能绕过（使用真实浏览器模拟）
- 成本风险（可通过AI限额控制在可接受范围）

**责任人**：后端工程师
**截止日期**：MVP上线前
**验收标准**：
- ✅ 行为检测服务实现
- ✅ AI生成限额控制
- ⏳ Captcha集成（可选）

---

### R-005: PostgreSQL查询性能瓶颈

**风险描述**：
高并发场景下，查询日志写入和单词查询可能成为性能瓶颈：
1. 每次查询需要写入query_logs表
2. 单词查询需要联表查询（words + query_logs）
3. 数据库连接池耗尽

**影响评估**：
- **性能影响**：响应时间增加，P95超过1秒
- **用户体验**：页面加载慢，用户流失
- **稳定性**：连接池耗尽导致新请求失败

**发生概率**：中（3分）
- MVP阶段用户量小（<1000 DAU），概率低
- 但增长后（>10000 DAU）几乎确定发生

**缓解措施**：

**1. 索引优化（必须实施）**

```sql
-- 查询日志表索引优化

-- 复合索引1：游客查询（guest_id + 日期）
CREATE INDEX CONCURRENTLY idx_query_logs_guest_date
ON query_logs (guest_session_id, query_date)
WHERE guest_session_id IS NOT NULL;

-- 复合索引2：用户查询（user_id + 日期）
CREATE INDEX CONCURRENTLY idx_query_logs_user_date
ON query_logs (user_id, query_date)
WHERE user_id IS NOT NULL;

-- 复合索引3：检查单词是否已查询
CREATE INDEX CONCURRENTLY idx_query_logs_guest_word_date
ON query_logs (guest_session_id, word_id, query_date)
WHERE guest_session_id IS NOT NULL;

-- 单词表索引
CREATE INDEX CONCURRENTLY idx_words_word_golden
ON words (word, is_golden);

-- 验证索引使用
EXPLAIN ANALYZE
SELECT COUNT(*) FROM query_logs
WHERE guest_session_id = 'abc123'
  AND query_date = '2025-10-16';

-- 期望：Index Scan，执行时间<5ms
```

**2. 异步写入查询日志（Phase 2实施）**

```python
# app/services/query_log_async.py

from asyncio import Queue
from typing import List

class AsyncQueryLogWriter:
    """
    异步查询日志写入器

    策略：
    - 查询日志先写入内存队列
    - 后台任务批量写入数据库
    - 降低对主请求的性能影响
    """

    def __init__(self, db: AsyncSession, batch_size: int = 100):
        self.db = db
        self.batch_size = batch_size
        self.queue: Queue[QueryLog] = Queue()
        self.buffer: List[QueryLog] = []

    async def enqueue(self, query_log: QueryLog):
        """添加到队列（非阻塞）"""
        await self.queue.put(query_log)

    async def worker(self):
        """后台任务：批量写入数据库"""
        while True:
            try:
                # 从队列取出
                query_log = await self.queue.get()
                self.buffer.append(query_log)

                # 达到批量大小或超时，批量写入
                if len(self.buffer) >= self.batch_size:
                    await self._flush()

            except Exception as e:
                logger.error("Query log async writer error", error=str(e))

    async def _flush(self):
        """批量写入数据库"""
        if not self.buffer:
            return

        try:
            self.db.add_all(self.buffer)
            await self.db.commit()
            logger.info(f"Flushed {len(self.buffer)} query logs")
            self.buffer.clear()
        except Exception as e:
            logger.error("Query log flush error", error=str(e))
            self.buffer.clear()
```

**3. 连接池配置优化（必须实施）**

```python
# app/core/database.py

from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    settings.database_url,
    pool_size=20,           # 常规连接数（根据并发调整）
    max_overflow=10,        # 峰值时额外连接数
    pool_timeout=30,        # 获取连接超时（秒）
    pool_recycle=3600,      # 连接回收时间（1小时）
    pool_pre_ping=True,     # 检测失效连接
    echo=False,
)

# 监控连接池状态
def get_pool_status():
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
    }
```

**4. 单词数据缓存（必须实施）**

```python
# app/services/word_cache.py

import json
from typing import Optional

class WordCacheService:
    """单词数据缓存服务"""

    async def get_word(self, word: str) -> Optional[Word]:
        """
        获取单词（优先从缓存）

        流程：
        1. 查Redis缓存
        2. 缓存未命中 → 查数据库
        3. 写入Redis缓存（TTL 7天）
        """
        cache_key = RedisKeys.word_cache(word)

        # 1. 查缓存
        cached = await self.redis.get(cache_key)
        if cached:
            logger.debug(f"Word cache hit: {word}")
            return Word(**json.loads(cached))

        # 2. 查数据库
        logger.debug(f"Word cache miss: {word}")
        result = await self.db.execute(
            select(Word).where(Word.word == word)
        )
        word_obj = result.scalar_one_or_none()

        if word_obj:
            # 3. 写入缓存
            cache_value = json.dumps(word_obj.to_dict())
            await self.redis.setex(cache_key, 604800, cache_value)  # 7天

        return word_obj
```

**残余风险**：
- 极高并发（>10万DAU）仍需数据库读写分离
- 缓存穿透风险（大量查询不存在的单词）

**责任人**：后端工程师
**截止日期**：MVP上线前
**验收标准**：
- ✅ 数据库索引优化完成
- ✅ 连接池配置优化
- ✅ 单词缓存实现
- ⏳ 异步写入（Phase 2）

---

### R-010: 游客转化率低于预期

**风险描述**：
虽然PRD v1.1已将游客限额提升到10次/天，但转化率仍可能低于预期（目标15%）：
1. 引导文案不够吸引人
2. 注册流程复杂
3. 注册价值不够明显

**影响评估**：
- **业务影响**：注册用户增长缓慢
- **收入影响**：付费用户基数小
- **产品影响**：难以验证PMF

**发生概率**：中（3分）
- 工具类产品平均转化率10-15%
- 新产品初期更低（5-10%）

**缓解措施**：

**1. A/B测试不同引导策略（必须实施）**

```typescript
// frontend/hooks/useABTest.ts

export function useGuestGuidanceVariant() {
  const [variant, setVariant] = useState<'A' | 'B' | 'C'>();

  useEffect(() => {
    // 随机分配用户到不同组
    const variants = ['A', 'B', 'C'];
    const assigned = variants[Math.floor(Math.random() * variants.length)];
    setVariant(assigned);

    // 记录到后端
    trackEvent('ab_test_assigned', { variant: assigned });
  }, []);

  return variant;
}

// 变体A：温和引导（当前设计）
// 变体B：激进引导（查询5次后弹窗）
// 变体C：价值强化（展示更多注册福利）
```

**2. 简化注册流程**

```typescript
// 当前注册流程（3步）：
// 1. 输入邮箱
// 2. 输入密码（需要8位+字母+数字）
// 3. 确认密码

// 优化后（2步）：
// 1. 输入邮箱
// 2. 输入密码（降低要求：6位即可）
// 自动跳过密码确认（前端实时验证）

// 进一步优化（1步，Phase 2）：
// 使用"魔法链接"登录（无需密码）
```

**3. 强化注册价值展示**

```typescript
// frontend/components/RegistrationValueProposition.tsx

const benefits = [
  { icon: "🎯", text: "每天50次查询", highlight: "5倍提升" },
  { icon: "⭐", text: "收藏最多50个单词", highlight: "系统复习" },
  { icon: "📊", text: "完整学习历史", highlight: "追踪进度" },
  { icon: "📧", text: "定期复习提醒", highlight: "不再遗忘" },
  { icon: "🎁", text: "注册即送7天Premium", highlight: "新用户福利" },
];
```

**4. 游客数据迁移（减少流失）**

```python
# app/api/v1/auth.py

@router.post("/convert-guest")
async def convert_guest_to_user(
    data: GuestConversionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    游客转注册用户

    自动迁移：
    - 查询历史
    - 已查询单词列表
    """
    # 创建用户
    user = User(email=data.email, password_hash=hash_password(data.password))
    db.add(user)

    # 迁移查询历史
    if data.guest_id:
        await db.execute(
            update(QueryLog)
            .where(QueryLog.guest_session_id == data.guest_id)
            .values(
                user_id=user.id,
                guest_session_id=None
            )
        )

    await db.commit()

    return {"message": "注册成功，您的查询历史已保留"}
```

**监控指标**：

```python
# 关键转化指标

# 1. 游客查询行为
- 查询1次后离开率（bounce rate）
- 查询3次后继续率
- 查询10次后注册率

# 2. 转化漏斗
- 查询页面 → 点击注册按钮
- 注册按钮 → 填写邮箱
- 填写邮箱 → 注册成功

# 3. 引导效果
- 不同阶段引导的点击率
- 不同文案的转化率
- A/B测试各变体的表现
```

**残余风险**：
- 转化率受产品本身价值影响（限流策略只是一部分）
- 需要持续优化产品体验

**责任人**：产品经理 + 前端工程师
**截止日期**：MVP上线后2周（收集数据后优化）
**验收标准**：
- ✅ A/B测试框架搭建
- ✅ 转化率监控埋点
- ⏳ 注册流程优化
- ⏳ 根据数据迭代引导策略

---

## 4. 风险监控仪表板

### 4.1 关键指标

```
┌───────────────────────────────────────────────────────────┐
│              游客模式健康度仪表板                          │
└───────────────────────────────────────────────────────────┘

系统可用性：
- Redis可用性：99.9% ✅
- PostgreSQL可用性：99.95% ✅
- API响应时间（P95）：350ms ✅

限流效果：
- IP限流拦截率：0.5% ✅
- 游客限额触发率：15% ✅
- 行为检测命中率：0.8% ✅

识别准确性：
- 游客识别准确率（Phase 1）：85% ⚠️
- 误判申诉率：2% ✅

业务指标：
- 游客日活（DAU）：500 ✅
- 游客查询量：2500/天 ✅
- 游客→注册转化率：12% ⚠️ (目标15%)
- AI生成成本：$8/天 ✅ (预算$15/天)

性能指标：
- 数据库连接池使用率：45% ✅
- Redis内存使用率：15% ✅
- 数据库慢查询次数：0 ✅
```

### 4.2 告警规则

| 告警名称 | 触发条件 | 级别 | 处理时间 |
|---------|---------|------|---------|
| Redis不可用 | 连接失败>3次/分钟 | 严重 | 立即 |
| 数据库慢查询 | 查询时间>1秒 | 高 | 5分钟内 |
| API响应慢 | P95>1秒 | 高 | 10分钟内 |
| 限流失效 | 单个游客查询>20次/天 | 高 | 15分钟内 |
| AI成本超预算 | >$20/天 | 中 | 1小时内 |
| 转化率异常低 | <5% | 中 | 24小时内 |

---

## 5. 应急响应计划

### 5.1 Redis完全故障

**症状**：
- Redis连接失败
- 限流检查报错
- 查询请求全部失败或不限流

**应急步骤**：

```
1. 确认故障（30秒内）
   - 检查Redis服务状态
   - 检查网络连接
   - 查看错误日志

2. 启用降级方案（1分钟内）
   - 系统自动切换到PostgreSQL限流
   - 验证降级后功能正常

3. 修复Redis（5-15分钟）
   - 重启Redis服务
   - 检查配置文件
   - 验证数据恢复

4. 切回主方案（5分钟）
   - 逐步切流（10% → 50% → 100%）
   - 监控性能和错误率
   - 确认Redis稳定后完全切回

5. 事后复盘（24小时内）
   - 根因分析
   - 改进措施
   - 文档更新
```

### 5.2 大规模爬虫攻击

**症状**：
- IP限流大量触发
- 行为检测频繁报警
- API响应时间增加
- AI成本暴增

**应急步骤**：

```
1. 确认攻击（1分钟内）
   - 检查异常IP列表
   - 分析查询模式
   - 确认是否为爬虫

2. 临时封禁（2分钟内）
   - 将攻击IP加入黑名单
   - 降低IP限流阈值（30→10次/分钟）
   - 启用Captcha验证

3. 限制AI生成（5分钟内）
   - 降低AI生成限额（5→2次/天）
   - 优先返回预生成手册

4. 持续监控（24小时）
   - 监控攻击IP行为
   - 逐步恢复正常限额
   - 收集攻击样本用于模型优化

5. 长期优化（1周内）
   - 增强行为检测模型
   - 扩展IP黑名单库
   - 考虑接入第三方反爬服务
```

---

## 6. 风险接受声明

以下低风险问题，在MVP阶段选择接受：

1. **R-007: 前端localStorage被清除**
   - 影响：游客获得额外免费次数
   - 接受理由：影响小，成本低
   - 监控：观察是否有大规模滥用

2. **R-006: OpenAI API故障**
   - 影响：新单词无法生成
   - 接受理由：预生成手册可覆盖80%场景
   - 备选：准备国产模型备用方案

3. **游客识别误判（Phase 1）**
   - 影响：同一网络多用户受影响
   - 接受理由：提供申诉渠道，Phase 2升级
   - 补偿：申诉用户临时提升限额

---

## 7. 总结

### 7.1 风险评估结论

| 风险等级 | 数量 | 状态 |
|---------|-----|------|
| 严重 | 2 | ✅ 已缓解 |
| 高 | 4 | ✅ 3个已缓解，1个待验证 |
| 中 | 3 | ✅ 已规划/可接受 |
| 低 | 1 | ✅ 可接受 |

**整体风险评估**：✅ 可控

**建议**：
1. 严重风险的缓解措施必须在MVP上线前完成
2. 高风险的监控和告警必须完善
3. 中低风险可在Phase 2优化

### 7.2 行动计划

**MVP上线前必须完成**：
- ✅ Redis降级方案实现
- ✅ 数据库索引优化
- ✅ 行为检测服务
- ✅ AI生成限额控制
- ✅ 监控告警配置

**Phase 2优化**：
- ⏳ 设备指纹识别
- ⏳ Redis Sentinel高可用
- ⏳ 异步查询日志写入
- ⏳ 基于转化率数据优化引导策略

**持续监控**：
- 📊 每日检查监控仪表板
- 📧 告警及时响应（<15分钟）
- 📝 每周风险评估会议
- 🔄 每月更新风险评估报告

---

**文档结束**

**版本**：v1.0
**日期**：2025-10-16
**下次评估**：2025-10-30（MVP上线后2周）
**责任人**：架构师
