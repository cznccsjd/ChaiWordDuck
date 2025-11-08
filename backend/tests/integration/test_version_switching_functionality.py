#!/usr/bin/env python3
"""
版本切换功能测试

测试prompt版本在不同场景下的切换和处理
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

from app.main import app
from app.core.config import settings, get_settings
from app.models.word import Word
from app.models.word_converter import WordDataConverter
from app.core.database import get_db, Base


class TestVersionSwitching:
    """版本切换功能测试"""

    @classmethod
    def setup_class(cls):
        """设置测试环境"""
        # 创建测试数据库
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )

        # 创建所有表
        Base.metadata.create_all(bind=cls.engine)

        # 创建测试会话
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        cls.db = TestingSessionLocal()

        # 创建测试客户端
        cls.client = TestClient(app)

        # 覆盖数据库依赖
        def override_get_db():
            try:
                yield cls.db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db

        # 设置测试数据
        cls._setup_test_data()

    @classmethod
    def teardown_class(cls):
        """清理测试环境"""
        cls.db.close()
        app.dependency_overrides.clear()

    @classmethod
    def _setup_test_data(cls):
        """设置不同版本的测试数据"""
        # v1.0格式的单词
        v1_word = Word(
            id=1,
            word="v1_legacy",
            phonetic="/v1/",
            part_of_speech="noun",
            translation="版本1传统",
            is_golden=False,
            is_legacy_format=True,
            prompt_version="v1.0",
            core_game="v1传统游戏",
            scenario_formal="v1正式场景",
            scenario_casual="v1休闲场景",
            etymology_breakdown="v1词源分解",
            etymology_story="v1词源故事",
            common_mistakes="v1常见错误",
            memory_trick="v1记忆技巧",
            source="legacy",
            language_code="zh",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        cls.db.add(v1_word)

        # v2.0格式的单词
        v2_word = Word(
            id=2,
            word="v2_new",
            phonetic="/v2/",
            part_of_speech="noun",
            translation="版本2新格式",
            is_golden=False,
            is_legacy_format=False,
            prompt_version="v2.0",
            core_game_new={"content": "v2结构化游戏", "version": "2.0"},
            game_boards={
                "board_a_speculative": {"example": "v2思辨场景", "version": "2.0"},
                "board_b_life": {"example": "v2生活场景", "version": "2.0"}
            },
            etymology_new={
                "breakdown": {"root": {"part": "v2词根分析", "version": "2.0"}},
                "story": "v2词源故事",
                "version_info": {"prompt_version": "2.0"}
            },
            common_mistakes_new={"warning": "v2警告信息", "version": "2.0"},
            memory_trick="v2记忆技巧",
            source="ai",
            language_code="en",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        cls.db.add(v2_word)

        # 无版本的单词
        no_version_word = Word(
            id=3,
            word="no_version",
            phonetic="/no/",
            part_of_speech="noun",
            translation="无版本",
            is_golden=False,
            is_legacy_format=True,
            prompt_version=None,
            core_game="游戏内容",
            scenario_formal="场景",
            scenario_casual="场景",
            etymology_breakdown="分解",
            etymology_story="故事",
            common_mistakes="错误",
            memory_trick="技巧",
            source="test",
            language_code="en",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        cls.db.add(no_version_word)

        cls.db.commit()

    def test_current_default_version(self):
        """测试当前默认版本"""
        assert settings.prompt_version == "v2.0"

    def test_version_configuration_switching_via_env(self):
        """测试通过环境变量切换版本"""
        # 保存原始环境变量
        original_prompt_version = os.environ.get('PROMPT_VERSION')

        try:
            # 设置新的环境变量
            os.environ['PROMPT_VERSION'] = 'v3.0'

            # 清除缓存并重新加载配置
            get_settings.cache_clear()
            new_settings = get_settings()

            # 验证版本已切换
            assert new_settings.prompt_version == "v3.0"

            # 测试AI响应转换使用新版本
            ai_response = {
                'word': 'test_v3',
                'phonetic': '/test/',
                'core_game': {'content': 'v3游戏内容'},
                'game_boards': {},
                'etymology': {},
                'common_mistakes': {}
            }

            with patch('app.models.word_converter.settings', new_settings):
                result = WordDataConverter.convert_ai_response_to_word(ai_response)
                assert result['prompt_version'] == "v3.0"

        finally:
            # 恢复原始环境变量
            if original_prompt_version:
                os.environ['PROMPT_VERSION'] = original_prompt_version
            elif 'PROMPT_VERSION' in os.environ:
                del os.environ['PROMPT_VERSION']

            # 清除缓存
            get_settings.cache_clear()

    def test_data_format_compatibility_across_versions(self):
        """测试不同版本数据格式的兼容性"""

        # 测试v1.0数据
        v1_result = WordDataConverter.legacy_to_new_format(
            self.db.query(Word).filter(Word.id == 1).first()
        )
        assert v1_result["prompt_version"] == "v1.0"
        assert v1_result["is_legacy_format"] is True

        # 测试v2.0数据
        v2_word = self.db.query(Word).filter(Word.id == 2).first()
        v2_result = WordDataConverter.get_word_display_format(v2_word, 'auto')
        assert v2_result["prompt_version"] == "v2.0"
        assert v2_result["is_legacy_format"] is False

        # 测试无版本数据
        no_version_result = WordDataConverter.legacy_to_new_format(
            self.db.query(Word).filter(Word.id == 3).first()
        )
        # 应该有默认版本
        assert no_version_result["prompt_version"] is not None
        assert no_version_result["prompt_version"] == "v1.0"  # 默认值

    @patch('app.models.word_converter.settings')
    def test_dynamic_version_switching_in_converter(self, mock_settings):
        """测试转换器中的动态版本切换"""
        # 测试v1.0配置
        mock_settings.prompt_version = "v1.0"

        ai_response = {
            'word': 'dynamic_test',
            'phonetic': '/test/',
            'core_game': {'content': '动态测试内容'},
            'game_boards': {},
            'etymology': {},
            'common_mistakes': {}
        }

        result_v1 = WordDataConverter.convert_ai_response_to_word(ai_response)
        assert result_v1['prompt_version'] == "v1.0"

        # 切换到v2.0配置
        mock_settings.prompt_version = "v2.0"

        result_v2 = WordDataConverter.convert_ai_response_to_word(ai_response)
        assert result_v2['prompt_version'] == "v2.0"

        # 验证其他字段不受版本切换影响
        assert result_v1['word'] == result_v2['word'] == 'dynamic_test'
        assert result_v1['is_legacy_format'] == result_v2['is_legacy_format'] is False

    def test_version_metadata_in_ai_responses(self):
        """测试AI响应中的版本元数据"""

        # 模拟包含版本信息的AI响应
        ai_response_with_version = {
            'word': 'versioned_word',
            'phonetic': '/test/',
            'core_game': {'content': '版本化游戏内容', 'prompt_version': 'v2.0'},
            'game_boards': {'version_info': {'prompt_version': 'v2.0'}},
            'etymology': {'version_metadata': {'generation_prompt': 'v2.0'}},
            'common_mistakes': {'version_tag': 'v2.0'},
            'version_info': {'explicit_version': 'v2.0'}
        }

        result = WordDataConverter.convert_ai_response_to_word(ai_response_with_version)
        assert result['prompt_version'] == settings.prompt_version  # 应该使用配置版本，不是AI响应中的版本

    def test_version_consistency_in_display_formats(self):
        """测试显示格式中的版本一致性"""

        # 测试不同格式下的版本信息一致性
        v2_word = self.db.query(Word).filter(Word.id == 2).first()

        # 测试auto格式
        auto_result = WordDataConverter.get_word_display_format(v2_word, 'auto')
        assert auto_result["prompt_version"] == "v2.0"

        # 测试legacy格式
        legacy_result = WordDataConverter.get_word_display_format(v2_word, 'legacy')
        assert legacy_result["prompt_version"] == "v2.0"

        # 测试new格式
        new_result = WordDataConverter.get_word_display_format(v2_word, 'new')
        assert new_result["prompt_version"] == "v2.0"

        # 验证所有格式返回相同的版本信息
        version_values = [auto_result["prompt_version"], legacy_result["prompt_version"], new_result["prompt_version"]]
        assert all(v == "v2.0" for v in version_values), "不同格式的版本信息不一致"

    def test_version_rollback_scenario(self):
        """测试版本回滚场景"""

        # 模拟从v2.0回滚到v1.0的场景
        with patch('app.models.word_converter.settings') as mock_settings:
            mock_settings.prompt_version = "v1.0"

            # 在v1.0配置下创建新数据
            ai_response = {
                'word': 'rollback_test',
                'phonetic': '/test/',
                'core_game': {'content': '回滚测试内容'},
                'game_boards': {},
                'etymology': {},
                'common_mistakes': {}
            }

            rollback_result = WordDataConverter.convert_ai_response_to_word(ai_response)
            assert rollback_result['prompt_version'] == "v1.0"

            # 恢复到v2.0
            mock_settings.prompt_version = "v2.0"

            current_result = WordDataConverter.convert_ai_response_to_word(ai_response)
            assert current_result['prompt_version'] == "v2.0"

            # 验证历史数据（v1.0）仍然可以正确处理
            v1_word = self.db.query(Word).filter(Word.id == 1).first()
            v1_display = WordDataConverter.get_word_display_format(v1_word, 'auto')
            assert v1_display["prompt_version"] == "v1.0"

    def test_version_upgrade_scenario(self):
        """测试版本升级场景"""

        # 模拟从v2.0升级到v3.0的场景
        with patch('app.models.word_converter.settings') as mock_settings:
            # 当前版本是v2.0
            mock_settings.prompt_version = "v2.0"

            v2_response = {
                'word': 'upgrade_test',
                'phonetic': '/test/',
                'core_game': {'content': 'v2升级内容', 'features': ['v2特性']},
                'game_boards': {},
                'etymology': {},
                'common_mistakes': {}
            }

            v2_result = WordDataConverter.convert_ai_response_to_word(v2_response)
            assert v2_result['prompt_version'] == "v2.0"

            # 升级到v3.0
            mock_settings.prompt_version = "v3.0"

            v3_response = {
                'word': 'upgrade_test',
                'phonetic': '/test/',
                'core_game': {'content': 'v3升级内容', 'features': ['v2特性', 'v3新特性']},
                'game_boards': {},
                'etymology': {},
                'common_mistakes': {}
            }

            v3_result = WordDataConverter.convert_ai_response_to_word(v3_response)
            assert v3_result['prompt_version'] == "v3.0"

    def test_version_mixed_data_handling(self):
        """测试混合版本数据处理"""

        # 模拟数据库中存在多个版本的数据
        mixed_versions = ["v1.0", "v1.5", "v2.0", None]

        for i, version in enumerate(mixed_versions):
            word = Word(
                id=100 + i,
                word=f"mixed_{i}",
                phonetic=f"/mixed{i}/",
                part_of_speech="noun",
                translation=f"混合测试{i}",
                is_golden=False,
                is_legacy_format=version in ["v1.0", "v1.5"],
                prompt_version=version,
                core_game="混合游戏内容" if version in ["v1.0", "v1.5"] else None,
                core_game_new={"content": "混合游戏内容"} if version == "v2.0" else None,
                scenario_formal="场景" if version in ["v1.0", "v1.5"] else None,
                scenario_casual="场景" if version in ["v1.0", "v1.5"] else None,
                etymology_breakdown="分解" if version in ["v1.0", "v1.5"] else None,
                etymology_story="故事" if version in ["v1.0", "v1.5"] else None,
                common_mistakes="错误" if version in ["v1.0", "v1.5"] else None,
                memory_trick="技巧",
                source="mixed_test",
                language_code="zh",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            self.db.add(word)
        self.db.commit()

        # 验证所有混合数据都能正确处理
        for i, version in enumerate(mixed_versions):
            word = self.db.query(Word).filter(Word.id == 100 + i).first()

            if word.is_legacy_format:
                result = WordDataConverter.legacy_to_new_format(word)
            else:
                result = WordDataConverter.get_word_display_format(word, 'auto')

            # 验证版本信息
            if version is None:
                assert result["prompt_version"] == "v1.0"  # 默认值
            else:
                assert result["prompt_version"] == version

            # 验证数据完整性
            assert "word" in result
            assert "is_legacy_format" in result

    def test_version_configuration_validation(self):
        """测试版本配置验证"""

        # 测试有效的版本格式
        valid_versions = ["v1.0", "v2.0", "v3.0", "v10.5", "v1.0.1"]

        for version in valid_versions:
            with patch('app.models.word_converter.settings') as mock_settings:
                mock_settings.prompt_version = version

                ai_response = {
                    'word': 'validation_test',
                    'phonetic': '/test/',
                    'core_game': {'content': '验证测试'},
                    'game_boards': {},
                    'etymology': {},
                    'common_mistakes': {}
                }

                result = WordDataConverter.convert_ai_response_to_word(ai_response)
                assert result['prompt_version'] == version

        # 测试无效的版本格式（应该被接受，因为系统对格式要求宽松）
        invalid_versions = ["", "invalid", None, "123"]

        for version in invalid_versions:
            with patch('app.models.word_converter.settings') as mock_settings:
                mock_settings.prompt_version = version

                try:
                    ai_response = {
                        'word': 'invalid_version_test',
                        'phonetic': '/test/',
                        'core_game': {'content': '无效版本测试'},
                        'game_boards': {},
                        'etymology': {},
                        'common_mistakes': {}
                    }

                    result = WordDataConverter.convert_ai_response_to_word(ai_response)
                    # 即使版本格式无效，也应该有某种处理
                    assert 'prompt_version' in result
                except Exception as e:
                    # 如果抛出异常，应该是预期的异常
                    assert isinstance(e, (ValueError, TypeError))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])