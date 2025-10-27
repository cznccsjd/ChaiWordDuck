"""
图片服务模块

提供图片生成、存储、压缩和管理功能
"""

from .image_storage_service import ImageStorageService, ImageStorageError

__all__ = [
    "ImageStorageService",
    "ImageStorageError",
]