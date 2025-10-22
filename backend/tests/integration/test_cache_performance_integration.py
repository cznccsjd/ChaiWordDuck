"""
缓存性能集成测试

验证缓存机制的性能优化效果和错误处理
"""
import json
import time
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient

from app.core.redis_keys import RedisKeys


@pytest.mark.asyncio
class TestCachePerformanceIntegration:
    """缓存性能集成测试"""

    async def test_cache_performance_requirement(
        self, async_client: AsyncClient, mock_redis: AsyncMock, test_user_token: str
    ):
        """验证缓存响应时间满足性能要求 (<50ms)"""
        normalized_word = "performance_test"

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

        # 执行多次性能测试
        response_times = []
        for i in range(10):
            start_time = time.time()
            response = await async_client.post(
                "/api/v1/words/query",
                json={"word": normalized_word},
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            response_time = (time.time() - start_time) * 1000
            response_times.append(response_time)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["word"] == normalized_word

        # 分析性能数据
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        # 验证性能要求
        assert avg_time < 50, f"平均响应时间 {avg_time:.2f}ms 超过50ms限制"
        assert max_time < 100, f"最大响应时间 {max_time:.2f}ms 过长"
        assert min_time < 30, f"最小响应时间 {min_time:.2f}ms 应该更快"

        print(f"缓存性能测试结果:")
        print(f"  平均响应时间: {avg_time:.2f}ms")
        print(f"  最大响应时间: {max_time:.2f}ms")
        print(f"  最小响应时间: {min_time:.2f}ms")
        print(f"  所有响应时间: {[f'{t:.2f}ms' for t in response_times]}")

    async def test_cache_vs_database_performance(
        self, async_client: AsyncClient, mock_redis: AsyncMock, test_user_token: str
    ):
        """比较缓存命中与数据库查询的性能差异"""
        normalized_word = "compare_test"

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

        # 测试缓存命中性能
        mock_redis.get.return_value = json.dumps(word_response_data)
        mock_redis.setex.return_value = True

        cache_times = []
        for _ in range(5):
            start_time = time.time()
            response = await async_client.post(
                "/api/v1/words/query",
                json={"word": normalized_word},
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            cache_times.append((time.time() - start_time) * 1000)
            assert response.status_code == 200

        # 测试缓存未命中（模拟数据库查询）
        mock_redis.get.return_value = None
        db_times = []
        for _ in range(3):  # 数据库查询测试次数少一些
            start_time = time.time()
            response = await async_client.post(
                "/api/v1/words/query",
                json={"word": f"db_{normalized_word}"},
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            db_times.append((time.time() - start_time) * 1000)
            # 数据库查询可能返回404，这是正常的

        # 计算性能提升
        avg_cache_time = sum(cache_times) / len(cache_times)
        avg_db_time = sum(db_times) / len(db_times) if db_times else avg_cache_time
        performance_improvement = ((avg_db_time - avg_cache_time) / avg_db_time) * 100 if avg_db_time > 0 else 0

        print(f"性能对比结果:")
        print(f"  缓存平均时间: {avg_cache_time:.2f}ms")
        print(f"  数据库平均时间: {avg_db_time:.2f}ms")
        print(f"  性能提升: {performance_improvement:.1f}%")

        # 验证缓存确实更快（至少快20%）
        if avg_db_time > 0:
            assert performance_improvement > 20, f"缓存性能提升不足: {performance_improvement:.1f}%"

    async def test_cache_error_resilience(
        self, async_client: AsyncClient, mock_redis: AsyncMock, test_user_token: str
    ):
        """测试Redis故障时的系统韧性"""
        normalized_word = "resilience_test"

        # 模拟Redis连接失败
        mock_redis.get.side_effect = Exception("Redis connection failed")
        mock_redis.setex.side_effect = Exception("Redis connection failed")

        # 系统应该仍然可以正常工作（降级到数据库查询）
        response = await async_client.post(
            "/api/v1/words/query",
            json={"word": normalized_word},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        # 系统应该仍然可以响应（可能是200或404，但不应该是500）
        assert response.status_code in [200, 404, 422]  # 422可能是单词验证失败

        print("Redis故障时系统正常降级处理 ✓")

    async def test_cache_consistency_under_load(
        self, async_client: AsyncClient, mock_redis: AsyncMock, test_user_token: str
    ):
        """测试高并发下的缓存一致性"""
        normalized_word = "concurrent_test"

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

        # 并发请求测试
        import asyncio
        tasks = []
        for i in range(20):
            task = async_client.post(
                "/api/v1/words/query",
                json={"word": normalized_word},
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            tasks.append(task)

        # 执行并发请求
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证所有请求都成功
        success_count = 0
        for response in responses:
            if hasattr(response, 'status_code'):
                if response.status_code == 200:
                    success_count += 1
                    data = response.json()
                    assert data["data"]["word"] == normalized_word
                    assert data["data"]["id"] == 1
            else:
                print(f"请求异常: {response}")

        print(f"并发测试结果: {success_count}/20 请求成功")
        assert success_count >= 18, f"并发成功率过低: {success_count}/20"

    async def test_cache_ttl_behavior(
        self, async_client: AsyncClient, mock_redis: AsyncMock, test_user_token: str
    ):
        """测试缓存TTL行为"""
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

        # 验证TTL设置正确
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == cache_key
        assert call_args[0][1] == 86400  # 24小时

        print("缓存TTL设置验证通过 ✓")

    async def test_cache_statistics_endpoint(
        self, async_client: AsyncClient, mock_redis: AsyncMock
    ):
        """测试缓存统计端点"""
        # 获取缓存统计
        response = await async_client.get("/api/v1/words/cache/stats")

        # 端点应该可以正常访问
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cache_hits" in data["data"]
        assert "cache_misses" in data["data"]
        assert "cache_hit_rate" in data["data"]
        assert "total_requests" in data["data"]
        assert "cache_ttl_hours" in data["data"]

        # 验证数据类型
        stats = data["data"]
        assert isinstance(stats["cache_hits"], int)
        assert isinstance(stats["cache_misses"], int)
        assert isinstance(stats["cache_hit_rate"], float)
        assert isinstance(stats["total_requests"], int)
        assert isinstance(stats["cache_ttl_hours"], float)
        assert stats["cache_ttl_hours"] == 24.0

        print("缓存统计端点验证通过 ✓")

    async def test_cache_stats_reset_endpoint(
        self, async_client: AsyncClient
    ):
        """测试缓存统计重置端点"""
        # 重置缓存统计
        response = await async_client.post("/api/v1/words/cache/reset-stats")

        # 端点应该可以正常访问
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "reset successfully" in data["data"]

        print("缓存统计重置端点验证通过 ✓")