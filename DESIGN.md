# 拆词鸭 ChaiWord Duck - 技术设计文档

## 1. 文档信息

| 属性 | 内容 |
|------|------|
| **文档版本** | v1.1 |
| **创建日期** | 2025-10-16 |
| **最后更新** | 2025-10-16 |
| **文档作者** | 架构师 |
| **审批状态** | 待评审 |
| **对应PRD版本** | PRD v1.1 |
| **相关文档** | [PRD.md](./docs/product/PRD.md), [PRD v1.1更新说明](./docs/product/PRD_v1.1_更新说明.md) |

---

## 2. 架构概述

### 2.1 设计原则

**核心原则**：
- **渐进式体验**：游客模式优先，降低使用门槛
- **可扩展性**：支持从100到100万用户的无缝扩展
- **性能优先**：95%请求响应时间 < 500ms
- **安全第一**：多层防护，防止滥用和攻击
- **可维护性**：清晰的代码结构，完善的文档和测试

**2025年技术标准**：
- 后端：Python 3.12+, FastAPI 0.104+, SQLAlchemy 2.0+ (async)
- 数据库：PostgreSQL 15+, Redis 7+
- 前端：React 18+, TypeScript 5+, Next.js 14+
- 部署：Docker, Kubernetes (可选), CI/CD with GitHub Actions

### 2.2 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         客户端层                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Web浏览器   │  │  移动浏览器   │  │    桌面应用   │          │
│  │  (React SPA) │  │ (响应式)     │  │   (未来)     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                         HTTPS/REST
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      API网关层 (可选)                            │
│  ┌────────────────────────────────────────────────────┐         │
│  │  Nginx / Caddy / Cloudflare (负载均衡 + SSL)        │         │
│  │  - Rate Limiting (30次/分钟/IP)                     │         │
│  │  - DDoS防护                                        │         │
│  │  - 静态资源CDN                                      │         │
│  └────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      应用层 (FastAPI)                            │
│                                                                  │
│  ┌───────────────────────────────────────────────────┐          │
│  │           认证与限流中间件                          │          │
│  │  - 可选认证 (Optional Authentication)              │          │
│  │  - 游客识别 (IP + 设备指纹)                         │          │
│  │  - Redis限流检查                                   │          │
│  └───────────────────────────────────────────────────┘          │
│                       │                                          │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐      │
│  │  用户API  │ 单词API  │ 收藏API  │ 查询API  │  AI API   │      │
│  │  /auth   │ /words   │/favorites│ /queries │  /ai     │      │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘      │
│                       │                                          │
│  ┌────────────────────────────────────────────────────┐         │
│  │              业务逻辑层 (Services)                   │         │
│  │  - AuthService (认证服务)                           │         │
│  │  - RateLimitService (限流服务) ⭐ 新增               │         │
│  │  - WordService (单词服务)                           │         │
│  │  - FavoriteService (收藏服务)                       │         │
│  │  - AIService (AI生成服务)                           │         │
│  │  - EmailService (邮件服务)                          │         │
│  └────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                       数据层                                     │
│                                                                  │
│  ┌──────────────────────┐      ┌──────────────────────┐        │
│  │   PostgreSQL 15+     │      │     Redis 7+         │        │
│  │  ─────────────────   │      │  ─────────────────   │        │
│  │  - users             │      │  - 限流计数器         │        │
│  │  - words             │      │  - 会话缓存          │        │
│  │  - favorites         │      │  - 单词缓存          │        │
│  │  - query_logs        │      │  - IP限流            │        │
│  │  - guest_sessions ⭐ │      └──────────────────────┘        │
│  └──────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    外部服务层                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  OpenAI API  │  │  SendGrid    │  │  Sentry监控  │         │
│  │  (AI生成)    │  │  (邮件服务)  │  │  (错误追踪)  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 技术栈总览

| 层级 | 技术选型 | 版本要求 | 说明 |
|------|---------|---------|------|
| **前端** | Next.js | 14+ | React SSR/SSG框架 |
| | React | 18+ | UI框架 |
| | TypeScript | 5+ | 类型安全 |
| | Tailwind CSS | 3+ | 样式框架 |
| | Zustand/Jotai | - | 轻量状态管理 |
| **后端** | FastAPI | 0.104+ | 现代Python Web框架 |
| | Python | 3.12+ | 编程语言 |
| | SQLAlchemy | 2.0+ | ORM (async模式) |
| | Pydantic | 2.0+ | 数据验证 |
| | asyncpg | - | PostgreSQL异步驱动 |
| | redis-py | 5.0+ | Redis客户端 (async支持) |
| **数据库** | PostgreSQL | 15+ | 关系数据库 |
| | Redis | 7+ | 缓存和限流 |
| **认证** | JWT | - | 无状态认证 |
| | bcrypt | - | 密码加密 |
| **部署** | Docker | 24+ | 容器化 |
| | Docker Compose | 2.0+ | 本地开发 |
| | GitHub Actions | - | CI/CD |
| | Vercel | - | 前端托管 (可选) |
| | Railway/Render | - | 后端托管 (可选) |

---

## 3. 游客模式技术架构 (v1.1核心特性)

### 3.1 设计理念

**从"限制体验"到"自由体验"**：

PRD v1.1的核心变更是将游客查询次数从1次/天提升到10次/天，采用"渐进式引导"而非"强制弹窗"。技术架构必须支持：

1. **可选认证** (Optional Authentication)
2. **精准的游客识别** (IP + 设备指纹)
3. **高性能限流** (Redis计数器)
4. **防滥用机制** (多层防护)

### 3.2 可选认证架构

#### 3.2.1 认证流程设计

```python
# 传统强制认证（v1.0）
@router.get("/words/query/{word}")
async def query_word(
    word: str,
    current_user: User = Depends(get_current_active_user),  # 必须登录
    db: AsyncSession = Depends(get_db),
):
    # 只有登录用户可以访问
    pass

# 可选认证（v1.1）⭐
@router.get("/words/query/{word}")
async def query_word(
    word: str,
    request: Request,
    user_or_guest: Union[User, GuestIdentifier] = Depends(get_user_or_guest),  # 可选
    db: AsyncSession = Depends(get_db),
):
    # 游客和登录用户都可以访问
    if isinstance(user_or_guest, User):
        # 注册用户逻辑
        pass
    else:
        # 游客逻辑
        pass
```

#### 3.2.2 依赖注入改造

**新增依赖注入函数**：

```python
# app/core/dependencies.py (新增)

from typing import Union, Optional
from fastapi import Request, Depends, HTTPException
from app.models import User
from app.schemas.guest import GuestIdentifier

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    可选认证：返回User或None

    Args:
        credentials: JWT认证凭证（可选）
        db: 数据库会话

    Returns:
        User对象（已登录）或None（游客）
    """
    if credentials is None:
        return None  # 游客模式

    # 有token，进行认证（复用现有get_current_user逻辑）
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        # Token无效，降级为游客
        logger.warning("Invalid token, fallback to guest mode")
        return None


async def get_user_or_guest(
    request: Request,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> Union[User, GuestIdentifier]:
    """
    统一用户和游客处理

    Args:
        request: HTTP请求对象（用于提取IP、User-Agent）
        user: 可选的User对象
        db: 数据库会话

    Returns:
        User对象（已登录）或GuestIdentifier对象（游客）
    """
    if user is not None:
        return user

    # 游客识别
    guest_identifier = await identify_guest(request, db)
    return guest_identifier
```

### 3.3 游客识别机制

#### 3.3.1 识别策略（多层识别）

**Phase 1 (MVP)：IP地址识别**

