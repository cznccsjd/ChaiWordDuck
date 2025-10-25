"""AI服务多语言支持测试"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from app.services.ai.base import WordManualData, AIServiceBase
from app.services.ai.gemini_service import GeminiService
from app.services.ai.openai_service import OpenAIService
from app.prompts.manager import get_prompt_manager
from app.prompts.enums import Language, AIProvider


class TestAIServiceMultiLanguage:
    """AI服务多语言功能测试基类"""

    @pytest.fixture
    def mock_word_data(self):
        """模拟返回的单词数据"""
        return WordManualData(
            word="test",
            phonetic="[test]",
            part_of_speech="noun",
            core_game="测试游戏内容",
            scenario_formal="正式场景：This is a test. 这是一个测试。",
            scenario_casual="日常场景：Let's test this. 我们来测试这个。",
            etymology_breakdown="词源拆解内容",
            etymology_story="词源故事",
            memory_trick="记忆技巧",
            common_mistakes="常见错误"
        )

    @pytest.fixture
    def mock_prompt_manager(self):
        """模拟Prompt管理器"""
        mock_manager = Mock()
        mock_manager.render_prompt.return_value = (
            "You are a professional English teaching expert.",
            "Please explain the word test."
        )
        mock_manager.get_provider_config.return_value = Mock(
            default_temperature=0.7,
            default_max_tokens=2000
        )
        return mock_manager

    @patch('app.services.ai.gemini_service.genai.Client')
    def test_gemini_service_language_parameter_chinese(self, mock_genai_client, mock_word_data):
        """测试Gemini服务中文语言参数"""
        # Mock client and response
        mock_client = Mock()
        mock_genai_client.return_value = mock_client

        mock_response = Mock()
        mock_response.text = mock_word_data.model_dump_json()
        mock_client.models.generate_content.return_value = mock_response

        # Mock prompt manager
        with patch('app.services.ai.gemini_service.get_prompt_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.render_prompt.return_value = (
                "你是一位专业的英语教学专家。",
                "请解释单词 test"
            )
            mock_get_manager.return_value = mock_manager

            # Create service and test
            service = GeminiService(api_key="test_key", model="gemini-2.5-flash", timeout=30)

            # Test with Chinese language parameter
            result = service.generate_word_manual("test", language=Language.CHINESE)

            # Verify prompt manager was called with correct language
            mock_manager.render_prompt.assert_called_once_with(
                word="test",
                language=Language.CHINESE,
                provider=AIProvider.GEMINI,
                prompt_type="word_generation"
            )

            # Verify result
            assert result.word == "test"
            assert isinstance(result, WordManualData)

    @patch('app.services.ai.gemini_service.genai.Client')
    def test_gemini_service_language_parameter_english(self, mock_genai_client, mock_word_data):
        """测试Gemini服务英文语言参数"""
        # Mock client and response
        mock_client = Mock()
        mock_genai_client.return_value = mock_client

        # Create English word data
        english_word_data = WordManualData(
            word="test",
            phonetic="[test]",
            part_of_speech="noun",
            core_game="Test game content",
            scenario_formal="Formal scenario: This is a test.",
            scenario_casual="Casual scenario: Let's test this.",
            etymology_breakdown="Etymology breakdown",
            etymology_story="Etymology story",
            memory_trick="Memory trick",
            common_mistakes="Common mistakes"
        )

        mock_response = Mock()
        mock_response.text = english_word_data.model_dump_json()
        mock_client.models.generate_content.return_value = mock_response

        # Mock prompt manager
        with patch('app.services.ai.gemini_service.get_prompt_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.render_prompt.return_value = (
                "You are a professional English teaching expert.",
                "Please explain the word test"
            )
            mock_get_manager.return_value = mock_manager

            # Create service and test
            service = GeminiService(api_key="test_key", model="gemini-2.5-flash", timeout=30)

            # Test with English language parameter
            result = service.generate_word_manual("test", language=Language.ENGLISH)

            # Verify prompt manager was called with correct language
            mock_manager.render_prompt.assert_called_once_with(
                word="test",
                language=Language.ENGLISH,
                provider=AIProvider.GEMINI,
                prompt_type="word_generation"
            )

            # Verify result
            assert result.word == "test"

    @patch('app.services.ai.gemini_service.genai.Client')
    def test_gemini_service_default_language(self, mock_genai_client, mock_word_data):
        """测试Gemini服务默认语言参数（中文）"""
        # Mock client and response
        mock_client = Mock()
        mock_genai_client.return_value = mock_client

        mock_response = Mock()
        mock_response.text = mock_word_data.model_dump_json()
        mock_client.models.generate_content.return_value = mock_response

        # Mock prompt manager
        with patch('app.services.ai.gemini_service.get_prompt_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.render_prompt.return_value = (
                "你是一位专业的英语教学专家。",
                "请解释单词 test"
            )
            mock_get_manager.return_value = mock_manager

            # Create service and test
            service = GeminiService(api_key="test_key", model="gemini-2.5-flash", timeout=30)

            # Test without language parameter (should default to Chinese)
            result = service.generate_word_manual("test")

            # Verify prompt manager was called with default language
            mock_manager.render_prompt.assert_called_once_with(
                word="test",
                language=Language.CHINESE,
                provider=AIProvider.GEMINI,
                prompt_type="word_generation"
            )

            # Verify result
            assert result.word == "test"

    @patch('app.services.ai.openai_service.AsyncOpenAI')
    @pytest.mark.asyncio
    async def test_openai_service_language_parameter_chinese(self, mock_openai_client, mock_word_data):
        """测试OpenAI服务中文语言参数"""
        # Mock client and response
        mock_client = AsyncMock()
        mock_openai_client.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = mock_word_data.model_dump_json()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Mock prompt manager
        with patch('app.services.ai.openai_service.get_prompt_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.render_prompt.return_value = (
                "你是一位专业的英语教学专家。",
                "请解释单词 test"
            )
            mock_manager.get_provider_config.return_value = Mock(
                default_temperature=0.7,
                default_max_tokens=2000
            )
            mock_get_manager.return_value = mock_manager

            # Create service and test
            service = OpenAIService(api_key="test_key", model="gpt-4", timeout=30)

            # Test with Chinese language parameter
            result = await service.generate_word_manual("test", language=Language.CHINESE)

            # Verify prompt manager was called with correct language
            mock_manager.render_prompt.assert_called_once_with(
                word="test",
                language=Language.CHINESE,
                provider=AIProvider.OPENAI,
                prompt_type="word_generation"
            )

            # Verify result
            assert result.word == "test"

    @patch('app.services.ai.openai_service.AsyncOpenAI')
    @pytest.mark.asyncio
    async def test_openai_service_language_parameter_english(self, mock_openai_client, mock_word_data):
        """测试OpenAI服务英文语言参数"""
        # Create English word data
        english_word_data = WordManualData(
            word="test",
            phonetic="[test]",
            part_of_speech="noun",
            core_game="Test game content",
            scenario_formal="Formal scenario: This is a test.",
            scenario_casual="Casual scenario: Let's test this.",
            etymology_breakdown="Etymology breakdown",
            etymology_story="Etymology story",
            memory_trick="Memory trick",
            common_mistakes="Common mistakes"
        )

        # Mock client and response
        mock_client = AsyncMock()
        mock_openai_client.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = english_word_data.model_dump_json()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Mock prompt manager
        with patch('app.services.ai.openai_service.get_prompt_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.render_prompt.return_value = (
                "You are a professional English teaching expert.",
                "Please explain the word test"
            )
            mock_manager.get_provider_config.return_value = Mock(
                default_temperature=0.7,
                default_max_tokens=2000
            )
            mock_get_manager.return_value = mock_manager

            # Create service and test
            service = OpenAIService(api_key="test_key", model="gpt-4", timeout=30)

            # Test with English language parameter
            result = await service.generate_word_manual("test", language=Language.ENGLISH)

            # Verify prompt manager was called with correct language
            mock_manager.render_prompt.assert_called_once_with(
                word="test",
                language=Language.ENGLISH,
                provider=AIProvider.OPENAI,
                prompt_type="word_generation"
            )

            # Verify result
            assert result.word == "test"

    @patch('app.services.ai.openai_service.AsyncOpenAI')
    @pytest.mark.asyncio
    async def test_openai_service_default_language(self, mock_openai_client, mock_word_data):
        """测试OpenAI服务默认语言参数（中文）"""
        # Mock client and response
        mock_client = AsyncMock()
        mock_openai_client.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = mock_word_data.model_dump_json()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Mock prompt manager
        with patch('app.services.ai.openai_service.get_prompt_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.render_prompt.return_value = (
                "你是一位专业的英语教学专家。",
                "请解释单词 test"
            )
            mock_manager.get_provider_config.return_value = Mock(
                default_temperature=0.7,
                default_max_tokens=2000
            )
            mock_get_manager.return_value = mock_manager

            # Create service and test
            service = OpenAIService(api_key="test_key", model="gpt-4", timeout=30)

            # Test without language parameter (should default to Chinese)
            result = await service.generate_word_manual("test")

            # Verify prompt manager was called with default language
            mock_manager.render_prompt.assert_called_once_with(
                word="test",
                language=Language.CHINESE,
                provider=AIProvider.OPENAI,
                prompt_type="word_generation"
            )

            # Verify result
            assert result.word == "test"

    def test_prompt_manager_language_support(self):
        """测试Prompt管理器多语言支持"""
        # This test will verify the actual prompt manager functionality
        prompt_manager = get_prompt_manager()

        # Test supported languages
        supported_languages = prompt_manager.get_supported_languages()
        assert Language.CHINESE in supported_languages
        assert Language.ENGLISH in supported_languages

        # Test template rendering for Chinese
        system_prompt, user_prompt = prompt_manager.render_prompt(
            word="test",
            language=Language.CHINESE,
            provider=AIProvider.GEMINI
        )

        assert system_prompt is not None
        assert user_prompt is not None
        assert "test" in user_prompt

        # Test template rendering for English
        system_prompt, user_prompt = prompt_manager.render_prompt(
            word="test",
            language=Language.ENGLISH,
            provider=AIProvider.OPENAI
        )

        assert system_prompt is not None
        assert user_prompt is not None
        assert "test" in user_prompt

    def test_language_parameter_validation(self):
        """测试语言参数验证"""
        prompt_manager = get_prompt_manager()

        # Test invalid language (should fallback to Chinese)
        system_prompt, user_prompt = prompt_manager.render_prompt(
            word="test",
            language="invalid_lang",
            provider=AIProvider.GEMINI
        )

        # Should still work (fallback to Chinese)
        assert system_prompt is not None
        assert user_prompt is not None

    @patch('app.services.ai.gemini_service.genai.Client')
    def test_language_fallback_mechanism(self, mock_genai_client, mock_word_data):
        """测试语言降级机制"""
        # Mock client and response
        mock_client = Mock()
        mock_genai_client.return_value = mock_client

        mock_response = Mock()
        mock_response.text = mock_word_data.model_dump_json()
        mock_client.models.generate_content.return_value = mock_response

        # Mock prompt manager to simulate fallback
        with patch('app.services.ai.gemini_service.get_prompt_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.render_prompt.return_value = (
                "你是一位专业的英语教学专家。",  # Falls back to Chinese
                "请解释单词 test"
            )
            mock_get_manager.return_value = mock_manager

            # Create service and test
            service = GeminiService(api_key="test_key", model="gemini-2.5-flash", timeout=30)

            # Test with unsupported language
            result = service.generate_word_manual("test", language="unsupported_lang")

            # Should still work with fallback
            assert result.word == "test"
            mock_manager.render_prompt.assert_called_once()