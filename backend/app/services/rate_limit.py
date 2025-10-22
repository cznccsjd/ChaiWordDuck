"""
查询限流服务

统一管理游客、注册用户、Premium用户的查询限制逻辑。
支持Redis缓存优化和数据库降级机制。
"""
from datetime import date
from typing import Optional, Tuple, Set
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, HTTPException, status

from app.models import User, QueryLog
from app.models.guest_query_log import GuestQueryLog
from app.core.config import settings
from app.core.logging import get_logger
from app.services.guest_identifier import GuestIdentifierService
from app.services.redis_rate_limit import RedisRateLimitService
from app.schemas.common import ErrorCode

logger = get_logger(__name__)


class RateLimitService:
    """
    统一的查询限流服务

    根据用户类型（游客/注册用户/Premium用户）实施不同的查询限制策略：
    - 游客：10次/天（基于IP）
    - 注册用户：50次/天
    - Premium用户：无限制

    去重逻辑：同一用户同一天查询同一单词，只计1次。
    """

    def __init__(self, db: AsyncSession, redis_client=None):
        """
        初始化限流服务

        Args:
            db: 数据库会话
            redis_client: Redis客户端（可选，用于缓存优化）
        """
        self.db = db
        self.redis_rate_limit_service = None

        # 如果提供了Redis客户端，初始化Redis限流服务
        if redis_client is not None:
            try:
                self.redis_rate_limit_service = RedisRateLimitService(redis_client)
                logger.info("Redis查询限制服务已启用")
            except Exception as e:
                logger.warning(f"Redis查询限制服务初始化失败，将使用数据库模式: {e}")
        else:
            logger.info("未提供Redis客户端，将使用数据库模式")

    async def check_and_record_query(
        self,
        word_id: int,
        user: Optional[User] = None,
        request: Optional[Request] = None,
    ) -> Tuple[bool, int, int, str]:
        """
        检查查询限制并记录查询日志

        优先使用Redis缓存，失败时自动降级到数据库模式。

        Args:
            word_id: 单词ID
            user: 用户对象（可选，None表示游客）
            request: 请求对象（游客模式必需）

        Returns:
            (是否允许查询, 已用次数, 总限额, 用户类型)
            - 已用次数: 今日已查询的不同单词数量
            - 总限额: 每日允许查询的单词数量（-1表示无限）
            - 用户类型: "guest" | "registered" | "premium"

        Raises:
            ValueError: 游客模式缺少request对象
            HTTPException: 超出查询限制（400）

        Examples:
            >>> # 游客查询
            >>> allowed, used, limit, user_type = await service.check_and_record_query(
            ...     word_id=123, user=None, request=request
            ... )
            >>> # 返回: (True, 1, 10, "guest")

            >>> # 注册用户查询
            >>> allowed, used, limit, user_type = await service.check_and_record_query(
            ...     word_id=123, user=current_user, request=None
            ... )
            >>> # 返回: (True, 5, 50, "registered")
        """
        # 优先使用Redis缓存
        if self.redis_rate_limit_service is not None:
            try:
                return await self.redis_rate_limit_service.check_and_record_query(
                    word_id=word_id,
                    user=user,
                    request=request
                )
            except HTTPException:
                # HTTPException需要重新抛出（如超出限制）
                raise
            except Exception as e:
                # Redis异常时记录日志并降级到数据库模式
                logger.warning(
                    f"Redis查询限制检查失败，降级到数据库模式: {e}",
                    extra={"word_id": word_id, "user_id": user.id if user else None}
                )

        # 降级到数据库模式
        today = date.today()

        if user is None:
            # 游客模式
            if request is None:
                raise ValueError("游客模式需要提供request对象以获取IP标识")

            return await self._check_guest_query(word_id, request, today)

        elif user.membership_tier == "premium":
            # Premium用户：无限制
            await self._record_user_query(user.id, word_id, today)
            logger.info(f"Premium用户 {user.id} 查询单词 {word_id}（无限制）")
            return (True, 0, -1, "premium")

        else:
            # 免费注册用户：50次/天
            return await self._check_user_query(user, word_id, today)

    async def _check_guest_query(
        self,
        word_id: int,
        request: Request,
        today: date,
    ) -> Tuple[bool, int, int, str]:
        """
        游客查询限制检查（10次/天）

        Args:
            word_id: 单词ID
            request: HTTP请求对象
            today: 今天的日期

        Returns:
            (是否允许, 已用次数, 限额, 用户类型)

        Raises:
            HTTPException: 超出限制时抛出400错误
        """
        identifier = GuestIdentifierService.get_identifier(request)
        limit = settings.guest_daily_limit

        # 检查今日是否已查询过该单词（去重）
        result = await self.db.execute(
            select(GuestQueryLog.id)
            .where(GuestQueryLog.identifier == identifier)
            .where(GuestQueryLog.word_id == word_id)
            .where(GuestQueryLog.query_date == today)
            .limit(1)
        )
        already_queried = result.scalar_one_or_none() is not None

        if already_queried:
            # 重复查询不计次数
            logger.info(
                f"游客 {identifier} 重复查询单词 {word_id}，不计次数",
                extra={"identifier": identifier, "word_id": word_id},
            )
            # 获取当前已用次数
            count_result = await self.db.execute(
                select(func.count(func.distinct(GuestQueryLog.word_id)))
                .where(GuestQueryLog.identifier == identifier)
                .where(GuestQueryLog.query_date == today)
            )
            used = count_result.scalar_one()
            return (True, used, limit, "guest")

        # 检查今日查询次数（去重统计）
        count_result = await self.db.execute(
            select(func.count(func.distinct(GuestQueryLog.word_id)))
            .where(GuestQueryLog.identifier == identifier)
            .where(GuestQueryLog.query_date == today)
        )
        used_queries = count_result.scalar_one()

        if used_queries >= limit:
            logger.warning(
                f"游客 {identifier} 今日查询次数已用完：{used_queries}/{limit}",
                extra={
                    "identifier": identifier,
                    "used_queries": used_queries,
                    "limit": limit,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": ErrorCode.QUERY_LIMIT_EXCEEDED,
                    "message": f"今日免费查询已用完（{limit}次）。注册可获得每日50次查询机会！",
                },
            )

        # 记录查询
        new_log = GuestQueryLog(
            identifier=identifier,
            word_id=word_id,
            query_date=today,
        )
        self.db.add(new_log)
        await self.db.commit()

        logger.info(
            f"游客 {identifier} 查询单词 {word_id}，今日第 {used_queries + 1}/{limit} 次",
            extra={
                "identifier": identifier,
                "word_id": word_id,
                "used_queries": used_queries + 1,
                "limit": limit,
            },
        )

        return (True, used_queries + 1, limit, "guest")

    async def _check_user_query(
        self,
        user: User,
        word_id: int,
        today: date,
    ) -> Tuple[bool, int, int, str]:
        """
        注册用户查询限制检查（50次/天）

        Args:
            user: 用户对象
            word_id: 单词ID
            today: 今天的日期

        Returns:
            (是否允许, 已用次数, 限额, 用户类型)

        Raises:
            HTTPException: 超出限制时抛出400错误
        """
        limit = settings.free_user_daily_limit

        # 检查今日是否已查询过该单词（去重）
        result = await self.db.execute(
            select(QueryLog.id)
            .where(QueryLog.user_id == user.id)
            .where(QueryLog.word_id == word_id)
            .where(QueryLog.query_date == today)
            .limit(1)
        )
        already_queried = result.scalar_one_or_none() is not None

        if already_queried:
            # 重复查询不计次数
            logger.info(
                f"用户 {user.id} 重复查询单词 {word_id}，不计次数",
                extra={"user_id": user.id, "word_id": word_id},
            )
            # 获取当前已用次数
            count_result = await self.db.execute(
                select(func.count(func.distinct(QueryLog.word_id)))
                .where(QueryLog.user_id == user.id)
                .where(QueryLog.query_date == today)
            )
            used = count_result.scalar_one()
            return (True, used, limit, "registered")

        # 检查今日查询次数（去重统计）
        count_result = await self.db.execute(
            select(func.count(func.distinct(QueryLog.word_id)))
            .where(QueryLog.user_id == user.id)
            .where(QueryLog.query_date == today)
        )
        used_queries = count_result.scalar_one()

        if used_queries >= limit:
            logger.warning(
                f"用户 {user.id} 今日查询次数已用完：{used_queries}/{limit}",
                extra={
                    "user_id": user.id,
                    "used_queries": used_queries,
                    "limit": limit,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": ErrorCode.QUERY_LIMIT_EXCEEDED,
                    "message": f"今日查询次数已用完（{limit}次）。升级Premium可无限查询！",
                },
            )

        # 记录查询
        await self._record_user_query(user.id, word_id, today)

        logger.info(
            f"用户 {user.id} 查询单词 {word_id}，今日第 {used_queries + 1}/{limit} 次",
            extra={
                "user_id": user.id,
                "word_id": word_id,
                "used_queries": used_queries + 1,
                "limit": limit,
            },
        )

        return (True, used_queries + 1, limit, "registered")

    async def _record_user_query(self, user_id: int, word_id: int, query_date: date):
        """
        记录用户查询日志

        Args:
            user_id: 用户ID
            word_id: 单词ID
            query_date: 查询日期
        """
        new_log = QueryLog(
            user_id=user_id,
            word_id=word_id,
            query_date=query_date,
        )
        self.db.add(new_log)
        await self.db.commit()

        logger.debug(
            f"已记录用户 {user_id} 查询单词 {word_id} 的日志",
            extra={"user_id": user_id, "word_id": word_id, "query_date": str(query_date)},
        )

    async def get_user_query_stats(
        self,
        user_id: Optional[int] = None,
        identifier: Optional[str] = None,
        query_date: Optional[date] = None,
    ) -> Tuple[int, Set[int]]:
        """
        获取用户/游客查询统计信息

        优先从Redis获取，失败时从数据库查询。

        Args:
            user_id: 用户ID（注册用户）
            identifier: 游客标识（游客）
            query_date: 查询日期（默认今天）

        Returns:
            (已查询次数, 已查询单词ID集合)
        """
        if query_date is None:
            query_date = date.today()

        # 优先从Redis获取统计
        if self.redis_rate_limit_service is not None:
            try:
                return await self.redis_rate_limit_service.get_user_query_stats(
                    user_id=user_id,
                    identifier=identifier,
                    query_date=query_date
                )
            except Exception as e:
                logger.warning(f"Redis统计查询失败，降级到数据库: {e}")

        # 从数据库查询统计
        return await self._get_stats_from_database(user_id, identifier, query_date)

    async def _get_stats_from_database(
        self,
        user_id: Optional[int],
        identifier: Optional[str],
        query_date: date,
    ) -> Tuple[int, Set[int]]:
        """
        从数据库获取查询统计

        Args:
            user_id: 用户ID
            identifier: 游客标识
            query_date: 查询日期

        Returns:
            (已查询次数, 已查询单词ID集合)
        """
        if user_id is not None:
            # 注册用户统计
            count_result = await self.db.execute(
                select(func.count(func.distinct(QueryLog.word_id)))
                .where(QueryLog.user_id == user_id)
                .where(QueryLog.query_date == query_date)
            )
            count = count_result.scalar_one()

            words_result = await self.db.execute(
                select(QueryLog.word_id)
                .where(QueryLog.user_id == user_id)
                .where(QueryLog.query_date == query_date)
            )
            word_ids = {row[0] for row in words_result.fetchall()}

        elif identifier is not None:
            # 游客统计
            count_result = await self.db.execute(
                select(func.count(func.distinct(GuestQueryLog.word_id)))
                .where(GuestQueryLog.identifier == identifier)
                .where(GuestQueryLog.query_date == query_date)
            )
            count = count_result.scalar_one()

            words_result = await self.db.execute(
                select(GuestQueryLog.word_id)
                .where(GuestQueryLog.identifier == identifier)
                .where(GuestQueryLog.query_date == query_date)
            )
            word_ids = {row[0] for row in words_result.fetchall()}

        else:
            raise ValueError("必须提供user_id或identifier")

        return count, word_ids

    async def clear_user_cache(
        self,
        user_id: Optional[int] = None,
        identifier: Optional[str] = None,
        query_date: Optional[date] = None,
    ):
        """
        清除用户/游客查询缓存

        Args:
            user_id: 用户ID（注册用户）
            identifier: 游客标识（游客）
            query_date: 查询日期（默认今天）
        """
        if self.redis_rate_limit_service is not None:
            try:
                await self.redis_rate_limit_service.clear_user_cache(
                    user_id=user_id,
                    identifier=identifier,
                    query_date=query_date
                )
                logger.info(f"已清除Redis查询缓存")
            except Exception as e:
                logger.warning(f"清除Redis缓存失败: {e}")

    async def health_check(self) -> dict:
        """
        查询限制服务健康检查

        Returns:
            健康状态信息
        """
        status = {
            "database": True,
            "redis": False,
            "cache_enabled": self.redis_rate_limit_service is not None
        }

        # 检查数据库连接
        try:
            from sqlalchemy import text
            await self.db.execute(text("SELECT 1"))
        except Exception as e:
            status["database"] = False
            logger.error(f"数据库健康检查失败: {e}")

        # 检查Redis连接
        if self.redis_rate_limit_service is not None:
            try:
                status["redis"] = await self.redis_rate_limit_service.health_check()
            except Exception as e:
                status["redis"] = False
                logger.error(f"Redis健康检查失败: {e}")

        return status