```python
# app/services/guest_identifier.py

import hashlib
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class GuestIdentifierService:
    """游客识别服务"""

    @staticmethod
    def get_client_ip(request: Request) -> str:
        """
        获取客户端真实IP

        优先级：
        1. X-Forwarded-For (代理/CDN场景)
        2. X-Real-IP (Nginx代理)
        3. request.client.host (直连)
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # X-Forwarded-For可能包含多个IP，取第一个
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host

    @staticmethod
    def generate_guest_id(ip: str, user_agent: str) -> str:
        """
        生成游客唯一标识

        Phase 1: IP + User-Agent Hash
        """
        combined = f"{ip}:{user_agent}"
        return hashlib.sha256(combined.encode()).hexdigest()

    async def identify_guest(
        self,
        request: Request,
        db: AsyncSession
    ) -> GuestIdentifier:
        """
        识别游客并返回标识对象
        """
        ip = self.get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "unknown")

        guest_id = self.generate_guest_id(ip, user_agent)

        # 查询或创建游客会话
        result = await db.execute(
            select(GuestSession).where(GuestSession.guest_id == guest_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            # 创建新游客会话
            session = GuestSession(
                guest_id=guest_id,
                ip_address=ip,
                user_agent_hash=hashlib.md5(user_agent.encode()).hexdigest(),
                last_query_date=datetime.utcnow(),
                query_count=0,
            )
            db.add(session)
            await db.commit()

        return GuestIdentifier(
            guest_id=guest_id,
            ip_address=ip,
            session=session,
        )
```

**Phase 2 (增强)：设备指纹识别**

```python
# 前端收集设备信息
// app/lib/fingerprint.ts

export interface DeviceFingerprint {
  screen: string;          // 屏幕分辨率
  timezone: string;        // 时区
  language: string;        // 语言
  platform: string;        // 平台
  canvas: string;          // Canvas指纹
  webgl: string;           // WebGL指纹
}

export function generateFingerprint(): DeviceFingerprint {
  return {
    screen: `${screen.width}x${screen.height}x${screen.colorDepth}`,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    language: navigator.language,
    platform: navigator.platform,
    canvas: getCanvasFingerprint(),
    webgl: getWebGLFingerprint(),
  };
}

function getCanvasFingerprint(): string {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  // Canvas绘制特定图案并生成hash
  // ...
  return hash;
}

// 后端验证设备指纹
# app/services/guest_identifier.py (Phase 2增强)

@staticmethod
def generate_guest_id_v2(
    ip: str,
    user_agent: str,
    fingerprint: Optional[dict]
) -> str:
    """
    Phase 2: IP + User-Agent + 设备指纹
    """
    components = [ip, user_agent]

    if fingerprint:
        components.extend([
            fingerprint.get("screen", ""),
            fingerprint.get("timezone", ""),
            fingerprint.get("canvas", ""),
            fingerprint.get("webgl", ""),
        ])

    combined = ":".join(components)
    return hashlib.sha256(combined.encode()).hexdigest()
```

#### 3.3.2 识别准确性评估

| 识别方案 | 准确率 | 误判风险 | 实施复杂度 | 推荐阶段 |
|---------|--------|---------|-----------|---------|
| **IP地址** | 70% | 同一网络多用户共享IP | 低 | MVP |
| **IP + User-Agent** | 85% | 相同设备不同浏览器识别为不同游客 | 低 | MVP |
| **IP + 设备指纹** | 95%+ | 隐私模式/VPN仍可能绕过 | 中 | Phase 2 |

**MVP推荐方案**：IP + User-Agent Hash

**理由**：
1. 实现简单，无需前端支持
2. 85%准确率满足初期需求
3. 可平滑升级到设备指纹方案

### 3.4 Redis限流架构

#### 3.4.1 限流键设计

```
限流键命名规范：
rate_limit:{scope}:{identifier}:{time_window}

示例：
- rate_limit:ip:192.168.1.100:minute           # IP分钟级限流
- rate_limit:guest:abc123def:2025-10-16        # 游客日限额
- rate_limit:user:123:2025-10-16              # 用户日限额
```

**完整键结构**：

```python
# app/core/redis_keys.py

class RedisKeys:
    """Redis键命名规范"""

    # IP限流（防爬虫）
    IP_RATE_LIMIT_MINUTE = "rate_limit:ip:{ip}:minute"      # TTL: 60s
    IP_RATE_LIMIT_HOUR = "rate_limit:ip:{ip}:hour"          # TTL: 3600s

    # 游客日限额
    GUEST_DAILY_LIMIT = "query_limit:guest:{guest_id}:{date}"  # TTL: 24h

    # 用户日限额
    USER_DAILY_LIMIT = "query_limit:user:{user_id}:{date}"     # TTL: 24h

    # 已查询单词集合（用于"重复查询不计次数"）
    GUEST_QUERIED_WORDS = "queried_words:guest:{guest_id}:{date}"  # TTL: 24h
    USER_QUERIED_WORDS = "queried_words:user:{user_id}:{date}"     # TTL: 24h

    # 单词缓存
    WORD_CACHE = "word:cache:{word}"                          # TTL: 7天

    @classmethod
    def get_guest_daily_limit_key(cls, guest_id: str, date: str) -> str:
        return cls.GUEST_DAILY_LIMIT.format(guest_id=guest_id, date=date)

    @classmethod
    def get_user_daily_limit_key(cls, user_id: int, date: str) -> str:
        return cls.USER_DAILY_LIMIT.format(user_id=user_id, date=date)
```

#### 3.4.2 限流服务实现

```python
# app/services/rate_limit.py

from typing import Tuple, Optional
from datetime import date, timedelta
from fastapi import HTTPException, status
from redis.asyncio import Redis
from app.core.config import settings
from app.core.redis_keys import RedisKeys
from app.models import User
from app.schemas.guest import GuestIdentifier

class RateLimitService:
    """查询限流服务"""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def check_query_limit(
        self,
        user_or_guest: Union[User, GuestIdentifier],
        word_id: int,
    ) -> Tuple[bool, int, int, str]:
        """
        检查查询限制

        Args:
            user_or_guest: User对象或GuestIdentifier对象
            word_id: 要查询的单词ID

        Returns:
            (是否允许查询, 已用次数, 总限额, 用户类型)

        Raises:
            HTTPException: 429 查询次数用尽
        """
        if isinstance(user_or_guest, User):
            return await self._check_user_limit(user_or_guest, word_id)
        else:
            return await self._check_guest_limit(user_or_guest, word_id)

    async def _check_guest_limit(
        self,
        guest: GuestIdentifier,
        word_id: int
    ) -> Tuple[bool, int, int, str]:
        """
        游客限流（10次/天）

        核心逻辑：
        1. 检查单词是否已查询过（已查询不计次数）
        2. 检查今日查询次数是否达到限制
        3. 记录查询并更新计数器
        """
        today = date.today().isoformat()
        guest_id = guest.guest_id

        # 检查单词是否已查询过
        queried_words_key = RedisKeys.get_guest_queried_words_key(guest_id, today)
        is_already_queried = await self.redis.sismember(
            queried_words_key,
            str(word_id)
        )

        if is_already_queried:
            # 已查询过，不计次数，直接返回
            used = await self._get_guest_used_queries(guest_id, today)
            return (True, used, settings.guest_daily_limit, "guest")

        # 首次查询，检查限额
        limit_key = RedisKeys.get_guest_daily_limit_key(guest_id, today)
        used_queries = await self.redis.get(limit_key)
        used_queries = int(used_queries) if used_queries else 0

        if used_queries >= settings.guest_daily_limit:
            # 超出限额
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "QUERY_LIMIT_EXCEEDED",
                    "message": f"游客今日查询次数已用完（{settings.guest_daily_limit}次/天）",
                    "used_queries": used_queries,
                    "total_limit": settings.guest_daily_limit,
                    "user_type": "guest",
                    "upgrade_message": "注册可获得每日50次查询",
                },
            )

        # 记录查询
        async with self.redis.pipeline(transaction=True) as pipe:
            # 增加计数
            pipe.incr(limit_key)
            pipe.expire(limit_key, 86400)  # 24小时过期

            # 添加到已查询集合
            pipe.sadd(queried_words_key, str(word_id))
            pipe.expire(queried_words_key, 86400)

            await pipe.execute()

        return (True, used_queries + 1, settings.guest_daily_limit, "guest")

    async def _check_user_limit(
        self,
        user: User,
        word_id: int
    ) -> Tuple[bool, int, int, str]:
        """
        注册用户限流（50次/天 或 无限）

        逻辑与游客类似，但限额不同
        """
        # Premium用户无限制
        if user.membership_tier == "premium":
            return (True, 0, -1, "premium")

        # 免费用户：50次/天
        today = date.today().isoformat()
        user_id = user.id

        # 检查单词是否已查询过
        queried_words_key = RedisKeys.get_user_queried_words_key(user_id, today)
        is_already_queried = await self.redis.sismember(
            queried_words_key,
            str(word_id)
        )

        if is_already_queried:
            used = await self._get_user_used_queries(user_id, today)
            return (True, used, settings.free_user_daily_limit, "free")

        # 首次查询，检查限额
        limit_key = RedisKeys.get_user_daily_limit_key(user_id, today)
        used_queries = await self.redis.get(limit_key)
        used_queries = int(used_queries) if used_queries else 0

        if used_queries >= settings.free_user_daily_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "QUERY_LIMIT_EXCEEDED",
                    "message": f"今日查询次数已用完（{settings.free_user_daily_limit}次/天）",
                    "used_queries": used_queries,
                    "total_limit": settings.free_user_daily_limit,
                    "user_type": "free",
                    "upgrade_message": "升级Premium可获得无限查询",
                },
            )

        # 记录查询
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.incr(limit_key)
            pipe.expire(limit_key, 86400)
            pipe.sadd(queried_words_key, str(word_id))
            pipe.expire(queried_words_key, 86400)
            await pipe.execute()

        return (True, used_queries + 1, settings.free_user_daily_limit, "free")

    async def get_remaining_queries(
        self,
        user_or_guest: Union[User, GuestIdentifier]
    ) -> Tuple[int, int, int]:
        """
        获取剩余查询次数

        Returns:
            (剩余次数, 已用次数, 总限额)
        """
        today = date.today().isoformat()

        if isinstance(user_or_guest, User):
            if user_or_guest.membership_tier == "premium":
                return (-1, 0, -1)  # 无限

            limit_key = RedisKeys.get_user_daily_limit_key(user_or_guest.id, today)
            total_limit = settings.free_user_daily_limit
        else:
            limit_key = RedisKeys.get_guest_daily_limit_key(user_or_guest.guest_id, today)
            total_limit = settings.guest_daily_limit

        used_queries = await self.redis.get(limit_key)
        used_queries = int(used_queries) if used_queries else 0
        remaining = max(0, total_limit - used_queries)

        return (remaining, used_queries, total_limit)
```

