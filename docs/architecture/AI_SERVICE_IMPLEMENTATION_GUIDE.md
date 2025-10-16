# AI服务实施指南（快速参考）

## 1. 核心设计决策总结

### 1.1 技术选型

| 决策点 | 选择 | 理由 |
|--------|------|------|
| **主AI提供商** | Gemini (gemini-1.5-flash) | 成本最低（$0.0002/次），速度快（2-3秒），满足MVP需求 |
| **备用AI提供商** | OpenAI (gpt-4o-mini) | 稳定性最高（99.9%），质量好，成本可接受（$0.0004/次）|
| **架构模式** | 抽象工厂 + 策略模式 | 易于扩展新AI提供商，支持运行时切换 |
| **并发控制** | Redis分布式锁 | 防止多用户同时查询同一新单词导致重复生成 |
| **降级策略** | 主服务失败自动切换备用服务 | 提高系统可用性，避免单点故障 |

### 1.2 成本对比（每月1000次AI生成）

| 提供商 | 单次成本 | 月成本 | 相对比例 |
|--------|---------|--------|---------|
| Gemini | $0.0002 | $6 | 基准 |
| OpenAI | $0.0004 | $12 | 2倍 |
| Claude | $0.009 | $270 | 45倍 |

**推荐配置**：主服务Gemini + 备用OpenAI = $6-12/月

---

## 2. 实施步骤（5步走）

### Step 1: 安装依赖

```bash
cd backend

# 使用PDM添加依赖
pdm add openai
pdm add google-generativeai

# 验证安装
pdm list | grep -E "openai|google-generativeai"
```

### Step 2: 配置环境变量

```bash
# .env（添加以下配置）

# 主AI提供商（推荐gemini）
AI_PRIMARY_PROVIDER=gemini
AI_FALLBACK_PROVIDER=openai

# Gemini配置（从 https://ai.google.dev/ 获取）
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXX
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TIMEOUT=30

# OpenAI配置（从 https://platform.openai.com/ 获取）
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXX
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT=30

# AI生成限额
GUEST_AI_GENERATION_LIMIT=5
FREE_USER_AI_GENERATION_LIMIT=20
PREMIUM_USER_AI_GENERATION_LIMIT=-1
```

### Step 3: 更新配置类

```python
# backend/app/core/config.py（在Settings类中添加）

from typing import Optional

class Settings(BaseSettings):
    # ... 现有配置 ...

    # ===== AI服务配置（新增）=====

    # 主AI提供商
    ai_primary_provider: str = Field(default="gemini")
    ai_fallback_provider: Optional[str] = Field(default="openai")

    # Gemini配置
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-1.5-flash")
    gemini_timeout: int = Field(default=30)

    # OpenAI配置（已存在，保留）
    # openai_api_key: str = Field(default="")
    # openai_model: str = Field(default="gpt-4o-mini")
    # openai_timeout: int = Field(default=30)

    # AI生成限额
    guest_ai_generation_limit: int = Field(default=5)
    free_user_ai_generation_limit: int = Field(default=20)
    premium_user_ai_generation_limit: int = Field(default=-1)
```

### Step 4: 创建AI服务模块

```bash
# 创建目录结构
mkdir -p backend/app/services/ai
touch backend/app/services/ai/__init__.py
touch backend/app/services/ai/base.py
touch backend/app/services/ai/openai_service.py
touch backend/app/services/ai/gemini_service.py
touch backend/app/services/ai/factory.py
touch backend/app/services/ai/manager.py
```

**文件清单**：
- `base.py`: 抽象基类（BaseAIService, WordHandbook, AIGenerationError）
- `openai_service.py`: OpenAI服务实现
- `gemini_service.py`: Gemini服务实现
- `factory.py`: 服务工厂（AIServiceFactory）
- `manager.py`: 生成管理器（AIGenerationManager）

**代码详见**：`AI_SERVICE_ARCHITECTURE.md` 第2-3节

### Step 5: 更新Redis键定义

```python
# backend/app/core/redis_keys.py（添加AI相关键）

class RedisKeys:
    # ... 现有键 ...

    # ===== AI生成相关（新增）=====
    AI_GENERATION_LOCK = "ai_generation:lock:{word}"
    GUEST_AI_GENERATION_COUNT = "ai_generation:count:guest:{guest_id}:{date}"
    USER_AI_GENERATION_COUNT = "ai_generation:count:user:{user_id}:{date}"

    @classmethod
    def get_ai_generation_lock(cls, word: str) -> str:
        return cls.AI_GENERATION_LOCK.format(word=word.lower())

    @classmethod
    def get_guest_ai_generation_count_key(cls, guest_id: str, date: str) -> str:
        return cls.GUEST_AI_GENERATION_COUNT.format(guest_id=guest_id, date=date)

    @classmethod
    def get_user_ai_generation_count_key(cls, user_id: int, date: str) -> str:
        return cls.USER_AI_GENERATION_COUNT.format(user_id=user_id, date=date)
```

