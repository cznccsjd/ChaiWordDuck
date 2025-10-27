"""图片生成服务单元测试"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from google.genai.errors import APIError

from app.services.ai.image_generation_service import ImageGenerationService, ImageGenerationError, ImageGenerationTimeoutError, ImageGenerationRateLimitError
from app.services.image.image_storage_service import ImageStorageService


class TestImageGenerationService:
    """图片生成服务测试类"""

    @pytest.fixture
    def mock_image_storage(self):
        """模拟图片存储服务"""
        storage_mock = Mock(spec=ImageStorageService)
        storage_mock.save_image.return_value = {
            "success": True,
            "filepath": "/test/path/test_image.jpg",
            "filename": "test_image.jpg",
            "size": 1024
        }
        return storage_mock

    @pytest.fixture
    def image_generation_service(self, mock_image_storage):
        """创建图片生成服务实例"""
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                gemini_api_key="test_api_key",
                imagen_model="imagen-3.0-generate-001",
                imagen_timeout=60,
                max_image_retries=3
            )
            with patch("google.genai.Client"):
                service = ImageGenerationService(image_storage=mock_image_storage)
                return service

    def test_initialization_success(self, mock_image_storage):
        """测试服务初始化成功"""
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                gemini_api_key="test_api_key",
                imagen_model="imagen-3.0-generate-001",
                imagen_timeout=60,
                max_image_retries=3
            )

            with patch("google.genai.Client") as mock_client:
                service = ImageGenerationService(image_storage=mock_image_storage)

                assert service.api_key == "test_api_key"
                assert service.model == "imagen-3.0-generate-001"
                assert service.timeout == 60
                assert service.max_retries == 3
                assert service.image_storage == mock_image_storage
                mock_client.assert_called_once()

    def test_initialization_invalid_api_key(self, mock_image_storage):
        """测试无效API密钥初始化失败"""
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                gemini_api_key="",  # 空API密钥
                imagen_model="imagen-3.0-generate-001"
            )

            with pytest.raises(ImageGenerationError, match="Gemini API Key未配置或无效"):
                ImageGenerationService(image_storage=mock_image_storage)

    def test_generate_word_image_success(self, image_generation_service):
        """测试成功生成单词图片"""
        # 模拟Gemini API响应
        mock_response = Mock()
        mock_response.generated_images = [
            Mock(image=b"fake_image_data")
        ]

        with patch.object(image_generation_service.client, 'generate_content') as mock_generate:
            mock_generate.return_value = mock_response

            result = image_generation_service.generate_word_image(
                word="elephant",
                style="educational",
                description="a cartoon elephant studying English"
            )

            # 验证返回结果
            assert result["success"] is True
            assert "filepath" in result
            assert "filename" in result
            assert "size" in result
            assert result["word"] == "elephant"
            assert result["style"] == "educational"

            # 验证存储服务被调用
            image_generation_service.image_storage.save_image.assert_called_once()

            # 验证API调用参数
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            assert call_args[1]["model"] == "imagen-3.0-generate-001"

    def test_generate_word_image_with_custom_parameters(self, image_generation_service):
        """测试使用自定义参数生成单词图片"""
        mock_response = Mock()
        mock_response.generated_images = [
            Mock(image=b"fake_image_data")
        ]

        with patch.object(image_generation_service.client, 'generate_content') as mock_generate:
            mock_generate.return_value = mock_response

            result = image_generation_service.generate_word_image(
                word="philosophy",
                style="realistic",
                description="ancient Greek philosopher teaching",
                aspect_ratio="16:9",
                negative_prompt="text, words, letters"
            )

            assert result["success"] is True
            assert result["word"] == "philosophy"
            assert result["style"] == "realistic"

    def test_generate_word_image_api_error(self, image_generation_service):
        """测试API错误处理"""
        with patch.object(image_generation_service.client, 'generate_content') as mock_generate:
            mock_generate.side_effect = APIError("Invalid API key")

            with pytest.raises(ImageGenerationError, match="Imagen API错误"):
                image_generation_service.generate_word_image(
                    word="test",
                    style="cartoon"
                )

    def test_generate_word_image_timeout_error(self, image_generation_service):
        """测试超时错误处理"""
        with patch.object(image_generation_service.client, 'generate_content') as mock_generate:
            mock_generate.side_effect = Exception("Request timeout")

            with pytest.raises(ImageGenerationTimeoutError, match="Imagen生成超时"):
                image_generation_service.generate_word_image(
                    word="test",
                    style="cartoon"
                )

    def test_generate_word_image_rate_limit_error(self, image_generation_service):
        """测试限流错误处理"""
        with patch.object(image_generation_service.client, 'generate_content') as mock_generate:
            mock_generate.side_effect = Exception("Rate limit exceeded")

            with pytest.raises(ImageGenerationRateLimitError, match="Imagen API限流"):
                image_generation_service.generate_word_image(
                    word="test",
                    style="cartoon"
                )

    def test_generate_word_image_storage_failure(self, image_generation_service):
        """测试图片存储失败"""
        # 模拟API成功但存储失败
        mock_response = Mock()
        mock_response.generated_images = [
            Mock(image=b"fake_image_data")
        ]

        # 模拟存储服务失败
        image_generation_service.image_storage.save_image.return_value = {
            "success": False,
            "error": "存储空间不足"
        }

        with patch.object(image_generation_service.client, 'generate_content') as mock_generate:
            mock_generate.return_value = mock_response

            with pytest.raises(ImageGenerationError, match="图片存储失败"):
                image_generation_service.generate_word_image(
                    word="test",
                    style="cartoon"
                )

    def test_generate_word_image_empty_response(self, image_generation_service):
        """测试空响应处理"""
        mock_response = Mock()
        mock_response.generated_images = []  # 空图片列表

        with patch.object(image_generation_service.client, 'generate_content') as mock_generate:
            mock_generate.return_value = mock_response

            with pytest.raises(ImageGenerationError, match="未生成任何图片"):
                image_generation_service.generate_word_image(
                    word="test",
                    style="cartoon"
                )

    def test_build_prompt_educational_style(self, image_generation_service):
        """测试构建教育风格prompt"""
        prompt = image_generation_service._build_prompt(
            word="butterfly",
            style="educational",
            description="colorful butterfly with labeled parts"
        )

        assert "butterfly" in prompt
        assert "educational" in prompt.lower()
        assert "colorful butterfly with labeled parts" in prompt
        assert "适合教学" in prompt

    def test_build_prompt_cartoon_style(self, image_generation_service):
        """测试构建卡通风格prompt"""
        prompt = image_generation_service._build_prompt(
            word="dinosaur",
            style="cartoon",
            description="friendly cartoon dinosaur"
        )

        assert "dinosaur" in prompt
        assert "cartoon" in prompt.lower()
        assert "friendly cartoon dinosaur" in prompt
        assert "可爱" in prompt or "卡通" in prompt

    def test_build_prompt_realistic_style(self, image_generation_service):
        """测试构建写实风格prompt"""
        prompt = image_generation_service._build_prompt(
            word="eagle",
            style="realistic",
            description="majestic eagle flying"
        )

        assert "eagle" in prompt
        assert "realistic" in prompt.lower()
        assert "majestic eagle flying" in prompt
        assert "真实" in prompt or "写实" in prompt

    def test_build_prompt_with_aspect_ratio(self, image_generation_service):
        """测试构建带长宽比的prompt"""
        prompt = image_generation_service._build_prompt(
            word="tree",
            style="educational",
            description="large oak tree",
            aspect_ratio="16:9"
        )

        assert "tree" in prompt
        assert "16:9" in prompt or "宽屏" in prompt

    def test_validate_style_valid(self, image_generation_service):
        """测试有效风格验证"""
        valid_styles = ["cartoon", "realistic", "educational", "watercolor", "sketch"]

        for style in valid_styles:
            assert image_generation_service._validate_style(style) is True

    def test_validate_style_invalid(self, image_generation_service):
        """测试无效风格验证"""
        invalid_styles = ["abstract", "modern", "invalid_style"]

        for style in invalid_styles:
            assert image_generation_service._validate_style(style) is False

    def test_validate_word_valid(self, image_generation_service):
        """测试有效单词验证"""
        valid_words = ["elephant", "butterfly", "philosophy", "computer"]

        for word in valid_words:
            assert image_generation_service._validate_word(word) is True

    def test_validate_word_invalid(self, image_generation_service):
        """测试无效单词验证"""
        invalid_words = ["", "   ", "test123", "@#$%", "verylongword" * 10]

        for word in invalid_words:
            assert image_generation_service._validate_word(word) is False

    def test_generate_word_image_retry_mechanism(self, image_generation_service):
        """测试重试机制"""
        mock_response = Mock()
        mock_response.generated_images = [
            Mock(image=b"fake_image_data")
        ]

        with patch.object(image_generation_service.client, 'generate_content') as mock_generate:
            # 第一次失败，第二次成功
            mock_generate.side_effect = [
                Exception("Temporary error"),
                mock_response
            ]

            result = image_generation_service.generate_word_image(
                word="test",
                style="cartoon"
            )

            assert result["success"] is True
            assert mock_generate.call_count == 2

    def test_generate_word_image_max_retries_exceeded(self, image_generation_service):
        """测试超过最大重试次数"""
        with patch.object(image_generation_service.client, 'generate_content') as mock_generate:
            mock_generate.side_effect = Exception("Persistent error")

            with pytest.raises(ImageGenerationError, match="生成失败"):
                image_generation_service.generate_word_image(
                    word="test",
                    style="cartoon"
                )

            # 验证重试次数
            assert mock_generate.call_count == image_generation_service.max_retries + 1

    def test_generate_batch_word_images(self, image_generation_service):
        """测试批量生成单词图片"""
        mock_response = Mock()
        mock_response.generated_images = [
            Mock(image=b"image1_data"),
            Mock(image=b"image2_data")
        ]

        with patch.object(image_generation_service, 'generate_word_image') as mock_generate:
            mock_generate.side_effect = [
                {"success": True, "filepath": "/test/image1.jpg", "word": "cat"},
                {"success": True, "filepath": "/test/image2.jpg", "word": "dog"}
            ]

            words = ["cat", "dog"]
            results = image_generation_service.generate_batch_word_images(
                words=words,
                style="cartoon"
            )

            assert len(results) == 2
            assert results[0]["word"] == "cat"
            assert results[1]["word"] == "dog"
            assert all(result["success"] for result in results)

    def test_generate_batch_word_images_partial_failure(self, image_generation_service):
        """测试批量生成部分失败"""
        with patch.object(image_generation_service, 'generate_word_image') as mock_generate:
            mock_generate.side_effect = [
                {"success": True, "filepath": "/test/image1.jpg", "word": "cat"},
                {"success": False, "error": "生成失败", "word": "dog"}
            ]

            words = ["cat", "dog"]
            results = image_generation_service.generate_batch_word_images(
                words=words,
                style="cartoon"
            )

            assert len(results) == 2
            assert results[0]["success"] is True
            assert results[1]["success"] is False

    def test_get_supported_styles(self, image_generation_service):
        """测试获取支持的图片风格"""
        styles = image_generation_service.get_supported_styles()

        assert isinstance(styles, list)
        assert len(styles) > 0
        assert "cartoon" in styles
        assert "realistic" in styles
        assert "educational" in styles

    def test_get_generation_stats(self, image_generation_service):
        """测试获取生成统计信息"""
        stats = image_generation_service.get_generation_stats()

        assert "supported_styles" in stats
        assert "max_retries" in stats
        assert "default_model" in stats
        assert "storage_service_available" in stats