"""Gemini AI服务实现 - 使用新版google-genai SDK"""
import json
import re
from google import genai
from google.genai.errors import APIError
from google.genai.types import Schema, Type

from app.services.ai.base import (
    AIServiceBase,
    WordManualData,
    GameBoard,
    EtymologyBreakdown,
    Etymology,
    CoreGame,
    CommonMistakes,
    GameBoards,
    AIServiceError,
    AITimeoutError,
    AIRateLimitError,
    AIParseError,
)
from app.prompts.manager import get_prompt_manager
from app.prompts.enums import Language, AIProvider, PromptType
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiService(AIServiceBase):
    """Gemini AI服务实现 - 使用新版SDK和结构化输出"""

    def __init__(self, api_key: str, model: str, timeout: int):
        """
        初始化Gemini服务

        Args:
            api_key: Gemini API密钥
            model: 模型名称（如gemini-2.5-flash）
            timeout: 请求超时时间（秒）
        """
        if not api_key or api_key == "your-gemini-api-key-here":
            raise AIServiceError("Gemini API Key未配置或无效")

        # 创建新版SDK客户端
        try:
            self.client = genai.Client(api_key=api_key)
            self.model = model
            self.timeout = timeout
            logger.info(f"Gemini service initialized with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise AIServiceError(f"Gemini客户端初始化失败: {str(e)}")

        # 定义响应Schema（完全匹配Prompt模板的嵌套结构）
        self.response_schema = Schema(
            type=Type.OBJECT,
            properties={
                "word": Schema(type=Type.STRING, description="学习的单词"),
                "phonetic": Schema(type=Type.STRING, description="国际音标"),
                "translation": Schema(type=Type.STRING, description="中文译文"),
                "part_of_speech": Schema(type=Type.STRING, description="单词词性"),
                "core_game": Schema(
                    type=Type.OBJECT,
                    properties={
                        "content": Schema(type=Type.STRING, description="核心游戏的描述")
                    },
                    required=["content"]
                ),
                "game_boards": Schema(
                    type=Type.OBJECT,
                    properties={
                        "board_a_speculative": Schema(
                            type=Type.OBJECT,
                            properties={
                                "type": Schema(type=Type.STRING, description="棋盘A (思辨场)"),
                                "name": Schema(type=Type.STRING, description="富有创意和指向性的场名A"),
                                "example": Schema(type=Type.STRING, description="中英文混合的完整示例")
                            },
                            required=["type", "name", "example"]
                        ),
                        "board_b_life": Schema(
                            type=Type.OBJECT,
                            properties={
                                "type": Schema(type=Type.STRING, description="棋盘B (生活场)"),
                                "name": Schema(type=Type.STRING, description="富有创意和指向性的场名B"),
                                "example": Schema(type=Type.STRING, description="中英文混合的完整示例")
                            },
                            required=["type", "name", "example"]
                        )
                    },
                    required=["board_a_speculative", "board_b_life"]
                ),
                "etymology": Schema(
                    type=Type.OBJECT,
                    properties={
                        "breakdown": Schema(
                            type=Type.OBJECT,
                            properties={
                                "prefix": Schema(
                                    type=Type.OBJECT,
                                    properties={
                                        "part": Schema(type=Type.STRING, description="前缀"),
                                        "meaning": Schema(type=Type.STRING, description="核心含义")
                                    },
                                    required=["part", "meaning"]
                                ),
                                "root": Schema(
                                    type=Type.OBJECT,
                                    properties={
                                        "part": Schema(type=Type.STRING, description="词根"),
                                        "meaning": Schema(type=Type.STRING, description="核心含义")
                                    },
                                    required=["part", "meaning"]
                                ),
                                "suffix": Schema(
                                    type=Type.OBJECT,
                                    properties={
                                        "part": Schema(type=Type.STRING, description="后缀"),
                                        "meaning": Schema(type=Type.STRING, description="核心含义")
                                    },
                                    required=["part", "meaning"]
                                )
                            },
                            required=["prefix", "root", "suffix"]
                        ),
                        "story": Schema(type=Type.STRING, description="组装故事的内容")
                    },
                    required=["breakdown", "story"]
                ),
                "common_mistakes": Schema(
                    type=Type.OBJECT,
                    properties={
                        "warning": Schema(type=Type.STRING, description="最容易犯的'规'/错招"),
                        "avoidance": Schema(type=Type.STRING, description="一句话避免'错招'的技巧")
                    },
                    required=["warning", "avoidance"]
                ),
                "memory_trick": Schema(type=Type.STRING, description="通关秘籍的内容")
            },
            required=[
                "word", "phonetic", "translation", "part_of_speech", "core_game",
                "game_boards", "etymology", "common_mistakes", "memory_trick"
            ]
        )

    def generate_word_manual(self, word: str, language: str = Language.CHINESE) -> WordManualData:
        """生成单词学习手册 - 同步版本

        Args:
            word: 目标单词
            language: 语言代码，默认为中文

        Returns:
            WordManualData: 生成的单词学习手册数据
        """
        try:
            logger.info(f"Gemini generating manual for: {word}, language: {language}")

            # 获取Prompt管理器和渲染模板
            prompt_manager = get_prompt_manager()
            system_prompt, user_prompt = prompt_manager.render_prompt(
                word=word,
                language=language,
                provider=AIProvider.GEMINI,
                prompt_type=PromptType.WORD_GENERATION
            )

            logger.info(f"Gemini API调用开始 - word: {word}, language: {language}, model: {self.model}")

            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=self.response_schema
                ),
            )

            # 处理响应 - 新版SDK返回直接是JSON文本
            if not response.text:
                logger.error("Gemini返回空内容")
                raise AIParseError("Gemini返回空内容")

            logger.debug(f"Gemini response received: {response.text[:200]}...")

            # 解析JSON响应
            word_data = self._parse_response(response.text)

            logger.info(f"Gemini successfully generated for: {word}")
            return word_data

        except AIParseError:
            # Re-raise parse errors without wrapping
            raise

        except APIError as e:
            # 处理APIError - 新版SDK的错误
            error_message = str(e)
            logger.error(f"Gemini API error for {word}: {e}")
            raise AIServiceError(f"Gemini API错误: {error_message}")

        except Exception as e:
            # 处理通用异常 - 包含错误关键词匹配
            error_message = str(e).lower()
            if "timeout" in error_message or "deadline" in error_message:
                logger.error(f"Gemini timeout for {word}: {e}")
                raise AITimeoutError(f"Gemini生成超时: {str(e)}")
            elif "rate limit" in error_message or "resource exhausted" in error_message or "quota" in error_message:
                logger.error(f"Gemini rate limit for {word}: {e}")
                raise AIRateLimitError(f"Gemini API限流: {str(e)}")
            elif "permission" in error_message or "unauthorized" in error_message or "forbidden" in error_message:
                logger.error(f"Gemini permission denied for {word}: {e}")
                raise AIServiceError(f"Gemini API密钥无效: {str(e)}")
            else:
                logger.error(f"Gemini unexpected error for {word}: {e}")
                raise AIServiceError(f"Gemini服务错误: {str(e)}")

    def _parse_response(self, response: str) -> WordManualData:
        """解析AI返回的JSON - 处理嵌套结构"""
        try:
            # 清理响应中的无效Unicode代理对字符
            cleaned_response = self._clean_invalid_unicode(response.strip())

            # 新版SDK使用结构化输出时，应该直接返回有效JSON
            data = json.loads(cleaned_response)

            # 记录接收到的数据结构（用于调试）
            logger.debug(f"Parsed response structure: {list(data.keys())}")

            # 验证必要的顶层字段
            required_fields = ["word", "core_game", "game_boards", "etymology", "common_mistakes", "memory_trick"]
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field: {field}")
                    raise AIParseError(f"响应缺少必要字段: {field}")

            # 验证嵌套结构
            if not isinstance(data["core_game"], dict) or "content" not in data["core_game"]:
                logger.error("Invalid core_game structure")
                raise AIParseError("core_game结构无效")

            if not isinstance(data["game_boards"], dict):
                logger.error("Invalid game_boards structure")
                raise AIParseError("game_boards结构无效")

            required_boards = ["board_a_speculative", "board_b_life"]
            for board in required_boards:
                if board not in data["game_boards"]:
                    logger.error(f"Missing required board: {board}")
                    raise AIParseError(f"game_boards缺少必要棋盘: {board}")

            if not isinstance(data["etymology"], dict):
                logger.error("Invalid etymology structure")
                raise AIParseError("etymology结构无效")

            if not isinstance(data["common_mistakes"], dict):
                logger.error("Invalid common_mistakes structure")
                raise AIParseError("common_mistakes结构无效")

            # 创建数据模型
            word_manual = WordManualData(**data)

            # 记录成功解析的详细信息
            logger.info(f"Successfully parsed word manual for: {word_manual.word}")
            logger.debug(f"Word manual structure: core_game={bool(word_manual.core_game)}, "
                        f"game_boards={bool(word_manual.game_boards)}, "
                        f"etymology={bool(word_manual.etymology)}")

            return word_manual

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, response: {response[:500]}")
            raise AIParseError(f"Gemini返回格式错误: {str(e)}")
        except Exception as e:
            logger.error(f"Parse error: {e}, response: {response[:500]}")
            raise AIParseError(f"数据解析失败: {str(e)}")

    def _clean_invalid_unicode(self, text: str) -> str:
        """
        清理文本中的无效Unicode代理对字符

        Args:
            text: 原始文本

        Returns:
            str: 清理后的文本
        """
        if not text:
            return text

        # 移除无效的代理对字符 (U+DC80-U+DFFF)
        cleaned = re.sub(r'[\udc80-\udfff]', '', text)

        # 记录清理统计
        if len(cleaned) != len(text):
            removed_count = len(text) - len(cleaned)
            logger.info(f"Cleaned {removed_count} invalid surrogate characters from AI response")

        return cleaned
