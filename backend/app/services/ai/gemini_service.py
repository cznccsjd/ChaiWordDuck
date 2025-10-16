"""Gemini AI服务实现"""
import json
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

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
    """Gemini AI服务实现"""

    def __init__(self, api_key: str, model: str, timeout: int):
        """
        初始化Gemini服务

        Args:
            api_key: Gemini API密钥
            model: 模型名称（如gemini-1.5-flash）
            timeout: 请求超时时间（秒）
        """
        if not api_key or api_key == "your-gemini-api-key-here":
            raise AIServiceError("Gemini API Key未配置或无效")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.timeout = timeout
        logger.info(f"Gemini service initialized with model: {model}")

    async def generate_word_manual(self, word: str) -> WordManualData:
        """生成单词学习手册"""
        try:
            logger.info(f"Gemini generating manual for: {word}")

            # 获取Prompt
            prompt = get_word_generation_prompt(word)

            # 配置生成参数
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            }

            # 调用Gemini API
            response = self.model.generate_content(
                prompt, generation_config=generation_config, request_options={"timeout": self.timeout}
            )

            # 提取响应内容
            if not response.text:
                raise AIParseError("Gemini返回空响应")

            content = response.text
            logger.debug(f"Gemini raw response: {content[:200]}...")

            # 解析JSON
            word_data = self._parse_response(content)

            logger.info(f"Gemini successfully generated for: {word}")
            return word_data

        except google_exceptions.DeadlineExceeded as e:
            logger.error(f"Gemini timeout for {word}: {e}")
            raise AITimeoutError(f"Gemini生成超时: {str(e)}")

        except google_exceptions.ResourceExhausted as e:
            logger.error(f"Gemini rate limit for {word}: {e}")
            raise AIRateLimitError(f"Gemini API限流: {str(e)}")

        except google_exceptions.PermissionDenied as e:
            logger.error(f"Gemini permission denied for {word}: {e}")
            raise AIServiceError(f"Gemini API密钥无效: {str(e)}")

        except Exception as e:
            logger.error(f"Gemini error for {word}: {e}")
            raise AIServiceError(f"Gemini服务错误: {str(e)}")

    def _parse_response(self, response: str) -> WordManualData:
        """解析AI返回的JSON"""
        try:
            # 去除可能的Markdown代码块
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            json_str = json_str.strip()

            # 解析JSON
            data = json.loads(json_str)

            # 验证并创建数据模型
            return WordManualData(**data)

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, response: {response[:500]}")
            raise AIParseError(f"Gemini返回格式错误: {str(e)}")
        except Exception as e:
            logger.error(f"Parse error: {e}, response: {response[:500]}")
            raise AIParseError(f"数据解析失败: {str(e)}")
