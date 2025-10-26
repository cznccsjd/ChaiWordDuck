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
    """测试成功生成单词手册 - 新的嵌套结构"""
    # Mock response with nested structure
    mock_response = Mock()
    mock_response.text = """{
        "word": "test",
        "phonetic": "/test/",
        "translation": "测试",
        "part_of_speech": "noun",
        "core_game": {
            "content": "这是一个验证和确认的语言游戏"
        },
        "game_boards": {
            "board_a_speculative": {
                "type": "棋盘A (思辨场)",
                "name": "科学实验场",
                "example": "在实验中，我们需要对每个假设进行严格的test（测试）以确保结果的准确性。"
            },
            "board_b_life": {
                "type": "棋盘B (生活场)",
                "name": "健康检查局",
                "example": "医生建议我每年都要进行一次全面体检，包括各种test（检查）项目。"
            }
        },
        "etymology": {
            "breakdown": {
                "prefix": {
                    "part": "test-",
                    "meaning": "测试"
                },
                "root": {
                    "part": "test",
                    "meaning": "验证"
                },
                "suffix": {
                    "part": "",
                    "meaning": ""
                }
            },
            "story": "来自古法语test，意为'陶罐'，后演变为'检验'的含义，就像检验陶罐的质量一样。"
        },
        "common_mistakes": {
            "warning": "容易与taste混淆",
            "avoidance": "记住：test是测试，taste是品尝，字母a和e的位置不同"
        },
        "memory_trick": "想象一个TEST（考试）正在检验你的知识水平"
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

        # Assertions for nested structure
        assert isinstance(result, WordManualData)
        assert result.word == "test"
        assert result.phonetic == "/test/"
        assert result.translation == "测试"
        assert result.part_of_speech == "noun"

        # Test nested objects
        assert result.core_game.content == "这是一个验证和确认的语言游戏"
        assert result.game_boards.board_a_speculative.name == "科学实验场"
        assert result.game_boards.board_b_life.name == "健康检查局"
        assert result.etymology.breakdown.root["part"] == "test"
        assert result.common_mistakes.warning == "容易与taste混淆"
        assert result.memory_trick == "想象一个TEST（考试）正在检验你的知识水平"

        # Test backward compatibility
        assert "科学实验场" in result.get_scenario_formal()
        assert "健康检查局" in result.get_scenario_casual()

        mock_client.models.generate_content.assert_called_once()


def test_gemini_generate_word_manual_with_whitespace():
    """测试解析带空格的JSON响应 - 嵌套结构"""
    # Mock response with whitespace and nested structure
    mock_response = Mock()
    mock_response.text = """
    {
        "word": "test",
        "phonetic": "/test/",
        "translation": "测试",
        "part_of_speech": "noun",
        "core_game": {
            "content": "这是一个验证和确认的语言游戏"
        },
        "game_boards": {
            "board_a_speculative": {
                "type": "棋盘A (思辨场)",
                "name": "科学实验场",
                "example": "在实验中，我们需要对每个假设进行严格的test（测试）以确保结果的准确性。"
            },
            "board_b_life": {
                "type": "棋盘B (生活场)",
                "name": "健康检查局",
                "example": "医生建议我每年都要进行一次全面体检，包括各种test（检查）项目。"
            }
        },
        "etymology": {
            "breakdown": {
                "prefix": {"part": "test-", "meaning": "测试"},
                "root": {"part": "test", "meaning": "验证"},
                "suffix": {"part": "", "meaning": ""}
            },
            "story": "来自古法语test，意为'陶罐'，后演变为'检验'的含义。"
        },
        "common_mistakes": {
            "warning": "容易与taste混淆",
            "avoidance": "记住：test是测试，taste是品尝，字母a和e的位置不同"
        },
        "memory_trick": "想象一个TEST（考试）正在检验你的知识水平"
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
        assert result.translation == "测试"
        assert result.core_game.content == "这是一个验证和确认的语言游戏"


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
    """测试Schema定义正确性 - 嵌套结构"""
    service = GeminiService(api_key="test_key_123", model="gemini-2.5-flash", timeout=30)

    # 检查Schema是否正确定义
    assert service.response_schema is not None
    assert hasattr(service.response_schema, 'properties')

    # 检查新增字段
    assert 'word' in service.response_schema.properties
    assert 'translation' in service.response_schema.properties
    assert 'core_game' in service.response_schema.properties
    assert 'game_boards' in service.response_schema.properties
    assert 'etymology' in service.response_schema.properties
    assert 'common_mistakes' in service.response_schema.properties

    # 检查嵌套结构
    assert service.response_schema.properties['core_game'].type.value == 'OBJECT'
    assert service.response_schema.properties['game_boards'].type.value == 'OBJECT'
    assert service.response_schema.properties['etymology'].type.value == 'OBJECT'
    assert service.response_schema.properties['common_mistakes'].type.value == 'OBJECT'

    # 检查必要字段数量（更新为新结构的字段数）
    assert len(service.response_schema.required) == 9
