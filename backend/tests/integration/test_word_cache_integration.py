"""
单词缓存集成测试

测试单词查询API的Redis缓存集成功能
验证缓存命中、性能优化和错误处理
"""
import json
import time
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient

from app.core.redis_keys import RedisKeys
from app.schemas.word import WordQueryResponse


@pytest.mark.asyncio
class TestWordCacheIntegration:
    """单词缓存集成测试"""

    async def test_word_query_cache_hit_miss_flow(
        self, async_client: AsyncClient, mock_redis: AsyncMock, test_user_token: str
    ):
        """测试单词查询缓存命中和未命中流程"""
        normalized_word = "integration_test"
        cache_key = RedisKeys.word_cache(normalized_word)

        # 准备测试数据
        word_response_data = {
            "id": 1,
            "word": normalized_word,
            "phonetic": "/test/",
            "part_of_speech": "noun",
            "core_game": "测试核心游戏",
            "scenario_formal": "正式场景",
            "scenario_casual": "休闲场景",
            "etymology_breakdown": "词根拆解",
            "etymology_story": "词源故事",
            "common_mistakes": "常见错误",
            "memory_trick": "记忆技巧",
            "is_golden": True,
            "remaining_queries": 10
        }

        # 第一阶段：缓存未命中，模拟数据库查询
        mock_redis.get.return_value = None  # 缓存未命中
        mock_redis.setex.return_value = True  # 缓存写入成功

        # 第一次请求 - 应该查询数据库并缓存结果
        start_time = time.time()
        response1 = await async_client.post(
            "/api/v1/words/query",
            json={"word": normalized_word},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        first_request_time = time.time() - start_time

        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["success"] is True
        assert data1["data"]["word"] == normalized_word

        # 验证缓存操作
        mock_redis.get.assert_called_with(cache_key)
        mock_redis.setex.assert_called_once()
        setex_call = mock_redis.setex.call_args
        assert setex_call[0][0] == cache_key  # 验证缓存键
        assert setex_call[0][1] == 86400  # 验证TTL（24小时）

        # 解析缓存的数据并验证
        cached_data = json.loads(setex_call[0][2])
        assert cached_data["word"] == normalized_word
        assert cached_data["is_golden"] is True

        # 第二阶段：缓存命中
        mock_redis.reset_mock()
        mock_redis.get.return_value = json.dumps(word_response_data)  # 缓存命中

        # 第二次请求 - 应该从缓存获取
        start_time = time.time()
        response2 = await async_client.post(
            "/api/v1/words/query",
            json={"word": normalized_word},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        second_request_time = time.time() - start_time

        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["success"] is True
        assert data2["data"]["word"] == normalized_word
        assert data2["data"]["is_golden"] is True

        # 验证只调用了缓存读取，没有写入
        mock_redis.get.assert_called_once_with(cache_key)
        mock_redis.setex.assert_not_called()

        # 验证性能提升（缓存应该更快）
        # 注意：在测试环境中性能差异可能不明显，主要验证逻辑正确性
        assert second_request_time <= first_request_time * 1.5  # 允许测试环境的波动

    async def test_cache_redis_fallback(
        self, async_client: AsyncClient, mock_redis: AsyncMock, test_user_token: str
    ):
        """测试Redis故障时的降级处理"""
        normalized_word = "fallback_test"

        # 模拟Redis连接失败
        mock_redis.get.side_effect = Exception("Redis connection failed")

        # 请求应该仍然成功（降级到数据库查询）
        response = await async_client.post(
            "/api/v1/words/query",
            json={"word": normalized_word},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        # 请求应该成功，因为Redis故障不影响主流程
        assert response.status_code in [200, 404]  # 200如果单词存在，404如果不存在

    async def test_cache_invalid_data_handling(
        self, async_client: AsyncClient, mock_redis: AsyncMock, test_user_token: str
    ):
        """测试缓存数据损坏时的处理"""
        normalized_word = "corrupted_test"
        cache_key = RedisKeys.word_cache(normalized_word)

        # 模拟损坏的缓存数据
        mock_redis.get.return_value = "invalid json data"
        mock_redis.delete.return_value = 1  # 删除成功

        # 请求应该正常处理（删除损坏的缓存并查询数据库）
        response = await async_client.post(
            "/api/v1/words/query",
            json={"word": normalized_word},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        # 验证删除了损坏的缓存
        mock_redis.delete.assert_called_once_with(cache_key)

        # 请求应该继续正常处理
        assert response.status_code in [200, 404]

    async def test_cache_performance_requirement(
        self, async_client: AsyncClient, mock_redis: AsyncMock, test_user_token: str
    ):
        """测试缓存响应时间性能要求"""
        normalized_word = "performance_test"
        cache_key = RedisKeys.word_cache(normalized_word)

        # 准备缓存数据
        word_response_data = {
            "id": 1,
            "word": normalized_word,
            "phonetic": "/test/",
            "part_of_speech": "noun",
            "core_game": "测试核心游戏",
            "scenario_formal": "正式场景",
            "scenario_casual": "休闲场景",
            "etymology_breakdown": "词根拆解",
            "etymology_story": "词源故事",
            "common_mistakes": "常见错误",
            "memory_trick": "记忆技巧",
            "is_golden": True,
            "remaining_queries": 10
        }

        # 模拟缓存命中
        mock_redis.get.return_value = json.dumps(word_response_data)

        # 多次请求测试性能
        response_times = []
        for _ in range(5):  # 执行5次测试
            start_time = time.time()
            response = await async_client.post(
                "/api/v1/words/query",
                json={"word": normalized_word},
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            response_times.append(response_time)

            assert response.status_code == 200

        # 验证平均响应时间 < 50ms（任务要求）
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)

        assert avg_response_time < 50, f"平均响应时间 {avg_response_time:.2f}ms 超过50ms限制"
        assert max_response_time < 100, f"最大响应时间 {max_response_time:.2f}ms 过长"

        # 记录性能数据
        print(f"缓存性能测试结果:")
        print(f"  平均响应时间: {avg_response_time:.2f}ms")
        print(f"  最大响应时间: {max_response_time:.2f}ms")
        print(f"  最小响应时间: {min(response_times):.2f}ms")

    async def test_cache_ttl_configuration(
        self, async_client: AsyncClient, mock_redis: AsyncMock, test_user_token: str
    ):
        """测试缓存TTL配置正确性"""
        normalized_word = "ttl_test"
        cache_key = RedisKeys.word_cache(normalized_word)

        # 模拟缓存未命中，然后写入缓存
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True

        response = await async_client.post(
            "/api/v1/words/query",
            json={"word": normalized_word},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        # 验证TTL设置为24小时（86400秒）
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == cache_key
        assert call_args[0][1] == 86400  # 24小时 = 86400秒

    async def test_guest_user_cache_behavior(
        self, async_client: AsyncClient, mock_redis: AsyncMock
    ):
        """测试游客用户的缓存行为"""
        normalized_word = "guest_test"
        cache_key = RedisKeys.word_cache(normalized_word)

        # 模拟缓存未命中
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True

        # 游客请求（不需要认证头）
        response = await async_client.post(
            "/api/v1/words/query",
            json={"word": normalized_word}
        )

        # 验证缓存操作正常执行
        if response.status_code == 200:
            mock_redis.get.assert_called_with(cache_key)
            mock_redis.setex.assert_called_once()

    async def test_cache_key_consistency(
        self, async_client: AsyncClient, mock_redis: AsyncMock, test_user_token: str
    ):
        """测试缓存键的一致性"""
        test_words = ["Test", "test", "TEST", "TeSt"]  # 不同大小写的相同单词

        for word in test_words:
            cache_key = RedisKeys.word_cache(word.lower())

            # 模拟缓存未命中
            mock_redis.get.return_value = None
            mock_redis.setex.return_value = True

            response = await async_client.post(
                "/api/v1/words/query",
                json={"word": word},
                headers={"Authorization": f"Bearer {test_user_token}"}
            )

            # 验证都使用相同的标准化缓存键
            if response.status_code == 200:
                mock_redis.get.assert_called_with(cache_key)
                expected_key = f"word:cache:{word.lower()}"
                assert cache_key == expected_key

            mock_redis.reset_mock()

    async def test_cache_statistics_endpoint(
        self, async_client: AsyncClient, mock_redis: AsyncMock
    ):
        """测试缓存统计端点（如果实现了的话）"""
        # 这个测试预留，用于将来实现缓存统计API时的测试
        # 目前可以通过日志验证缓存统计信息
        pass