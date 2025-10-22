"""
Redis客户端配置

提供Redis连接管理和客户端获取功能
"""
import logging
from typing import Optional

import redis.asyncio as redis
from redis.asyncio import Redis, ConnectionPool

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# 全局Redis客户端实例
_redis_client: Optional[Redis] = None
_redis_pool: Optional[ConnectionPool] = None


async def get_redis_client() -> Redis:
    """
    获取Redis客户端实例

    使用单例模式，确保整个应用只有一个Redis连接池

    Returns:
        Redis: Redis客户端实例

    Raises:
        Exception: Redis连接失败时抛出异常
    """
    global _redis_client, _redis_pool

    if _redis_client is None:
        try:
            # 创建连接池
            _redis_pool = ConnectionPool.from_url(
                settings.redis_url,
                password=settings.redis_password if settings.redis_password else None,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,  # 连接池大小
                retry_on_timeout=True,  # 超时重试
                socket_keepalive=True,  # 保持连接
                socket_keepalive_options={},  # TCP keepalive选项
                health_check_interval=30,  # 健康检查间隔
            )

            # 创建Redis客户端
            _redis_client = Redis(connection_pool=_redis_pool)

            # 测试连接
            await _redis_client.ping()

            logger.info(
                "Redis client initialized successfully",
                redis_url=settings.redis_url,
                max_connections=20
            )

        except Exception as e:
            logger.error(
                "Failed to initialize Redis client",
                error=str(e),
                redis_url=settings.redis_url
            )
            raise Exception(f"Redis连接失败: {str(e)}")

    return _redis_client


async def close_redis_client():
    """关闭Redis连接池"""
    global _redis_client, _redis_pool

    if _redis_client:
        try:
            await _redis_client.close()
            logger.info("Redis client closed")
        except Exception as e:
            logger.error("Error closing Redis client", error=str(e))
        finally:
            _redis_client = None

    if _redis_pool:
        try:
            await _redis_pool.disconnect()
            logger.info("Redis connection pool closed")
        except Exception as e:
            logger.error("Error closing Redis connection pool", error=str(e))
        finally:
            _redis_pool = None


async def check_redis_health() -> bool:
    """
    检查Redis健康状态

    Returns:
        bool: Redis是否健康
    """
    try:
        client = await get_redis_client()
        await client.ping()
        return True
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        return False


class RedisService:
    """
    Redis服务基类

    提供通用的Redis操作方法和错误处理
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    async def get_client(self) -> Redis:
        """获取Redis客户端，包含错误处理"""
        try:
            return await get_redis_client()
        except Exception as e:
            self.logger.error("Failed to get Redis client", error=str(e))
            raise

    async def safe_get(self, key: str) -> Optional[str]:
        """
        安全的Redis GET操作

        Args:
            key: Redis键

        Returns:
            Optional[str]: 值或None（如果键不存在或发生错误）
        """
        try:
            client = await self.get_client()
            value = await client.get(key)
            return value
        except Exception as e:
            self.logger.error("Redis GET operation failed", key=key, error=str(e))
            return None

    async def safe_setex(self, key: str, ttl: int, value: str) -> bool:
        """
        安全的Redis SETEX操作

        Args:
            key: Redis键
            ttl: 过期时间（秒）
            value: 要存储的值

        Returns:
            bool: 操作是否成功
        """
        try:
            client = await self.get_client()
            result = await client.setex(key, ttl, value)
            return bool(result)
        except Exception as e:
            self.logger.error("Redis SETEX operation failed", key=key, ttl=ttl, error=str(e))
            return False

    async def safe_delete(self, key: str) -> bool:
        """
        安全的Redis DELETE操作

        Args:
            key: Redis键

        Returns:
            bool: 操作是否成功
        """
        try:
            client = await self.get_client()
            result = await client.delete(key)
            return True  # 即使键不存在也认为操作成功
        except Exception as e:
            self.logger.error("Redis DELETE operation failed", key=key, error=str(e))
            return False

    async def safe_exists(self, key: str) -> bool:
        """
        安全的Redis EXISTS操作

        Args:
            key: Redis键

        Returns:
            bool: 键是否存在
        """
        try:
            client = await self.get_client()
            result = await client.exists(key)
            return bool(result)
        except Exception as e:
            self.logger.error("Redis EXISTS operation failed", key=key, error=str(e))
            return False

    async def safe_expire(self, key: str, ttl: int) -> bool:
        """
        安全的Redis EXPIRE操作

        Args:
            key: Redis键
            ttl: 过期时间（秒）

        Returns:
            bool: 操作是否成功
        """
        try:
            client = await self.get_client()
            result = await client.expire(key, ttl)
            return bool(result)
        except Exception as e:
            self.logger.error("Redis EXPIRE operation failed", key=key, ttl=ttl, error=str(e))
            return False