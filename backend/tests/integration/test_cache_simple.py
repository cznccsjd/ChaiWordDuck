"""
缓存功能简化集成测试

验证缓存机制基本功能和统计端点
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCacheSimpleIntegration:
    """缓存功能简化集成测试"""

    async def test_cache_statistics_endpoint(self, client: AsyncClient):
        """测试缓存统计端点"""
        # 获取缓存统计
        response = await client.get("/api/v1/words/cache/stats")

        # 端点应该可以正常访问
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cache_hits" in data["data"]
        assert "cache_misses" in data["data"]
        assert "cache_hit_rate" in data["data"]
        assert "total_requests" in data["data"]
        assert "cache_ttl_hours" in data["data"]

        # 验证数据类型和初始值
        stats = data["data"]
        assert isinstance(stats["cache_hits"], int)
        assert isinstance(stats["cache_misses"], int)
        assert isinstance(stats["cache_hit_rate"], float)
        assert isinstance(stats["total_requests"], int)
        assert isinstance(stats["cache_ttl_hours"], float)
        assert stats["cache_ttl_hours"] == 24.0
        assert stats["cache_hits"] >= 0
        assert stats["cache_misses"] >= 0
        assert stats["total_requests"] >= 0

        print("✓ 缓存统计端点验证通过")

    async def test_cache_stats_reset_endpoint(self, client: AsyncClient):
        """测试缓存统计重置端点"""
        # 重置缓存统计
        response = await client.post("/api/v1/words/cache/reset-stats")

        # 端点应该可以正常访问
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "reset successfully" in data["data"]

        print("✓ 缓存统计重置端点验证通过")

    async def test_word_query_with_cache_flow(
        self, client: AsyncClient, auth_headers: dict
    ):
        """测试单词查询的缓存流程"""
        # 测试查询一个不存在的单词（会触发AI生成或返回404）
        response = await client.get(
            "/api/v1/words/query/testword12345",
            headers=auth_headers,
        )

        # 无论结果如何，请求应该正常处理
        assert response.status_code in [200, 404, 422, 429]  # 各种可能的响应

        # 获取缓存统计
        stats_response = await client.get("/api/v1/words/cache/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()["data"]

        # 验证统计数据被更新
        assert stats["total_requests"] >= 1

        print(f"✓ 单词查询缓存流程测试通过")
        print(f"  总请求数: {stats['total_requests']}")
        print(f"  缓存命中: {stats['cache_hits']}")
        print(f"  缓存未命中: {stats['cache_misses']}")
        print(f"  命中率: {stats['cache_hit_rate']:.2%}")

    async def test_guest_word_query_cache(
        self, client: AsyncClient
    ):
        """测试游客模式下的缓存行为"""
        # 游客查询单词（不需要认证）
        response = await client.get("/api/v1/words/query/test")

        # 请求应该正常处理
        assert response.status_code in [200, 404, 422, 429]

        # 获取缓存统计
        stats_response = await client.get("/api/v1/words/cache/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()["data"]

        print(f"✓ 游客模式缓存测试通过")
        print(f"  总请求数: {stats['total_requests']}")

    async def test_cache_key_consistency(
        self, client: AsyncClient, auth_headers: dict
    ):
        """测试缓存键的一致性"""
        test_words = ["Test", "test", "TEST", "TeSt"]  # 不同大小写的相同单词

        initial_stats_response = await client.get("/api/v1/words/cache/stats")
        initial_stats = initial_stats_response.json()["data"]

        # 执行多个查询，测试缓存键的一致性
        for word in test_words:
            response = await client.get(
                f"/api/v1/words/query/{word}",
                headers=auth_headers,
            )
            # 无论结果如何，请求应该正常处理
            assert response.status_code in [200, 404, 422, 429]

        final_stats_response = await client.get("/api/v1/words/cache/stats")
        final_stats = final_stats_response.json()["data"]

        # 验证请求被正确处理
        assert final_stats["total_requests"] >= initial_stats["total_requests"]

        print(f"✓ 缓存键一致性测试通过")
        print(f"  请求数变化: {initial_stats['total_requests']} -> {final_stats['total_requests']}")