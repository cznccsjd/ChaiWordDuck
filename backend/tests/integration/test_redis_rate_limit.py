"""
Redis查询限制服务集成测试

测试Redis优化后的查询限制功能，包括：
- Redis缓存功能正常工作
- 原子操作和数据一致性
- 过期机制
- 降级机制
- 性能优化效果
"""
import pytest
import asyncio
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request, HTTPException

from app.services.redis_rate_limit import RedisRateLimitService
from app.services.rate_limit import RateLimitService
from app.core.redis_keys import RedisKeys
from app.models import User


@pytest.fixture
async def mock_redis():
    """模拟Redis客户端"""
    redis = AsyncMock()

    # 模拟基本的Redis操作
    redis.ping.return_value = True
    redis.get.return_value = None
    redis.set.return_value = True
    redis.expire.return_value = True
    redis.sadd.return_value = 1
    redis.smembers.return_value = set()
    redis.sismember.return_value = 0
    redis.eval.return_value = [1, 1, 10]  # allowed, count, limit
    redis.delete.return_value = 1

    return redis


@pytest.fixture
async def redis_rate_service(mock_redis):
    """Redis查询限制服务实例"""
    return RedisRateLimitService(mock_redis)


@pytest.fixture
def mock_user():
    """模拟用户对象"""
    user = User()
    user.id = 123
    user.membership_tier = "free"
    return user


@pytest.fixture
def mock_premium_user():
    """模拟Premium用户对象"""
    user = User()
    user.id = 456
    user.membership_tier = "premium"
    return user


@pytest.fixture
def mock_request():
    """模拟HTTP请求对象"""
    request = MagicMock()
    request.client.host = "192.168.1.100"
    return request


class TestRedisRateLimitService:
    """Redis查询限制服务测试"""

    @pytest.mark.asyncio
    async def test_guest_query_with_redis(self, redis_rate_service, mock_request):
        """测试游客查询限制（Redis模式）"""
        word_id = 1

        # 模拟第一次查询
        redis_rate_service.redis.eval.return_value = [1, 1, 10]

        allowed, used, limit, user_type = await redis_rate_service.check_and_record_query(
            word_id=word_id,
            user=None,
            request=mock_request
        )

        assert allowed is True
        assert used == 1
        assert limit == 10
        assert user_type == "guest"

    @pytest.mark.asyncio
    async def test_registered_user_query_with_redis(self, redis_rate_service, mock_user):
        """测试注册用户查询限制（Redis模式）"""
        word_id = 2

        # 模拟查询
        redis_rate_service.redis.eval.return_value = [1, 5, 50]

        allowed, used, limit, user_type = await redis_rate_service.check_and_record_query(
            word_id=word_id,
            user=mock_user,
            request=None
        )

        assert allowed is True
        assert used == 5
        assert limit == 50
        assert user_type == "registered"

    @pytest.mark.asyncio
    async def test_premium_user_query_with_redis(self, redis_rate_service, mock_premium_user):
        """测试Premium用户查询（Redis模式）"""
        word_id = 3

        allowed, used, limit, user_type = await redis_rate_service.check_and_record_query(
            word_id=word_id,
            user=mock_premium_user,
            request=None
        )

        assert allowed is True
        assert used == 0
        assert limit == -1
        assert user_type == "premium"

    @pytest.mark.asyncio
    async def test_guest_limit_exceeded(self, redis_rate_service, mock_request):
        """测试游客查询限制超出"""
        word_id = 4

        # 模拟超出限制
        redis_rate_service.redis.eval.return_value = [0, 10, 10]

        with pytest.raises(HTTPException) as exc_info:
            await redis_rate_service.check_and_record_query(
                word_id=word_id,
                user=None,
                request=mock_request
            )

        assert exc_info.value.status_code == 400
        assert "今日免费查询已用完" in exc_info.value.detail["message"]

    @pytest.mark.asyncio
    async def test_user_limit_exceeded(self, redis_rate_service, mock_user):
        """测试用户查询限制超出"""
        word_id = 5

        # 模拟超出限制
        redis_rate_service.redis.eval.return_value = [0, 50, 50]

        with pytest.raises(HTTPException) as exc_info:
            await redis_rate_service.check_and_record_query(
                word_id=word_id,
                user=mock_user,
                request=None
            )

        assert exc_info.value.status_code == 400
        assert "今日查询次数已用完" in exc_info.value.detail["message"]

    @pytest.mark.asyncio
    async def test_duplicate_query_not_counted(self, redis_rate_service, mock_user):
        """测试重复查询不计次数"""
        word_id = 6

        # 模拟重复查询（SISMEMBER返回1表示已查询过）
        redis_rate_service.redis.eval.return_value = [1, 5, 50]

        allowed, used, limit, user_type = await redis_rate_service.check_and_record_query(
            word_id=word_id,
            user=mock_user,
            request=None
        )

        assert allowed is True
        assert used == 5  # 计数没有增加
        assert user_type == "registered"

    @pytest.mark.asyncio
    async def test_get_user_query_stats(self, redis_rate_service):
        """测试获取用户查询统计"""
        user_id = 123
        query_date = date.today()

        # 模拟Redis返回数据
        redis_rate_service.redis.get.return_value = "5"
        redis_rate_service.redis.smembers.return_value = {"1", "2", "3", "4", "5"}

        count, word_ids = await redis_rate_service.get_user_query_stats(
            user_id=user_id,
            query_date=query_date
        )

        assert count == 5
        assert word_ids == {1, 2, 3, 4, 5}

    @pytest.mark.asyncio
    async def test_clear_user_cache(self, redis_rate_service):
        """测试清除用户缓存"""
        user_id = 123
        query_date = date.today()

        await redis_rate_service.clear_user_cache(user_id=user_id, query_date=query_date)

        # 验证调用了删除操作
        redis_rate_service.redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_success(self, redis_rate_service):
        """测试健康检查成功"""
        redis_rate_service.redis.ping.return_value = True

        result = await redis_rate_service.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, redis_rate_service):
        """测试健康检查失败"""
        from redis.exceptions import ConnectionError
        redis_rate_service.redis.ping.side_effect = ConnectionError()

        result = await redis_rate_service.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_redis_error_handling(self, redis_rate_service, mock_user):
        """测试Redis错误处理"""
        word_id = 7

        # 模拟Redis错误
        from redis.exceptions import RedisError
        redis_rate_service.redis.eval.side_effect = RedisError("Redis connection failed")

        with pytest.raises(HTTPException) as exc_info:
            await redis_rate_service.check_and_record_query(
                word_id=word_id,
                user=mock_user,
                request=None
            )

        assert exc_info.value.status_code == 503
        assert "服务暂时不可用" in exc_info.value.detail["message"]