---

## 3. API集成（核心逻辑）

### 3.1 单词查询流程改造

```python
# backend/app/api/v1/words.py（修改query_word_internal函数）

from app.services.ai.manager import AIGenerationManager
from app.services.ai.base import AIGenerationError
from app.core.redis_keys import RedisKeys

async def query_word_internal(
    word_text: str,
    current_user: Optional[User],
    db: AsyncSession,
    request: Optional[Request] = None,
    redis: Optional[Redis] = None,  # 新增Redis依赖
) -> WordQueryResponse:
    """
    单词查询（增强：支持AI生成）

    流程：
    1. 查询数据库
    2. 如果不存在 → 检查AI生成限额 → 调用AI生成 → 存储 → 返回
    3. 如果存在 → 检查查询限额 → 返回
    """
    normalized_word = word_text.strip().lower()

    # ... 验证逻辑（省略）...

    # 查询单词
    result = await db.execute(
        select(Word).where(Word.word == normalized_word)
    )
    word = result.scalar_one_or_none()

    # ===== 核心改动：单词不存在时AI生成 =====
    if not word:
        logger.info(f"单词不存在，尝试AI生成: {normalized_word}")

        # 1. 检查AI生成限额
        await check_ai_generation_limit(current_user, request, redis)

        # 2. 调用AI生成
        try:
            ai_manager = AIGenerationManager(redis)
            handbook = await ai_manager.generate_word_handbook(normalized_word)

            # 3. 存储到数据库
            word = Word(
                word=handbook.word,
                phonetic=handbook.phonetic,
                part_of_speech=handbook.part_of_speech,
                core_game=handbook.core_game,
                scenario_formal=handbook.scenario_formal,
                scenario_casual=handbook.scenario_casual,
                etymology_breakdown=handbook.etymology_breakdown,
                etymology_story=handbook.etymology_story,
                common_mistakes=handbook.common_mistakes,
                memory_trick=handbook.memory_trick,
                is_golden=False,
                source="ai",
            )
            db.add(word)
            await db.commit()
            await db.refresh(word)

            logger.info(f"AI生成成功: {normalized_word}, word_id={word.id}")

        except AIGenerationError as e:
            logger.error(f"AI生成失败: {e.message}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "code": ErrorCode.AI_GENERATION_FAILED,
                    "message": f"AI生成失败，请稍后重试",
                },
            )

    # ... 后续逻辑（查询限额检查、记录日志等）...

    return WordQueryResponse(...)
```

### 3.2 AI生成限额检查

```python
# backend/app/api/v1/words.py（新增函数）

async def check_ai_generation_limit(
    current_user: Optional[User],
    request: Optional[Request],
    redis: Redis,
):
    """
    检查AI生成限额

    限额：
    - 游客：5次/天
    - 免费用户：20次/天
    - Premium用户：无限制

    Raises:
        HTTPException: 429 超出限额
    """
    from app.services.guest_identifier import GuestIdentifierService

    today = date.today().isoformat()

    if current_user is None:
        # 游客模式
        identifier = GuestIdentifierService.get_identifier(request)
        limit = settings.guest_ai_generation_limit
        count_key = RedisKeys.get_guest_ai_generation_count_key(identifier, today)
        user_type = "游客"

    elif current_user.membership_tier == "premium":
        # Premium用户无限制
        return

    else:
        # 免费注册用户
        limit = settings.free_user_ai_generation_limit
        count_key = RedisKeys.get_user_ai_generation_count_key(current_user.id, today)
        user_type = "免费用户"

    # 获取今日已生成次数
    current_count = await redis.get(count_key)
    used = int(current_count) if current_count else 0

    if used >= limit:
        logger.warning(f"{user_type} AI生成限额已用完: {used}/{limit}")
        raise HTTPException(
            status_code=429,
            detail={
                "code": ErrorCode.AI_GENERATION_LIMIT_EXCEEDED,
                "message": f"今日AI生成次数已用完（{limit}次）。"
                          f"{'注册可获得20次/天' if current_user is None else '升级Premium可无限生成'}！",
            },
        )

    # 递增计数
    await redis.incr(count_key)
    await redis.expire(count_key, 86400)  # 24小时过期
```