#### 3.4.3 IP限流（防爬虫）

```python
# app/middleware/ip_rate_limit.py

from fastapi import Request, HTTPException, status
from redis.asyncio import Redis
from app.core.redis_keys import RedisKeys
from app.core.config import settings

class IPRateLimitMiddleware:
    """IP级别限流中间件（防爬虫/DDoS）"""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def check_ip_rate_limit(self, request: Request):
        """
        检查IP限流

        限制：30次/分钟/IP
        """
        # 获取客户端IP
        ip = self._get_client_ip(request)

        # 检查分钟级限流
        minute_key = RedisKeys.IP_RATE_LIMIT_MINUTE.format(ip=ip)

        # 使用Redis INCR实现原子计数
        count = await self.redis.incr(minute_key)

        if count == 1:
            # 首次请求，设置过期时间
            await self.redis.expire(minute_key, 60)

        if count > settings.rate_limit_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "IP_RATE_LIMIT_EXCEEDED",
                    "message": f"请求过于频繁，请稍后再试（限制：{settings.rate_limit_per_minute}次/分钟）",
                },
            )

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """获取客户端真实IP"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host
```

### 3.5 数据模型设计

#### 3.5.1 游客会话表 (guest_sessions)

```python
# app/models/guest.py

from sqlalchemy import String, Integer, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base

class GuestSession(Base):
    """
    游客会话表

    存储游客标识和查询统计（仅用于备份/分析，限流使用Redis）
    """
    __tablename__ = "guest_sessions"

    # 主键：游客唯一标识（SHA256 hash）
    guest_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="游客唯一标识（IP+UA hash）"
    )

    # 识别信息
    ip_address: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
        comment="IP地址（IPv4/IPv6）"
    )
    user_agent_hash: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="User-Agent MD5 hash"
    )

    # 统计信息（从Redis同步，用于数据分析）
    total_queries: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="总查询次数"
    )
    last_query_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后查询时间"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )

    # 索引
    __table_args__ = (
        Index("idx_guest_ip", "ip_address"),
        Index("idx_guest_last_query", "last_query_date"),
        Index("idx_guest_created", "created_at"),
    )
```

**注意**：
- 游客的实时限流数据存储在Redis中（高性能）
- PostgreSQL的guest_sessions表仅用于：
  - 长期数据分析（转化率、使用模式）
  - Redis故障时的降级方案
  - 定期清理过期游客数据（90天未活跃）

#### 3.5.2 查询日志表更新 (query_logs)

```python
# app/models/query_log.py (更新)

class QueryLog(Base):
    """
    查询日志表

    记录用户和游客的查询历史（用于复习提醒和数据分析）
    """
    __tablename__ = "query_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # 外键：用户或游客（二选一）
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    guest_session_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("guest_sessions.guest_id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # 查询信息
    word_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("words.id", ondelete="CASCADE"),
        nullable=False
    )
    query_date: Mapped[date] = mapped_column(Date, nullable=False)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    # 约束：确保要么是用户查询，要么是游客查询
    __table_args__ = (
        CheckConstraint(
            "(user_id IS NOT NULL AND guest_session_id IS NULL) OR "
            "(user_id IS NULL AND guest_session_id IS NOT NULL)",
            name="check_query_log_owner",
        ),
        Index("idx_query_logs_user_date", "user_id", "query_date"),
        Index("idx_query_logs_guest_date", "guest_session_id", "query_date"),
    )
```

#### 3.5.3 用户表更新 (users)

```python
# app/models/user.py (更新membership_tier检查约束)

class User(Base):
    """用户表"""
    __tablename__ = "users"

    # ... 其他字段保持不变 ...

    membership_tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="free",
        comment="会员等级：free | premium"
    )

    __table_args__ = (
        CheckConstraint(
            "membership_tier IN ('free', 'premium')",
            name="check_membership_tier",
        ),
    )
```

### 3.6 配置更新

```python
# app/core/config.py (更新)

class Settings(BaseSettings):
    # ... 现有配置 ...

    # 查询限制配置（更新为v1.1规格）
    guest_daily_limit: int = Field(
        default=10,
        description="游客每日查询限制"
    )
    free_user_daily_limit: int = Field(
        default=50,
        description="免费用户每日查询限制"
    )
    premium_user_daily_limit: int = Field(
        default=-1,
        description="Premium用户查询限制（-1=无限）"
    )

    # IP限流配置
    rate_limit_per_minute: int = Field(
        default=30,
        description="IP每分钟请求限制（防爬虫）"
    )

    # Redis配置
    redis_host: str = Field(
        default="localhost",
        env="REDIS_HOST"
    )
    redis_port: int = Field(
        default=6379,
        env="REDIS_PORT"
    )
    redis_db: int = Field(
        default=0,
        env="REDIS_DB"
    )
    redis_password: Optional[str] = Field(
        default=None,
        env="REDIS_PASSWORD"
    )

    @property
    def redis_url(self) -> str:
        """生成Redis连接URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
```

### 3.7 API响应格式设计

#### 3.7.1 单词查询响应（统一格式）