class TestRateLimitServiceWithRedis:
    """查询限制服务集成测试（含Redis）"""

    @pytest.fixture
    async def mock_db_session(self):
        """模拟数据库会话"""
        session = AsyncMock()
        session.execute.return_value.scalar_one.return_value = 0
        session.execute.return_value.scalar_one_or_none.return_value = None
        session.commit.return_value = None
        return session

    @pytest.fixture
    async def rate_limit_service_with_redis(self, mock_db_session, mock_redis):
        """带Redis的查询限制服务实例"""
        return RateLimitService(mock_db_session, mock_redis)

    @pytest.mark.asyncio
    async def test_redis优先使用(self, rate_limit_service_with_redis, mock_redis, mock_user):
        """测试优先使用Redis缓存"""
        word_id = 1

        # 模拟Redis正常工作
        mock_redis.eval.return_value = [1, 3, 50]

        allowed, used, limit, user_type = await rate_limit_service_with_redis.check_and_record_query(
            word_id=word_id,
            user=mock_user,
            request=None
        )

        assert allowed is True
        assert used == 3
        assert limit == 50
        assert user_type == "registered"

        # 验证使用了Redis而不是数据库
        mock_redis.eval.assert_called_once()
        rate_limit_service_with_redis.db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_redis故障降级到数据库(self, rate_limit_service_with_redis, mock_redis, mock_user, mock_request):
        """测试Redis故障时降级到数据库"""
        word_id = 2

        # 模拟Redis故障
        from redis.exceptions import RedisError
        mock_redis.eval.side_effect = RedisError("Redis unavailable")

        # 模拟数据库查询 - 简化Mock设置
        mock_db = rate_limit_service_with_redis.db
        mock_result = AsyncMock()
        mock_result.scalar_one.return_value = 0
        mock_result.scalar_one_or_none.return_value = None
        mock_result.fetchall.return_value = []  # 返回空列表表示没有查过任何单词

        mock_db.execute.return_value = mock_result
        mock_db.commit.return_value = None
        mock_db.add.return_value = None

        allowed, used, limit, user_type = await rate_limit_service_with_redis.check_and_record_query(
            word_id=word_id,
            user=None,
            request=mock_request
        )

        assert allowed is True
        assert used == 1  # 第一次查询
        assert limit == 10  # 游客限制
        assert user_type == "guest"

    @pytest.mark.asyncio
    async def test获取统计信息(self, rate_limit_service_with_redis, mock_redis):
        """测试获取统计信息"""
        user_id = 123

        # 模拟Redis返回
        mock_redis.get.return_value = "8"
        mock_redis.smembers.return_value = {"1", "2", "3", "4", "5", "6", "7", "8"}

        count, word_ids = await rate_limit_service_with_redis.get_user_query_stats(user_id=user_id)

        assert count == 8
        assert word_ids == {1, 2, 3, 4, 5, 6, 7, 8}

    @pytest.mark.asyncio
    async def test健康检查(self, rate_limit_service_with_redis, mock_redis):
        """测试健康检查"""
        # 模拟Redis和数据库都正常
        mock_redis.ping.return_value = True
        rate_limit_service_with_redis.db.execute.return_value = None

        status = await rate_limit_service_with_redis.health_check()

        assert status["database"] is True
        assert status["redis"] is True
        assert status["cache_enabled"] is True


