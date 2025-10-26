"""Gemini服务嵌套结构测试 - 新版Schema测试"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.ai.gemini_service import GeminiService
from app.services.ai.base import (
    WordManualData, GameBoard, EtymologyBreakdown, Etymology,
    CoreGame, CommonMistakes, GameBoards,
    AIServiceError, AITimeoutError, AIRateLimitError, AIParseError
)
from google.genai.errors import APIError


class TestGeminiServiceNestedStructure:
    """测试Gemini服务的嵌套JSON结构支持"""

    def test_gemini_service_nested_schema_definition(self):
        """测试嵌套Schema定义正确性"""
        service = GeminiService(api_key="test_key_123", model="gemini-2.5-flash", timeout=30)

        # 检查Schema是否正确定义
        assert service.response_schema is not None
        assert hasattr(service.response_schema, 'properties')

        # 检查新增字段
        assert 'translation' in service.response_schema.properties
        assert 'game_boards' in service.response_schema.properties
        assert 'etymology' in service.response_schema.properties
        assert 'common_mistakes' in service.response_schema.properties

        # 检查嵌套结构
        assert service.response_schema.properties['game_boards'].type.value == 'OBJECT'
        assert service.response_schema.properties['etymology'].type.value == 'OBJECT'
        assert service.response_schema.properties['common_mistakes'].type.value == 'OBJECT'

        # 检查必要字段数量
        assert len(service.response_schema.required) == 9

    def test_gemini_generate_nested_word_manual_success(self):
        """测试成功生成嵌套结构的单词手册"""
        # Mock nested response
        mock_response = Mock()
        mock_response.text = """{
            "word": "accommodation",
            "phonetic": "[əˌkɒməˈdeɪʃən]",
            "translation": "住宿，适应，调适",
            "part_of_speech": "noun",
            "core_game": {
                "content": "这是一个关于'适应空间'和'相互包容'的情感游戏"
            },
            "game_boards": {
                "board_a_speculative": {
                    "type": "棋盘A (思辨场)",
                    "name": "职场包容牌局",
                    "example": "成功的婚姻需要双方不断地进行情感accommodation（调适），以应对彼此性格和生活习惯的差异。"
                },
                "board_b_life": {
                    "type": "棋盘B (生活场)",
                    "name": "旅行找宿局",
                    "example": "我们提前预订了酒店，但他们说在旅游旺季，找到便宜的accommodation（住宿）非常困难。"
                }
            },
            "etymology": {
                "breakdown": {
                    "prefix": {
                        "part": "ac-",
                        "meaning": "去，向"
                    },
                    "root": {
                        "part": "modus",
                        "meaning": "模式，方式"
                    },
                    "suffix": {
                        "part": "-ation",
                        "meaning": "行为，过程"
                    }
                },
                "story": "最初来自拉丁语accommodare，意为'使适应'，后来演变为包含'提供住所'和'适应调整'的双重含义。"
            },
            "common_mistakes": {
                "warning": "容易与accommodation中的两个c和两个m混淆，常拼写错误",
                "avoidance": "记住：两个c（如car）和两个m（如moon），共4个m音节"
            },
            "memory_trick": "想象一个AC（空调）房间里有MODEM（调制解调器），需要适应（accommodation）网络信号"
        }"""

        with patch("google.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            service = GeminiService(api_key="test_key_123", model="gemini-2.5-flash", timeout=30)
            result = service.generate_word_manual("accommodation")

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

            mock_client.models.generate_content.assert_called_once()

    def test_gemini_backward_compatibility_methods(self):
        """测试向后兼容性方法"""
        # 创建测试数据
        test_data = {
            "word": "test",
            "phonetic": "/test/",
            "translation": "测试",
            "part_of_speech": "noun",
            "core_game": {"content": "测试核心游戏"},
            "game_boards": {
                "board_a_speculative": {
                    "type": "棋盘A (思辨场)",
                    "name": "思辨场名",
                    "example": "思辨场示例：test（测试）"
                },
                "board_b_life": {
                    "type": "棋盘B (生活场)",
                    "name": "生活场名",
                    "example": "生活场示例：test（测试）"
                }
            },
            "etymology": {
                "breakdown": {
                    "prefix": {"part": "test-", "meaning": "测试"},
                    "root": {"part": "root", "meaning": "词根"},
                    "suffix": {"part": "-ing", "meaning": "后缀"}
                },
                "story": "测试词源故事"
            },
            "common_mistakes": {
                "warning": "测试警告",
                "avoidance": "测试避免方法"
            },
            "memory_trick": "测试记忆技巧"
        }

        word_manual = WordManualData(**test_data)

        # 测试向后兼容性方法
        assert word_manual.get_scenario_formal() == "思辨场名：思辨场示例：test（测试）"
        assert word_manual.get_scenario_casual() == "生活场名：生活场示例：test（测试）"
        assert "前缀：test-（测试）" in word_manual.get_etymology_breakdown()
        assert word_manual.get_etymology_story() == "测试词源故事"
        assert word_manual.get_core_game_content() == "测试核心游戏"
        assert word_manual.get_memory_trick() == "测试记忆技巧"
        assert "测试警告" in word_manual.get_common_mistakes()

    def test_gemini_nested_validation_missing_field(self):
        """测试嵌套结构字段验证 - 缺少必要字段"""
        # Mock response missing required nested field
        mock_response = Mock()
        mock_response.text = """{
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

        with patch("google.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            service = GeminiService(api_key="test_key_123", model="gemini-2.5-flash", timeout=30)

            with pytest.raises(AIParseError, match="响应缺少必要字段"):
                service.generate_word_manual("test")

    def test_gemini_nested_validation_invalid_structure(self):
        """测试嵌套结构字段验证 - 无效结构"""
        # Mock response with invalid nested structure
        mock_response = Mock()
        mock_response.text = """{
            "word": "test",
            "phonetic": "/test/",
            "translation": "test translation",
            "part_of_speech": "noun",
            "core_game": "invalid_string_structure",
            "game_boards": {
                "board_a_speculative": {
                    "type": "Board A",
                    "name": "Field Name A",
                    "example": "Example A"
                },
                "board_b_life": {
                    "type": "Board B",
                    "name": "Field Name B",
                    "example": "Example B"
                }
            },
            "etymology": {
                "breakdown": {
                    "prefix": {"part": "pre-", "meaning": "prefix"},
                    "root": {"part": "root", "meaning": "root word"},
                    "suffix": {"part": "-suffix", "meaning": "suffix"}
                },
                "story": "etymology story"
            },
            "common_mistakes": {
                "warning": "warning",
                "avoidance": "avoidance method"
            },
            "memory_trick": "memory trick"
        }"""

        with patch("google.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            service = GeminiService(api_key="test_key_123", model="gemini-2.5-flash", timeout=30)

            with pytest.raises(AIParseError, match="core_game结构无效"):
                service.generate_word_manual("test")

    def test_gemini_nested_validation_missing_board(self):
        """测试嵌套结构字段验证 - 缺少棋盘"""
        # Mock response missing required board
        mock_response = Mock()
        mock_response.text = """{
            "word": "test",
            "phonetic": "/test/",
            "translation": "test translation",
            "part_of_speech": "noun",
            "core_game": {
                "content": "test game content"
            },
            "game_boards": {
                "board_a_speculative": {
                    "type": "Board A",
                    "name": "Field Name A",
                    "example": "Example A"
                }
            },
            "etymology": {
                "breakdown": {
                    "prefix": {"part": "pre-", "meaning": "prefix"},
                    "root": {"part": "root", "meaning": "root word"},
                    "suffix": {"part": "-suffix", "meaning": "suffix"}
                },
                "story": "etymology story"
            },
            "common_mistakes": {
                "warning": "warning",
                "avoidance": "avoidance method"
            },
            "memory_trick": "memory trick"
        }"""

        with patch("google.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            service = GeminiService(api_key="test_key_123", model="gemini-2.5-flash", timeout=30)

            with pytest.raises(AIParseError, match="game_boards缺少必要棋盘"):
                service.generate_word_manual("test")

    def test_gemini_nested_unicode_cleaning(self):
        """测试嵌套结构的Unicode清理"""
        # Mock response with invalid Unicode characters
        mock_response = Mock()
        mock_response.text = """{
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

        with patch("google.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            service = GeminiService(api_key="test_key_123", model="gemini-2.5-flash", timeout=30)
            result = service.generate_word_manual("test")

            # 验证Unicode清理
            assert result.core_game.content == "测试游戏清理"
            assert result.game_boards.board_a_speculative.name == "场名A"
            assert "\\udc80" not in result.core_game.content
            assert "\\udc80" not in result.game_boards.board_a_speculative.name