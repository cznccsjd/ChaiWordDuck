"""
图片存储管理服务

提供图片文件的本地存储、验证、压缩和管理功能
"""

import os
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageOps
import io

from app.core.logging import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)


class ImageStorageError(Exception):
    """图片存储相关错误"""
    pass


class ImageStorageService:
    """图片存储管理服务"""

    def __init__(self):
        """初始化图片存储服务"""
        self.settings = get_settings()
        self.storage_path = getattr(self.settings, 'image_storage_path', 'uploads/images')
        self.max_file_size = getattr(self.settings, 'max_image_size_mb', 5) * 1024 * 1024  # MB to bytes
        self.allowed_formats = getattr(self.settings, 'allowed_image_formats_list', ['jpg', 'jpeg', 'png', 'webp'])

        # 确保存储目录存在
        self._ensure_directory_exists(self.storage_path)

        logger.info(f"Image storage service initialized: path={self.storage_path}, "
                   f"max_size={self.max_file_size/1024/1024:.1f}MB, "
                   f"formats={self.allowed_formats}")

    def save_image(self, image_data: bytes, filename: str, subfolder: str = "") -> Dict[str, Any]:
        """
        保存图片文件

        Args:
            image_data: 图片二进制数据
            filename: 原始文件名
            subfolder: 子文件夹路径

        Returns:
            Dict: 保存结果，包含success, filepath, filename, size等信息
        """
        try:
            logger.debug(f"Saving image: {filename}, size: {len(image_data)} bytes")

            # 验证图片格式
            if not self._validate_image_format(filename):
                error_msg = f"不支持的图片格式: {filename}"
                logger.warning(error_msg)
                return {"success": False, "error": error_msg}

            # 验证图片大小
            if not self._validate_image_size(image_data):
                error_msg = f"图片文件过大: {len(image_data)} bytes"
                logger.warning(error_msg)
                return {"success": False, "error": error_msg}

            # 验证图片数据完整性
            if not self._validate_image_data(image_data):
                error_msg = "无法识别的图片格式或数据损坏"
                logger.warning(error_msg)
                return {"success": False, "error": error_msg}

            # 生成唯一文件名
            file_extension = Path(filename).suffix.lower()
            unique_filename = self._generate_unique_filename(
                Path(filename).stem, file_extension.lstrip('.')
            )

            # 构建完整文件路径
            if subfolder:
                full_folder = os.path.join(self.storage_path, subfolder)
                self._ensure_directory_exists(full_folder)
                filepath = os.path.join(full_folder, unique_filename)
            else:
                filepath = os.path.join(self.storage_path, unique_filename)

            # 如果图片过大，进行压缩
            processed_data = self._compress_image_if_needed(image_data)

            # 保存图片文件
            with open(filepath, 'wb') as f:
                f.write(processed_data)

            # 验证保存的文件
            if not os.path.exists(filepath):
                raise ImageStorageError("文件保存失败")

            file_size = os.path.getsize(filepath)

            result = {
                "success": True,
                "filepath": filepath,
                "filename": unique_filename,
                "original_filename": filename,
                "size": file_size,
                "folder": subfolder,
                "created_at": datetime.now().isoformat(),
                "compressed": len(processed_data) < len(image_data)
            }

            logger.info(f"Image saved successfully: {unique_filename}, size: {file_size} bytes")
            return result

        except Exception as e:
            error_msg = f"保存图片时发生错误: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def get_image_info(self, filepath: str) -> Dict[str, Any]:
        """
        获取图片文件信息

        Args:
            filepath: 图片文件路径

        Returns:
            Dict: 图片信息
        """
        try:
            if not os.path.exists(filepath):
                return {"exists": False, "error": "文件不存在"}

            file_size = os.path.getsize(filepath)
            file_stat = os.stat(filepath)

            # 尝试读取图片信息
            try:
                with Image.open(filepath) as img:
                    width, height = img.size
                    format_name = img.format
                    mode = img.mode
            except Exception as e:
                logger.warning(f"Cannot read image info for {filepath}: {e}")
                width, height, format_name, mode = 0, 0, "unknown", "unknown"

            return {
                "exists": True,
                "filepath": filepath,
                "size": file_size,
                "width": width,
                "height": height,
                "format": format_name,
                "mode": mode,
                "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            }

        except Exception as e:
            error_msg = f"获取图片信息时发生错误: {str(e)}"
            logger.error(error_msg)
            return {"exists": False, "error": error_msg}

    def delete_image(self, filepath: str) -> Dict[str, Any]:
        """
        删除图片文件

        Args:
            filepath: 图片文件路径

        Returns:
            Dict: 删除结果
        """
        try:
            if not os.path.exists(filepath):
                error_msg = "文件不存在"
                logger.warning(f"Attempted to delete non-existent file: {filepath}")
                return {"success": False, "error": error_msg}

            os.remove(filepath)

            logger.info(f"Image deleted successfully: {filepath}")
            return {"success": True, "message": "文件删除成功"}

        except Exception as e:
            error_msg = f"删除图片时发生错误: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def list_images(self, folder: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """
        列出指定文件夹中的图片

        Args:
            folder: 文件夹路径
            limit: 最大返回数量

        Returns:
            List[Dict]: 图片信息列表
        """
        try:
            search_path = os.path.join(self.storage_path, folder) if folder else self.storage_path

            if not os.path.exists(search_path):
                return []

            images = []
            for filename in os.listdir(search_path):
                if len(images) >= limit:
                    break

                filepath = os.path.join(search_path, filename)
                if os.path.isfile(filepath) and self._validate_image_format(filename):
                    info = self.get_image_info(filepath)
                    if info["exists"]:
                        info["folder"] = folder
                        images.append(info)

            # 按修改时间排序，最新的在前
            images.sort(key=lambda x: x.get("modified_at", ""), reverse=True)
            return images

        except Exception as e:
            logger.error(f"列出图片时发生错误: {str(e)}")
            return []

    def _validate_image_format(self, filename: str) -> bool:
        """验证图片文件格式"""
        if not filename:
            return False

        file_extension = Path(filename).suffix.lower().lstrip('.')
        return file_extension in self.allowed_formats

    def _validate_image_size(self, image_data: bytes) -> bool:
        """验证图片文件大小"""
        return 0 < len(image_data) <= self.max_file_size

    def _validate_image_data(self, image_data: bytes) -> bool:
        """验证图片数据完整性"""
        if not image_data:
            return False

        try:
            # 尝试用PIL打开图片数据
            with Image.open(io.BytesIO(image_data)) as img:
                # 验证图片可以被正确读取
                img.verify()

            # 再次尝试加载图片
            with Image.open(io.BytesIO(image_data)) as img:
                # 尝试获取图片基本信息
                _ = img.size
                _ = img.format

            return True
        except Exception as e:
            logger.warning(f"Image data validation failed: {e}")
            return False

    def _generate_unique_filename(self, base_name: str, extension: str) -> str:
        """生成唯一的文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_id = str(uuid.uuid4())[:8]

        # 清理基础文件名中的特殊字符
        clean_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_name = clean_name.replace(' ', '_')

        return f"{clean_name}_{timestamp}_{random_id}.{extension}"

    def _ensure_directory_exists(self, directory: str) -> None:
        """确保目录存在，如果不存在则创建"""
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as e:
            logger.error(f"无法创建存储目录 {directory}: {e}")
            raise ImageStorageError(f"无法创建存储目录: {str(e)}")

    def _compress_image_if_needed(self, image_data: bytes, max_size_mb: float = 2.0) -> bytes:
        """
        如果图片过大则进行压缩

        Args:
            image_data: 原始图片数据
            max_size_mb: 最大允许大小（MB）

        Returns:
            bytes: 处理后的图片数据
        """
        current_size_mb = len(image_data) / (1024 * 1024)

        # 如果图片不大，直接返回
        if current_size_mb <= max_size_mb:
            return image_data

        logger.info(f"Compressing image from {current_size_mb:.2f}MB to under {max_size_mb}MB")

        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # 转换为RGB模式（如果需要）
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background

                # 逐步降低质量直到满足大小要求
                quality = 95
                while quality > 10:
                    output = io.BytesIO()
                    img.save(output, format='JPEG', quality=quality, optimize=True)
                    compressed_data = output.getvalue()

                    compressed_size_mb = len(compressed_data) / (1024 * 1024)
                    if compressed_size_mb <= max_size_mb:
                        logger.info(f"Image compressed to {compressed_size_mb:.2f}MB with quality {quality}")
                        return compressed_data

                    quality -= 10

                # 如果质量降到最低仍然过大，调整尺寸
                if len(compressed_data) / (1024 * 1024) > max_size_mb:
                    width, height = img.size
                    scale_factor = 0.8

                    while scale_factor > 0.3:
                        new_width = int(width * scale_factor)
                        new_height = int(height * scale_factor)
                        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                        output = io.BytesIO()
                        resized_img.save(output, format='JPEG', quality=85, optimize=True)
                        compressed_data = output.getvalue()

                        if len(compressed_data) / (1024 * 1024) <= max_size_mb:
                            logger.info(f"Image resized to {new_width}x{new_height} and compressed")
                            return compressed_data

                        scale_factor -= 0.1

                # 返回最后的压缩结果
                logger.warning(f"Image compression completed, final size: {len(compressed_data) / (1024 * 1024):.2f}MB")
                return compressed_data

        except Exception as e:
            logger.error(f"Image compression failed: {e}")
            # 压缩失败，返回原始数据
            return image_data

    def _compress_image(self, image_data: bytes) -> bytes:
        """
        压缩图片（无大小限制，只优化）

        Args:
            image_data: 原始图片数据

        Returns:
            bytes: 压缩后的图片数据
        """
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # 转换为RGB模式（如果需要）
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background

                # 自动压缩优化
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=90, optimize=True)
                return output.getvalue()

        except Exception as e:
            logger.error(f"Image compression failed: {e}")
            return image_data

    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            total_files = 0
            total_size = 0
            format_counts = {}

            for root, dirs, files in os.walk(self.storage_path):
                for file in files:
                    filepath = os.path.join(root, file)
                    if self._validate_image_format(file):
                        total_files += 1
                        file_size = os.path.getsize(filepath)
                        total_size += file_size

                        # 统计格式
                        file_ext = Path(file).suffix.lower().lstrip('.')
                        format_counts[file_ext] = format_counts.get(file_ext, 0) + 1

            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "storage_path": self.storage_path,
                "format_counts": format_counts,
                "max_file_size_mb": self.max_file_size / (1024 * 1024),
                "allowed_formats": self.allowed_formats
            }

        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {"error": str(e)}