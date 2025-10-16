"""Gemini服务单元测试"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.ai.gemini_service import GeminiService
from app.services.ai.base import WordManualData, AIServiceError, AITimeoutError, AIRateLimitError, AIParseError
from google.api_core import exceptions as google_exceptions


@pytest.mark.asyncio
async def test_gemini_service_initialization():
    """测试Gemini服务初始化"""
    service = GeminiService(api_key="test_key_123", model="gemini-1.5-flash", timeout=30)
    assert service.model is not None
    assert service.timeout == 30


@pytest.mark.asyncio
async def test_gemini_service_invalid_key():
    """测试无效API Key"""
    with pytest.raises(AIServiceError, match="Gemini API Key未配置或无效"):
        GeminiService(api_key="", model="gemini-1.5-flash", timeout=30)

    with pytest.raises(AIServiceError, match="Gemini API Key未配置或无效"):
        GeminiService(api_key="your-gemini-api-key-here", model="gemini-1.5-flash", timeout=30)


@pytest.mark.asyncio
async def test_gemini_generate_word_manual_success():
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

    with patch("google.generativeai.configure"):
        with patch("google.generativeai.GenerativeModel") as mock_model_class:
            # Setup mock
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_model

            # Create service
            service = GeminiService(api_key="test_key_123", model="gemini-1.5-flash", timeout=30)

            # Test generation
            result = await service.generate_word_manual("test")

            # Assertions
            assert isinstance(result, WordManualData)
            assert result.word == "test"
            assert result.phonetic == "/test/"
            assert result.core_game == "测试游戏"
            mock_model.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_gemini_generate_word_manual_with_markdown():
    """测试解析带Markdown代码块的响应"""
    # Mock response with markdown
    mock_response = Mock()
    mock_response.text = """```json
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
```"""

    with patch("google.generativeai.configure"):
        with patch("google.generativeai.GenerativeModel") as mock_model_class:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_model

            service = GeminiService(api_key="test_key_123", model="gemini-1.5-flash", timeout=30)
            result = await service.generate_word_manual("test")

            assert isinstance(result, WordManualData)
            assert result.word == "test"


@pytest.mark.asyncio
async def test_gemini_timeout_error():
    """测试超时错误"""
    with patch("google.generativeai.configure"):
        with patch("google.generativeai.GenerativeModel") as mock_model_class:
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = google_exceptions.DeadlineExceeded("Timeout")
            mock_model_class.return_value = mock_model

            service = GeminiService(api_key="test_key_123", model="gemini-1.5-flash", timeout=30)

            with pytest.raises(AITimeoutError, match="Gemini生成超时"):
                await service.generate_word_manual("test")


@pytest.mark.asyncio
async def test_gemini_rate_limit_error():
    """测试限流错误"""
    with patch("google.generativeai.configure"):
        with patch("google.generativeai.GenerativeModel") as mock_model_class:
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = google_exceptions.ResourceExhausted("Rate limit")
            mock_model_class.return_value = mock_model

            service = GeminiService(api_key="test_key_123", model="gemini-1.5-flash", timeout=30)

            with pytest.raises(AIRateLimitError, match="Gemini API限流"):
                await service.generate_word_manual("test")


@pytest.mark.asyncio
async def test_gemini_permission_denied_error():
    """测试API密钥无效错误"""
    with patch("google.generativeai.configure"):
        with patch("google.generativeai.GenerativeModel") as mock_model_class:
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = google_exceptions.PermissionDenied("Invalid API key")
            mock_model_class.return_value = mock_model

            service = GeminiService(api_key="test_key_123", model="gemini-1.5-flash", timeout=30)

            with pytest.raises(AIServiceError, match="Gemini API密钥无效"):
                await service.generate_word_manual("test")


@pytest.mark.asyncio
async def test_gemini_empty_response():
    """测试空响应"""
    mock_response = Mock()
    mock_response.text = ""

    with patch("google.generativeai.configure"):
        with patch("google.generativeai.GenerativeModel") as mock_model_class:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_model

            service = GeminiService(api_key="test_key_123", model="gemini-1.5-flash", timeout=30)

            with pytest.raises(AIParseError, match="Gemini返回空响应"):
                await service.generate_word_manual("test")


@pytest.mark.asyncio
async def test_gemini_invalid_json_response():
    """测试无效JSON响应"""
    mock_response = Mock()
    mock_response.text = "This is not valid JSON"

    with patch("google.generativeai.configure"):
        with patch("google.generativeai.GenerativeModel") as mock_model_class:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_model

            service = GeminiService(api_key="test_key_123", model="gemini-1.5-flash", timeout=30)

            with pytest.raises(AIParseError, match="Gemini返回格式错误"):
                await service.generate_word_manual("test")
