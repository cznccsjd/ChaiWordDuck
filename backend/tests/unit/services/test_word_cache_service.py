"""
单词缓存服务测试

测试Redis缓存机制的单词查询服务
遵循TDD方法，先写测试再实现功能
"""
import json
from datetime import datetime
from unittest.mock import AsyncMock, patch
import pytest

from app.services.word_cache_service import WordCacheService
from app.models.word import Word
from app.schemas.word import WordQueryResponse
from app.core.redis_keys import RedisKeys


class TestWordCacheService:
    """单词缓存服务测试类"""

    @pytest.fixture
    def mock_redis(self):
        """模拟Redis客户端"""
        mock_redis = AsyncMock()
        return mock_redis

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        mock_db = AsyncMock()
        return mock_db

    @pytest.fixture
    def word_cache_service(self):
        """单词缓存服务实例"""
        return WordCacheService()

    @pytest.fixture
    def sample_word(self):
        """示例单词数据"""
        return Word(
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
            source="manual",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    @pytest.fixture
    def sample_word_response(self, sample_word):
        """示例单词查询响应"""
        return WordQueryResponse(
            id=sample_word.id,
            word=sample_word.word,
            phonetic=sample_word.phonetic,
            part_of_speech=sample_word.part_of_speech,
            core_game=sample_word.core_game,
            scenario_formal=sample_word.scenario_formal,
            scenario_casual=sample_word.scenario_casual,
            etymology_breakdown=sample_word.etymology_breakdown,
            etymology_story=sample_word.etymology_story,
            common_mistakes=sample_word.common_mistakes,
            memory_trick=sample_word.memory_trick,
            is_golden=sample_word.is_golden,
            remaining_queries=10
        )

    @pytest.mark.asyncio
    async def test_get_cached_word_hit(self, word_cache_service, sample_word_response):
        """测试缓存命中场景"""
        # Arrange
        normalized_word = "test"
        cached_data = sample_word_response.model_dump_json()

        with patch.object(word_cache_service, 'safe_get', return_value=cached_data):
            # Act
            result = await word_cache_service.get_cached_word(normalized_word)

            # Assert
            assert result is not None
            assert result.word == "test"
            assert result.is_golden is True

    @pytest.mark.asyncio
    async def test_get_cached_word_miss(self, word_cache_service):
        """测试缓存未命中场景"""
        # Arrange
        normalized_word = "nonexistent"

        with patch.object(word_cache_service, 'safe_get', return_value=None):
            # Act
            result = await word_cache_service.get_cached_word(normalized_word)

            # Assert
            assert result is None

    @pytest.mark.asyncio
    async def test_get_cached_word_redis_error(self, word_cache_service):
        """测试Redis连接错误时的降级处理"""
        # Arrange
        normalized_word = "test"

        with patch.object(word_cache_service, 'safe_get', side_effect=Exception("Redis connection failed")):
            # Act
            result = await word_cache_service.get_cached_word(normalized_word)

            # Assert
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_word_success(self, word_cache_service, mock_redis, sample_word_response):
        """测试成功缓存单词数据"""
        # Arrange
        normalized_word = "test"
        cache_key = RedisKeys.word_cache(normalized_word)
        expected_ttl = 86400  # 24小时

        mock_redis.setex.return_value = True

        # Act
        result = await word_cache_service.cache_word(normalized_word, sample_word_response)

        # Assert
        assert result is True
        mock_redis.setex.assert_called_once_with(
            cache_key,
            expected_ttl,
            sample_word_response.model_dump_json()
        )

    @pytest.mark.asyncio
    async def test_cache_word_redis_error(self, word_cache_service, mock_redis, sample_word_response):
        """测试Redis写入错误时的处理"""
        # Arrange
        normalized_word = "test"

        mock_redis.setex.side_effect = Exception("Redis write failed")

        # Act
        result = await word_cache_service.cache_word(normalized_word, sample_word_response)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_word_cache_success(self, word_cache_service, mock_redis):
        """测试成功使单词缓存失效"""
        # Arrange
        normalized_word = "test"
        cache_key = RedisKeys.word_cache(normalized_word)

        mock_redis.delete.return_value = 1

        # Act
        result = await word_cache_service.invalidate_word_cache(normalized_word)

        # Assert
        assert result is True
        mock_redis.delete.assert_called_once_with(cache_key)

    @pytest.mark.asyncio
    async def test_invalidate_word_cache_not_exists(self, word_cache_service, mock_redis):
        """测试使不存在的单词缓存失效"""
        # Arrange
        normalized_word = "nonexistent"
        cache_key = RedisKeys.word_cache(normalized_word)

        mock_redis.delete.return_value = 0

        # Act
        result = await word_cache_service.invalidate_word_cache(normalized_word)

        # Assert
        assert result is True  # 即使缓存不存在也返回成功
        mock_redis.delete.assert_called_once_with(cache_key)

    @pytest.mark.asyncio
    async def test_invalidate_word_cache_redis_error(self, word_cache_service, mock_redis):
        """测试Redis删除错误时的处理"""
        # Arrange
        normalized_word = "test"

        mock_redis.delete.side_effect = Exception("Redis delete failed")

        # Act
        result = await word_cache_service.invalidate_word_cache(normalized_word)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_cache_word_data_serialization(self, word_cache_service, mock_redis):
        """测试缓存数据序列化/反序列化"""
        # Arrange
        normalized_word = "test"
        cache_key = RedisKeys.word_cache(normalized_word)
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

        # 模拟序列化后的数据
        serialized_data = word_response.model_dump_json()
        mock_redis.get.return_value = serialized_data
        mock_redis.setex.return_value = True

        # Act - 缓存数据
        cache_result = await word_cache_service.cache_word(normalized_word, word_response)
        assert cache_result is True

        # Act - 获取缓存数据
        result = await word_cache_service.get_cached_word(normalized_word)

        # Assert - 验证数据完整性
        assert result is not None
        assert result.id == word_response.id
        assert result.word == word_response.word
        assert result.phonetic == word_response.phonetic
        assert result.core_game == word_response.core_game
        assert result.is_golden == word_response.is_golden
        assert result.remaining_queries == word_response.remaining_queries

        # 验证Redis操作调用
        mock_redis.setex.assert_called_once_with(
            cache_key,
            86400,
            serialized_data
        )
        mock_redis.get.assert_called_once_with(cache_key)

    @pytest.mark.asyncio
    async def test_get_cached_word_invalid_json(self, word_cache_service, mock_redis):
        """测试缓存数据损坏（无效JSON）的处理"""
        # Arrange
        normalized_word = "test"
        cache_key = RedisKeys.word_cache(normalized_word)

        mock_redis.get.return_value = "invalid json data"

        # Act
        result = await word_cache_service.get_cached_word(normalized_word)

        # Assert
        assert result is None
        mock_redis.get.assert_called_once_with(cache_key)

    @pytest.mark.asyncio
    async def test_cache_ttl_configuration(self, word_cache_service, mock_redis, sample_word_response):
        """测试缓存TTL配置正确性"""
        # Arrange
        normalized_word = "test"
        cache_key = RedisKeys.word_cache(normalized_word)
        expected_ttl = 86400  # 24小时，根据任务要求

        mock_redis.setex.return_value = True

        # Act
        await word_cache_service.cache_word(normalized_word, sample_word_response)

        # Assert
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == cache_key  # 验证缓存键
        assert call_args[0][1] == expected_ttl  # 验证TTL
        assert call_args[0][2] == sample_word_response.model_dump_json()  # 验证数据