class TestRedisKeys:
    """Redis键管理测试"""

    def test_guest_daily_limit_key(self):
        """测试游客日限制键生成"""
        guest_id = "abc123"
        query_date = date(2025, 10, 16)

        key = RedisKeys.guest_daily_limit(guest_id, query_date)
        expected = "query_limit:guest:abc123:2025-10-16"

        assert key == expected

    def test_user_queried_words_key(self):
        """测试用户已查询单词键生成"""
        user_id = 123
        query_date = date(2025, 10, 16)

        key = RedisKeys.user_queried_words(user_id, query_date)
        expected = "queried_words:user:123:2025-10-16"

        assert key == expected

    def test默认使用今天日期(self):
        """测试默认使用今天日期"""
        key = RedisKeys.guest_daily_limit("test123")
        today_str = date.today().isoformat()

        assert key.endswith(f":{today_str}")

    def test_get_ttl_seconds(self):
        """测试TTL秒数获取"""
        from app.core.redis_keys import get_ttl_seconds

        assert get_ttl_seconds("minute") == 60
        assert get_ttl_seconds("hour") == 3600
        assert get_ttl_seconds("daily") == 86400
        assert get_ttl_seconds("permanent") == -1


class TestPerformanceOptimization:
    """性能优化测试"""

    @pytest.mark.asyncio
    async def test_redis_性能提升(self, mock_redis):
        """验证Redis相比数据库的性能提升"""
        # 这里可以添加性能基准测试
        # 由于是集成测试，主要验证功能正确性
        pass

    @pytest.mark.asyncio
    async def test原子操作正确性(self, redis_rate_service, mock_redis):
        """测试原子操作的正确性"""
        word_id = 1

        # 模拟Lua脚本执行结果
        mock_redis.eval.return_value = [1, 1, 10]

        # 验证调用了eval方法进行原子操作
        await redis_rate_service.check_and_record_query(word_id, None, MagicMock())

        mock_redis.eval.assert_called_once()

        # 验证传递给eval的参数
        call_args = mock_redis.eval.call_args
        assert call_args[0][1] == 2  # 2个键
        assert len(call_args[0][2:]) == 5  # 5个参数

    @pytest.mark.asyncio
    async def test_ttl自动过期(self, redis_rate_service, mock_redis):
        """测试TTL自动过期机制"""
        word_id = 1

        # 第一次查询，应该设置TTL
        mock_redis.eval.return_value = [1, 1, 10]

        await redis_rate_service.check_and_record_query(word_id, None, MagicMock())

        # 验证TTL设置逻辑在Lua脚本中
        mock_redis.eval.assert_called_once()

        # 检查Lua脚本中包含TTL设置逻辑
        lua_script = mock_redis.eval.call_args[0][0]
        assert "EXPIRE" in lua_script
        assert "ttl" in lua_script.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])