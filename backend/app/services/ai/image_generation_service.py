"""
图片生成服务 - 基于Google Gemini Imagen 3

提供基于单词含义生成教学图片的功能
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from google import genai
from google.genai.errors import APIError

from app.services.image.image_storage_service import ImageStorageService, ImageStorageError
from app.core.logging import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)


class ImageGenerationError(Exception):
    """图片生成相关错误"""
    pass


class ImageGenerationTimeoutError(ImageGenerationError):
    """图片生成超时错误"""
    pass


class ImageGenerationRateLimitError(ImageGenerationError):
    """图片生成限流错误"""
    pass


class ImageGenerationService:
    """基于Gemini Imagen 3的图片生成服务"""

    # 支持的图片风格
    SUPPORTED_STYLES = [
        "cartoon",      # 卡通风格
        "realistic",    # 写实风格
        "educational",  # 教育风格
        "watercolor",   # 水彩风格
        "sketch",       # 素描风格
    ]

    def __init__(self, image_storage: Optional[ImageStorageService] = None):
        """
        初始化图片生成服务

        Args:
            image_storage: 图片存储服务实例，如果为None则创建新实例
        """
        self.settings = get_settings()
        self.api_key = getattr(self.settings, 'gemini_api_key', '')
        self.model = getattr(self.settings, 'imagen_model', 'imagen-3.0-generate-001')
        self.timeout = getattr(self.settings, 'imagen_timeout', 60)
        self.max_retries = getattr(self.settings, 'max_image_retries', 3)

        # 验证API密钥
        if not self.api_key or self.api_key == "your-gemini-api-key-here":
            raise ImageGenerationError("Gemini API Key未配置或无效")

        # 初始化Gemini客户端
        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"Image generation service initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize image generation client: {e}")
            raise ImageGenerationError(f"图片生成客户端初始化失败: {str(e)}")

        # 初始化图片存储服务
        self.image_storage = image_storage or ImageStorageService()

        logger.info(f"ImageGenerationService initialized: model={self.model}, "
                   f"timeout={self.timeout}s, max_retries={self.max_retries}")

    def generate_word_image(
        self,
        word: str,
        style: str = "educational",
        description: str = "",
        aspect_ratio: str = "1:1",
        negative_prompt: str = "text, words, letters, numbers",
        language: str = "zh"
    ) -> Dict[str, Any]:
        """
        为指定单词生成教学图片

        Args:
            word: 目标单词
            style: 图片风格
            description: 图片描述
            aspect_ratio: 长宽比 ("1:1", "16:9", "9:16")
            negative_prompt: 负面提示词
            language: 语言代码

        Returns:
            Dict: 生成结果，包含success, filepath等信息
        """
        try:
            logger.info(f"Generating image for word: {word}, style: {style}")

            # 验证输入参数
            if not self._validate_word(word):
                raise ImageGenerationError("无效的单词格式")

            if not self._validate_style(style):
                raise ImageGenerationError(f"不支持的图片风格: {style}")

            # 构建prompt
            prompt = self._build_prompt(
                word=word,
                style=style,
                description=description,
                aspect_ratio=aspect_ratio,
                language=language
            )

            # 带重试机制的图片生成
            image_data = self._generate_with_retry(prompt, aspect_ratio, negative_prompt)

            # 存储图片
            filename = f"{word}_{style}_{int(time.time())}.jpg"
            storage_result = self.image_storage.save_image(
                image_data=image_data,
                filename=filename,
                subfolder=f"words/{word}"
            )

            if not storage_result["success"]:
                raise ImageGenerationError(f"图片存储失败: {storage_result['error']}")

            result = {
                "success": True,
                "filepath": storage_result["filepath"],
                "filename": storage_result["filename"],
                "size": storage_result["size"],
                "word": word,
                "style": style,
                "description": description,
                "aspect_ratio": aspect_ratio,
                "language": language,
                "compressed": storage_result.get("compressed", False),
                "created_at": storage_result.get("created_at"),
                "model_used": self.model
            }

            logger.info(f"Image generated successfully for {word}: {storage_result['filename']}")
            return result

        except ImageGenerationError:
            # 重新抛出已知错误
            raise
        except Exception as e:
            error_message = str(e).lower()
            if "timeout" in error_message or "deadline" in error_message:
                logger.error(f"Image generation timeout for {word}: {e}")
                raise ImageGenerationTimeoutError(f"Imagen生成超时: {str(e)}")
            elif "rate limit" in error_message or "resource exhausted" in error_message or "quota" in error_message:
                logger.error(f"Image generation rate limit for {word}: {e}")
                raise ImageGenerationRateLimitError(f"Imagen API限流: {str(e)}")
            elif "permission" in error_message or "unauthorized" in error_message or "forbidden" in error_message:
                logger.error(f"Image generation permission denied for {word}: {e}")
                raise ImageGenerationError(f"Imagen API密钥无效: {str(e)}")
            else:
                logger.error(f"Image generation error for {word}: {e}")
                raise ImageGenerationError(f"Imagen服务错误: {str(e)}")

    def generate_batch_word_images(
        self,
        words: List[str],
        style: str = "educational",
        description_template: str = "",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        批量生成单词图片

        Args:
            words: 单词列表
            style: 图片风格
            description_template: 描述模板，可以使用{word}变量
            **kwargs: 其他生成参数

        Returns:
            List[Dict]: 生成结果列表
        """
        results = []

        logger.info(f"Starting batch image generation for {len(words)} words")

        for i, word in enumerate(words):
            try:
                # 如果提供了描述模板，为每个单词生成具体描述
                description = description_template.format(word=word) if description_template else ""

                result = self.generate_word_image(
                    word=word,
                    style=style,
                    description=description,
                    **kwargs
                )

                results.append(result)
                logger.info(f"Generated image {i+1}/{len(words)}: {word}")

            except Exception as e:
                error_result = {
                    "success": False,
                    "error": str(e),
                    "word": word,
                    "style": style
                }
                results.append(error_result)
                logger.error(f"Failed to generate image for {word}: {e}")

                # 如果是限流错误，等待一段时间后继续
                if "rate limit" in str(e).lower():
                    logger.info("Rate limit detected, waiting before continuing...")
                    time.sleep(2)

        successful_count = sum(1 for r in results if r.get("success"))
        logger.info(f"Batch generation completed: {successful_count}/{len(words)} successful")

        return results

    def _generate_with_retry(self, prompt: str, aspect_ratio: str, negative_prompt: str) -> bytes:
        """
        带重试机制的图片生成

        Args:
            prompt: 生成提示词
            aspect_ratio: 长宽比
            negative_prompt: 负面提示词

        Returns:
            bytes: 生成的图片数据
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Image generation retry attempt {attempt}/{self.max_retries}")
                    time.sleep(2 ** attempt)  # 指数退避

                # 调用Gemini Imagen API
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        # Imagen 3 特定配置
                        response_modalities=["Image"],
                        generation_config=genai.types.GenerationConfig(
                            # 图片生成配置
                            aspect_ratio=aspect_ratio,
                            negative_prompt=negative_prompt,
                            # 其他参数根据Imagen 3文档调整
                        ),
                    )
                )

                # 提取图片数据
                if not response.candidates or not response.candidates[0].content:
                    raise ImageGenerationError("未生成任何图片")

                # 获取生成的图片
                generated_images = response.candidates[0].content.parts
                if not generated_images:
                    raise ImageGenerationError("生成的图片为空")

                # 提取图片二进制数据
                image_data = None
                for part in generated_images:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_data = part.inline_data.data
                        break

                if not image_data:
                    raise ImageGenerationError("无法提取图片数据")

                logger.debug(f"Image generated successfully, size: {len(image_data)} bytes")
                return image_data

            except APIError as e:
                last_error = e
                logger.warning(f"API error on attempt {attempt}: {e}")

                # 检查是否应该重试的错误
                if self._should_retry_error(str(e)) and attempt < self.max_retries:
                    continue
                else:
                    break

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error on attempt {attempt}: {e}")
                if attempt == self.max_retries:
                    break

        # 所有重试都失败了
        if last_error:
            if isinstance(last_error, APIError):
                raise ImageGenerationError(f"Imagen API错误: {str(last_error)}")
            else:
                raise ImageGenerationError(f"生成失败: {str(last_error)}")
        else:
            raise ImageGenerationError("生成失败: 未知错误")

    def _build_prompt(
        self,
        word: str,
        style: str,
        description: str,
        aspect_ratio: str,
        language: str = "zh"
    ) -> str:
        """
        构建图片生成提示词

        Args:
            word: 目标单词
            style: 图片风格
            description: 图片描述
            aspect_ratio: 长宽比
            language: 语言代码

        Returns:
            str: 构建的提示词
        """
        # 风格相关的修饰词
        style_modifiers = {
            "cartoon": "可爱卡通风格，色彩鲜艳，适合儿童学习",
            "realistic": "写实风格，真实感强，高清细节",
            "educational": "教育插画风格，清晰易懂，适合教学",
            "watercolor": "水彩画风格，柔和自然，艺术感强",
            "sketch": "素描风格，线条简洁，突出重点"
        }

        modifier = style_modifiers.get(style, "教育插画风格")

        # 基础提示词结构
        if language == "zh":
            prompt = f"""