```python
# app/schemas/word.py (更新)

from pydantic import BaseModel, Field
from typing import Optional

class WordQueryResponse(BaseModel):
    """单词查询响应"""

    # 单词数据
    id: int
    word: str
    phonetic: Optional[str]
    part_of_speech: Optional[str]
    core_game: str
    scenario_formal: str
    scenario_casual: str
    etymology_breakdown: str
    etymology_story: Optional[str]
    common_mistakes: str
    memory_trick: str
    is_golden: bool

    # 查询限制信息 ⭐ 新增
    remaining_queries: int = Field(
        description="剩余查询次数（-1表示无限）"
    )
    total_queries: int = Field(
        description="总查询限额（-1表示无限）"
    )
    user_type: str = Field(
        description="用户类型：guest | free | premium"
    )

    # 引导信息 ⭐ 新增
    upgrade_message: Optional[str] = Field(
        default=None,
        description="升级引导文案（游客/免费用户显示）"
    )

    class Config:
        from_attributes = True

# 示例响应
{
  "success": true,
  "data": {
    "id": 1,
    "word": "accountability",
    "phonetic": "/əˌkaʊntəˈbɪləti/",
    "core_game": "问责制的核心是'能算清账'...",
    "remaining_queries": 7,
    "total_queries": 10,
    "user_type": "guest",
    "upgrade_message": "注册可获得每日50次查询 + 收藏功能"
  }
}
```

### 3.8 数据库迁移脚本

```python
# alembic/versions/001_add_guest_mode_support.py

"""Add guest mode support (v1.1)

Revision ID: 001_guest_mode
Revises:
Create Date: 2025-10-16

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # 创建游客会话表
    op.create_table(
        'guest_sessions',
        sa.Column('guest_id', sa.String(64), primary_key=True),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_agent_hash', sa.String(32), nullable=False),
        sa.Column('total_queries', sa.Integer, default=0),
        sa.Column('last_query_date', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # 创建索引
    op.create_index('idx_guest_ip', 'guest_sessions', ['ip_address'])
    op.create_index('idx_guest_last_query', 'guest_sessions', ['last_query_date'])
    op.create_index('idx_guest_created', 'guest_sessions', ['created_at'])

    # 更新查询日志表，添加游客外键
    op.add_column(
        'query_logs',
        sa.Column('guest_session_id', sa.String(64), nullable=True)
    )
    op.create_foreign_key(
        'fk_query_logs_guest',
        'query_logs', 'guest_sessions',
        ['guest_session_id'], ['guest_id'],
        ondelete='CASCADE'
    )
    op.create_index('idx_query_logs_guest_date', 'query_logs', ['guest_session_id', 'query_date'])

    # 更新配置默认值（通过ALTER TABLE或应用层处理）
    # 注意：查询限制配置存储在app/core/config.py，无需数据库变更

def downgrade():
    op.drop_index('idx_query_logs_guest_date', 'query_logs')
    op.drop_constraint('fk_query_logs_guest', 'query_logs', type_='foreignkey')
    op.drop_column('query_logs', 'guest_session_id')

    op.drop_index('idx_guest_created', 'guest_sessions')
    op.drop_index('idx_guest_last_query', 'guest_sessions')
    op.drop_index('idx_guest_ip', 'guest_sessions')
    op.drop_table('guest_sessions')
```

---

## 4. 防滥用机制设计

### 4.1 多层防护架构

```
┌─────────────────────────────────────────────────────────────┐
│                    防滥用层级架构                            │
└─────────────────────────────────────────────────────────────┘

【层级1：网络层防护】
├─ Cloudflare DDoS防护
├─ Nginx/Caddy Rate Limiting (粗粒度)
└─ 地理位置封禁（可选）

【层级2：IP限流】⭐ 必须
├─ 30次/分钟/IP（正常用户不会超过）
├─ 1000次/小时/IP
└─ 异常IP自动封禁（24小时）

【层级3：游客限流】⭐ 必须
├─ 10次/天（基于IP+UA hash）
├─ 已查询单词不计次数
└─ Redis计数器 + TTL自动重置

【层级4：行为检测】⭐ 推荐
├─ 短时间内连续查询相同单词（<5秒） → 可疑
├─ 查询模式异常（按字母顺序/数字顺序） → 爬虫
└─ 触发Captcha人机验证

【层级5：业务逻辑保护】
├─ AI生成限流（避免大量消耗API费用）
├─ 数据库查询优化（防止慢查询拖垮系统）
└─ 响应限速（防止数据批量导出）
```

### 4.2 异常行为检测

```python
# app/services/abuse_detection.py

from typing import Optional, List
from datetime import datetime, timedelta
from redis.asyncio import Redis

class AbuseDetectionService:
    """滥用行为检测服务"""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def detect_suspicious_pattern(
        self,
        identifier: str,  # IP或guest_id
        word: str,
    ) -> Optional[str]:
        """
        检测可疑查询模式

        Returns:
            检测到的模式类型，或None
        """
        # 检测1：短时间内重复查询相同单词
        recent_queries_key = f"abuse:recent:{identifier}"
        recent = await self.redis.lrange(recent_queries_key, 0, 4)  # 最近5次

        if recent.count(word.encode()) >= 3:
            return "REPEATED_QUERY"

        # 记录本次查询
        await self.redis.lpush(recent_queries_key, word)
        await self.redis.ltrim(recent_queries_key, 0, 9)  # 保留最近10次
        await self.redis.expire(recent_queries_key, 300)  # 5分钟过期

        # 检测2：按字母顺序查询（爬虫特征）
        if len(recent) >= 4:
            words = [w.decode() for w in recent[:4]]
            if self._is_alphabetical_sequence(words):
                return "ALPHABETICAL_CRAWLING"

        return None

    @staticmethod
    def _is_alphabetical_sequence(words: List[str]) -> bool:
        """检测是否为字母顺序"""
        first_chars = [w[0].lower() for w in words if w]
        return first_chars == sorted(first_chars)

    async def should_trigger_captcha(self, identifier: str) -> bool:
        """
        判断是否需要触发Captcha验证

        条件：
        1. 被标记为可疑行为
        2. 短时间内大量请求
        """
        captcha_key = f"captcha:required:{identifier}"
        return bool(await self.redis.get(captcha_key))

    async def mark_as_suspicious(self, identifier: str, reason: str):
        """标记为可疑用户，要求Captcha验证"""
        captcha_key = f"captcha:required:{identifier}"
        await self.redis.setex(captcha_key, 3600, reason)  # 1小时
```

### 4.3 Captcha集成（可选）

```python
# app/services/captcha.py

import httpx
from app.core.config import settings

class CaptchaService:
    """人机验证服务（使用Google reCAPTCHA或hCaptcha）"""

    async def verify_captcha(self, token: str, ip: str) -> bool:
        """
        验证Captcha令牌

        Args:
            token: 前端生成的Captcha token
            ip: 客户端IP

        Returns:
            是否通过验证
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={
                    "secret": settings.recaptcha_secret_key,
                    "response": token,
                    "remoteip": ip,
                },
                timeout=5,
            )

            result = response.json()
            return result.get("success", False)
```

### 4.4 成本控制机制

**问题**：AI生成单词手册成本约$0.01/次，恶意刷量可能导致成本暴增。

**解决方案**：

1. **优先返回预生成手册**（0成本）
2. **AI生成限流**：每个IP/游客每天最多生成5个新单词
3. **热门单词预生成**：定期爬取高频查询单词，批量预生成
4. **成本告警**：OpenAI API费用超过$100/天时触发告警

```python
# app/services/word_generation.py

class WordGenerationService:
    """单词生成服务（AI集成）"""

    async def generate_or_fetch_word(
        self,
        word: str,
        identifier: str
    ) -> Word:
        """
        查询或生成单词

        优先级：
        1. 黄金手册（人工审核）
        2. AI生成缓存
        3. 新AI生成（检查限额）
        """
        # 1. 查询数据库
        existing = await self.db.get_word_by_text(word)
        if existing:
            return existing

        # 2. 检查AI生成限额（防止滥用）
        generation_key = f"ai:generation:{identifier}:{date.today()}"
        count = await self.redis.get(generation_key)
        if count and int(count) >= 5:
            raise HTTPException(
                status_code=429,
                detail="AI生成限额已用完（5个/天），请明日再试或注册获得更多配额"
            )

        # 3. 调用AI生成
        word_data = await self.ai_service.generate_word(word)

        # 4. 保存到数据库
        new_word = await self.db.create_word(word_data)

        # 5. 更新生成计数
        await self.redis.incr(generation_key)
        await self.redis.expire(generation_key, 86400)

        return new_word
```

---

## 5. API设计规范

### 5.1 RESTful API设计

**基础URL**：`https://api.chaiwordduck.com/v1`

