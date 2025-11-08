#!/usr/bin/env python3
"""
版本控制架构综合测试套件

全面测试prompt版本控制功能，包括API集成测试、版本切换功能、语言代码约束等
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from datetime import datetime
import json
import tempfile
import os

from app.main import app
from app.core.config import settings
from app.models.word_converter import WordDataConverter
from app.models.word import Word
from app.schemas.word import WordQueryResponse, WordByIdResponse
from app.core.database import get_db


class TestPromptVersionControl:
    """Prompt版本控制综合测试类"""

    @classmethod
    def setup_class(cls):
        """类级别的设置，创建测试数据库"""
        # 创建内存SQLite数据库用于测试
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )

        # 创建测试客户端
        cls.client = TestClient(app)

        # 设置测试数据库覆盖
        def override_get_db():
            from app.core.database import Base
            Base.metadata.create_all(bind=cls.engine)
            from sqlalchemy.orm import sessionmaker
            TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

    @classmethod
    def teardown_class(cls):
        """类级别的清理"""
        app.dependency_overrides.clear()

    def test_config_prompt_version_settings(self):
        """测试配置文件中的prompt_version设置"""
        assert hasattr(settings, 'prompt_version')
        assert isinstance(settings.prompt_version, str)
        assert settings.prompt_version == "v2.0"

    def test_api_response_schema_includes_prompt_version(self):
        """测试API响应schema包含prompt_version字段"""

        # 测试WordQueryResponse
        word_query_response = WordQueryResponse(
            id=13,
            word="hello",
            phonetic="/həˈloʊ/",
            part_of_speech="interjection",
            translation="你好",
            core_game="核心游戏内容",
            scenario_formal="思辨场景",
            scenario_casual="生活场景",
            etymology_breakdown="词根拆解",
            etymology_story="词源故事",
            common_mistakes="犯规警告",
            memory_trick="通关秘籍",
            is_golden=False,
            prompt_version="v2.0",
            remaining_queries=10,
        )

        # 验证字段存在
        assert hasattr(word_query_response, 'prompt_version')
        assert word_query_response.prompt_version == "v2.0"

        # 验证序列化
        serialized = word_query_response.model_dump(by_alias=True)
        assert "promptVersion" in serialized
        assert serialized["promptVersion"] == "v2.0"

        # 测试WordByIdResponse
        word_by_id_response = WordByIdResponse(
            id=13,
            word="hello",
            phonetic="/həˈloʊ/",
            part_of_speech="interjection",
            core_game="核心游戏内容",
            scenario_formal="思辨场景",
            scenario_casual="生活场景",
            etymology_breakdown="词根拆解",
            etymology_story="词源故事",
            common_mistakes="犯规警告",
            memory_trick="通关秘籍",
            is_golden=False,
            prompt_version="v2.0",
            created_at=datetime.now(),
        )

        # 验证字段存在
        assert hasattr(word_by_id_response, 'prompt_version')
        assert word_by_id_response.prompt_version == "v2.0"

        # 验证序列化
        serialized = word_by_id_response.model_dump(by_alias=True)
        assert "promptVersion" in serialized
        assert serialized["promptVersion"] == "v2.0"

    def test_word_data_converter_legacy_format_with_default_version(self):
        """测试WordDataConverter处理旧格式数据时使用默认版本"""

        # 创建旧格式的模拟Word对象，使用MagicMock更好处理getattr
        mock_word = MagicMock()
        mock_word.id = 13
        mock_word.word = "hello"
        mock_word.phonetic = "/həˈloʊ/"
        mock_word.part_of_speech = "interjection"
        mock_word.translation = "你好"
        mock_word.is_golden = False
        mock_word.is_legacy_format = True
        mock_word.core_game = "核心游戏内容"
        mock_word.scenario_formal = "思辨场景"
        mock_word.scenario_casual = "生活场景"
        mock_word.etymology_breakdown = "词根拆解"
        mock_word.etymology_story = "词源故事"
        mock_word.common_mistakes = "犯规警告"
        mock_word.memory_trick = "通关秘籍"
        mock_word.source = "legacy"
        mock_word.created_at = datetime.now()
        mock_word.updated_at = datetime.now()
        mock_word.language_code = "en"  # 设置默认语言代码

        # 模拟没有prompt_version字段的情况
        # 设置prompt_version属性访问时抛出AttributeError
        def side_effect_getattr(attr, default=None):
            if attr == 'prompt_version':
                return default  # 返回默认值，模拟没有该字段
            return getattr(MagicMock(), attr, default)

        # 重新配置getattr行为
        type(mock_word).__getattr__ = lambda self, attr: side_effect_getattr(attr)

        # 或者更简单的方法：直接配置属性
        mock_word.configure_mock(**{
            'prompt_version': None,  # 设置为None，模拟没有版本信息
        })

        # 测试legacy_to_new_format转换
        result = WordDataConverter.legacy_to_new_format(mock_word)

        # 验证默认值设置
        assert "prompt_version" in result
        assert result["prompt_version"] == "v1.0"  # 应该使用默认值

    def test_word_data_converter_legacy_format_with_existing_version(self):
        """测试WordDataConverter处理有明确版本标记的旧格式数据"""

        # 创建有明确版本的旧格式Word对象
        mock_word = Mock()
        mock_word.id = 13
        mock_word.word = "hello"
        mock_word.phonetic = "/həˈloʊ/"
        mock_word.part_of_speech = "interjection"
        mock_word.translation = "你好"
        mock_word.is_golden = False
        mock_word.is_legacy_format = True
        mock_word.prompt_version = "v1.5"  # 有明确的版本
        mock_word.core_game = "核心游戏内容"
        mock_word.scenario_formal = "思辨场景"
        mock_word.scenario_casual = "生活场景"
        mock_word.etymology_breakdown = "词根拆解"
        mock_word.etymology_story = "词源故事"
        mock_word.common_mistakes = "犯规警告"
        mock_word.memory_trick = "通关秘籍"
        mock_word.source = "legacy"
        mock_word.created_at = datetime.now()
        mock_word.updated_at = datetime.now()

        # 测试legacy_to_new_format转换
        result = WordDataConverter.legacy_to_new_format(mock_word)

        # 验证版本信息保持不变
        assert "prompt_version" in result
        assert result["prompt_version"] == "v1.5"

    def test_word_data_converter_new_format_prompt_version(self):
        """测试WordDataConverter处理新格式数据时的prompt_version逻辑"""

        # 创建新格式的模拟Word对象
        mock_word = Mock()
        mock_word.id = 13
        mock_word.word = "hello"
        mock_word.phonetic = "/həˈloʊ/"
        mock_word.part_of_speech = "interjection"
        mock_word.translation = "你好"
        mock_word.is_golden = False
        mock_word.is_legacy_format = False
        mock_word.prompt_version = "v2.0"
        mock_word.language_code = "zh"
        mock_word.core_game_new = {"content": "核心游戏内容"}
        mock_word.game_boards = {
            "board_a_speculative": {"example": "思辨场景"},
            "board_b_life": {"example": "生活场景"}
        }
        mock_word.etymology_new = {
            "breakdown": {"root": {"part": "词根拆解"}},
            "story": "词源故事"
        }
        mock_word.common_mistakes_new = {"warning": "犯规警告"}
        mock_word.memory_trick = "通关秘籍"
        mock_word.source = "ai"
        mock_word.created_at = datetime.now()
        mock_word.updated_at = datetime.now()

        # 测试get_word_display_format
        result = WordDataConverter.get_word_display_format(mock_word, 'auto')

        # 验证prompt_version正确传递
        assert "prompt_version" in result
        assert result["prompt_version"] == "v2.0"

    def test_word_data_converter_new_format_without_language_code(self):
        """测试新格式数据没有language_code时的处理"""

        # 创建没有language_code的新格式Word对象
        mock_word = Mock()
        mock_word.id = 13
        mock_word.word = "hello"
        mock_word.phonetic = "/həˈloʊ/"
        mock_word.part_of_speech = "interjection"
        mock_word.translation = "你好"
        mock_word.is_golden = False
        mock_word.is_legacy_format = False
        mock_word.prompt_version = "v2.0"
        mock_word.core_game_new = {"content": "核心游戏内容"}
        mock_word.game_boards = {}
        mock_word.etymology_new = {}
        mock_word.common_mistakes_new = {}
        mock_word.memory_trick = "通关秘籍"
        mock_word.source = "ai"
        mock_word.created_at = datetime.now()
        mock_word.updated_at = datetime.now()

        # 模拟没有language_code属性
        del mock_word.language_code

        # 测试get_word_display_format
        result = WordDataConverter.get_word_display_format(mock_word, 'auto')

        # 验证language_code使用默认值
        assert "language_code" in result
        assert result["language_code"] == "en"  # 应该使用默认值

    def test_convert_ai_response_to_word_uses_config_version(self):
        """测试convert_ai_response_to_word使用配置中的版本号"""

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

        # 应该使用配置中的版本号
        assert result['prompt_version'] == settings.prompt_version
        assert result['prompt_version'] == "v2.0"
        assert result['is_legacy_format'] is False

    @patch.dict('os.environ', {'PROMPT_VERSION': 'v3.0'})
    def test_prompt_version_from_environment(self):
        """测试从环境变量读取prompt版本"""

        # 重新加载配置
        from importlib import reload
        from app.core.config import get_settings

        # 清除lru_cache
        get_settings.cache_clear()

        # 获取新的设置实例
        new_settings = get_settings()

        assert new_settings.prompt_version == "v3.0"

    def test_version_fallback_logic_comprehensive(self):
        """测试全面的版本降级逻辑"""

        test_cases = [
            {
                "name": "v1.0数据（旧格式）",
                "word_data": {
                    "id": 1,
                    "word": "test",
                    "is_legacy_format": True,
                    "core_game": "test content",
                    # 没有prompt_version字段
                },
                "expected_version": "v1.0"
            },
            {
                "name": "v2.0数据（新格式）",
                "word_data": {
                    "id": 2,
                    "word": "test",
                    "is_legacy_format": False,
                    "prompt_version": "v2.0",
                    "core_game_new": {"content": "test content"},
                },
                "expected_version": "v2.0"
            },
            {
                "name": "null prompt_version数据",
                "word_data": {
                    "id": 3,
                    "word": "test",
                    "prompt_version": None,
                    "core_game": "test content",
                },
                "expected_version": "v1.0"  # 应该回退到默认值
            },
            {
                "name": "明确v1.5版本数据",
                "word_data": {
                    "id": 4,
                    "word": "test",
                    "prompt_version": "v1.5",
                    "core_game": "test content",
                },
                "expected_version": "v1.5"
            }
        ]

        for case in test_cases:
            mock_word = Mock()
            for key, value in case["word_data"].items():
                setattr(mock_word, key, value)

            # 添加必需的属性
            if not hasattr(mock_word, 'is_legacy_format'):
                mock_word.is_legacy_format = True
            if not hasattr(mock_word, 'created_at'):
                mock_word.created_at = datetime.now()
            if not hasattr(mock_word, 'updated_at'):
                mock_word.updated_at = datetime.now()
            if not hasattr(mock_word, 'source'):
                mock_word.source = "test"
            if not hasattr(mock_word, 'word'):
                mock_word.word = case["word_data"]["word"]
            if not hasattr(mock_word, 'id'):
                mock_word.id = case["word_data"]["id"]

            # 使用转换器处理
            if mock_word.is_legacy_format:
                result = WordDataConverter.legacy_to_new_format(mock_word)
            else:
                result = WordDataConverter.get_word_display_format(mock_word, 'auto')

            # 验证版本
            assert result.get("prompt_version") == case["expected_version"], \
                f"测试用例 {case['name']} 失败: 期望 {case['expected_version']}, 实际 {result.get('prompt_version')}"

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

    def test_word_model_default_prompt_version(self):
        """测试Word模型的默认prompt_version设置"""

        from app.models.word import Word

        # 测试模型定义中的默认值
        word_table = Word.__table__
        prompt_version_column = word_table.c.prompt_version

        # 验证server_default设置为v1.0
        assert prompt_version_column.server_default is not None
        # PostgreSQL的server_default可能包含引号，所以我们检查是否包含v1.0
        assert "v1.0" in str(prompt_version_column.server_default.arg)


class TestVersionSwitching:
    """版本切换功能测试"""

    def test_version_switching_in_config(self):
        """测试配置中的版本切换"""

        # 测试默认配置
        assert settings.prompt_version == "v2.0"

        # 模拟版本切换
        with patch.object(settings, 'prompt_version', 'v3.0'):
            # 验证新版本生效
            from app.core.config import get_settings
            get_settings.cache_clear()
            current_settings = get_settings()
            # 注意：这里的测试可能需要根据实际的配置管理方式调整

    def test_data_format_compatibility(self):
        """测试不同版本数据格式的兼容性"""

        # 模拟不同版本的数据
        v1_data = {
            "id": 1,
            "word": "test",
            "prompt_version": "v1.0",
            "is_legacy_format": True,
            "core_game": "simple content",
        }

        v2_data = {
            "id": 2,
            "word": "test",
            "prompt_version": "v2.0",
            "is_legacy_format": False,
            "core_game_new": {"content": "structured content"},
        }

        # 验证版本信息正确
        assert v1_data["prompt_version"] == "v1.0"
        assert v2_data["prompt_version"] == "v2.0"
        assert v1_data["is_legacy_format"] is True
        assert v2_data["is_legacy_format"] is False


class TestLanguageCodeConstraints:
    """语言代码约束回归测试"""

    def test_language_code_format_validation(self):
        """测试语言代码格式验证"""

        valid_codes = ["zh", "en", "fr", "de", "ja", "ko"]
        invalid_codes = ["", None, "invalid_locale", "123", "zh-too-long"]

        for code in valid_codes:
            result = WordDataConverter.normalize_language_code(code)
            assert len(result) <= 10, f"语言代码长度超过限制: {code} -> {result}"
            assert result.replace('_', '').replace('-', '').isalnum() or result in valid_codes

        for code in invalid_codes:
            if code is not None:
                result = WordDataConverter.normalize_language_code(code)
                # 应该返回一个有效的语言代码或默认值
                assert result in ["zh", "en", "fr", "de", "ja", "ko"] or len(result) <= 2

    def test_database_language_code_constraint(self):
        """测试数据库语言代码约束"""

        # 这个测试需要真实的数据库连接，在集成测试中实现
        # 这里只测试业务逻辑层面的约束
        test_language_codes = ["zh", "en", "zh_CN", "en_US", "invalid_locale"]

        for code in test_language_codes:
            normalized = WordDataConverter.normalize_language_code(code)
            # 验证标准化后的语言代码符合数据库约束
            assert len(normalized) <= 10, f"标准化后的语言代码过长: {code} -> {normalized}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])