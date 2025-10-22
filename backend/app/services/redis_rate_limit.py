"""
Redis查询限制缓存服务

使用Redis优化查询限制检查性能，减少数据库访问频率。
"""
import asyncio
from datetime import date, timedelta
from typing import Optional, Tuple, Set
from redis.asyncio import Redis
from redis.exceptions import RedisError, ConnectionError
from fastapi import Request, HTTPException, status

from app.core.redis_keys import RedisKeys, get_ttl_seconds
from app.core.config import settings
from app.core.logging import get_logger
from app.models import User
from app.schemas.common import ErrorCode

logger = get_logger(__name__)


class RedisRateLimitService:
    """
    Redis查询限制缓存服务

    使用Redis实现高性能的查询限制检查：
    - 游客：10次/天（基于IP）
    - 注册用户：50次/天
    - Premium用户：无限制

    Redis数据结构：
    - String: 计数器（已查询次数）
    - Set: 已查询单词ID集合（去重用）
    - TTL: 24小时自动过期
    """

    def __init__(self, redis_client: Redis):
        """
        初始化Redis限流服务

        Args:
            redis_client: Redis异步客户端
        """
        self.redis = redis_client
        self.ttl_seconds = get_ttl_seconds("daily")

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

        Raises:
            ValueError: 游客模式缺少request对象
            HTTPException: 超出查询限制
        """
        today = date.today()

        if user is None:
            # 游客模式
            if request is None:
                raise ValueError("游客模式需要提供request对象以获取IP标识")
            return await self._check_guest_query_with_redis(word_id, request, today)

        elif user.membership_tier == "premium":
            # Premium用户：无限制
            await self._record_user_query_with_redis(user.id, word_id, today)
            logger.info(f"Premium用户 {user.id} 查询单词 {word_id}（无限制）")
            return (True, 0, -1, "premium")

        else:
            # 免费注册用户：50次/天
            return await self._check_user_query_with_redis(user, word_id, today)

    async def _check_guest_query_with_redis(
        self,
        word_id: int,
        request: Request,
        today: date,
    ) -> Tuple[bool, int, int, str]:
        """
        使用Redis检查游客查询限制（10次/天）

        Args:
            word_id: 单词ID
            request: HTTP请求对象
            today: 今天的日期

        Returns:
            (是否允许, 已用次数, 限额, 用户类型)
        """
        from app.services.guest_identifier import GuestIdentifierService

        identifier = GuestIdentifierService.get_identifier(request)
        limit = settings.guest_daily_limit

        # 生成Redis键
        counter_key = RedisKeys.guest_daily_limit(identifier, today)
        words_key = RedisKeys.guest_queried_words(identifier, today)

        try:
            # 原子操作：检查并更新查询统计
            result = await self._atomic_check_and_increment(
                counter_key=counter_key,
                words_key=words_key,
                word_id=word_id,
                limit=limit,
                identifier=identifier,
                user_type="guest"
            )

            return result

        except RedisError as e:
            # Redis故障时抛出异常，由上层处理降级
            logger.error(
                f"Redis查询限制检查失败: {e}",
                extra={"identifier": identifier, "word_id": word_id, "error": str(e)}
            )
            raise RedisError(f"Redis服务不可用: {e}")

    async def _check_user_query_with_redis(
        self,
        user: User,
        word_id: int,
        today: date,
    ) -> Tuple[bool, int, int, str]:
        """
        使用Redis检查注册用户查询限制（50次/天）

        Args:
            user: 用户对象
            word_id: 单词ID
            today: 今天的日期

        Returns:
            (是否允许, 已用次数, 限额, 用户类型)
        """
        limit = settings.free_user_daily_limit

        # 生成Redis键
        counter_key = RedisKeys.user_daily_limit(user.id, today)
        words_key = RedisKeys.user_queried_words(user.id, today)

        try:
            # 原子操作：检查并更新查询统计
            result = await self._atomic_check_and_increment(
                counter_key=counter_key,
                words_key=words_key,
                word_id=word_id,
                limit=limit,
                identifier=str(user.id),
                user_type="registered"
            )

            return result

        except RedisError as e:
            # Redis故障时抛出异常，由上层处理降级
            logger.error(
                f"Redis查询限制检查失败: {e}",
                extra={"user_id": user.id, "word_id": word_id, "error": str(e)}
            )
            raise RedisError(f"Redis服务不可用: {e}")

    async def _atomic_check_and_increment(
        self,
        counter_key: str,
        words_key: str,
        word_id: int,
        limit: int,
        identifier: str,
        user_type: str,
    ) -> Tuple[bool, int, int, str]:
        """
        原子操作：检查限制并增加计数

        使用Redis事务和Lua脚本确保原子性：
        1. 检查单词是否已查询过
        2. 如果未查询过，增加计数器
        3. 检查是否超出限制
        4. 记录已查询单词

        Args:
            counter_key: 计数器键
            words_key: 已查询单词集合键
            word_id: 单词ID
            limit: 查询限制
            identifier: 用户/游客标识
            user_type: 用户类型

        Returns:
            (是否允许, 已用次数, 限额, 用户类型)
        """
        # Lua脚本确保原子操作
        lua_script = """
        -- 获取参数
        local counter_key = KEYS[1]
        local words_key = KEYS[2]
        local word_id = ARGV[1]
        local limit = tonumber(ARGV[2])
        local ttl = tonumber(ARGV[3])

        -- 检查单词是否已查询过
        local is_new_query = redis.call('SISMEMBER', words_key, word_id)

        if is_new_query == 0 then
            -- 新查询，需要增加计数
            local current_count = redis.call('INCR', counter_key)

            -- 设置过期时间（只在第一次设置时）
            if current_count == 1 then
                redis.call('EXPIRE', counter_key, ttl)
                redis.call('EXPIRE', words_key, ttl)
            end

            -- 检查是否超出限制
            if current_count > limit then
                -- 超出限制，回滚计数并记录单词
                redis.call('DECR', counter_key)
                return {0, current_count - 1, limit}
            end

            -- 未超出限制，记录已查询单词
            redis.call('SADD', words_key, word_id)
            return {1, current_count, limit}
        else
            -- 重复查询，不计次数
            local current_count = tonumber(redis.call('GET', counter_key) or 0)
            return {1, current_count, limit}
        end
        """

        try:
            # 执行Lua脚本
            result = await self.redis.eval(
                lua_script,
                2,  # 键的数量
                counter_key,
                words_key,
                str(word_id),
                str(limit),
                str(self.ttl_seconds)
            )

            allowed, used_count, limit = result

            # 记录日志
            if allowed == 1:
                if user_type == "guest":
                    logger.info(
                        f"游客 {identifier} 查询单词 {word_id}，今日第 {used_count}/{limit} 次",
                        extra={
                            "identifier": identifier,
                            "word_id": word_id,
                            "used_queries": used_count,
                            "limit": limit,
                            "user_type": user_type
                        }
                    )
                else:
                    logger.info(
                        f"用户 {identifier} 查询单词 {word_id}，今日第 {used_count}/{limit} 次",
                        extra={
                            "user_id": identifier,
                            "word_id": word_id,
                            "used_queries": used_count,
                            "limit": limit,
                            "user_type": user_type
                        }
                    )

                return (True, used_count, limit, user_type)
            else:
                # 超出限制
                if user_type == "guest":
                    logger.warning(
                        f"游客 {identifier} 今日查询次数已用完：{used_count}/{limit}",
                        extra={
                            "identifier": identifier,
                            "used_queries": used_count,
                            "limit": limit,
                        }
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": ErrorCode.QUERY_LIMIT_EXCEEDED,
                            "message": f"今日免费查询已用完（{limit}次）。注册可获得每日50次查询机会！",
                        },
                    )
                else:
                    logger.warning(
                        f"用户 {identifier} 今日查询次数已用完：{used_count}/{limit}",
                        extra={
                            "user_id": identifier,
                            "used_queries": used_count,
                            "limit": limit,
                        }
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": ErrorCode.QUERY_LIMIT_EXCEEDED,
                            "message": f"今日查询次数已用完（{limit}次）。升级Premium可无限查询！",
                        },
                    )

        except RedisError as e:
            logger.error(f"Redis原子操作失败: {e}")
            raise

    async def _record_user_query_with_redis(
        self,
        user_id: int,
        word_id: int,
        query_date: date,
    ):
        """
        使用Redis记录Premium用户查询（仅记录，不做限制）

        Args:
            user_id: 用户ID
            word_id: 单词ID
            query_date: 查询日期
        """
        words_key = RedisKeys.user_queried_words(user_id, query_date)

        try:
            # 仅记录已查询单词，不做计数限制
            await self.redis.sadd(words_key, str(word_id))
            await self.redis.expire(words_key, self.ttl_seconds)

            logger.debug(
                f"已记录Premium用户 {user_id} 查询单词 {word_id}",
                extra={"user_id": user_id, "word_id": word_id}
            )

        except RedisError as e:
            # Premium用户记录失败不影响业务
            logger.warning(
                f"Premium用户查询记录失败: {e}",
                extra={"user_id": user_id, "word_id": word_id, "error": str(e)}
            )

    async def get_user_query_stats(
        self,
        user_id: Optional[int] = None,
        identifier: Optional[str] = None,
        query_date: Optional[date] = None,
    ) -> Tuple[int, Set[int]]:
        """
        获取用户/游客查询统计信息

        Args:
            user_id: 用户ID（注册用户）
            identifier: 游客标识（游客）
            query_date: 查询日期（默认今天）

        Returns:
            (已查询次数, 已查询单词ID集合)
        """
        if query_date is None:
            query_date = date.today()

        if user_id is not None:
            counter_key = RedisKeys.user_daily_limit(user_id, query_date)
            words_key = RedisKeys.user_queried_words(user_id, query_date)
        elif identifier is not None:
            counter_key = RedisKeys.guest_daily_limit(identifier, query_date)
            words_key = RedisKeys.guest_queried_words(identifier, query_date)
        else:
            raise ValueError("必须提供user_id或identifier")

        try:
            # 并发获取计数和单词集合
            count_task = self.redis.get(counter_key)
            words_task = self.redis.smembers(words_key)

            count_str, word_id_strs = await asyncio.gather(count_task, words_task)

            count = int(count_str or 0)
            word_ids = {int(wid) for wid in word_id_strs if wid.isdigit()}

            return count, word_ids

        except RedisError as e:
            logger.error(f"获取查询统计失败: {e}")
            return 0, set()

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
        if query_date is None:
            query_date = date.today()

        if user_id is not None:
            keys = [
                RedisKeys.user_daily_limit(user_id, query_date),
                RedisKeys.user_queried_words(user_id, query_date),
            ]
        elif identifier is not None:
            keys = [
                RedisKeys.guest_daily_limit(identifier, query_date),
                RedisKeys.guest_queried_words(identifier, query_date),
            ]
        else:
            raise ValueError("必须提供user_id或identifier")

        try:
            await self.redis.delete(*keys)
            logger.info(f"已清除查询缓存: {keys}")
        except RedisError as e:
            logger.error(f"清除查询缓存失败: {e}")

    async def health_check(self) -> bool:
        """
        Redis健康检查

        Returns:
            True表示Redis可用，False表示不可用
        """
        try:
            await self.redis.ping()
            return True
        except (ConnectionError, RedisError):
            return False