**认证方式**：
- Bearer Token (JWT) - 注册用户
- 无认证 - 游客模式

**通用响应格式**：

```json
// 成功响应
{
  "success": true,
  "data": { ... },
  "message": "操作成功"  // 可选
}

// 错误响应
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": { ... }  // 可选，额外信息
  }
}
```

### 5.2 核心API端点

#### 5.2.1 单词查询 API

**GET /v1/words/query/{word}**

```
描述：查询单词详细信息（支持游客和注册用户）

请求头：
  Authorization: Bearer {token}  # 可选，游客可省略

路径参数：
  word: string  # 要查询的单词

响应示例（游客）：
{
  "success": true,
  "data": {
    "id": 1,
    "word": "accountability",
    "phonetic": "/əˌkaʊntəˈbɪləti/",
    "part_of_speech": "n.",
    "core_game": "问责制的核心是'能算清账'...",
    "scenario_formal": "In a democratic society...",
    "scenario_casual": "Boss: Who broke the printer?",
    "etymology_breakdown": "ac-count-ability",
    "etymology_story": "源自拉丁语...",
    "common_mistakes": "易错：accountibility ❌",
    "memory_trick": "账户(account) + 能力(ability)",
    "is_golden": true,
    "remaining_queries": 7,
    "total_queries": 10,
    "user_type": "guest",
    "upgrade_message": "注册可获得每日50次查询 + 收藏功能"
  }
}

错误响应：
- 404: 单词不存在
- 429: 查询次数用尽
- 429: IP请求过于频繁
```

#### 5.2.2 查询限制信息 API

**GET /v1/words/query-limit**

```
描述：获取当前用户的查询限制信息

请求头：
  Authorization: Bearer {token}  # 可选

响应示例：
{
  "success": true,
  "data": {
    "user_type": "guest",
    "remaining_queries": 7,
    "used_queries": 3,
    "total_queries": 10,
    "reset_at": "2025-10-17T00:00:00Z",
    "queried_words": [
      {"id": 1, "word": "accountability"},
      {"id": 5, "word": "entrepreneurship"},
      {"id": 12, "word": "infrastructure"}
    ]
  }
}
```

#### 5.2.3 游客转化API（新增）

**POST /v1/auth/convert-guest**

```
描述：将游客数据迁移到注册用户

请求体：
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "guest_id": "abc123def456..."  # 前端保存的游客标识
}

响应：
{
  "success": true,
  "data": {
    "user": { ... },
    "access_token": "jwt_token",
    "migrated_data": {
      "query_logs": 3,  # 迁移的查询记录数
      "message": "您的查询历史已成功保留"
    }
  }
}

说明：
- 将游客的查询历史迁移到新注册用户
- 游客会话数据保留30天后自动清理
```

### 5.3 错误码规范

```python
# app/schemas/common.py

class ErrorCode:
    """统一错误码"""

    # 认证错误 (401)
    UNAUTHORIZED = "UNAUTHORIZED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"

    # 权限错误 (403)
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

    # 资源错误 (404)
    WORD_NOT_FOUND = "WORD_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"

    # 业务逻辑错误 (400)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    QUERY_LIMIT_EXCEEDED = "QUERY_LIMIT_EXCEEDED"
    FAVORITE_LIMIT_EXCEEDED = "FAVORITE_LIMIT_EXCEEDED"

    # 限流错误 (429)
    IP_RATE_LIMIT_EXCEEDED = "IP_RATE_LIMIT_EXCEEDED"
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"

    # 服务错误 (500)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
```

---

## 6. 前端架构设计

### 6.1 技术栈

| 技术 | 用途 | 备注 |
|------|------|------|
| Next.js 14+ | React SSR/SSG框架 | App Router模式 |
| React 18+ | UI框架 | Server Components + Client Components |
| TypeScript 5+ | 类型安全 | 严格模式 |
| Tailwind CSS 3+ | 样式框架 | 响应式设计 |
| Zustand/Jotai | 状态管理 | 轻量级，无需Redux |
| React Query | 服务端状态管理 | 缓存、自动重新获取 |
| Axios | HTTP客户端 | 拦截器支持 |

### 6.2 游客模式前端实现

#### 6.2.1 游客识别（前端）

```typescript
// app/lib/guest-identifier.ts

import { v4 as uuidv4 } from 'uuid';

export interface GuestIdentifier {
  guestId: string;
  createdAt: string;
}

export class GuestIdentifierManager {
  private static STORAGE_KEY = 'chaiword_guest_id';

  /**
   * 获取或创建游客标识
   */
  static getOrCreateGuestId(): GuestIdentifier {
    // 优先从 localStorage 读取
    const stored = localStorage.getItem(this.STORAGE_KEY);
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch (e) {
        // 解析失败，重新生成
      }
    }

    // 生成新的游客ID
    const guestId: GuestIdentifier = {
      guestId: uuidv4(),
      createdAt: new Date().toISOString(),
    };

    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(guestId));
    return guestId;
  }

  /**
   * 清除游客标识（用户注册后调用）
   */
  static clearGuestId(): void {
    localStorage.removeItem(this.STORAGE_KEY);
  }
}
```

#### 6.2.2 查询次数管理

```typescript
// app/hooks/useQueryLimit.ts

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

export interface QueryLimitInfo {
  userType: 'guest' | 'free' | 'premium';
  remainingQueries: number;
  usedQueries: number;
  totalQueries: number;
  resetAt: string;
}

export function useQueryLimit() {
  return useQuery({
    queryKey: ['queryLimit'],
    queryFn: async () => {
      const response = await apiClient.get<QueryLimitInfo>('/words/query-limit');
      return response.data;
    },
    staleTime: 60000, // 1分钟内不重新请求
    refetchOnWindowFocus: true, // 窗口获得焦点时刷新
  });
}
```

#### 6.2.3 渐进式引导组件

```typescript
// app/components/GuestGuidance.tsx

import { useQueryLimit } from '@/hooks/useQueryLimit';
import { useAuth } from '@/hooks/useAuth';

export function GuestGuidance() {
  const { data: limitInfo } = useQueryLimit();
  const { isAuthenticated } = useAuth();

  // 已登录用户不显示引导
  if (isAuthenticated) return null;

  // 游客引导逻辑（根据PRD v1.1四阶段设计）
  const { usedQueries, totalQueries } = limitInfo || {};

  // 阶段1：初次体验（1-3次）- 小字提示
  if (usedQueries >= 1 && usedQueries <= 3) {
    return (
      <div className="text-xs text-gray-500 mt-4 text-center">
        💡 注册后可收藏单词、查看学习历史
      </div>
    );
  }

  // 阶段2：产生粘性（4-7次）- 收藏按钮引导（在WordCard组件中处理）

  // 阶段3：接近限制（8-10次）- 顶部提示
  if (usedQueries >= 8 && usedQueries < totalQueries) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
        <p className="text-sm text-yellow-800">
          ⚠️ 今日剩余查询次数：{totalQueries - usedQueries}/{totalQueries}
        </p>
        <p className="text-xs text-yellow-600 mt-1">
          注册可获得每日50次查询 + 无限收藏
        </p>
        <button className="mt-2 text-sm text-yellow-700 underline">
          立即注册
        </button>
      </div>
    );
  }

  // 阶段4：达到限制（10次后）- 全屏引导（在QueryPage中处理）

  return null;
}
```

#### 6.2.4 查询限制达到时的引导页面

