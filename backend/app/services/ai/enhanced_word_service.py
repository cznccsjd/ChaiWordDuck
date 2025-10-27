"""
增强的单词手册服务 - 集成图片生成功能

结合文本生成和图片生成，提供完整的单词学习手册
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

from app.services.ai.base import AIServiceBase, WordManualData, AIServiceError
from app.services.ai.gemini_service import GeminiService
from app.services.ai.image_generation_service import ImageGenerationService, ImageGenerationError
from app.services.image.image_storage_service import ImageStorageService
from app.core.logging import get_logger

logger = get_logger(__name__)


class EnhancedWordService(AIServiceBase):
    """
    增强的单词手册服务

    集成了文本生成和图片生成功能，提供完整的单词学习体验
    """

    def __init__(
        self,
        text_service: Optional[AIServiceBase] = None,
        image_service: Optional[ImageGenerationService] = None,
        enable_image_generation: bool = True
    ):
        """
        初始化增强单词服务

        Args:
            text_service: 文本生成服务
            image_service: 图片生成服务
            enable_image_generation: 是否启用图片生成
        """
        # 初始化文本服务
        if text_service is None:
            self.text_service = GeminiService()
        else:
            self.text_service = text_service

        # 初始化图片服务
        if enable_image_generation:
            if image_service is None:
                try:
                    storage_service = ImageStorageService()
                    self.image_service = ImageGenerationService(storage_service)
                    self.enable_image_generation = True
                    logger.info("Image generation service initialized successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize image service: {e}")
                    self.image_service = None
                    self.enable_image_generation = False
            else:
                self.image_service = image_service
                self.enable_image_generation = True
        else:
            self.image_service = None
            self.enable_image_generation = False

        logger.info(f"EnhancedWordService initialized: text_service={type(self.text_service).__name__}, "
                   f"image_generation_enabled={self.enable_image_generation}")

    def generate_word_manual(
        self,
        word: str,
        language: str = "zh",
        generate_images: Optional[bool] = None,
        image_styles: Optional[List[str]] = None,
        **kwargs
    ) -> WordManualData:
        """
        生成带图片的单词学习手册

        Args:
            word: 目标单词
            language: 语言代码
            generate_images: 是否生成图片，None时使用默认设置
            image_styles: 图片风格列表，None时使用默认风格
            **kwargs: 其他参数

        Returns:
            WordManualData: 包含图片的单词学习手册
        """
        try:
            logger.info(f"Generating enhanced word manual for: {word}")

            # 确定是否生成图片
            should_generate_images = generate_images if generate_images is not None else self.enable_image_generation

            # 步骤1：生成文本内容
            logger.debug(f"Generating text content for: {word}")
            word_manual = self.text_service.generate_word_manual(word, language)

            # 步骤2：生成图片（如果启用）
            if should_generate_images and self.image_service:
                logger.debug(f"Generating images for: {word}")
                images = self._generate_word_images_async(
                    word=word,
                    manual=word_manual,
                    styles=image_styles or ["educational", "cartoon"],
                    **kwargs
                )
                word_manual.images = images
            else:
                word_manual.images = None
                logger.debug(f"Image generation disabled for: {word}")

            logger.info(f"Enhanced word manual generated for: {word}")
            return word_manual

        except Exception as e:
            logger.error(f"Failed to generate enhanced word manual for {word}: {e}")
            # 如果图片生成失败，仍然返回文本内容
            if isinstance(e, ImageGenerationError):
                logger.warning(f"Image generation failed for {word}, returning text only: {e}")
                try:
                    word_manual = self.text_service.generate_word_manual(word, language)
                    word_manual.images = None
                    return word_manual
                except Exception as text_error:
                    logger.error(f"Text generation also failed for {word}: {text_error}")
                    raise AIServiceError(f"文本和图片生成都失败: {str(text_error)}")
            else:
                raise AIServiceError(f"生成增强单词手册失败: {str(e)}")

    def _generate_word_images_async(
        self,
        word: str,
        manual: WordManualData,
        styles: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        异步生成多个风格的单词图片

        Args:
            word: 目标单词
            manual: 单词手册数据
            styles: 图片风格列表
            **kwargs: 其他参数

        Returns:
            Dict: 图片生成结果
        """
        try:
            # 准备图片生成任务
            image_tasks = []

            for style in styles:
                # 为不同风格生成不同的描述
                description = self._build_image_description(word, manual, style)

                task = {
                    "word": word,
                    "style": style,
                    "description": description,
                    "aspect_ratio": "1:1",  # 默认正方形
                    **kwargs
                }
                image_tasks.append(task)

            # 并发执行图片生成任务
            logger.info(f"Starting concurrent image generation for {word}: {len(image_tasks)} tasks")
            images = self._execute_concurrent_generation(image_tasks)

            return {
                "success": True,
                "images": images,
                "total_generated": len(images),
                "styles_requested": styles,
                "generation_time": images[0].get("generation_time", 0) if images else 0
            }

        except Exception as e:
            logger.error(f"Failed to generate images for {word}: {e}")
            return {
                "success": False,
                "error": str(e),
                "images": [],
                "total_generated": 0
            }

    def _execute_concurrent_generation(self, tasks: List[Dict[str, Any]], max_workers: int = 2) -> List[Dict[str, Any]]:
        """
        并发执行图片生成任务

        Args:
            tasks: 生成任务列表
            max_workers: 最大并发数

        Returns:
            List[Dict]: 生成结果列表
        """
        results = []

        def generate_single_image(task: Dict[str, Any]) -> Dict[str, Any]:
            """生成单个图片的任务函数"""
            start_time = time.time()
            try:
                result = self.image_service.generate_word_image(**task)
                generation_time = time.time() - start_time
                result["generation_time"] = generation_time
                return result
            except Exception as e:
                generation_time = time.time() - start_time
                return {
                    "success": False,
                    "error": str(e),
                    "word": task.get("word"),
                    "style": task.get("style"),
                    "generation_time": generation_time
                }

        try:
            # 使用线程池并发执行
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_task = {
                    executor.submit(generate_single_image, task): task
                    for task in tasks
                }

                # 收集结果
                for future in future_to_task:
                    try:
                        result = future.result(timeout=120)  # 2分钟超时
                        results.append(result)
                    except Exception as e:
                        task = future_to_task[future]
                        logger.error(f"Image generation task failed for {task.get('word')}: {e}")
                        results.append({
                            "success": False,
                            "error": str(e),
                            "word": task.get("word"),
                            "style": task.get("style")
                        })

        except Exception as e:
            logger.error(f"Concurrent image generation failed: {e}")

        # 按成功状态排序，成功的在前面
        results.sort(key=lambda x: x.get("success", False), reverse=True)
        return results

    def _build_image_description(self, word: str, manual: WordManualData, style: str) -> str:
        """
        根据单词手册内容和图片风格构建图片描述

        Args:
            word: 目标单词
            manual: 单词手册数据
            style: 图片风格

        Returns:
            str: 图片描述
        """
        try:
            # 基础描述元素
            elements = []

            # 单词翻译
            if manual.translation:
                elements.append(f"代表'{manual.translation}'")

            # 根据风格调整描述
            if style == "educational":
                elements.append("教育插图")
                if manual.core_game.content:
                    elements.append(f"展现'{manual.core_game.content[:20]}...'的场景")
                elements.append("清晰易懂，适合学习")

            elif style == "cartoon":
                elements.append("卡通风格")
                elements.append("可爱有趣")
                if manual.translation:
                    elements.append(f"与{manual.translation}相关的动画场景")

            elif style == "realistic":
                elements.append("写实风格")
                elements.append("真实感强")
                if manual.translation:
                    elements.append(f"体现{manual.translation}的真实场景")

            # 组合描述
            description = " ".join(elements)

            logger.debug(f"Built image description for {word} ({style}): {description}")
            return description

        except Exception as e:
            logger.warning(f"Failed to build image description for {word}: {e}")
            # 返回简单描述
            return f"展现{word}含义的{style}图片"

    def generate_batch_word_manuals(
        self,
        words: List[str],
        language: str = "zh",
        generate_images: Optional[bool] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        批量生成带图片的单词手册

        Args:
            words: 单词列表
            language: 语言代码
            generate_images: 是否生成图片
            **kwargs: 其他参数

        Returns:
            List[Dict]: 生成结果列表
        """
        results = []

        logger.info(f"Starting batch enhanced word manual generation for {len(words)} words")

        for i, word in enumerate(words):
            try:
                logger.info(f"Processing word {i+1}/{len(words)}: {word}")

                start_time = time.time()
                word_manual = self.generate_word_manual(
                    word=word,
                    language=language,
                    generate_images=generate_images,
                    **kwargs
                )
                processing_time = time.time() - start_time

                result = {
                    "success": True,
                    "word": word,
                    "manual": word_manual,
                    "processing_time": processing_time,
                    "index": i
                }

                results.append(result)
                logger.info(f"Successfully generated manual for {word} in {processing_time:.2f}s")

            except Exception as e:
                logger.error(f"Failed to generate manual for {word}: {e}")
                result = {
                    "success": False,
                    "error": str(e),
                    "word": word,
                    "index": i
                }
                results.append(result)

        # 统计结果
        successful_count = sum(1 for r in results if r.get("success"))
        total_time = sum(r.get("processing_time", 0) for r in results if r.get("success"))

        logger.info(f"Batch generation completed: {successful_count}/{len(words)} successful in {total_time:.2f}s total")

        return results

    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态信息

        Returns:
            Dict: 服务状态
        """
        status = {
            "text_service": {
                "type": type(self.text_service).__name__,
                "available": True
            },
            "image_generation_enabled": self.enable_image_generation
        }

        if self.image_service:
            try:
                image_stats = self.image_service.get_generation_stats()
                status["image_service"] = {
                    "type": type(self.image_service).__name__,
                    "available": image_stats.get("api_configured", False),
                    "stats": image_stats
                }
            except Exception as e:
                status["image_service"] = {
                    "type": type(self.image_service).__name__,
                    "available": False,
                    "error": str(e)
                }
        else:
            status["image_service"] = None

        return status