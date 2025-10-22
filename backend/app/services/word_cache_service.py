"""
单词缓存服务

提供单词数据的Redis缓存功能，优化查询性能
实现24小时过期策略和缓存命中率统计
"""
import json
import time
from typing import Optional

from app.core.redis import RedisService
from app.core.redis_keys import RedisKeys
from app.core.logging import get_logger, log_with_context
from app.schemas.word import WordQueryResponse

logger = get_logger(__name__)


class WordCacheService(RedisService):
    """
    单词缓存服务

    职责：
    - 管理单词数据的Redis缓存
    - 实现24小时过期策略
    - 提供缓存降级机制
    - 记录缓存命中率和性能指标
    """

    CACHE_TTL_SECONDS = 86400  # 24小时，根据任务要求

    def __init__(self):
        super().__init__()
        self._cache_hits = 0
        self._cache_misses = 0

    async def get_cached_word(self, normalized_word: str) -> Optional[WordQueryResponse]:
        """
        从缓存获取单词数据

        Args:
            normalized_word: 标准化的单词文本（小写）

        Returns:
            Optional[WordQueryResponse]: 缓存的单词数据，如果不存在则返回None

        性能要求：
        - 缓存命中时响应时间 < 50ms
        - Redis故障时自动降级返回None
        """
        start_time = time.time()
        cache_key = RedisKeys.word_cache(normalized_word)

        try:
            # 从Redis获取缓存数据
            cached_data = await self.safe_get(cache_key)

            if cached_data is None:
                # 缓存未命中
                self._cache_misses += 1
                log_with_context(
                    logger,
                    "debug",
                    "Word cache miss",
                    word=normalized_word,
                    cache_key=cache_key,
                    response_time_ms=round((time.time() - start_time) * 1000, 2)
                )
                return None

            # 解析JSON数据
            try:
                word_data = json.loads(cached_data)
                word_response = WordQueryResponse(**word_data)

                # 缓存命中
                self._cache_hits += 1
                response_time_ms = round((time.time() - start_time) * 1000, 2)

                log_with_context(
                    logger,
                    "info",
                    "Word cache hit",
                    word=normalized_word,
                    word_id=word_response.id,
                    is_golden=word_response.is_golden,
                    response_time_ms=response_time_ms,
                    cache_hit_rate=self._get_cache_hit_rate()
                )

                # 性能检查
                if response_time_ms >= 50:
                    log_with_context(
                        logger,
                        "warning",
                        "Word cache response time exceeded threshold",
                        word=normalized_word,
                        response_time_ms=response_time_ms,
                        threshold_ms=50
                    )

                return word_response

            except (json.JSONDecodeError, TypeError) as e:
                # 缓存数据损坏，记录并删除损坏的缓存
                self.logger.warning(
                    "Invalid cached word data, removing corrupted cache",
                    word=normalized_word,
                    cache_key=cache_key,
                    error=str(e)
                )
                await self.safe_delete(cache_key)
                self._cache_misses += 1
                return None

        except Exception as e:
            # Redis连接或其他错误，记录并降级处理
            log_with_context(
                logger,
                "error",
                "Redis cache operation failed, falling back to database",
                word=normalized_word,
                error=str(e)
            )
            self._cache_misses += 1
            return None

    async def cache_word(self, normalized_word: str, word_response: WordQueryResponse) -> bool:
        """
        将单词数据存储到缓存

        Args:
            normalized_word: 标准化的单词文本（小写）
            word_response: 单词查询响应数据

        Returns:
            bool: 缓存操作是否成功

        功能：
        - 使用JSON序列化存储数据
        - 设置24小时过期时间
        - Redis故障时不影响主流程
        """
        start_time = time.time()
        cache_key = RedisKeys.word_cache(normalized_word)

        try:
            # 序列化数据
            cached_data = word_response.model_dump_json()

            # 存储到Redis，设置过期时间
            success = await self.safe_setex(
                cache_key,
                self.CACHE_TTL_SECONDS,
                cached_data
            )

            response_time_ms = round((time.time() - start_time) * 1000, 2)

            if success:
                log_with_context(
                    logger,
                    "info",
                    "Word cached successfully",
                    word=normalized_word,
                    word_id=word_response.id,
                    is_golden=word_response.is_golden,
                    cache_ttl_hours=self.CACHE_TTL_SECONDS / 3600,
                    response_time_ms=response_time_ms
                )
            else:
                log_with_context(
                    logger,
                    "warning",
                    "Failed to cache word data",
                    word=normalized_word,
                    word_id=word_response.id,
                    response_time_ms=response_time_ms
                )

            return success

        except Exception as e:
            # 序列化或其他错误
            log_with_context(
                logger,
                "error",
                "Error caching word data",
                word=normalized_word,
                word_id=word_response.id,
                error=str(e)
            )
            return False

    async def invalidate_word_cache(self, normalized_word: str) -> bool:
        """
        使单词缓存失效

        Args:
            normalized_word: 标准化的单词文本（小写）

        Returns:
            bool: 操作是否成功

        用途：
        - 单词数据更新后清理旧缓存
        - 管理员手动清理缓存
        """
        start_time = time.time()
        cache_key = RedisKeys.word_cache(normalized_word)

        try:
            success = await self.safe_delete(cache_key)
            response_time_ms = round((time.time() - start_time) * 1000, 2)

            log_with_context(
                logger,
                "info",
                "Word cache invalidated",
                word=normalized_word,
                cache_key=cache_key,
                success=success,
                response_time_ms=response_time_ms
            )

            return success

        except Exception as e:
            log_with_context(
                logger,
                "error",
                "Error invalidating word cache",
                word=normalized_word,
                error=str(e)
            )
            return False

    def _get_cache_hit_rate(self) -> float:
        """
        计算缓存命中率

        Returns:
            float: 缓存命中率（0.0-1.0）
        """
        total_requests = self._cache_hits + self._cache_misses
        if total_requests == 0:
            return 0.0
        return round(self._cache_hits / total_requests, 4)

    def get_cache_stats(self) -> dict:
        """
        获取缓存统计信息

        Returns:
            dict: 包含命中、未命中次数和命中率的统计信息
        """
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate": self._get_cache_hit_rate(),
            "total_requests": self._cache_hits + self._cache_misses,
            "cache_ttl_hours": self.CACHE_TTL_SECONDS / 3600
        }

    def reset_cache_stats(self):
        """重置缓存统计计数器"""
        self._cache_hits = 0
        self._cache_misses = 0
        self.logger.info("Word cache statistics reset")

    async def warm_cache(self, words: list[WordQueryResponse]) -> dict:
        """
        缓存预热

        Args:
            words: 要预热的单词数据列表

        Returns:
            dict: 预热结果统计

        用途：
        - 应用启动时预加载热门单词
        - 提高首次访问性能
        """
        start_time = time.time()
        success_count = 0
        error_count = 0

        self.logger.info(
            "Starting word cache warm-up",
            word_count=len(words)
        )

        for word_response in words:
            success = await self.cache_word(
                word_response.word.lower(),
                word_response
            )
            if success:
                success_count += 1
            else:
                error_count += 1

        total_time_ms = round((time.time() - start_time) * 1000, 2)

        stats = {
            "total_words": len(words),
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": round(success_count / len(words), 4) if words else 0,
            "total_time_ms": total_time_ms,
            "avg_time_per_word_ms": round(total_time_ms / len(words), 2) if words else 0
        }

        self.logger.info(
            "Word cache warm-up completed",
            **stats
        )

        return stats


# 全局缓存服务实例
_word_cache_service: Optional[WordCacheService] = None


def get_word_cache_service() -> WordCacheService:
    """
    获取单词缓存服务实例

    Returns:
        WordCacheService: 单词缓存服务实例
    """
    global _word_cache_service
    if _word_cache_service is None:
        _word_cache_service = WordCacheService()
    return _word_cache_service