```typescript
// app/components/QueryLimitReached.tsx

export function QueryLimitReached() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
        <div className="text-center">
          {/* 插图 */}
          <div className="mb-6">
            <img src="/duck-thinking.svg" alt="鸭子思考" className="w-32 h-32 mx-auto" />
          </div>

          {/* 标题 */}
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            今日免费查询已用完
          </h2>
          <p className="text-gray-600 mb-6">
            您今天已经查询了10个单词啦！
          </p>

          {/* 价值对比表 */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 mb-6">
            <h3 className="font-semibold text-gray-900 mb-3">注册后可获得：</h3>
            <ul className="space-y-2 text-left">
              <li className="flex items-center text-sm">
                <span className="text-green-500 mr-2">✓</span>
                每日50次查询（5倍提升）
              </li>
              <li className="flex items-center text-sm">
                <span className="text-green-500 mr-2">✓</span>
                收藏单词功能（最多50个）
              </li>
              <li className="flex items-center text-sm">
                <span className="text-green-500 mr-2">✓</span>
                完整学习历史记录
              </li>
              <li className="flex items-center text-sm">
                <span className="text-green-500 mr-2">✓</span>
                定期复习提醒邮件
              </li>
            </ul>
          </div>

          {/* 行动按钮 */}
          <div className="space-y-3">
            <button className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700">
              立即注册（免费）
            </button>
            <button className="w-full bg-gray-100 text-gray-700 py-3 rounded-lg font-semibold hover:bg-gray-200">
              明天再来
            </button>
          </div>

          {/* 小字说明 */}
          <p className="text-xs text-gray-500 mt-4">
            注册仅需邮箱，30秒完成
          </p>
        </div>
      </div>
    </div>
  );
}
```

### 6.3 前端路由设计

```
/                          # 首页（搜索框）
/word/[word]               # 单词详情页（五步手册）
/word/[id]                 # 单词详情页（通过ID访问，不计次数）
/auth/login                # 登录页
/auth/register             # 注册页
/auth/forgot-password      # 忘记密码
/dashboard                 # 用户Dashboard
/favorites                 # 我的收藏
/history                   # 查询历史
/settings                  # 设置
/upgrade                   # 升级Premium页面
```

---

## 7. 部署架构设计

### 7.1 Docker Compose部署（开发/测试环境）

```yaml
# docker-compose.yml

version: '3.9'

services:
  # 后端服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/chaiword_duck
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000/v1
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev

  # PostgreSQL数据库
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=chaiword_duck
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 7.2 生产环境部署（Kubernetes）

```yaml
# k8s/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: chaiword-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chaiword-backend
  template:
    metadata:
      labels:
        app: chaiword-backend
    spec:
      containers:
      - name: backend
        image: ghcr.io/chaiword/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: chaiword-secrets
              key: database-url
        - name: REDIS_HOST
          value: "redis-service"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: chaiword-backend-service
spec:
  selector:
    app: chaiword-backend
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 7.3 CI/CD流程（GitHub Actions）

```yaml
# .github/workflows/deploy.yml

name: Deploy to Production

on:
  push:
    branches:
      - main

jobs:
  backend-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest tests/ --cov=app --cov-report=xml

      - name: Build Docker image
        run: |
          docker build -t ghcr.io/chaiword/backend:${{ github.sha }} ./backend
          docker tag ghcr.io/chaiword/backend:${{ github.sha }} ghcr.io/chaiword/backend:latest

      - name: Push to GitHub Container Registry
        run: |
          echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker push ghcr.io/chaiword/backend:${{ github.sha }}
          docker push ghcr.io/chaiword/backend:latest

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/chaiword-backend backend=ghcr.io/chaiword/backend:${{ github.sha }}
          kubectl rollout status deployment/chaiword-backend

  frontend-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

---

## 8. 技术风险评估与缓解

### 8.1 高风险问题

#### 风险1：Redis故障导致限流失效

**影响**：所有用户无法查询单词，或限流失效导致滥用

**可能性**：中（Redis单点故障）

**缓解措施**：
1. **降级方案**：Redis不可用时降级到PostgreSQL限流
   ```python
   async def check_query_limit_with_fallback(...):
       try:
           return await redis_rate_limit_service.check(...)
       except RedisConnectionError:
           logger.error("Redis unavailable, fallback to PostgreSQL")
           return await postgres_rate_limit_service.check(...)
   ```

2. **Redis高可用**：使用Redis Sentinel或Redis Cluster
3. **监控告警**：Redis连接失败立即告警

#### 风险2：IP识别不准确（NAT/代理）

**影响**：同一网络多用户共享限额，或恶意用户频繁切换IP绕过限制

**可能性**：高（校园网、公司网络常见）

**缓解措施**：
1. **Phase 1（MVP）**：接受误判，10次限额足够大部分场景
2. **Phase 2**：引入设备指纹识别（Canvas + WebGL）
3. **Phase 3**：用户反馈机制（"限额异常？点击申诉"）

#### 风险3：恶意用户频繁切换IP/浏览器

**影响**：绕过限流，大量消耗AI生成配额

**可能性**：中（需要一定技术能力）

**缓解措施**：
1. **行为检测**：识别爬虫模式（字母顺序查询、高频重复）
2. **Captcha验证**：可疑行为触发人机验证
3. **AI生成限额**：单独限制AI生成次数（5次/天/IP）
4. **成本告警**：OpenAI费用异常增长时自动暂停AI生成

#### 风险4：高并发下Redis压力过大

**影响**：限流响应变慢，甚至超时

**可能性**：低（需要1万+并发）

**缓解措施**：
1. **Redis优化**：使用Pipeline批量操作
2. **连接池**：合理配置Redis连接池大小
3. **分片**：Redis Cluster按用户ID/guest_id分片
4. **本地缓存**：Nginx层缓存静态响应（如"已用完"状态）

### 8.2 中风险问题

#### 风险5：PostgreSQL查询性能瓶颈

**影响**：查询日志写入慢，影响用户体验

**可能性**：中（高并发场景）

**缓解措施**：
1. **异步写入**：查询日志通过消息队列异步写入
2. **批量插入**：累积100条或10秒后批量写入
3. **索引优化**：确保(user_id, query_date)和(guest_id, query_date)有复合索引
4. **分区表**：按月分区query_logs表（可选）

#### 风险6：第三方服务故障（OpenAI API）

**影响**：新单词无法生成，用户体验受损

**可能性**：低（OpenAI稳定性较高）

**缓解措施**：
1. **预生成机制**：高频单词提前生成
2. **备用模型**：OpenAI不可用时切换到国产模型（文心一言、通义千问）
3. **优雅降级**：显示"AI生成服务暂时不可用，请稍后再试"

### 8.3 低风险问题

#### 风险7：前端localStorage被清除

**影响**：游客ID丢失，查询次数重置（用户可能获得额外免费次数）

**可能性**：中（用户主动清除或隐私模式）

**缓解措施**：
1. **接受风险**：游客获得额外次数对产品影响小
2. **多重识别**：配合Cookie、设备指纹
3. **服务端验证**：最终限流以服务端Redis为准

---

## 9. 测试策略

### 9.1 测试层级

```
┌─────────────────────────────────────────────────────────┐
│                    测试金字塔                            │
└─────────────────────────────────────────────────────────┘

                      E2E测试
                    (Playwright)
                  ┌──────────────┐
                  │  关键流程     │  覆盖率目标：100%
                  │  10个测试用例 │
                  └──────────────┘
                        ▲
                        │
              ┌─────────────────────┐
              │    集成测试 (Pytest)  │
              │  API + DB + Redis   │  覆盖率目标：≥90%
              │    50个测试用例      │
              └─────────────────────┘
                        ▲
                        │
        ┌───────────────────────────────────┐
        │       单元测试 (Pytest + Jest)     │
        │   业务逻辑 + 工具函数             │  覆盖率目标：≥95%
        │         200个测试用例             │
        └───────────────────────────────────┘
```

### 9.2 游客模式测试用例

#### 9.2.1 单元测试

```python
# backend/tests/unit/test_rate_limit_service.py

import pytest
from datetime import date
from app.services.rate_limit import RateLimitService

