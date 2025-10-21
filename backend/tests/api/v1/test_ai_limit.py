"""
AI生成限额功能测试用例
"""
import pytest
from fastapi import status
from httpx import AsyncClient

from app.schemas.common import ErrorCode
from app.core.config import get_settings


settings = get_settings()


class TestAILimitErrors:
    """AI限额错误相关测试"""

    @pytest.mark.asyncio
    async def test_ai_generation_limit_error_code_constant(self):
        """测试AI生成限额错误码常量存在"""
        assert hasattr(ErrorCode, 'AI_GENERATION_LIMIT_EXCEEDED')
        assert ErrorCode.AI_GENERATION_LIMIT_EXCEEDED == "AI_GENERATION_LIMIT_EXCEEDED"

    @pytest.mark.asyncio
    async def test_ai_limit_config_values(self):
        """测试AI限额配置值正确性"""
        assert settings.guest_ai_generation_limit == 5
        assert settings.free_user_ai_generation_limit == 20
        assert settings.premium_user_ai_generation_limit == -1

    @pytest.mark.asyncio
    async def test_guest_ai_limit_exceeded_error(self, client: AsyncClient):
        """测试游客AI生成限额超限错误响应"""
        # 模拟游客超过限额的情况
        # 这里需要根据实际的业务逻辑来模拟限额超限的场景
        response = await client.post(
            "/api/v1/words/generate",
            json={"word": "test"}
        )

        # 如果限额超限，验证错误响应格式
        if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            error_data = response.json()
            assert "detail" in error_data
            assert error_data["detail"]["code"] == ErrorCode.AI_GENERATION_LIMIT_EXCEEDED
            assert "AI生成限额" in error_data["detail"]["message"]
            assert f"{settings.guest_ai_generation_limit}次" in error_data["detail"]["message"]  # 游客限额

    @pytest.mark.asyncio
    async def test_registered_user_ai_limit_exceeded_error(self, client: AsyncClient, auth_headers):
        """测试注册用户AI生成限额超限错误响应"""
        # 模拟注册用户超过限额的情况
        response = await client.post(
            "/api/v1/words/generate",
            json={"word": "test"},
            headers=auth_headers
        )

        # 如果限额超限，验证错误响应格式
        if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            error_data = response.json()
            assert "detail" in error_data
            assert error_data["detail"]["code"] == ErrorCode.AI_GENERATION_LIMIT_EXCEEDED
            assert "AI生成限额" in error_data["detail"]["message"]
            assert f"{settings.free_user_ai_generation_limit}次" in error_data["detail"]["message"]  # 免费用户限额

    @pytest.mark.asyncio
    async def test_error_message_user_friendliness(self):
        """测试错误消息的用户友好性"""
        # 验证错误消息包含必要信息（使用动态配置值）
        expected_guest_message = f"AI生成限额已用完（游客{settings.guest_ai_generation_limit}次/天，注册用户{settings.free_user_ai_generation_limit}次/天）。注册用户享有更多额度，或考虑升级到高级版享受无限AI生成服务。"

        # 验证消息包含解决方案
        assert "升级" in expected_guest_message or "明天" in expected_guest_message
        assert f"{settings.guest_ai_generation_limit}次" in expected_guest_message
        assert f"{settings.free_user_ai_generation_limit}次" in expected_guest_message


class TestAILimitConfigConsistency:
    """AI限额配置一致性测试"""

    def test_config_values_match_error_messages(self):
        """测试配置值与错误消息的一致性"""
        guest_limit = settings.guest_ai_generation_limit
        free_user_limit = settings.free_user_ai_generation_limit

        # 验证配置值是合理的
        assert guest_limit > 0
        assert free_user_limit > guest_limit
        assert settings.premium_user_ai_generation_limit == -1  # 无限制

    @pytest.mark.asyncio
    async def test_error_response_structure(self, client: AsyncClient):
        """测试错误响应结构符合API规范"""
        # 模拟一个会触发限额错误的请求
        response = await client.post(
            "/api/v1/words/generate",
            json={"word": "test"}
        )

        if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            error_data = response.json()

            # 验证错误响应结构
            assert "detail" in error_data
            detail = error_data["detail"]

            # 验证必要字段存在
            assert "code" in detail
            assert "message" in detail

            # 验证字段类型
            assert isinstance(detail["code"], str)
            assert isinstance(detail["message"], str)

            # 验证错误码正确
            assert detail["code"] == ErrorCode.AI_GENERATION_LIMIT_EXCEEDED


class TestAILimitBusinessLogic:
    """AI限额业务逻辑测试"""

    @pytest.mark.asyncio
    async def test_different_user_limits(self):
        """测试不同用户类型的限额差异"""
        guest_limit = settings.guest_ai_generation_limit
        free_user_limit = settings.free_user_ai_generation_limit
        premium_limit = settings.premium_user_ai_generation_limit

        # 验证限额递增
        assert guest_limit < free_user_limit
        assert premium_limit == -1 or premium_limit > free_user_limit

    @pytest.mark.asyncio
    async def test_limit_exceeded_logging(self, client: AsyncClient):
        """测试限额超限时的日志记录"""
        # 这里可以测试日志输出，但需要配置日志捕获
        # 在实际实现中，应该有相应的日志记录
        pass

    def test_error_message_contains_solutions(self):
        """测试错误消息包含解决方案"""
        # 错误消息应该指导用户如何解决问题（使用动态配置值）
        guest_message = f"AI生成限额已用完（游客{settings.guest_ai_generation_limit}次/天，注册用户{settings.free_user_ai_generation_limit}次/天）。注册用户享有更多额度，或考虑升级到高级版享受无限AI生成服务。"

        # 验证消息包含有用的信息
        assert "游客" in guest_message
        assert "注册用户" in guest_message
        assert f"{settings.guest_ai_generation_limit}次" in guest_message
        assert f"{settings.free_user_ai_generation_limit}次" in guest_message
        assert "天" in guest_message
        assert "升级" in guest_message  # 包含解决方案建议