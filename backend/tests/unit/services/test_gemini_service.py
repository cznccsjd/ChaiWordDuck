"""Gemini服务单元测试 - 新版SDK"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.ai.gemini_service import GeminiService
from app.services.ai.base import WordManualData, AIServiceError, AITimeoutError, AIRateLimitError, AIParseError
from google.genai.errors import APIError


def test_gemini_service_initialization():
    """测试Gemini服务初始化"""
    service = GeminiService(api_key="test_key_123", model="gemini-2.5-flash", timeout=30)
    assert service.model == "gemini-2.5-flash"
    assert service.timeout == 30
    assert service.client is not None


def test_gemini_service_invalid_key():
    """测试无效API Key"""
    with pytest.raises(AIServiceError, match="Gemini API Key未配置或无效"):
        GeminiService(api_key="", model="gemini-2.5-flash", timeout=30)

    with pytest.raises(AIServiceError, match="Gemini API Key未配置或无效"):
        GeminiService(api_key="your-gemini-api-key-here", model="gemini-2.5-flash", timeout=30)


def test_gemini_generate_word_manual_success():
    """测试成功生成单词手册"""
    # Mock response
    mock_response = Mock()
    mock_response.text = """{
        "word": "test",
        "phonetic": "/test/",
        "part_of_speech": "noun",
        "core_game": "测试游戏",
        "scenario_formal": "This is a test.",
        "scenario_casual": "Let's test it!",
        "etymology_breakdown": "From Latin testum",
        "etymology_story": "Ancient testing story",
        "memory_trick": "Remember: test = 测试",
        "common_mistakes": "Don't confuse with taste"
    }"""

    with patch("google.genai.Client") as mock_client_class:
        # Setup mock
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Create service
        service = GeminiService(api_key="test_key_123", model="gemini-2.5-flash", timeout=30)

        # Test generation
        result = service.generate_word_manual("test")

        # Assertions
        assert isinstance(result, WordManualData)
        assert result.word == "test"
        assert result.phonetic == "/test/"
        assert result.core_game == "测试游戏"
        mock_client.models.generate_content.assert_called_once()


def test_gemini_generate_word_manual_with_whitespace():
    """测试解析带空格的JSON响应"""
    # Mock response with whitespace
    mock_response = Mock()
    mock_response.text = """
    {
        "word": "test",
        "phonetic": "/test/",
        "part_of_speech": "noun",
        "core_game": "测试游戏",
        "scenario_formal": "This is a test.",
        "scenario_casual": "Let's test it!",
        "etymology_breakdown": "From Latin testum",
        "etymology_story": "Ancient testing story",
        "memory_trick": "Remember: test = 测试",
        "common_mistakes": "Don't confuse with taste"
    }
    """

    with patch("google.genai.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = GeminiService(api_key="test_key_123", model="gemini-2.5-flash", timeout=30)
        result = service.generate_word_manual("test")

        assert isinstance(result, WordManualData)
        assert result.word == "test"


def test_gemini_timeout_error():
    """测试超时错误"""
    with patch("google.genai.Client") as mock_client_class:
        mock_client = MagicMock()
        # 使用通用Exception模拟超时错误，包含timeout关键词
        mock_client.models.generate_content.side_effect = Exception("Request timeout occurred")
        mock_client_class.return_value = mock_client

        service = GeminiService(api_key="test_key_123", model="gemini-2.5-flash", timeout=30)

        with pytest.raises(AITimeoutError, match="Gemini生成超时"):
            service.generate_word_manual("test")


def test_gemini_rate_limit_error():
    """测试限流错误"""
    with patch("google.genai.Client") as mock_client_class:
        mock_client = MagicMock()
        # 使用通用Exception模拟限流错误，包含rate limit关键词
        mock_client.models.generate_content.side_effect = Exception("Rate limit exceeded")
        mock_client_class.return_value = mock_client

        service = GeminiService(api_key="test_key_123", model="gemini-2.5-flash", timeout=30)

        with pytest.raises(AIRateLimitError, match="Gemini API限流"):
            service.generate_word_manual("test")


def test_gemini_permission_denied_error():
    """测试API密钥无效错误"""
    with patch("google.genai.Client") as mock_client_class:
        mock_client = MagicMock()
        # 使用通用Exception模拟权限错误，包含permission关键词
        mock_client.models.generate_content.side_effect = Exception("Permission denied")
        mock_client_class.return_value = mock_client

        service = GeminiService(api_key="test_key_123", model="gemini-2.5-flash", timeout=30)

        with pytest.raises(AIServiceError, match="Gemini API密钥无效"):
            service.generate_word_manual("test")


def test_gemini_empty_response():
    """测试空响应"""
    mock_response = Mock()
    mock_response.text = ""

    with patch("google.genai.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = GeminiService(api_key="test_key_123", model="gemini-2.5-flash", timeout=30)

        with pytest.raises(AIParseError, match="Gemini返回空内容"):
            service.generate_word_manual("test")


def test_gemini_invalid_json_response():
    """测试无效JSON响应"""
    mock_response = Mock()
    mock_response.text = "This is not valid JSON"

    with patch("google.genai.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        service = GeminiService(api_key="test_key_123", model="gemini-2.5-flash", timeout=30)

        with pytest.raises(AIParseError, match="Gemini返回格式错误"):
            service.generate_word_manual("test")


def test_gemini_service_schema_definition():
    """测试Schema定义正确性"""
    service = GeminiService(api_key="test_key_123", model="gemini-2.5-flash", timeout=30)

    # 检查Schema是否正确定义
    assert service.response_schema is not None
    assert hasattr(service.response_schema, 'properties')
    assert 'word' in service.response_schema.properties
    assert 'core_game' in service.response_schema.properties
    assert len(service.response_schema.required) == 10