@pytest.mark.asyncio
class TestRateLimitService:
    """限流服务单元测试"""

    async def test_guest_first_query_success(self, redis_mock, guest_identifier):
        """测试：游客首次查询成功"""
        service = RateLimitService(redis_mock)

        allowed, used, total, user_type = await service.check_query_limit(
            guest_identifier, word_id=1
        )

        assert allowed is True
        assert used == 1
        assert total == 10
        assert user_type == "guest"

    async def test_guest_repeated_query_not_counted(self, redis_mock, guest_identifier):
        """测试：游客重复查询不计次数"""
        service = RateLimitService(redis_mock)

        # 第一次查询
        await service.check_query_limit(guest_identifier, word_id=1)

        # 第二次查询同一单词
        allowed, used, total, _ = await service.check_query_limit(
            guest_identifier, word_id=1
        )

        assert allowed is True
        assert used == 1  # 次数不增加

    async def test_guest_limit_exceeded(self, redis_mock, guest_identifier):
        """测试：游客超出限额"""
        service = RateLimitService(redis_mock)

        # 查询10个不同单词
        for i in range(1, 11):
            await service.check_query_limit(guest_identifier, word_id=i)

        # 第11次查询应失败
        with pytest.raises(HTTPException) as exc:
            await service.check_query_limit(guest_identifier, word_id=11)

        assert exc.value.status_code == 429
        assert "QUERY_LIMIT_EXCEEDED" in str(exc.value.detail)
```

#### 9.2.2 集成测试

```python
# backend/tests/integration/test_guest_mode.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestGuestMode:
    """游客模式集成测试"""

    async def test_guest_query_word_without_auth(self, client: AsyncClient):
        """测试：游客无需认证即可查询单词"""
        response = await client.get("/v1/words/query/accountability")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["word"] == "accountability"
        assert data["user_type"] == "guest"
        assert data["remaining_queries"] == 9

    async def test_guest_query_limit_enforcement(self, client: AsyncClient):
        """测试：游客查询次数限制强制执行"""
        # 查询10次
        for i in range(10):
            response = await client.get(f"/v1/words/query/test{i}")
            assert response.status_code == 200

        # 第11次应失败
        response = await client.get("/v1/words/query/test11")
        assert response.status_code == 429
        assert "QUERY_LIMIT_EXCEEDED" in response.json()["error"]["code"]

    async def test_guest_to_user_migration(self, client: AsyncClient):
        """测试：游客转注册用户后数据迁移"""
        # 1. 游客查询3个单词
        await client.get("/v1/words/query/word1")
        await client.get("/v1/words/query/word2")
        await client.get("/v1/words/query/word3")

        # 2. 注册账号
        response = await client.post("/v1/auth/register", json={
            "email": "test@example.com",
            "password": "SecurePass123"
        })
        assert response.status_code == 201
        token = response.json()["data"]["access_token"]

        # 3. 验证查询历史已迁移
        response = await client.get(
            "/v1/words/query-limit",
            headers={"Authorization": f"Bearer {token}"}
        )
        data = response.json()["data"]
        assert data["used_queries"] == 3
        assert len(data["queried_words"]) == 3
```

#### 9.2.3 E2E测试

```typescript
// frontend/tests/e2e/guest-mode.spec.ts

import { test, expect } from '@playwright/test';

test.describe('游客模式', () => {
  test('游客可以无需登录查询单词', async ({ page }) => {
    // 访问首页
    await page.goto('/');

    // 输入单词并搜索
    await page.fill('[data-testid="search-input"]', 'accountability');
    await page.click('[data-testid="search-button"]');

    // 验证跳转到单词详情页
    await expect(page).toHaveURL(/\/word\/accountability/);

    // 验证五步手册展示
    await expect(page.locator('[data-testid="core-game"]')).toBeVisible();
    await expect(page.locator('[data-testid="scenarios"]')).toBeVisible();

    // 验证剩余次数显示
    await expect(page.locator('text=/剩余.*9\/10/')).toBeVisible();
  });

  test('游客查询10次后显示引导注册', async ({ page }) => {
    await page.goto('/');

    // 查询10个不同单词
    for (let i = 1; i <= 10; i++) {
      await page.fill('[data-testid="search-input"]', `test${i}`);
      await page.click('[data-testid="search-button"]');
      await page.waitForLoadState('networkidle');
    }

    // 尝试查询第11个单词
    await page.fill('[data-testid="search-input"]', 'test11');
    await page.click('[data-testid="search-button"]');

    // 验证显示注册引导页面
    await expect(page.locator('text=/今日免费查询已用完/')).toBeVisible();
    await expect(page.locator('[data-testid="register-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="tomorrow-button"]')).toBeVisible();
  });

  test('游客重复查询同一单词不消耗次数', async ({ page }) => {
    await page.goto('/');

    // 第一次查询
    await page.fill('[data-testid="search-input"]', 'accountability');
    await page.click('[data-testid="search-button"]');
    await expect(page.locator('text=/剩余.*9\/10/')).toBeVisible();

    // 返回首页
    await page.click('[data-testid="logo"]');

    // 第二次查询同一单词
    await page.fill('[data-testid="search-input"]', 'accountability');
    await page.click('[data-testid="search-button"]');

    // 验证次数未减少
    await expect(page.locator('text=/剩余.*9\/10/')).toBeVisible();
  });
});
```

### 9.3 性能测试

```python
# backend/tests/performance/test_load.py

import asyncio
from locust import HttpUser, task, between

class WordQueryUser(HttpUser):
    """模拟用户查询单词"""
    wait_time = between(1, 3)  # 每次请求间隔1-3秒

    @task(10)  # 权重10
    def query_existing_word(self):
        """查询已存在的单词（命中缓存）"""
        self.client.get("/v1/words/query/accountability")

    @task(2)  # 权重2
    def query_new_word(self):
        """查询新单词（触发AI生成）"""
        import random
        word = f"test{random.randint(1, 10000)}"
        self.client.get(f"/v1/words/query/{word}")

    @task(5)  # 权重5
    def get_query_limit(self):
        """获取查询限制信息"""
        self.client.get("/v1/words/query-limit")

# 运行性能测试
# locust -f tests/performance/test_load.py --headless \
#        -u 100 -r 10 --run-time 5m --host http://localhost:8000
```

**性能目标**：
- 100并发用户：平均响应时间 < 200ms，P95 < 500ms
- 1000并发用户：平均响应时间 < 500ms，P95 < 1000ms
- 错误率 < 0.1%

---

## 10. 监控与可观测性

### 10.1 监控指标

```python
# app/core/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# 业务指标
query_requests_total = Counter(
    'query_requests_total',
    '查询请求总数',
    ['user_type', 'status']  # guest/free/premium, success/failed
)

query_limit_exceeded_total = Counter(
    'query_limit_exceeded_total',
    '查询限额超出次数',
    ['user_type']
)

guest_to_user_conversion_total = Counter(
    'guest_to_user_conversion_total',
    '游客转注册用户数'
)

# 性能指标
query_duration_seconds = Histogram(
    'query_duration_seconds',
    '查询响应时间（秒）',
    ['endpoint']
)

# 系统指标
redis_connection_errors = Counter(
    'redis_connection_errors_total',
    'Redis连接错误次数'
)

database_query_duration = Histogram(
    'database_query_duration_seconds',
    '数据库查询时间（秒）',
    ['operation']
)
```

### 10.2 日志规范

```python
# app/core/logging.py

import structlog
from datetime import datetime

