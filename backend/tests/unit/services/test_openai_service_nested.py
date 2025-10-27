"""OpenAI服务嵌套结构测试 - 新版Schema测试"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.ai.openai_service import OpenAIService
from app.services.ai.base import (
    WordManualData, GameBoard, EtymologyBreakdown, Etymology,
    CoreGame, CommonMistakes, GameBoards,
    AIServiceError, AITimeoutError, AIRateLimitError, AIParseError
)
from openai import OpenAIError, APITimeoutError, RateLimitError


class TestOpenAIServiceNestedStructure:
    """测试OpenAI服务的嵌套JSON结构支持"""

    @pytest.mark.asyncio
    async def test_openai_generate_nested_word_manual_success(self):
        """测试成功生成嵌套结构的单词手册"""
        # Mock nested response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """{
            "word": "accommodation",
            "phonetic": "[əˌkɒməˈdeɪʃən]",
            "translation": "accommodation",
            "part_of_speech": "noun",
            "core_game": {
                "content": "This is a game about adapting spaces and mutual inclusion"
            },
            "game_boards": {
                "board_a_speculative": {
                    "type": "Board A (Academic)",
                    "name": "Workplace Inclusion",
                    "example": "Successful marriage requires continuous emotional accommodation to cope with personality differences."
                },
                "board_b_life": {
                    "type": "Board B (Life)",
                    "name": "Travel Lodging",
                    "example": "We booked the hotel in advance, but finding cheap accommodation during peak season is very difficult."
                }
            },
            "etymology": {
                "breakdown": {
                    "prefix": {
                        "part": "ac-",
                        "meaning": "to, toward"
                    },
                    "root": {
                        "part": "modus",
                        "meaning": "mode, manner"
                    },
                    "suffix": {
                        "part": "-ation",
                        "meaning": "process, action"
                    }
                },
                "story": "Originally from Latin accommodare, meaning 'to adapt', later evolved to include providing shelter and adjusting meanings."
            },
            "common_mistakes": {
                "warning": "Easily confused with double c and double m in accommodation",
                "avoidance": "Remember: two c (like car) and two m (like moon)"
            },
            "memory_trick": "Imagine an AC room with a MODEM, needing accommodation of network signals"
        }"""

        with patch("app.prompts.manager.get_prompt_manager") as mock_prompt_manager:
            # Mock prompt manager
            mock_pm = Mock()
            mock_pm.render_prompt.return_value = ("system_prompt", "user_prompt")
            mock_pm.get_provider_config.return_value = Mock(
                default_temperature=0.7,
                default_max_tokens=2000
            )
            mock_prompt_manager.return_value = mock_pm

            with patch("openai.AsyncOpenAI") as mock_client_class:
                mock_client = AsyncMock()
                # 直接返回mock_response，不需要await
                mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
                mock_client_class.return_value = mock_client

                service = OpenAIService(api_key="test_key_123", model="gpt-4o-mini", timeout=30)
                result = await service.generate_word_manual("accommodation")

                # 验证嵌套结构
                assert isinstance(result, WordManualData)
                assert result.word == "accommodation"
                assert result.translation == "住宿，适应，调适"

                # 验证核心游戏
                assert isinstance(result.core_game, CoreGame)
                assert "适应空间" in result.core_game.content

                # 验证游戏棋盘
                assert isinstance(result.game_boards, GameBoards)
                assert isinstance(result.game_boards.board_a_speculative, GameBoard)
                assert isinstance(result.game_boards.board_b_life, GameBoard)
                assert result.game_boards.board_a_speculative.name == "职场包容牌局"
                assert result.game_boards.board_b_life.name == "旅行找宿局"

                # 验证词源
                assert isinstance(result.etymology, Etymology)
                assert isinstance(result.etymology.breakdown, EtymologyBreakdown)
                assert result.etymology.breakdown.prefix["part"] == "ac-"
                assert "适应" in result.etymology.story

                # 验证常见错误
                assert isinstance(result.common_mistakes, CommonMistakes)
                assert "混淆" in result.common_mistakes.warning
                assert "记住" in result.common_mistakes.avoidance

    @pytest.mark.asyncio
    async def test_openai_nested_validation_missing_field(self):
        """测试嵌套结构字段验证 - 缺少必要字段"""
        # Mock response missing required nested field
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """{
            "word": "test",
            "phonetic": "/test/",
            "core_game": {
                "content": "测试游戏"
            },
            "game_boards": {
                "board_a_speculative": {
                    "type": "棋盘A",
                    "name": "场名A",
                    "example": "示例A"
                },
                "board_b_life": {
                    "type": "棋盘B",
                    "name": "场名B",
                    "example": "示例B"
                }
            },
            "etymology": {
                "breakdown": {
                    "prefix": {"part": "pre-", "meaning": "前缀"},
                    "root": {"part": "root", "meaning": "词根"},
                    "suffix": {"part": "-suffix", "meaning": "后缀"}
                },
                "story": "词源故事"
            },
            "common_mistakes": {
                "warning": "警告",
                "avoidance": "避免方法"
            }
        }"""  # 缺少memory_trick字段

        with patch("app.prompts.manager.get_prompt_manager") as mock_prompt_manager:
            mock_pm = Mock()
            mock_pm.render_prompt.return_value = ("system_prompt", "user_prompt")
            mock_pm.get_provider_config.return_value = Mock(
                default_temperature=0.7,
                default_max_tokens=2000
            )
            mock_prompt_manager.return_value = mock_pm

            with patch("openai.AsyncOpenAI") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
                mock_client_class.return_value = mock_client

                service = OpenAIService(api_key="test_key_123", model="gpt-4o-mini", timeout=30)

                with pytest.raises(AIParseError, match="响应缺少必要字段"):
                    await service.generate_word_manual("test")

    @pytest.mark.asyncio
    async def test_openai_nested_validation_invalid_structure(self):
        """测试嵌套结构字段验证 - 无效结构"""
        # Mock response with invalid nested structure
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """{
            "word": "test",
            "phonetic": "/test/",
            "translation": "测试",
            "part_of_speech": "noun",
            "core_game": "invalid_string_structure",  # 应该是对象
            "game_boards": {
                "board_a_speculative": {
                    "type": "棋盘A",
                    "name": "场名A",
                    "example": "示例A"
                },
                "board_b_life": {
                    "type": "棋盘B",
                    "name": "场名B",
                    "example": "示例B"
                }
            },
            "etymology": {
                "breakdown": {
                    "prefix": {"part": "pre-", "meaning": "前缀"},
                    "root": {"part": "root", "meaning": "词根"},
                    "suffix": {"part": "-suffix", "meaning": "后缀"}
                },
                "story": "词源故事"
            },
            "common_mistakes": {
                "warning": "警告",
                "avoidance": "避免方法"
            },
            "memory_trick": "记忆技巧"
        }"""

        with patch("app.prompts.manager.get_prompt_manager") as mock_prompt_manager:
            mock_pm = Mock()
            mock_pm.render_prompt.return_value = ("system_prompt", "user_prompt")
            mock_pm.get_provider_config.return_value = Mock(
                default_temperature=0.7,
                default_max_tokens=2000
            )
            mock_prompt_manager.return_value = mock_pm

            with patch("openai.AsyncOpenAI") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
                mock_client_class.return_value = mock_client

                service = OpenAIService(api_key="test_key_123", model="gpt-4o-mini", timeout=30)

                with pytest.raises(AIParseError, match="core_game结构无效"):
                    await service.generate_word_manual("test")

    @pytest.mark.asyncio
    async def test_openai_nested_unicode_cleaning(self):
        """测试嵌套结构的Unicode清理"""
        # Mock response with invalid Unicode characters
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """{
            "word": "test",
            "phonetic": "/test/",
            "translation": "测试",
            "part_of_speech": "noun",
            "core_game": {
                "content": "测试游戏\\udc80清理"
            },
            "game_boards": {
                "board_a_speculative": {
                    "type": "棋盘A",
                    "name": "场名\\udc80A",
                    "example": "示例A"
                },
                "board_b_life": {
                    "type": "棋盘B",
                    "name": "场名B",
                    "example": "示例B"
                }
            },
            "etymology": {
                "breakdown": {
                    "prefix": {"part": "pre-", "meaning": "前缀"},
                    "root": {"part": "root", "meaning": "词根"},
                    "suffix": {"part": "-suffix", "meaning": "后缀"}
                },
                "story": "词源故事"
            },
            "common_mistakes": {
                "warning": "警告",
                "avoidance": "避免方法"
            },
            "memory_trick": "记忆技巧"
        }"""

        with patch("app.prompts.manager.get_prompt_manager") as mock_prompt_manager:
            mock_pm = Mock()
            mock_pm.render_prompt.return_value = ("system_prompt", "user_prompt")
            mock_pm.get_provider_config.return_value = Mock(
                default_temperature=0.7,
                default_max_tokens=2000
            )
            mock_prompt_manager.return_value = mock_pm

            with patch("openai.AsyncOpenAI") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
                mock_client_class.return_value = mock_client

                service = OpenAIService(api_key="test_key_123", model="gpt-4o-mini", timeout=30)
                result = await service.generate_word_manual("test")

                # 验证Unicode清理
                assert result.core_game.content == "测试游戏清理"
                assert result.game_boards.board_a_speculative.name == "场名A"
                assert "\\udc80" not in result.core_game.content
                assert "\\udc80" not in result.game_boards.board_a_speculative.name