请为英语单词"{word}"创作一幅{modifier}的教学图片。

单词含义：{description if description else "与单词含义相关的场景"}

要求：
1. 图片要清晰展示单词的含义
2. 风格要{modifier}
3. 不要包含任何文字、字母或数字
4. 适合语言学习场景
5. 长宽比为{aspect_ratio}

请直接生成图片，不要添加额外的解释或文字说明。
            """.strip()
        else:
            prompt = f"""
Create an educational illustration for the English word "{word}" in {style.replace('_', ' ')} style.

Word meaning: {description if description else "Scene related to the word's meaning"}

Requirements:
1. The image should clearly represent the word's meaning
2. Style should be {style.replace('_', ' ')}
3. Do not include any text, letters, or numbers
4. Suitable for language learning scenarios
5. Aspect ratio: {aspect_ratio}

Please generate the image directly without additional explanations.
            """.strip()

        return prompt

    def _validate_word(self, word: str) -> bool:
        """
        验证单词格式

        Args:
            word: 待验证的单词

        Returns:
            bool: 是否有效
        """
        if not word or not isinstance(word, str):
            return False

        word = word.strip()
        if not word:
            return False

        # 检查长度和字符
        if len(word) > 50:
            return False

        # 检查是否包含非法字符
        if any(char in word for char in ['<', '>', '|', '&', '$', '%', '@', '#']):
            return False

        # 检查是否只包含字母和连字符
        if not all(char.isalpha() or char == '-' or char.isspace() for char in word):
            return False

        return True

    def _validate_style(self, style: str) -> bool:
        """
        验证图片风格

        Args:
            style: 待验证的风格

        Returns:
            bool: 是否有效
        """
        return style in self.SUPPORTED_STYLES

    def _should_retry_error(self, error_message: str) -> bool:
        """
        判断错误是否应该重试

        Args:
            error_message: 错误消息

        Returns:
            bool: 是否应该重试
        """
        error_lower = error_message.lower()

        # 不应该重试的错误
        no_retry_keywords = [
            "permission denied",
            "unauthorized",
            "invalid api key",
            "forbidden",
            "not found",
            "invalid request"
        ]

        for keyword in no_retry_keywords:
            if keyword in error_lower:
                return False

        # 应该重试的错误
        retry_keywords = [
            "timeout",
            "deadline exceeded",
            "rate limit",
            "resource exhausted",
            "quota exceeded",
            "internal error",
            "service unavailable"
        ]

        for keyword in retry_keywords:
            if keyword in error_lower:
                return True

        # 默认不重试
        return False

    def get_supported_styles(self) -> List[str]:
        """
        获取支持的图片风格列表

        Returns:
            List[str]: 支持的风格列表
        """
        return self.SUPPORTED_STYLES.copy()

    def get_generation_stats(self) -> Dict[str, Any]:
        """
        获取生成服务统计信息

        Returns:
            Dict: 统计信息
        """
        return {
            "supported_styles": self.get_supported_styles(),
            "max_retries": self.max_retries,
            "default_model": self.model,
            "timeout_seconds": self.timeout,
            "storage_service_available": self.image_storage is not None,
            "api_configured": bool(self.api_key and self.api_key != "your-gemini-api-key-here")
        }