def configure_logging():
    """配置结构化日志"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

# 使用示例
logger = structlog.get_logger(__name__)

logger.info(
    "word_query_attempt",
    user_id=user.id,
    user_type="guest",
    word="accountability",
    ip="192.168.1.100",
    remaining_queries=7
)
```

### 10.3 告警规则

```yaml
# monitoring/alerts.yml

groups:
  - name: chaiword_alerts
    interval: 30s
    rules:
      # 查询限额耗尽率异常
      - alert: HighQueryLimitExceededRate
        expr: |
          rate(query_limit_exceeded_total[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "查询限额超出频率过高"
          description: "过去5分钟内有{{ $value }}次查询限额超出"

      # Redis连接失败
      - alert: RedisConnectionFailure
        expr: |
          rate(redis_connection_errors_total[1m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis连接失败"
          description: "Redis连接出现错误，限流功能可能受影响"

      # API响应时间过长
      - alert: HighAPILatency
        expr: |
          histogram_quantile(0.95,
            rate(query_duration_seconds_bucket[5m])
          ) > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API响应时间过长"
          description: "P95响应时间超过1秒"

      # 游客转化率异常低
      - alert: LowGuestConversionRate
        expr: |
          rate(guest_to_user_conversion_total[1h]) /
          rate(query_requests_total{user_type="guest"}[1h]) < 0.05
        for: 1h
        labels:
          severity: info
        annotations:
          summary: "游客转化率低于5%"
          description: "过去1小时游客转化率：{{ $value | humanizePercentage }}"
```

---

## 11. 实施计划

### 11.1 Phase 1: MVP（2周）

**目标**：实现游客模式基础功能

**Week 1: 后端基础**
- [ ] Redis集成和连接配置
- [ ] 游客识别服务（IP + User-Agent）
- [ ] RateLimitService实现（Redis计数器）
- [ ] 依赖注入改造（get_user_or_guest）
- [ ] 数据库迁移（guest_sessions表）
- [ ] 单元测试（覆盖率≥95%）

**Week 2: API和集成**
- [ ] 单词查询API改造（支持游客）
- [ ] 查询限制API更新
- [ ] IP限流中间件
- [ ] 集成测试（覆盖率≥90%）
- [ ] 前端适配（游客模式UI）
- [ ] E2E测试（关键流程）

**交付物**：
- ✅ 游客可查询10个单词/天
- ✅ 注册用户可查询50个单词/天
- ✅ 重复查询不计次数
- ✅ IP限流（30次/分钟）

### 11.2 Phase 2: 增强体验（1周）

**目标**：优化游客体验和防滥用

**任务**：
- [ ] 渐进式引导UI（4个阶段）
- [ ] 查询限制达到时的引导页面
- [ ] 异常行为检测服务
- [ ] Captcha集成（可选）
- [ ] 游客转注册数据迁移
- [ ] A/B测试准备（不同引导文案）

**交付物**：
- ✅ 温和的渐进式引导
- ✅ 防滥用机制（行为检测）
- ✅ 游客数据可迁移到注册用户

### 11.3 Phase 3: 设备指纹识别（1周）

**目标**：提升游客识别准确性

**任务**：
- [ ] 前端设备指纹收集（Canvas + WebGL）
- [ ] 后端设备指纹验证
- [ ] GuestIdentifierService v2
- [ ] 隐私声明更新（告知指纹收集）
- [ ] 测试和优化

**交付物**：
- ✅ 游客识别准确率 > 95%
- ✅ 降低误判（同一网络多用户）

### 11.4 Phase 4: 监控与优化（持续）

**任务**：
- [ ] Prometheus + Grafana监控面板
- [ ] 告警规则配置
- [ ] 性能测试和优化
- [ ] 成本分析和优化
- [ ] 根据数据调整限额策略

**交付物**：
- ✅ 完整监控体系
- ✅ 自动告警
- ✅ 性能达标（P95 < 500ms）

---

## 12. 附录

### 12.1 Redis数据结构示例

```
# 游客日限额计数
redis> GET query_limit:guest:abc123def:2025-10-16
"7"

# 已查询单词集合
redis> SMEMBERS queried_words:guest:abc123def:2025-10-16
1) "1"
2) "5"
3) "12"
4) "23"
5) "45"
6) "67"
7) "89"

# IP分钟级限流
redis> GET rate_limit:ip:192.168.1.100:minute
"15"

# TTL检查
redis> TTL query_limit:guest:abc123def:2025-10-16
(integer) 43200  # 12小时后过期
```

### 12.2 数据库索引优化

```sql
-- 查询日志表索引优化
CREATE INDEX CONCURRENTLY idx_query_logs_user_date
ON query_logs (user_id, query_date)
WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_query_logs_guest_date
ON query_logs (guest_session_id, query_date)
WHERE guest_session_id IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_query_logs_word
ON query_logs (word_id);

-- 游客会话表索引
CREATE INDEX CONCURRENTLY idx_guest_ip
ON guest_sessions (ip_address);

CREATE INDEX CONCURRENTLY idx_guest_last_query
ON guest_sessions (last_query_date)
WHERE last_query_date > NOW() - INTERVAL '90 days';

-- 分析查询性能
EXPLAIN ANALYZE
SELECT COUNT(*) FROM query_logs
WHERE user_id = 123 AND query_date = '2025-10-16';
```

### 12.3 环境变量配置清单

```bash
# .env.example

# 应用配置
APP_ENV=production
DEBUG=false

# 数据库配置
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/chaiword_duck
DATABASE_POOL_SIZE=20

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password

# JWT配置
JWT_SECRET_KEY=your-secret-key-min-32-chars-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080

# 查询限制配置（v1.1）
GUEST_DAILY_LIMIT=10
FREE_USER_DAILY_LIMIT=50
PREMIUM_USER_DAILY_LIMIT=-1

# IP限流配置
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=1000

# OpenAI配置
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.7

# 邮件配置
SENDGRID_API_KEY=SG...
FROM_EMAIL=noreply@chaiwordduck.com

# Sentry配置
SENTRY_DSN=https://...

# CORS配置
CORS_ORIGINS=https://chaiwordduck.com,https://www.chaiwordduck.com
```

### 12.4 技术栈版本锁定

```toml
# backend/pyproject.toml

[tool.poetry.dependencies]
python = "^3.12"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
sqlalchemy = {extras = ["asyncio"], version = "^2.0.0"}
asyncpg = "^0.29.0"
redis = {extras = ["hiredis"], version = "^5.0.0"}
pydantic = "^2.4.0"
pydantic-settings = "^2.0.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
alembic = "^1.12.0"
httpx = "^0.25.0"
structlog = "^23.2.0"
prometheus-client = "^0.19.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
black = "^23.10.0"
ruff = "^0.1.0"
mypy = "^1.6.0"
```

```json
// frontend/package.json

{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.2.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.4.0",
    "axios": "^1.5.0",
    "tailwindcss": "^3.3.0"
  },
  "devDependencies": {
    "@playwright/test": "^1.40.0",
    "@types/react": "^18.2.0",
    "eslint": "^8.52.0",
    "prettier": "^3.0.0"
  }
}
```

---

## 13. 总结

### 13.1 核心设计决策

1. **可选认证架构**：支持游客和注册用户，降低使用门槛
2. **Redis限流**：高性能、精准的查询限制实现
3. **渐进式识别**：从IP+UA（MVP）到设备指纹（Phase 2）
4. **多层防护**：IP限流 + 游客限额 + 行为检测 + Captcha
5. **优雅降级**：Redis故障时降级到PostgreSQL

### 13.2 技术亮点

- ✅ **高性能**：Redis原子操作，P95响应时间 < 500ms
- ✅ **高可用**：Redis Sentinel + PostgreSQL降级
- ✅ **高扩展**：支持从100到100万用户
- ✅ **低成本**：预生成 + AI限流，控制OpenAI费用
- ✅ **好体验**：温和引导，不强制注册

### 13.3 与PRD v1.1的对齐

| PRD需求 | 技术实现 | 状态 |
|---------|---------|------|
| 游客10次/天 | Redis计数器 + TTL | ✅ 已设计 |
| 注册用户50次/天 | Redis计数器（不同key） | ✅ 已设计 |
| 重复查询不计次数 | Redis Set存储已查询单词ID | ✅ 已设计 |
| IP限流30次/分钟 | Redis INCR + 中间件 | ✅ 已设计 |
| 渐进式引导（4阶段） | 前端条件渲染 | ✅ 已设计 |
| 设备指纹识别 | Canvas + WebGL（Phase 2） | ⏳ Phase 2 |
| 防滥用机制 | 行为检测 + Captcha | ✅ 已设计 |

### 13.4 后续优化方向

1. **设备指纹识别**：提升游客识别准确率到95%+
2. **Redis Cluster**：应对高并发场景（10万+DAU）
3. **GraphQL API**：优化前端查询性能
4. **WebSocket实时推送**：实时更新查询次数
5. **机器学习反作弊**：识别更复杂的爬虫模式

---

**文档结束**

**版本**：v1.1
**日期**：2025-10-16
**状态**：待评审
**作者**：架构师

---

**变更日志**：
- v1.1 (2025-10-16): 新增游客模式完整技术设计
- v1.0 (未发布): 初始版本
