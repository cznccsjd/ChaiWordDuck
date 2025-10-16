"""AI工厂主备切换测试"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.ai.factory import AIServiceFactory
from app.services.ai.base import AIServiceError
from app.services.ai.gemini_service import GeminiService
from app.services.ai.openai_service import OpenAIService


@pytest.fixture(autouse=True)
def reset_factory():
    """每个测试前重置工厂实例"""
    AIServiceFactory.reset_instance()
    yield
    AIServiceFactory.reset_instance()


def test_factory_primary_success():
    """测试主服务（Gemini）成功初始化"""
    # Mock settings
    mock_settings = Mock()
    mock_settings.ai_primary_provider = "gemini"
    mock_settings.ai_fallback_provider = "openai"
    mock_settings.gemini_api_key = "test_gemini_key"
    mock_settings.gemini_model = "gemini-1.5-flash"
    mock_settings.gemini_timeout = 30
    mock_settings.openai_api_key = "test_openai_key"
    mock_settings.openai_model = "gpt-4o-mini"
    mock_settings.openai_timeout = 30

    with patch("app.services.ai.factory.get_settings", return_value=mock_settings):
        with patch("google.generativeai.configure"):
            with patch("google.generativeai.GenerativeModel"):
                # Get service
                service = AIServiceFactory.get_service()

                # Assertions
                assert service is not None
                assert isinstance(service, GeminiService)
                assert AIServiceFactory.get_current_provider() == "gemini"


def test_factory_fallback_on_primary_failure():
    """测试主服务失败时切换到备用服务（OpenAI）"""
    # Mock settings
    mock_settings = Mock()
    mock_settings.ai_primary_provider = "gemini"
    mock_settings.ai_fallback_provider = "openai"
    mock_settings.gemini_api_key = ""  # Invalid key to trigger failure
    mock_settings.gemini_model = "gemini-1.5-flash"
    mock_settings.gemini_timeout = 30
    mock_settings.openai_api_key = "test_openai_key"
    mock_settings.openai_model = "gpt-4o-mini"
    mock_settings.openai_timeout = 30

    with patch("app.services.ai.factory.get_settings", return_value=mock_settings):
        with patch("openai.OpenAI"):
            # Get service (should fallback to OpenAI)
            service = AIServiceFactory.get_service()

            # Assertions
            assert service is not None
            assert isinstance(service, OpenAIService)
            assert AIServiceFactory.get_current_provider() == "openai"


def test_factory_both_providers_fail():
    """测试主备服务都失败时抛出异常"""
    # Mock settings with invalid keys for both providers
    mock_settings = Mock()
    mock_settings.ai_primary_provider = "gemini"
    mock_settings.ai_fallback_provider = "openai"
    mock_settings.gemini_api_key = ""  # Invalid
    mock_settings.gemini_model = "gemini-1.5-flash"
    mock_settings.gemini_timeout = 30
    mock_settings.openai_api_key = ""  # Invalid
    mock_settings.openai_model = "gpt-4o-mini"
    mock_settings.openai_timeout = 30

    with patch("app.services.ai.factory.get_settings", return_value=mock_settings):
        # Should raise AIServiceError
        with pytest.raises(AIServiceError, match="Both primary .* and fallback .* AI providers failed"):
            AIServiceFactory.get_service()


def test_factory_singleton_pattern():
    """测试单例模式：同一配置下返回同一实例"""
    # Mock settings
    mock_settings = Mock()
    mock_settings.ai_primary_provider = "gemini"
    mock_settings.ai_fallback_provider = "openai"
    mock_settings.gemini_api_key = "test_gemini_key"
    mock_settings.gemini_model = "gemini-1.5-flash"
    mock_settings.gemini_timeout = 30
    mock_settings.openai_api_key = "test_openai_key"
    mock_settings.openai_model = "gpt-4o-mini"
    mock_settings.openai_timeout = 30

    with patch("app.services.ai.factory.get_settings", return_value=mock_settings):
        with patch("google.generativeai.configure"):
            with patch("google.generativeai.GenerativeModel"):
                # Get service twice
                service1 = AIServiceFactory.get_service()
                service2 = AIServiceFactory.get_service()

                # Should be the same instance
                assert service1 is service2


def test_factory_unsupported_provider():
    """测试不支持的提供商"""
    # Mock settings with unsupported provider
    mock_settings = Mock()
    mock_settings.ai_primary_provider = "unsupported_provider"
    mock_settings.ai_fallback_provider = "openai"
    mock_settings.openai_api_key = "test_openai_key"
    mock_settings.openai_model = "gpt-4o-mini"
    mock_settings.openai_timeout = 30

    with patch("app.services.ai.factory.get_settings", return_value=mock_settings):
        with patch("openai.OpenAI"):
            # Should fallback to openai since primary is unsupported
            service = AIServiceFactory.get_service()
            assert isinstance(service, OpenAIService)


def test_factory_reset_instance():
    """测试重置实例功能"""
    # Mock settings
    mock_settings = Mock()
    mock_settings.ai_primary_provider = "gemini"
    mock_settings.ai_fallback_provider = "openai"
    mock_settings.gemini_api_key = "test_gemini_key"
    mock_settings.gemini_model = "gemini-1.5-flash"
    mock_settings.gemini_timeout = 30

    with patch("app.services.ai.factory.get_settings", return_value=mock_settings):
        with patch("google.generativeai.configure"):
            with patch("google.generativeai.GenerativeModel"):
                # Get service
                service1 = AIServiceFactory.get_service()
                assert service1 is not None

                # Reset
                AIServiceFactory.reset_instance()
                assert AIServiceFactory._instance is None
                assert AIServiceFactory._current_provider is None

                # Get service again (should create new instance)
                service2 = AIServiceFactory.get_service()
                assert service2 is not None
                # Note: Can't compare instances directly as they're recreated
