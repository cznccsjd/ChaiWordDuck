"""Gemini AI服务实现 - 使用新版google-genai SDK"""
import json
from google import genai
from google.genai.errors import APIError
from google.genai.types import Schema, Type

from app.services.ai.base import (
    AIServiceBase,
    WordManualData,
    AIServiceError,
    AITimeoutError,
    AIRateLimitError,
    AIParseError,
)
from app.prompts.word_generation import get_word_generation_prompt
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

        # 定义响应Schema（基于成功测试的结构）
        self.response_schema = Schema(
            type=Type.OBJECT,
            properties={
                "word": Schema(type=Type.STRING, description="学习的单词"),
                "phonetic": Schema(type=Type.STRING, description="国际音标"),
                "part_of_speech": Schema(type=Type.STRING, description="单词词性"),
                "core_game": Schema(type=Type.STRING, description="核心语言游戏内容（拆解和创意说明）"),
                "scenario_formal": Schema(type=Type.STRING, description="正式场景例句（英文 + 中文翻译）"),
                "scenario_casual": Schema(type=Type.STRING, description="日常场景例句（英文 + 中文翻译）"),
                "etymology_breakdown": Schema(type=Type.STRING, description="词源拆解内容（词根、前缀、后缀分析）"),
                "etymology_story": Schema(type=Type.STRING, description="词源故事（简短有趣的历史背景）"),
                "memory_trick": Schema(type=Type.STRING, description="记忆小窍门（联想法、谐音法等）"),
                "common_mistakes": Schema(type=Type.STRING, description="常见错误（学习者容易犯的错误）")
            },
            required=[
                "word", "phonetic", "part_of_speech", "core_game", "scenario_formal",
                "scenario_casual", "etymology_breakdown", "etymology_story",
                "memory_trick", "common_mistakes"
            ]
        )

    def generate_word_manual(self, word: str) -> WordManualData:
        """生成单词学习手册 - 同步版本"""
        try:
            logger.info(f"Gemini generating manual for: {word}")

            # 获取Prompt
            prompt = get_word_generation_prompt(word)

            # 调用Gemini API - 使用新版SDK的同步方法
            logger.info(f"Gemini API调用开始 - word: {word}, model: {self.model}")

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction="你是一位专业的英语教学专家，擅长使用'五步语言游戏学习法'帮助学习者记忆长单词。",
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
        """解析AI返回的JSON - 新版SDK应该直接返回有效JSON"""
        try:
            # 新版SDK使用结构化输出时，应该直接返回有效JSON
            # 不再需要去除Markdown代码块等处理
            data = json.loads(response.strip())

            # 验证并创建数据模型
            return WordManualData(**data)

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, response: {response[:500]}")
            raise AIParseError(f"Gemini返回格式错误: {str(e)}")
        except Exception as e:
            logger.error(f"Parse error: {e}, response: {response[:500]}")
            raise AIParseError(f"数据解析失败: {str(e)}")
