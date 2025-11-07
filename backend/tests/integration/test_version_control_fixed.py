#!/usr/bin/env python3
"""
修复版本的版本控制测试

专注于关键功能测试，避免复杂的Mock设置
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from app.main import app
from app.core.config import settings
from app.models.word_converter import WordDataConverter
from app.models.word import Word
from app.schemas.word import WordQueryResponse, WordByIdResponse


class TestVersionControlCore:
    """版本控制核心功能测试"""

    def test_config_has_prompt_version(self):
        """测试配置中包含prompt_version字段"""
        assert hasattr(settings, 'prompt_version')
        assert isinstance(settings.prompt_version, str)
        assert settings.prompt_version == "v2.0"

    def test_word_query_response_schema(self):
        """测试WordQueryResponse schema包含prompt_version字段"""
        response = WordQueryResponse(
            id=1,
            word="test",
            phonetic="/test/",
            part_of_speech="noun",
            translation="测试",
            core_game="核心游戏",
            scenario_formal="思辨场景",
            scenario_casual="生活场景",
            etymology_breakdown="词根拆解",
            etymology_story="词源故事",
            common_mistakes="常见错误",
            memory_trick="记忆技巧",
            is_golden=False,
            prompt_version="v2.0",
            remaining_queries=10,
        )

        assert response.prompt_version == "v2.0"

        # 测试序列化
        serialized = response.model_dump(by_alias=True)
        assert "promptVersion" in serialized
        assert serialized["promptVersion"] == "v2.0"

    def test_word_by_id_response_schema(self):
        """测试WordByIdResponse schema包含prompt_version字段"""
        response = WordByIdResponse(
            id=1,
            word="test",
            phonetic="/test/",
            part_of_speech="noun",
            translation="测试",
            core_game="核心游戏",
            scenario_formal="思辨场景",
            scenario_casual="生活场景",
            etymology_breakdown="词根拆解",
            etymology_story="词源故事",
            common_mistakes="常见错误",
            memory_trick="记忆技巧",
            is_golden=False,
            prompt_version="v2.0",
            created_at=datetime.now(),
        )

        assert response.prompt_version == "v2.0"

        # 测试序列化
        serialized = response.model_dump(by_alias=True)
        assert "promptVersion" in serialized
        assert serialized["promptVersion"] == "v2.0"

    def test_convert_ai_response_uses_config_version(self):
        """测试AI响应转换使用配置中的版本号"""
        ai_response = {
            'word': 'test',
            'phonetic': 'test',
            'core_game': {'content': 'test game'},
            'game_boards': {},
            'etymology': {},
            'common_mistakes': {}
        }

        result = WordDataConverter.convert_ai_response_to_word(ai_response)

        assert result['prompt_version'] == settings.prompt_version
        assert result['prompt_version'] == "v2.0"
        assert result['is_legacy_format'] is False

    def test_language_code_normalization(self):
        """测试语言代码标准化功能"""
        test_cases = [
            ("zh_CN", "zh"),
            ("zh_CN.GB2312", "zh"),
            ("en_US", "en"),
            ("en_GB", "en"),
            ("zh", "zh"),
            ("en", "en"),
            ("fr_FR", "fr"),
            ("de_DE", "de"),
        ]

        for input_code, expected_code in test_cases:
            result = WordDataConverter.normalize_language_code(input_code)
            assert result == expected_code, \
                f"语言代码标准化失败: {input_code} -> {result}, 期望 {expected_code}"

    def test_language_code_normalization_edge_cases(self):
        """测试语言代码标准化的边界情况"""
        # 测试空字符串和None
        assert WordDataConverter.normalize_language_code("") == ""
        assert WordDataConverter.normalize_language_code(None) == ""

        # 测试超长字符串
        long_code = "zh_CN.GB2312.very.long.locale.string"
        normalized = WordDataConverter.normalize_language_code(long_code)
        assert len(normalized) <= 10  # 应该被截断

    def test_word_model_default_version(self):
        """测试Word模型的默认版本设置"""
        from app.models.word import Word

        # 检查模型定义
        word_table = Word.__table__
        prompt_version_column = word_table.c.prompt_version

        assert prompt_version_column.server_default is not None
        assert "v1.0" in str(prompt_version_column.server_default.arg)

    @patch.dict('os.environ', {'PROMPT_VERSION': 'v3.0'})
    def test_environment_variable_override(self):
        """测试环境变量覆盖配置"""
        from importlib import reload
        from app.core.config import get_settings

        # 清除缓存
        get_settings.cache_clear()

        # 重新加载配置
        new_settings = get_settings()
        assert new_settings.prompt_version == "v3.0"

        # 恢复原始设置
        get_settings.cache_clear()


class TestLegacyFormatHandling:
    """旧格式数据处理测试"""

    def test_legacy_format_with_magic_mock(self):
        """测试使用MagicMock模拟旧格式数据处理"""

        # 创建MagicMock对象来模拟旧格式Word
        mock_word = MagicMock()
        mock_word.id = 1
        mock_word.word = "legacy_word"
        mock_word.phonetic = "/test/"
        mock_word.part_of_speech = "noun"
        mock_word.translation = "测试"
        mock_word.is_golden = False
        mock_word.is_legacy_format = True
        mock_word.core_game = "传统游戏内容"
        mock_word.scenario_formal = "正式场景"
        mock_word.scenario_casual = "休闲场景"
        mock_word.etymology_breakdown = "词源分解"
        mock_word.etymology_story = "词源故事"
        mock_word.common_mistakes = "常见错误"
        mock_word.memory_trick = "记忆技巧"
        mock_word.source = "legacy"
        mock_word.created_at = datetime.now()
        mock_word.updated_at = datetime.now()
        mock_word.language_code = "zh"

        # 明确设置prompt_version为None来模拟旧数据
        mock_word.prompt_version = None

        # 测试转换
        result = WordDataConverter.legacy_to_new_format(mock_word)

        # 验证结果
        assert result["prompt_version"] == "v1.0"  # 应该使用默认值
        assert result["is_legacy_format"] is True
        assert result["word"] == "legacy_word"

    def test_legacy_format_with_explicit_version(self):
        """测试有明确版本的旧格式数据"""

        mock_word = MagicMock()
        mock_word.id = 2
        mock_word.word = "legacy_word_v1_5"
        mock_word.phonetic = "/test/"
        mock_word.part_of_speech = "noun"
        mock_word.translation = "测试"
        mock_word.is_golden = False
        mock_word.is_legacy_format = True
        mock_word.core_game = "传统游戏内容"
        mock_word.scenario_formal = "正式场景"
        mock_word.scenario_casual = "休闲场景"
        mock_word.etymology_breakdown = "词源分解"
        mock_word.etymology_story = "词源故事"
        mock_word.common_mistakes = "常见错误"
        mock_word.memory_trick = "记忆技巧"
        mock_word.source = "legacy"
        mock_word.created_at = datetime.now()
        mock_word.updated_at = datetime.now()
        mock_word.language_code = "zh"

        # 明确设置版本
        mock_word.prompt_version = "v1.5"

        # 测试转换
        result = WordDataConverter.legacy_to_new_format(mock_word)

        # 验证版本保持不变
        assert result["prompt_version"] == "v1.5"
        assert result["is_legacy_format"] is True


class TestNewFormatHandling:
    """新格式数据处理测试"""

    def test_new_format_display(self):
        """测试新格式数据的显示处理"""

        mock_word = MagicMock()
        mock_word.id = 3
        mock_word.word = "new_word"
        mock_word.phonetic = "/test/"
        mock_word.part_of_speech = "noun"
        mock_word.translation = "测试"
        mock_word.is_golden = False
        mock_word.is_legacy_format = False
        mock_word.prompt_version = "v2.0"
        mock_word.language_code = "zh"
        mock_word.core_game_new = {"content": "结构化游戏内容"}
        mock_word.game_boards = {
            "board_a_speculative": {"example": "思辨场景"},
            "board_b_life": {"example": "生活场景"}
        }
        mock_word.etymology_new = {
            "breakdown": {"root": {"part": "词根分析"}},
            "story": "词源故事"
        }
        mock_word.common_mistakes_new = {"warning": "警告信息"}
        mock_word.memory_trick = "记忆技巧"
        mock_word.source = "ai"
        mock_word.created_at = datetime.now()
        mock_word.updated_at = datetime.now()

        # 测试显示格式转换
        result = WordDataConverter.get_word_display_format(mock_word, 'auto')

        # 验证结果
        assert result["prompt_version"] == "v2.0"
        assert result["is_legacy_format"] is False
        assert "language_code" in result
        assert result["language_code"] == "zh"

    def test_new_format_without_language_code(self):
        """测试没有语言代码的新格式数据处理"""

        mock_word = MagicMock()
        mock_word.id = 4
        mock_word.word = "new_word_no_lang"
        mock_word.phonetic = "/test/"
        mock_word.part_of_speech = "noun"
        mock_word.translation = "测试"
        mock_word.is_golden = False
        mock_word.is_legacy_format = False
        mock_word.prompt_version = "v2.0"
        mock_word.core_game_new = {"content": "结构化游戏内容"}
        mock_word.game_boards = {}
        mock_word.etymology_new = {}
        mock_word.common_mistakes_new = {}
        mock_word.memory_trick = "记忆技巧"
        mock_word.source = "ai"
        mock_word.created_at = datetime.now()
        mock_word.updated_at = datetime.now()

        # 配置language_code属性访问返回默认值
        mock_word.language_code = None

        # 测试显示格式转换
        result = WordDataConverter.get_word_display_format(mock_word, 'auto')

        # 验证语言代码使用默认值
        assert "language_code" in result
        # normalize_language_code会处理None值
        assert result["language_code"] == ""  # None经过normalize_language_code处理后的结果


class TestVersionCompatibility:
    """版本兼容性测试"""

    def test_version_fallback_comprehensive(self):
        """测试版本回退机制"""

        test_cases = [
            {
                "name": "None版本",
                "prompt_version": None,
                "expected": "v1.0"
            },
            {
                "name": "空字符串版本",
                "prompt_version": "",
                "expected": "v1.0"
            },
            {
                "name": "v1.0版本",
                "prompt_version": "v1.0",
                "expected": "v1.0"
            },
            {
                "name": "v2.0版本",
                "prompt_version": "v2.0",
                "expected": "v2.0"
            }
        ]

        for case in test_cases:
            mock_word = MagicMock()
            mock_word.id = 1
            mock_word.word = "test"
            mock_word.is_legacy_format = True
            mock_word.core_game = "test content"
            mock_word.prompt_version = case["prompt_version"]
            mock_word.created_at = datetime.now()
            mock_word.updated_at = datetime.now()
            mock_word.language_code = "en"

            # 测试转换
            result = WordDataConverter.legacy_to_new_format(mock_word)

            # 验证版本回退逻辑
            actual_version = result.get("prompt_version")
            expected_version = case["expected"]

            assert actual_version == expected_version, \
                f"版本回退测试失败 {case['name']}: 期望 {expected_version}, 实际 {actual_version}"


class TestLanguageCodeConstraints:
    """语言代码约束测试"""

    def test_language_code_length_constraint(self):
        """测试语言代码长度约束"""

        # 测试各种语言代码格式
        test_codes = [
            "zh",           # 2字符
            "en",           # 2字符
            "zh_CN",        # 5字符
            "en_US",        # 5字符
            "zh_CN.GB2312", # 12字符，应该被截断
        ]

        for code in test_codes:
            normalized = WordDataConverter.normalize_language_code(code)
            # 验证标准化后的代码长度合理
            assert len(normalized) <= 10, f"语言代码过长: {code} -> {normalized}"
            # 验证只包含有效字符
            assert normalized.replace('_', '').replace('-', '').isalpha() or normalized == "", \
                f"语言代码包含无效字符: {code} -> {normalized}"

    def test_database_compatibility(self):
        """测试数据库兼容性"""

        # 测试数据库字段长度限制
        max_length = 10
        test_codes = ["zh", "en", "fr", "de", "ja", "ko", "zh_CN", "en_US"]

        for code in test_codes:
            normalized = WordDataConverter.normalize_language_code(code)
            assert len(normalized) <= max_length, \
                f"语言代码超出数据库字段长度限制: {code} -> {normalized}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])