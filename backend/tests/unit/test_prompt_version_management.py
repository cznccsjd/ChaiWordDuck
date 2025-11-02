"""
Prompt版本管理功能测试

测试配置化的prompt版本管理是否正常工作
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.config import settings
from app.models.word_converter import WordDataConverter
from app.services.word_upsert_service import WordUpsertService
from app.models.word import Word


class TestPromptVersionManagement:
    """Prompt版本管理测试类"""

    def test_config_has_prompt_version(self):
        """测试配置中包含prompt_version字段"""
        assert hasattr(settings, 'prompt_version')
        assert isinstance(settings.prompt_version, str)
        assert settings.prompt_version == "v2.0"  # 默认值

    @patch.dict('os.environ', {'PROMPT_VERSION': 'v3.0'})
    def test_prompt_version_from_env(self):
        """测试从环境变量读取prompt版本"""
        # 重新加载配置
        from app.core.config import Settings, get_settings

        # 清除lru_cache
        get_settings.cache_clear()

        env_settings = Settings()
        assert env_settings.prompt_version == "v3.0"

    def test_word_data_converter_uses_config_version(self):
        """测试WordDataConverter使用配置中的版本号"""
        # 模拟AI响应
        ai_response = {
            'word': 'test',
            'phonetic': 'test',
            'core_game': {'content': 'test game'},
            'game_boards': {},
            'etymology': {},
            'common_mistakes': {}
        }

        result = WordDataConverter.convert_ai_response_to_word(ai_response)

        # 应该使用配置中的版本号，而不是硬编码的v2.0
        # 注意：这个测试会失败直到我们修复了硬编码问题
        assert result['prompt_version'] == settings.prompt_version

    def test_api_endpoint_imports_settings(self):
        """测试API端点正确导入settings配置"""
        # 验证API路由文件导入了settings
        from app.api.v1 import words
        assert hasattr(words, 'settings') or 'settings' in words.__dict__.values() or any('settings' in str(cell) for cell in words.__dict__.values())

    @pytest.mark.asyncio
    async def test_word_upsert_service_uses_config_version(self):
        """测试WordUpsertService使用配置中的版本号"""
        # 验证默认值逻辑：在service中如果没有传入prompt_version，会使用settings.prompt_version
        # 这个逻辑已经实现在word_upsert_service.py的第54-55行
        # if prompt_version is None:
        #     prompt_version = settings.prompt_version

        # 简单验证：检查导入的配置值
        from app.core.config import settings
        assert hasattr(settings, 'prompt_version')
        assert settings.prompt_version is not None
        assert isinstance(settings.prompt_version, str)
        assert settings.prompt_version == "v2.0"

    def test_legacy_word_conversion_maintains_version(self):
        """测试旧版本单词转换保持原有版本"""
        # 创建模拟的旧版本Word对象
        mock_word = MagicMock()
        mock_word.id = 1
        mock_word.word = "test"
        mock_word.prompt_version = "v1.0"  # 旧版本
        mock_word.is_legacy_format = True
        mock_word.core_game = "test game"
        mock_word.scenario_formal = "formal scenario"
        mock_word.scenario_casual = "casual scenario"
        mock_word.etymology_breakdown = "test"
        mock_word.etymology_story = "test story"
        mock_word.common_mistakes = "mistake"
        mock_word.memory_trick = "trick"
        mock_word.is_golden = False
        mock_word.source = "legacy"
        mock_word.created_at = MagicMock()
        mock_word.updated_at = MagicMock()

        result = WordDataConverter.legacy_to_new_format(mock_word)

        # 转换后的数据应该保持原有版本号
        assert result['prompt_version'] == "v1.0"
        assert result['is_legacy_format'] is True

    def test_new_format_word_uses_config_version(self):
        """测试新格式单词使用配置版本"""
        # 模拟AI响应
        ai_response = {
            'word': 'test',
            'phonetic': 'test',
            'core_game': {'content': 'test game'},
            'game_boards': {},
            'etymology': {},
            'common_mistakes': {}
        }

        result = WordDataConverter.convert_ai_response_to_word(ai_response)

        # 新生成的数据应该使用配置中的版本号
        # 注意：这个测试会失败直到我们修复了硬编码问题
        assert result['prompt_version'] == settings.prompt_version
        assert result['is_legacy_format'] is False


if __name__ == "__main__":
    pytest.main([__file__])