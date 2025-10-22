"""
单词缓存服务简化测试

专注于验证核心缓存逻辑的正确性
"""
import json
from datetime import datetime
from unittest.mock import AsyncMock, patch
import pytest

from app.services.word_cache_service import WordCacheService
from app.models.word import Word
from app.schemas.word import WordQueryResponse
from app.core.redis_keys import RedisKeys


class TestWordCacheServiceSimple:
    """单词缓存服务简化测试类"""

    @pytest.fixture
    def cache_service(self):
        """缓存服务实例"""
        return WordCacheService()

    @pytest.fixture
    def sample_word_response(self):
        """示例单词查询响应"""
        return WordQueryResponse(
            id=1,
            word="test",
            phonetic="/test/",
            part_of_speech="noun",
            core_game="测试核心游戏",
            scenario_formal="正式场景",
            scenario_casual="休闲场景",
            etymology_breakdown="词根拆解",
            etymology_story="词源故事",
            common_mistakes="常见错误",
            memory_trick="记忆技巧",
            is_golden=True,
            remaining_queries=10
        )

    @pytest.mark.asyncio
    async def test_get_cached_word_hit(self, cache_service, sample_word_response):
        """测试缓存命中场景"""
        normalized_word = "test"
        cached_data = sample_word_response.model_dump_json()

        with patch.object(cache_service, 'safe_get', return_value=cached_data):
            result = await cache_service.get_cached_word(normalized_word)

            assert result is not None
            assert result.word == "test"
            assert result.is_golden is True
            assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_cached_word_miss(self, cache_service):
        """测试缓存未命中场景"""
        normalized_word = "nonexistent"

        with patch.object(cache_service, 'safe_get', return_value=None):
            result = await cache_service.get_cached_word(normalized_word)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_cached_word_redis_error(self, cache_service):
        """测试Redis连接错误时的降级处理"""
        normalized_word = "test"

        with patch.object(cache_service, 'safe_get', side_effect=Exception("Redis connection failed")):
            result = await cache_service.get_cached_word(normalized_word)

            assert result is None

    @pytest.mark.asyncio
    async def test_cache_word_success(self, cache_service, sample_word_response):
        """测试成功缓存单词数据"""
        normalized_word = "test"

        with patch.object(cache_service, 'safe_setex', return_value=True):
            result = await cache_service.cache_word(normalized_word, sample_word_response)

            assert result is True

    @pytest.mark.asyncio
    async def test_cache_word_redis_error(self, cache_service, sample_word_response):
        """测试Redis写入错误时的处理"""
        normalized_word = "test"

        with patch.object(cache_service, 'safe_setex', side_effect=Exception("Redis write failed")):
            result = await cache_service.cache_word(normalized_word, sample_word_response)

            assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_word_cache_success(self, cache_service):
        """测试成功使单词缓存失效"""
        normalized_word = "test"

        with patch.object(cache_service, 'safe_delete', return_value=True):
            result = await cache_service.invalidate_word_cache(normalized_word)

            assert result is True

    @pytest.mark.asyncio
    async def test_invalidate_word_cache_redis_error(self, cache_service):
        """测试Redis删除错误时的处理"""
        normalized_word = "test"

        with patch.object(cache_service, 'safe_delete', side_effect=Exception("Redis delete failed")):
            result = await cache_service.invalidate_word_cache(normalized_word)

            assert result is False

    @pytest.mark.asyncio
    async def test_cache_word_data_serialization(self, cache_service):
        """测试缓存数据序列化/反序列化"""
        normalized_word = "test"
        word_response = WordQueryResponse(
            id=1,
            word="test",
            phonetic="/test/",
            part_of_speech="noun",
            core_game="测试核心游戏",
            scenario_formal="正式场景",
            scenario_casual="休闲场景",
            etymology_breakdown="词根拆解",
            etymology_story="词源故事",
            common_mistakes="常见错误",
            memory_trick="记忆技巧",
            is_golden=True,
            remaining_queries=10
        )

        serialized_data = word_response.model_dump_json()

        # 测试缓存存储
        with patch.object(cache_service, 'safe_setex', return_value=True) as mock_setex:
            cache_result = await cache_service.cache_word(normalized_word, word_response)
            assert cache_result is True
            mock_setex.assert_called_once_with(
                RedisKeys.word_cache(normalized_word),
                86400,
                serialized_data
            )

        # 测试缓存读取
        with patch.object(cache_service, 'safe_get', return_value=serialized_data):
            result = await cache_service.get_cached_word(normalized_word)

            assert result is not None
            assert result.id == word_response.id
            assert result.word == word_response.word
            assert result.phonetic == word_response.phonetic
            assert result.core_game == word_response.core_game
            assert result.is_golden == word_response.is_golden
            assert result.remaining_queries == word_response.remaining_queries

    @pytest.mark.asyncio
    async def test_get_cached_word_invalid_json(self, cache_service):
        """测试缓存数据损坏（无效JSON）的处理"""
        normalized_word = "test"

        with patch.object(cache_service, 'safe_get', return_value="invalid json data"), \
             patch.object(cache_service, 'safe_delete', return_value=True):
            result = await cache_service.get_cached_word(normalized_word)

            assert result is None

    def test_cache_stats(self, cache_service):
        """测试缓存统计功能"""
        # 初始状态
        stats = cache_service.get_cache_stats()
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["cache_hit_rate"] == 0.0
        assert stats["cache_ttl_hours"] == 24.0

        # 重置统计
        cache_service.reset_cache_stats()
        stats = cache_service.get_cache_stats()
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0

    @pytest.mark.asyncio
    async def test_cache_ttl_configuration(self, cache_service, sample_word_response):
        """测试缓存TTL配置正确性"""
        normalized_word = "test"
        expected_ttl = 86400  # 24小时

        with patch.object(cache_service, 'safe_setex', return_value=True) as mock_setex:
            await cache_service.cache_word(normalized_word, sample_word_response)

            call_args = mock_setex.call_args
            assert call_args[0][1] == expected_ttl  # 验证TTL

    @pytest.mark.asyncio
    async def test_warm_cache(self, cache_service):
        """测试缓存预热功能"""
        word_responses = [
            WordQueryResponse(
                id=1,
                word="word1",
                phonetic="/word1/",
                part_of_speech="noun",
                core_game="游戏1",
                scenario_formal="场景1",
                scenario_casual="休闲1",
                etymology_breakdown="拆解1",
                etymology_story="故事1",
                common_mistakes="错误1",
                memory_trick="技巧1",
                is_golden=False,
                remaining_queries=10
            ),
            WordQueryResponse(
                id=2,
                word="word2",
                phonetic="/word2/",
                part_of_speech="verb",
                core_game="游戏2",
                scenario_formal="场景2",
                scenario_casual="休闲2",
                etymology_breakdown="拆解2",
                etymology_story="故事2",
                common_mistakes="错误2",
                memory_trick="技巧2",
                is_golden=True,
                remaining_queries=10
            )
        ]

        with patch.object(cache_service, 'safe_setex', return_value=True):
            stats = await cache_service.warm_cache(word_responses)

            assert stats["total_words"] == 2
            assert stats["success_count"] == 2
            assert stats["error_count"] == 0
            assert stats["success_rate"] == 1.0