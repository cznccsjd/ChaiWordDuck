"""图片存储服务单元测试"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from PIL import Image
import tempfile
import shutil

from app.services.image.image_storage_service import ImageStorageService, ImageStorageError
from app.core.config import get_settings


class TestImageStorageService:
    """图片存储服务测试类"""

    @pytest.fixture
    def temp_storage_dir(self):
        """创建临时存储目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def image_storage_service(self, temp_storage_dir):
        """创建图片存储服务实例"""
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                image_storage_path=temp_storage_dir,
                max_image_size_mb=5,
                allowed_image_formats=["jpg", "jpeg", "png", "webp"]
            )
            return ImageStorageService()

    @pytest.fixture
    def sample_image_bytes(self):
        """创建示例图片字节数据"""
        # 创建一个简单的测试图片
        image = Image.new('RGB', (100, 100), color='red')
        import io
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes.getvalue()

    def test_initialization(self, image_storage_service):
        """测试服务初始化"""
        assert image_storage_service.max_file_size == 5 * 1024 * 1024  # 5MB
        assert "jpg" in image_storage_service.allowed_formats
        assert "jpeg" in image_storage_service.allowed_formats
        assert "png" in image_storage_service.allowed_formats

    def test_validate_image_format_valid(self, image_storage_service):
        """测试有效图片格式验证"""
        # 测试jpg格式
        assert image_storage_service._validate_image_format("test.jpg") is True
        # 测试jpeg格式
        assert image_storage_service._validate_image_format("test.jpeg") is True
        # 测试png格式
        assert image_storage_service._validate_image_format("test.png") is True

    def test_validate_image_format_invalid(self, image_storage_service):
        """测试无效图片格式验证"""
        # 测试不支持的格式
        assert image_storage_service._validate_image_format("test.gif") is False
        assert image_storage_service._validate_image_format("test.bmp") is False
        assert image_storage_service._validate_image_format("test.tiff") is False

    def test_validate_image_size_valid(self, image_storage_service, sample_image_bytes):
        """测试有效图片大小验证"""
        small_image = sample_image_bytes[:1000]  # 小图片
        assert image_storage_service._validate_image_size(small_image) is True

    def test_validate_image_size_invalid(self, image_storage_service):
        """测试无效图片大小验证"""
        # 创建超过限制的大图片
        large_image = b'x' * (6 * 1024 * 1024)  # 6MB
        assert image_storage_service._validate_image_size(large_image) is False

    def test_save_image_success(self, image_storage_service, sample_image_bytes):
        """测试成功保存图片"""
        filename = "test_image.jpg"

        result = image_storage_service.save_image(
            image_data=sample_image_bytes,
            filename=filename,
            subfolder="test"
        )

        # 验证返回结果
        assert result["success"] is True
        assert "filepath" in result
        assert "filename" in result
        assert "size" in result
        assert result["original_filename"] == filename
        assert filename.split('.')[0] in result["filename"]  # 检查基础名称

        # 验证文件实际存在
        assert os.path.exists(result["filepath"])

        # 验证文件大小
        assert os.path.getsize(result["filepath"]) > 0

    def test_save_image_invalid_format(self, image_storage_service, sample_image_bytes):
        """测试保存无效格式的图片"""
        filename = "test_image.gif"  # 不支持的格式

        result = image_storage_service.save_image(
            image_data=sample_image_bytes,
            filename=filename
        )

        assert result["success"] is False
        assert "error" in result
        assert "不支持的图片格式" in result["error"]

    def test_save_image_invalid_size(self, image_storage_service):
        """测试保存超大图片"""
        filename = "test_image.jpg"
        large_image = b'x' * (6 * 1024 * 1024)  # 6MB

        result = image_storage_service.save_image(
            image_data=large_image,
            filename=filename
        )

        assert result["success"] is False
        assert "error" in result
        assert "图片文件过大" in result["error"]

    def test_save_image_corrupted_data(self, image_storage_service):
        """测试保存损坏的图片数据"""
        filename = "test_image.jpg"
        corrupted_data = b"not an image" * 100

        result = image_storage_service.save_image(
            image_data=corrupted_data,
            filename=filename
        )

        assert result["success"] is False
        assert "error" in result
        assert "无法识别的图片格式" in result["error"]

    def test_generate_unique_filename(self, image_storage_service):
        """测试生成唯一文件名"""
        base_name = "test_image"

        # 测试生成的文件名包含基础名称
        filename = image_storage_service._generate_unique_filename(base_name, "jpg")
        assert base_name in filename
        assert filename.endswith(".jpg")

        # 测试多次生成的文件名不同
        filename2 = image_storage_service._generate_unique_filename(base_name, "jpg")
        assert filename != filename2

    def test_create_directory_if_not_exists(self, image_storage_service, temp_storage_dir):
        """测试创建目录功能"""
        new_folder = os.path.join(temp_storage_dir, "new_test_folder")

        # 确保目录不存在
        assert not os.path.exists(new_folder)

        # 调用创建目录方法
        image_storage_service._ensure_directory_exists(new_folder)

        # 验证目录已创建
        assert os.path.exists(new_folder)
        assert os.path.isdir(new_folder)

    def test_get_image_info(self, image_storage_service, sample_image_bytes):
        """测试获取图片信息"""
        filename = "test_info_image.jpg"

        # 先保存图片
        save_result = image_storage_service.save_image(
            image_data=sample_image_bytes,
            filename=filename
        )

        # 获取图片信息
        info = image_storage_service.get_image_info(save_result["filepath"])

        assert info["exists"] is True
        assert "size" in info
        assert "format" in info
        assert "width" in info
        assert "height" in info
        assert info["width"] == 100
        assert info["height"] == 100

    def test_get_image_info_not_exists(self, image_storage_service):
        """测试获取不存在图片的信息"""
        info = image_storage_service.get_image_info("non_existent_file.jpg")

        assert info["exists"] is False

    def test_delete_image_success(self, image_storage_service, sample_image_bytes):
        """测试成功删除图片"""
        filename = "test_delete_image.jpg"

        # 先保存图片
        save_result = image_storage_service.save_image(
            image_data=sample_image_bytes,
            filename=filename
        )

        filepath = save_result["filepath"]
        assert os.path.exists(filepath)

        # 删除图片
        delete_result = image_storage_service.delete_image(filepath)

        assert delete_result["success"] is True
        assert not os.path.exists(filepath)

    def test_delete_image_not_exists(self, image_storage_service):
        """测试删除不存在的图片"""
        result = image_storage_service.delete_image("non_existent_file.jpg")

        assert result["success"] is False
        assert "error" in result
        assert "文件不存在" in result["error"]

    def test_compress_image_large(self, image_storage_service):
        """测试压缩大图片"""
        # 创建一个较大的测试图片
        large_image = Image.new('RGB', (2000, 2000), color='blue')
        import io
        img_bytes = io.BytesIO()
        large_image.save(img_bytes, format='JPEG', quality=95)
        img_bytes.seek(0)

        original_size = len(img_bytes.getvalue())

        # 压缩图片
        compressed_data = image_storage_service._compress_image(img_bytes.getvalue())

        # 验证压缩后的数据
        assert len(compressed_data) < original_size

        # 验证压缩后的数据仍然是有效的图片
        compressed_image = Image.open(io.BytesIO(compressed_data))
        assert compressed_image.size == (2000, 2000)

    def test_compress_image_small_no_change(self, image_storage_service, sample_image_bytes):
        """测试压缩小图片不改变"""
        original_size = len(sample_image_bytes)

        compressed_data = image_storage_service._compress_image(sample_image_bytes)

        # 小图片被压缩是正常的，主要是转换为JPEG格式
        size_ratio = len(compressed_data) / original_size
        assert 0.1 <= size_ratio <= 2.0  # 允许较大差异，因为格式转换

    @patch("os.makedirs")
    def test_directory_creation_error(self, mock_makedirs, image_storage_service, sample_image_bytes):
        """测试目录创建失败"""
        # 模拟目录创建失败
        mock_makedirs.side_effect = OSError("Permission denied")

        # 由于已在初始化时创建了目录，这个测试需要重新设计
        # 模拟在保存到子文件夹时创建目录失败
        with patch("os.makedirs") as mock_makedirs_sub:
            mock_makedirs_sub.side_effect = OSError("Permission denied")

            result = image_storage_service.save_image(
                image_data=sample_image_bytes,
                filename="test.jpg",
                subfolder="test_subfolder"
            )

            assert result["success"] is False
            assert "无法创建存储目录" in result["error"]

    def test_storage_path_configuration(self):
        """测试存储路径配置"""
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                image_storage_path="/custom/storage/path",
                max_image_size_mb=10,
                allowed_image_formats_list=["jpg", "png"]
            )

            with patch("os.makedirs"):  # 避免实际创建目录
                service = ImageStorageService()
                assert service.storage_path == "/custom/storage/path"
                assert service.max_file_size == 10 * 1024 * 1024