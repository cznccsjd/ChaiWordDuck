"""Gemini AI服务实现 - 使用新版google-genai SDK"""
import json
import random
import re
import time
from google import genai
from google.genai.errors import APIError
from google.genai.types import HttpOptions,Schema, Type

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
            self.model = model
            self.timeout = timeout
            # 创建 HttpOptions 实例
            http_opts = HttpOptions(
                timeout=timeout 
            )
            self.client = genai.Client(api_key=api_key, http_options=http_opts)   # 使用http_options设置超时时间
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
        """生成单词学习手册 - 用户友好的重试版本"""
        MAX_RETRIES = 4     # 最大重试次数
        TOTAL_TIMEOUT = 8   # 总超时时间（秒）

        # 定义重试间隔：1秒 → 2秒 → 3秒，加随机抖动避免重试风暴
        RETRY_DELAYS = [1, 2, 3]

        def should_retry(error: Exception) -> bool:
            """
            判断是否应该重试的错误类型

            Args:
                error: 捕获的异常

            Returns:
                bool: 是否应该重试
            """
            error_message = str(error).lower()
            error_type = type(error).__name__

            # 不应该重试的错误（逻辑错误）
            if error_type == "ValidationError":
                logger.warning(f"参数验证失败，不重试: {error}")
                return False
            elif "word not found" in error_message or "单词不存在" in error_message:
                logger.warning(f"词汇不存在，不重试: {error}")
                return False
            elif "quota exceeded" in error_message or "配额用完" in error_message:
                logger.warning(f"配额用完，不重试: {error}")
                return False
            elif "permission denied" in error_message or "unauthorized" in error_message:
                logger.warning(f"API密钥无效，不重试: {error}")
                return False

            # 应该重试的错误（临时性错误）
            if error_type == "AIParseError":
                logger.info(f"解析错误，准备重试: {error}")
                return True
            elif error_type == "APIError":
                logger.info(f"API错误，准备重试: {error}")
                return True
            elif "timeout" in error_message or "deadline" in error_message:
                logger.info(f"超时错误，准备重试: {error}")
                return True
            elif "rate limit" in error_message or "resource exhausted" in error_message:
                logger.info(f"限流错误，准备重试: {error}")
                return True
            elif "connection" in error_message or "network" in error_message:
                logger.info(f"网络错误，准备重试: {error}")
                return True
            elif "internal" in error_message or "server" in error_message:
                logger.info(f"服务器内部错误，准备重试: {error}")
                return True

            # 其他未知错误，为用户友好起见也重试
            logger.info(f"未知错误，为用户友好起见准备重试: {error}")
            return True

        def wait_with_jitter(base_delay: float) -> float:
            """
            添加随机抖动的等待时间

            Args:
                base_delay: 基础等待时间

            Returns:
                float: 实际等待时间
            """
            # 添加 ±25% 的随机抖动，避免重试风暴
            jitter_factor = random.uniform(0.75, 1.25)
            return base_delay * jitter_factor

        attempt = 0
        start_time = time.time()

        while attempt < MAX_RETRIES:
            attempt += 1

            try:
                logger.info(f"Gemini API调用开始 - 尝试 {attempt}/{MAX_RETRIES}, word: {word}, model: {self.model}")

                # 获取Prompt
                prompt = get_word_generation_prompt(word)

                # 调用Gemini API - 使用新版SDK的同步方法
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

                # 计算总耗时
                total_time = time.time() - start_time
                logger.info(f"Gemini successfully generated for: {word}, 尝试次数: {attempt}, 总耗时: {total_time:.2f}秒")
                return word_data

            except Exception as e:
                error_message = str(e)
                error_type = type(e).__name__

                # 检查是否应该重试
                if not should_retry(e):
                    logger.error(f"非临时性错误，不重试: {error_type} - {error_message}")
                    # 重新抛出原始异常，保持现有的异常类型体系
                    if error_type == "AIParseError":
                        raise
                    elif "timeout" in error_message.lower() or "deadline" in error_message.lower():
                        raise AITimeoutError(f"Gemini生成超时: {error_message}")
                    elif "rate limit" in error_message.lower() or "resource exhausted" in error_message.lower():
                        raise AIRateLimitError(f"Gemini API限流: {error_message}")
                    elif "permission denied" in error_message.lower() or "unauthorized" in error_message.lower():
                        raise AIServiceError(f"Gemini API密钥无效: {error_message}")
                    else:
                        raise AIServiceError(f"Gemini服务错误: {error_message}")

                # 如果是最后一次尝试，直接抛出异常
                if attempt >= MAX_RETRIES:
                    total_time = time.time() - start_time
                    logger.error(f"Gemini API重试失败，已达最大重试次数 {MAX_RETRIES}，总耗时: {total_time:.2f}秒，最后错误: {error_type} - {error_message}")

                    # 保持现有的异常类型体系
                    if error_type == "AIParseError":
                        raise
                    elif "timeout" in error_message.lower() or "deadline" in error_message.lower():
                        raise AITimeoutError(f"Gemini生成超时（重试 {MAX_RETRIES} 次后仍失败）: {error_message}")
                    elif "rate limit" in error_message.lower() or "resource exhausted" in error_message.lower():
                        raise AIRateLimitError(f"Gemini API限流（重试 {MAX_RETRIES} 次后仍失败）: {error_message}")
                    else:
                        raise AIServiceError(f"Gemini API错误（重试 {MAX_RETRIES} 次后仍失败）: {error_message}")

                # 计算等待时间并等待
                if attempt <= len(RETRY_DELAYS):
                    base_delay = RETRY_DELAYS[attempt - 1]
                else:
                    base_delay = RETRY_DELAYS[-1]

                # 添加随机抖动
                actual_delay = wait_with_jitter(base_delay)

                # 检查总超时时间
                elapsed_time = time.time() - start_time
                remaining_time = TOTAL_TIMEOUT - elapsed_time

                if remaining_time <= 0:
                    logger.error(f"总超时时间 {TOTAL_TIMEOUT} 秒已到，停止重试，当前尝试: {attempt}")
                    raise AIServiceError(f"Gemini生成超时（总时间超过 {TOTAL_TIMEOUT} 秒）")

                # 如果下次重试会超过总超时时间，减少等待时间
                if actual_delay > remaining_time:
                    actual_delay = remaining_time * 0.9
                    logger.warning(f"调整等待时间为 {actual_delay:.2f} 秒以避免超过总超时限制")

                logger.info(f"第 {attempt} 次重试将在 {actual_delay:.2f} 秒后开始，原因: {error_type} - {error_message}")
                time.sleep(actual_delay)

    def _parse_response(self, response: str) -> WordManualData:
        """解析AI返回的JSON - 新版SDK应该直接返回有效JSON"""
        try:
            # 清理响应中的无效Unicode代理对字符
            cleaned_response = self._clean_invalid_unicode(response.strip())

            # 新版SDK使用结构化输出时，应该直接返回有效JSON
            # 不再需要去除Markdown代码块等处理
            data = json.loads(cleaned_response)

            # 验证并创建数据模型
            return WordManualData(**data)

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