### 3.3 更新路由依赖注入

```python
# backend/app/api/v1/words.py（修改路由函数）

from app.core.database import get_redis  # 假设有这个依赖函数

@router.get("/query/{word}")
async def query_word_by_path(
    word: str,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),  # 新增Redis依赖
):
    response_data = await query_word_internal(
        word,
        current_user,
        db,
        request,
        redis,  # 传递Redis
    )
    return SuccessResponse(data=response_data)


@router.post("/query")
async def query_word(
    data: WordQueryRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),  # 新增Redis依赖
):
    response_data = await query_word_internal(
        data.word,
        current_user,
        db,
        request,
        redis,  # 传递Redis
    )
    return SuccessResponse(data=response_data)
```

---

## 4. 测试验证

### 4.1 单元测试

```bash
# 运行AI服务单元测试
pdm run pytest tests/unit/test_ai_services.py -v
```

```python
# tests/unit/test_ai_services.py（示例）

import pytest
from app.services.ai.gemini_service import GeminiService
from app.services.ai.openai_service import OpenAIService


@pytest.mark.asyncio
async def test_gemini_service():
    """测试Gemini服务生成"""
    service = GeminiService()
    handbook = await service.generate_word_handbook("serendipity")

    assert handbook.word == "serendipity"
    assert handbook.core_game
    assert handbook.etymology_breakdown
    assert len(handbook.memory_trick) > 0


@pytest.mark.asyncio
async def test_openai_service():
    """测试OpenAI服务生成"""
    service = OpenAIService()
    handbook = await service.generate_word_handbook("serendipitous")

    assert handbook.word == "serendipitous"
    assert handbook.scenario_formal
    assert handbook.common_mistakes
```

### 4.2 集成测试

```bash
# 运行集成测试
pdm run pytest tests/integration/test_ai_generation.py -v
```

```python
# tests/integration/test_ai_generation.py（示例）

@pytest.mark.asyncio
async def test_word_query_with_ai_generation(client, test_db):
    """测试单词查询（新单词自动AI生成）"""

    # 1. 查询不存在的单词
    response = await client.get("/api/v1/words/query/serendipitous")

    # 2. 验证响应
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["word"] == "serendipitous"
    assert data["data"]["core_game"]

    # 3. 验证数据库已存储
    word = await test_db.execute(
        select(Word).where(Word.word == "serendipitous")
    )
    assert word.scalar_one_or_none() is not None
    assert word.scalar_one().source == "ai"


@pytest.mark.asyncio
async def test_ai_generation_limit(client, mock_redis):
    """测试AI生成限额"""

    # 游客模式，连续生成6个新单词（超出5次限额）
    for i in range(6):
        word = f"testword{i}"
        response = await client.get(f"/api/v1/words/query/{word}")

        if i < 5:
            # 前5次应该成功
            assert response.status_code == 200
        else:
            # 第6次应该被限流
            assert response.status_code == 429
            assert "AI生成次数已用完" in response.json()["detail"]["message"]
```

### 4.3 手动测试

```bash
# 启动后端服务
pdm run uvicorn app.main:app --reload

# 测试AI生成（使用curl）
curl -X GET "http://localhost:8000/api/v1/words/query/serendipitous" \
  -H "Content-Type: application/json"

# 预期响应：
# {
#   "success": true,
#   "data": {
#     "id": 123,
#     "word": "serendipitous",
#     "core_game": "意外之喜的发现者",
#     "scenario_formal": "...",
#     "etymology_breakdown": "...",
#     ...
#   }
# }
```

---

## 5. 监控和运维

### 5.1 健康检查

```python
# backend/app/api/endpoints/health.py（新增AI健康检查）

@router.get("/health/ai")
async def health_check_ai(redis: Redis = Depends(get_redis)):
    """
    AI服务健康检查

    返回：
    {
      "status": "healthy" | "degraded" | "unhealthy",
      "services": {
        "gemini": true,
        "openai": true
      }
    }
    """
    from app.services.ai.manager import AIGenerationManager

    manager = AIGenerationManager(redis)
    service_status = await manager.get_service_status()

    healthy_count = sum(1 for s in service_status.values() if s)
    total_count = len(service_status)

    if healthy_count == total_count:
        status = "healthy"
    elif healthy_count > 0:
        status = "degraded"
    else:
        status = "unhealthy"

    return {
        "status": status,
        "services": service_status,
        "timestamp": datetime.utcnow().isoformat(),
    }
```

