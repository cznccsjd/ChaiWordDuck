"""OpenAI服务实现"""
import json
from typing import Any
from openai import AsyncOpenAI
from openai import OpenAIError, APITimeoutError, RateLimitError

from app.services.ai.base import (
    AIServiceBase, WordManualData,
    AIServiceError, AITimeoutError, AIRateLimitError, AIParseError
)
from app.prompts.manager import get_prompt_manager
from app.prompts.enums import Language, AIProvider, PromptType
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

    async def generate_word_manual(self, word: str, language: str = Language.CHINESE) -> WordManualData:
        """生成单词学习手册

        Args:
            word: 目标单词
            language: 语言代码，默认为中文

        Returns:
            WordManualData: 生成的单词学习手册数据
        """
        try:
            logger.info(f"OpenAI generating manual for: {word}, language: {language}")

            # 获取Prompt管理器和渲染模板
            prompt_manager = get_prompt_manager()
            system_prompt, user_prompt = prompt_manager.render_prompt(
                word=word,
                language=language,
                provider=AIProvider.OPENAI,
                prompt_type=PromptType.WORD_GENERATION
            )

            # 获取提供商配置
            provider_config = prompt_manager.get_provider_config(AIProvider.OPENAI)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=provider_config.default_temperature,
                max_tokens=provider_config.default_max_tokens
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
