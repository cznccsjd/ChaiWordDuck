"""OpenAI服务实现"""
import json
from typing import Any
from openai import AsyncOpenAI
from openai import OpenAIError, APITimeoutError, RateLimitError

from app.services.ai.base import (
    AIServiceBase, WordManualData,
    AIServiceError, AITimeoutError, AIRateLimitError, AIParseError
)
from app.prompts.word_generation import get_word_generation_prompt
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIService(AIServiceBase):
    """OpenAI服务实现"""

    def __init__(self, api_key: str, model: str, timeout: int):
        """
        初始化OpenAI服务

        Args:
            api_key: OpenAI API密钥
            model: 模型名称（如gpt-4o-mini）
            timeout: 请求超时时间（秒）
        """
        if not api_key or api_key == "sk-your-openai-api-key-optional":
            raise AIServiceError("OpenAI API Key未配置或无效")

        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        logger.info(f"OpenAI service initialized with model: {model}")

    async def generate_word_manual(self, word: str) -> WordManualData:
        """生成单词学习手册"""
        try:
            logger.info(f"OpenAI generating manual for: {word}")

            prompt = get_word_generation_prompt(word)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是专业的英语教学专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            content = response.choices[0].message.content
            logger.debug(f"OpenAI raw response: {content[:200]}...")

            word_data = self._parse_response(content)
            logger.info(f"OpenAI successfully generated for: {word}")
            return word_data

        except APITimeoutError as e:
            logger.error(f"OpenAI timeout: {e}")
            raise AITimeoutError(f"AI生成超时: {str(e)}")
        except RateLimitError as e:
            logger.error(f"OpenAI rate limit: {e}")
            raise AIRateLimitError(f"API限流: {str(e)}")
        except OpenAIError as e:
            logger.error(f"OpenAI error: {e}")
            raise AIServiceError(f"AI服务错误: {str(e)}")

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

            data = json.loads(json_str)
            return WordManualData(**data)

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            raise AIParseError(f"AI返回格式错误: {str(e)}")
        except Exception as e:
            logger.error(f"Parse error: {e}")
            raise AIParseError(f"数据解析失败: {str(e)}")
