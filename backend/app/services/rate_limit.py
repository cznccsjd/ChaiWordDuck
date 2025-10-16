"""
查询限流服务

统一管理游客、注册用户、Premium用户的查询限制逻辑。
"""
from datetime import date
from typing import Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, HTTPException, status

from app.models import User, QueryLog
from app.models.guest_query_log import GuestQueryLog
from app.core.config import settings
from app.core.logging import get_logger
from app.services.guest_identifier import GuestIdentifierService
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

    def __init__(self, db: AsyncSession):
        """
        初始化限流服务

        Args:
            db: 数据库会话
        """
        self.db = db

    async def check_and_record_query(
        self,
        word_id: int,
        user: Optional[User] = None,
        request: Optional[Request] = None,
    ) -> Tuple[bool, int, int, str]:
        """
        检查查询限制并记录查询日志

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
