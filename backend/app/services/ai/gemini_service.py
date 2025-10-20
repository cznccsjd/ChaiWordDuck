"""Gemini AI服务实现"""
import json
import ssl
import asyncio
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

        # 配置SSL上下文以解决Windows环境下的证书验证问题
        try:
            # 创建一个不过度严格的SSL上下文
            ssl_context = ssl.create_default_context()
            # 在Windows环境下，可能需要禁用证书吊销检查
            if hasattr(ssl_context, 'check_hostname'):
                ssl_context.check_hostname = True
            if hasattr(ssl_context, 'verify_mode'):
                ssl_context.verify_mode = ssl.CERT_REQUIRED
        except Exception as e:
            logger.warning(f"Failed to create SSL context: {e}, using default")
            ssl_context = None

        # 配置Gemini API
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
            logger.info(f"Gemini API调用开始 - word: {word}, prompt_length: {len(prompt)}")
            logger.info(f"Gemini API配置 - model: {self.model._model_name}, timeout: {self.timeout}s")
            logger.debug(f"Sending request to Gemini API with timeout: {self.timeout}s")
            try:
                # 添加网络超时保护，使用asyncio.wait_for
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.model.generate_content,
                        prompt,
                        generation_config=generation_config,
                        request_options={"timeout": self.timeout}
                    ),
                    timeout=self.timeout + 10  # 额外10秒缓冲
                )
                logger.info(f"Gemini API响应接收成功 - candidates: {len(response.candidates) if response.candidates else 0}")
            except asyncio.TimeoutError:
                logger.error(f"Gemini API network timeout after {self.timeout + 10}s for word: {word}")
                raise AITimeoutError(f"网络请求超时，请检查网络连接后重试")
            except Exception as api_error:
                logger.error(f"Gemini API call failed before response: {type(api_error).__name__}: {api_error}")
                # 检查是否是网络连接问题
                if "connection" in str(api_error).lower() or "network" in str(api_error).lower():
                    raise AIServiceError("无法连接到Google API，请检查网络连接或使用代理")
                # 重新抛出以被外层的异常捕获处理
                raise

            # 提取响应内容 - 修复版本，处理安全过滤器和其他异常情况
            try:
                # 检查响应候选
                if not response.candidates:
                    logger.error("Gemini返回无候选响应")
                    raise AIParseError("Gemini返回无候选响应")

                candidate = response.candidates[0]

                # 检查完成原因 - 改进版本，避免过度拦截
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = candidate.finish_reason
                    # 明确的安全过滤器情况才抛出错误
                    if finish_reason == 2:  # SAFETY
                        logger.error(f"Gemini内容被安全过滤器阻止，finish_reason={finish_reason}, word: {word}")
                        raise AIParseError("内容被安全过滤器阻止，请稍后重试或尝试其他词汇")
                    # 明确的token限制情况，记录警告但不抛出错误
                    elif finish_reason == 3:  # MAX_TOKENS
                        logger.warning(f"Gemini响应因token限制被截断，finish_reason={finish_reason}")
                        # 不要抛出错误，继续处理已有的内容
                    # 其他finish_reason值，记录日志但根据内容情况决定是否抛出错误
                    elif finish_reason not in [1, 3]:  # 不是STOP或MAX_TOKENS
                        logger.warning(f"Gemini异常结束，finish_reason={finish_reason}")
                        # 先尝试获取内容，如果内容为空再抛出错误

                # 检查内容
                if not hasattr(candidate, 'content') or not candidate.content:
                    logger.error("Gemini返回空内容")
                    raise AIParseError("Gemini返回空内容")

                # 安全获取文本 - 改进版本，支持多种内容格式
                content = ""
                if hasattr(candidate, 'content') and candidate.content:
                    # 尝试多种方式获取内容
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                content += part.text
                    # 尝试直接获取text属性
                    elif hasattr(candidate.content, 'text') and candidate.content.text:
                        content = candidate.content.text
                    # 尝试其他可能的属性
                    else:
                        logger.warning(f"无法识别的内容格式: {type(candidate.content)}")

                if not content.strip():
                    logger.error("Gemini返回文本为空")
                    raise AIParseError("Gemini返回文本为空")

            except AttributeError as ae:
                logger.error(f"访问Gemini响应属性时出错: {ae}")
                raise AIParseError(f"Gemini响应格式异常: {str(ae)}")
            except Exception as e:
                logger.error(f"解析Gemini响应时出错: {e}")
                raise AIParseError(f"响应解析失败: {str(e)}")

            logger.debug(f"Gemini raw response: {content[:200]}...")

            # 解析JSON
            word_data = self._parse_response(content)

            logger.info(f"Gemini successfully generated for: {word}")
            return word_data

        except AIParseError:
            # Re-raise parse errors without wrapping
            raise

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