### 5.2 日志监控

```python
# 关键日志示例

# AI生成成功
logger.info(
    "AI生成单词手册成功",
    extra={
        "word": "serendipitous",
        "provider": "gemini",
        "duration_ms": 2500,
        "cost_usd": 0.0002,
    }
)

# AI生成失败
logger.error(
    "AI生成失败",
    extra={
        "word": "serendipitous",
        "provider": "gemini",
        "error": "API超时",
        "attempt": 3,
    },
    exc_info=True
)

# 降级切换
logger.warning(
    "主服务失败，切换到备用服务",
    extra={
        "word": "serendipitous",
        "primary_provider": "gemini",
        "fallback_provider": "openai",
    }
)
```

### 5.3 成本监控

```python
# backend/app/services/ai/metrics.py（成本统计）

class AIMetricsCollector:
    """AI指标收集器"""

    async def get_daily_cost(self, date: str) -> float:
        """
        获取某日AI生成总成本

        Returns:
            float: 总成本（美元）
        """
        # TODO: 从日志或数据库统计
        pass

    async def get_monthly_cost(self, year: int, month: int) -> float:
        """
        获取某月AI生成总成本

        Returns:
            float: 总成本（美元）
        """
        # TODO: 汇总每日成本
        pass
```

---

## 6. 常见问题（FAQ）

### Q1: 为什么选择Gemini作为主服务？

**A**: 成本最低（比OpenAI便宜50%），速度快（2-3秒），质量满足MVP需求。

### Q2: 如果Gemini API故障怎么办？

**A**: 自动切换到备用服务（OpenAI），确保系统可用性。

### Q3: 如何防止多用户同时查询同一新单词导致重复生成？

**A**: 使用Redis分布式锁（`ai_generation:lock:{word}`），同一时刻只允许一个请求生成。

### Q4: 游客AI生成次数用完后怎么办？

**A**: 提示用户注册（免费用户20次/天）或升级Premium（无限）。

### Q5: 如何估算AI成本？

**A**:
- Gemini: $0.0002/次 × 每日生成次数 × 30天
- 示例：100次/天 × 30 = $6/月

### Q6: 生成的单词手册质量不高怎么办？

**A**:
1. 调整系统Prompt（`base.py`的`_build_system_prompt`）
2. 切换到质量更高的模型（如gpt-4o）
3. 添加用户反馈机制，人工审核

### Q7: 是否支持批量预生成？

**A**: 当前不支持，Phase 2可以添加后台任务批量生成高频单词。

---

## 7. 下一步（后端开发工程师执行）

### 7.1 实施任务清单

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
  - [ ] 增加AI生成逻辑
  - [ ] 增加AI生成限额检查
  - [ ] 增加Redis依赖注入
- [ ] 编写单元测试（tests/unit/test_ai_services.py）
- [ ] 编写集成测试（tests/integration/test_ai_generation.py）
- [ ] 手动测试验证
- [ ] 添加健康检查端点（app/api/endpoints/health.py）
- [ ] 文档更新（README.md, API文档）

### 7.2 预估工作量

| 任务 | 预估时间 |
|------|---------|
| 环境配置和依赖安装 | 0.5小时 |
| AI服务模块开发 | 4小时 |
| API集成和限额检查 | 2小时 |
| 单元测试编写 | 2小时 |
| 集成测试编写 | 2小时 |
| 手动测试和调试 | 1小时 |
| 文档更新 | 1小时 |
| **总计** | **12.5小时** |

### 7.3 风险点

1. **API Key配置错误**：
   - 风险：服务无法启动
   - 缓解：添加启动时健康检查

2. **AI API限流**：
   - 风险：高并发时被限流
   - 缓解：实现请求队列和速率限制

3. **生成质量不稳定**：
   - 风险：用户体验差
   - 缓解：添加质量评分和人工审核

---

## 8. 参考资料

- **Gemini API文档**: https://ai.google.dev/docs
- **OpenAI API文档**: https://platform.openai.com/docs
- **架构设计详细文档**: `AI_SERVICE_ARCHITECTURE.md`
- **项目约束文档**: `CLAUDE.md`（包管理工具、Git规范等）

---

**文档版本**: v1.0
**创建日期**: 2025-10-16
**作者**: 架构师
**适用角色**: 后端开发工程师
