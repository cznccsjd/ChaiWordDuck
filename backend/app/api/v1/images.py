"""
图片生成API路由

提供基于单词含义生成教学图片的API端点
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import os

from app.services.ai.image_generation_service import (
    ImageGenerationService,
    ImageGenerationError,
    ImageGenerationTimeoutError,
    ImageGenerationRateLimitError
)
from app.services.image.image_storage_service import ImageStorageService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# 请求模型
class ImageGenerationRequest(BaseModel):
    word: str = Field(..., description="目标单词", min_length=1, max_length=50)
    style: str = Field(default="educational", description="图片风格")
    description: str = Field(default="", description="图片描述", max_length=200)
    aspect_ratio: str = Field(default="1:1", description="长宽比: 1:1, 16:9, 9:16")
    negative_prompt: str = Field(default="text, words, letters, numbers", description="负面提示词")
    language: str = Field(default="zh", description="语言代码")


class BatchImageGenerationRequest(BaseModel):
    words: List[str] = Field(..., description="单词列表", min_items=1, max_items=10)
    style: str = Field(default="educational", description="图片风格")
    description_template: str = Field(default="", description="描述模板，可使用{word}变量", max_length=200)
    aspect_ratio: str = Field(default="1:1", description="长宽比")
    negative_prompt: str = Field(default="text, words, letters, numbers", description="负面提示词")
    language: str = Field(default="zh", description="语言代码")


# 响应模型
class ImageGenerationResponse(BaseModel):
    success: bool
    filepath: Optional[str] = None
    filename: Optional[str] = None
    size: Optional[int] = None
    word: Optional[str] = None
    style: Optional[str] = None
    description: Optional[str] = None
    aspect_ratio: Optional[str] = None
    language: Optional[str] = None
    compressed: Optional[bool] = None
    created_at: Optional[str] = None
    model_used: Optional[str] = None
    error: Optional[str] = None


class BatchImageGenerationResponse(BaseModel):
    success_count: int
    total_count: int
    results: List[ImageGenerationResponse]


# 依赖注入
def get_image_generation_service() -> ImageGenerationService:
    """获取图片生成服务实例"""
    try:
        storage_service = ImageStorageService()
        return ImageGenerationService(image_storage=storage_service)
    except Exception as e:
        logger.error(f"Failed to initialize image generation service: {e}")
        raise HTTPException(status_code=500, detail="图片生成服务初始化失败")


def get_image_storage_service() -> ImageStorageService:
    """获取图片存储服务实例"""
    try:
        return ImageStorageService()
    except Exception as e:
        logger.error(f"Failed to initialize image storage service: {e}")
        raise HTTPException(status_code=500, detail="图片存储服务初始化失败")


@router.post("/generate", response_model=ImageGenerationResponse)
async def generate_word_image(
    request: ImageGenerationRequest,
    background_tasks: BackgroundTasks,
    service: ImageGenerationService = Depends(get_image_generation_service)
):
    """
    生成单词教学图片

    Args:
        request: 图片生成请求
        background_tasks: 后台任务
        service: 图片生成服务

    Returns:
        ImageGenerationResponse: 生成结果
    """
    try:
        logger.info(f"Generating image for word: {request.word}")

        # 验证风格
        if request.style not in service.get_supported_styles():
            raise HTTPException(
                status_code=400,
                detail=f"不支持的图片风格: {request.style}"
            )

        # 验证长宽比
        valid_ratios = ["1:1", "16:9", "9:16", "4:3", "3:4"]
        if request.aspect_ratio not in valid_ratios:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的长宽比: {request.aspect_ratio}"
            )

        # 生成图片
        result = service.generate_word_image(
            word=request.word,
            style=request.style,
            description=request.description,
            aspect_ratio=request.aspect_ratio,
            negative_prompt=request.negative_prompt,
            language=request.language
        )

        # 记录生成统计（后台任务）
        background_tasks.add_task(
            logger.info,
            f"Image generation completed: {request.word} -> {result['filepath']}"
        )

        return ImageGenerationResponse(**result)

    except ImageGenerationTimeoutError as e:
        logger.error(f"Image generation timeout: {e}")
        raise HTTPException(status_code=408, detail="图片生成超时，请稍后重试")

    except ImageGenerationRateLimitError as e:
        logger.error(f"Image generation rate limit: {e}")
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后重试")

    except ImageGenerationError as e:
        logger.error(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in image generation: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/generate-batch", response_model=BatchImageGenerationResponse)
async def generate_batch_word_images(
    request: BatchImageGenerationRequest,
    background_tasks: BackgroundTasks,
    service: ImageGenerationService = Depends(get_image_generation_service)
):
    """
    批量生成单词教学图片

    Args:
        request: 批量生成请求
        background_tasks: 后台任务
        service: 图片生成服务

    Returns:
        BatchImageGenerationResponse: 批量生成结果
    """
    try:
        logger.info(f"Starting batch image generation for {len(request.words)} words")

        # 验证风格
        if request.style not in service.get_supported_styles():
            raise HTTPException(
                status_code=400,
                detail=f"不支持的图片风格: {request.style}"
            )

        # 验证单词数量
        if len(request.words) > 10:
            raise HTTPException(
                status_code=400,
                detail="单次批量生成最多支持10个单词"
            )

        # 批量生成
        results = service.generate_batch_word_images(
            words=request.words,
            style=request.style,
            description_template=request.description_template,
            aspect_ratio=request.aspect_ratio,
            negative_prompt=request.negative_prompt,
            language=request.language
        )

        # 转换为响应模型
        response_results = []
        successful_count = 0

        for result in results:
            response_result = ImageGenerationResponse(**result)
            response_results.append(response_result)
            if result.get("success"):
                successful_count += 1

        # 记录批量生成统计（后台任务）
        background_tasks.add_task(
            logger.info,
            f"Batch image generation completed: {successful_count}/{len(request.words)} successful"
        )

        return BatchImageGenerationResponse(
            success_count=successful_count,
            total_count=len(request.words),
            results=response_results
        )

    except ImageGenerationError as e:
        logger.error(f"Batch image generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in batch image generation: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/download/{filename}")
async def download_image(
    filename: str,
    storage_service: ImageStorageService = Depends(get_image_storage_service)
):
    """
    下载生成的图片文件

    Args:
        filename: 文件名
        storage_service: 图片存储服务

    Returns:
        FileResponse: 图片文件
    """
    try:
        # 查找文件
        image_files = storage_service.list_images(limit=1000)
        target_file = None

        for image in image_files:
            if image.get("filename") == filename:
                target_file = image
                break

        if not target_file:
            raise HTTPException(status_code=404, detail="图片文件不存在")

        filepath = target_file["filepath"]

        # 检查文件是否存在
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="图片文件不存在")

        # 返回文件
        return FileResponse(
            filepath,
            media_type="image/jpeg",
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading image {filename}: {e}")
        raise HTTPException(status_code=500, detail="下载图片失败")


@router.get("/styles")
async def get_supported_styles(
    service: ImageGenerationService = Depends(get_image_generation_service)
):
    """
    获取支持的图片风格列表

    Args:
        service: 图片生成服务

    Returns:
        Dict: 支持的风格列表
    """
    try:
        styles = service.get_supported_styles()
        return {
            "supported_styles": styles,
            "default_style": "educational"
        }
    except Exception as e:
        logger.error(f"Error getting supported styles: {e}")
        raise HTTPException(status_code=500, detail="获取支持的风格列表失败")


@router.get("/stats")
async def get_generation_stats(
    service: ImageGenerationService = Depends(get_image_generation_service),
    storage_service: ImageStorageService = Depends(get_image_storage_service)
):
    """
    获取图片生成服务统计信息

    Args:
        service: 图片生成服务
        storage_service: 图片存储服务

    Returns:
        Dict: 统计信息
    """
    try:
        # 获取生成服务统计
        gen_stats = service.get_generation_stats()

        # 获取存储服务统计
        storage_stats = storage_service.get_storage_stats()

        return {
            "generation_service": gen_stats,
            "storage_service": storage_stats
        }
    except Exception as e:
        logger.error(f"Error getting generation stats: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")


@router.get("/list")
async def list_images(
    folder: str = Query(default="", description="文件夹路径"),
    limit: int = Query(default=50, ge=1, le=200, description="最大返回数量"),
    storage_service: ImageStorageService = Depends(get_image_storage_service)
):
    """
    列出存储的图片

    Args:
        folder: 文件夹路径
        limit: 最大返回数量
        storage_service: 图片存储服务

    Returns:
        Dict: 图片列表
    """
    try:
        images = storage_service.list_images(folder=folder, limit=limit)

        return {
            "images": images,
            "count": len(images),
            "folder": folder,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error listing images: {e}")
        raise HTTPException(status_code=500, detail="列出图片失败")


@router.delete("/{filepath:path}")
async def delete_image(
    filepath: str,
    storage_service: ImageStorageService = Depends(get_image_storage_service)
):
    """
    删除图片文件

    Args:
        filepath: 文件路径
        storage_service: 图片存储服务

    Returns:
        Dict: 删除结果
    """
    try:
        # 安全检查：确保路径在存储目录内
        if ".." in filepath or filepath.startswith("/"):
            raise HTTPException(status_code=400, detail="无效的文件路径")

        result = storage_service.delete_image(filepath)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error", "删除失败"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image {filepath}: {e}")
        raise HTTPException(status_code=500, detail="删除图片失败")