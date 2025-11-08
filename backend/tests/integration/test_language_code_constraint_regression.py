#!/usr/bin/env python3
"""
语言代码约束回归测试

确保语言代码相关的修复不会导致回归问题
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.models.word import Word
from app.models.word_converter import WordDataConverter
from app.core.database import Base


class TestLanguageCodeConstraintRegression:
    """语言代码约束回归测试"""

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

    @classmethod
    def teardown_class(cls):
        """清理测试环境"""
        cls.db.close()

    def test_language_code_normalization_comprehensive(self):
        """测试语言代码标准化的全面场景"""

        test_cases = [
            # (输入, 期望输出, 描述)
            ("zh", "zh", "2字符中文代码"),
            ("en", "en", "2字符英文代码"),
            ("fr", "en", "2字符非法代码，默认英文"),
            ("de", "en", "2字符非法代码，默认英文"),
            ("ja", "en", "2字符非法代码，默认英文"),
            ("ko", "en", "2字符非法代码，默认英文"),

            ("zh_CN", "zh", "5字符中文代码（下划线）"),
            ("zh-TW", "zh", "5字符中文代码（连字符）"),
            ("zh-tw", "zh", "5字符中文代码（小写）"),
            ("en_US", "en", "5字符英文代码（下划线）"),
            ("en-GB", "en", "5字符英文代码（连字符）"),
            ("en-gb", "en", "5字符英文代码（小写）"),

            ("zh_CN.GB2312", "zh", "长中文代码"),
            ("en_US.UTF-8", "en", "长英文代码"),
            ("", "en", "空字符串，默认英文"),
            (None, "en", "None值，默认英文"),

            # 边界情况
            ("ZH", "zh", "大写代码"),
            ("EN", "en", "大写英文代码"),
            ("Zh_Cn", "zh", "混合大小写"),
            ("En_Us", "en", "混合大小写英文"),
        ]

        for input_code, expected_code, description in test_cases:
            result = WordDataConverter.normalize_language_code(input_code)
            assert result == expected_code, \
                f"语言代码标准化失败 {description}: {input_code} -> {result}, 期望 {expected_code}"

    def test_language_code_length_constraints(self):
        """测试语言代码长度约束"""

        # 测试各种长度的语言代码
        test_cases = [
            "zh",                    # 2字符
            "en",                    # 2字符
            "zh_CN",                 # 5字符
            "en_US",                 # 5字符
            "zh_CN.GB2312",          # 12字符
            "en_US.UTF-8.LATIN-1",   # 19字符
            "x" * 50,               # 50字符
        ]

        for code in test_cases:
            normalized = WordDataConverter.normalize_language_code(code)

            # 验证标准化后的代码长度合理（最多10字符）
            assert len(normalized) <= 10, \
                f"标准化后的语言代码过长: {code} ({len(code)}) -> {normalized} ({len(normalized)})"

            # 验证只包含有效字符
            valid_chars = set('abcdefghijklmnopqrstuvwxyz_-')
            normalized_chars = set(normalized.lower())
            assert normalized_chars.issubset(valid_chars) or normalized == "", \
                f"语言代码包含无效字符: {code} -> {normalized}"

    def test_database_language_code_field_constraints(self):
        """测试数据库语言代码字段约束"""

        # 测试各种语言代码是否可以保存到数据库
        test_language_codes = [
            "zh",
            "en",
            "fr",
            "de",
            "ja",
            "ko",
            "zh_CN",  # 会被标准化为 "zh"
            "en_US",  # 会被标准化为 "en"
        ]

        for i, lang_code in enumerate(test_language_codes):
            # 标准化语言代码
            normalized_code = WordDataConverter.normalize_language_code(lang_code)

            # 创建测试单词
            word = Word(
                id=i + 100,  # 避免ID冲突
                word=f"test_word_{i}",
                phonetic=f"/test{i}/",
                part_of_speech="noun",
                translation=f"测试单词{i}",
                is_golden=False,
                is_legacy_format=True,
                core_game=f"游戏内容{i}",
                scenario_formal="正式场景",
                scenario_casual="休闲场景",
                etymology_breakdown="词源分解",
                etymology_story="词源故事",
                common_mistakes="常见错误",
                memory_trick="记忆技巧",
                source="test",
                language_code=normalized_code,  # 使用标准化后的代码
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # 保存到数据库
            self.db.add(word)
            self.db.commit()

            # 验证保存成功
            assert word.id is not None
            assert word.language_code == normalized_code

    def test_extreme_language_code_cases(self):
        """测试极端语言代码情况"""

        extreme_cases = [
            ("", "en", "空字符串"),
            ("   ", "en", "空白字符串"),
            ("INVALID_LOCALE_CODE_123", "en", "无效的长代码"),
            ("12345", "en", "纯数字代码"),
            ("zh@#$%", "zh", "包含特殊字符的代码"),
            ("en-very-long-locale-code", "en", "过长的连字符代码"),
        ]

        for input_code, expected_code, description in extreme_cases:
            result = WordDataConverter.normalize_language_code(input_code)
            assert result == expected_code, \
                f"极端情况处理失败 {description}: {input_code} -> {result}, 期望 {expected_code}"

    def test_language_code_migration_compatibility(self):
        """测试语言代码迁移兼容性"""

        # 模拟历史数据中的各种语言代码格式
        legacy_language_codes = [
            "zh_CN",
            "zh-TW",
            "en_US",
            "en-GB",
            "zh",
            "en",
            None,
            "",
        ]

        for i, lang_code in enumerate(legacy_language_codes):
            # 创建模拟历史数据
            word = Word(
                id=i + 200,
                word=f"legacy_word_{i}",
                phonetic=f"/legacy{i}/",
                part_of_speech="noun",
                translation=f"历史数据{i}",
                is_golden=False,
                is_legacy_format=True,
                core_game=f"历史游戏{i}",
                scenario_formal="历史正式场景",
                scenario_casual="历史休闲场景",
                etymology_breakdown="历史词源分解",
                etymology_story="历史词源故事",
                common_mistakes="历史常见错误",
                memory_trick="历史记忆技巧",
                source="legacy",
                language_code=lang_code,  # 使用原始语言代码
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            self.db.add(word)
            self.db.commit()

            # 测试数据转换器处理历史语言代码
            result = WordDataConverter.legacy_to_new_format(word)

            # 验证语言代码被正确标准化
            assert "language_code" in result
            normalized_lang = result["language_code"]
            assert len(normalized_lang) <= 10, f"历史数据语言代码未正确标准化: {lang_code} -> {normalized_lang}"

    def test_language_code_validation_in_word_conversion(self):
        """测试单词转换中的语言代码验证"""

        # 测试AI响应转换中的语言代码处理
        ai_response = {
            'word': 'test_ai_word',
            'phonetic': '/test/',
            'core_game': {'content': 'AI游戏内容'},
            'game_boards': {},
            'etymology': {},
            'common_mistakes': {}
        }

        # 测试不同的语言代码
        test_language_codes = [
            "zh_CN",
            "en_US",
            "zh",
            "en",
            None,
            "",
            "invalid_long_locale_code"
        ]

        for lang_code in test_language_codes:
            result = WordDataConverter.convert_ai_response_to_word(
                ai_response,
                language_code=lang_code or "en"  # 确保不传None
            )

            # 验证语言代码被正确处理
            assert "language_code" in result
            normalized_lang = result["language_code"]
            assert len(normalized_lang) <= 10, f"AI转换语言代码处理失败: {lang_code} -> {normalized_lang}"

    def test_language_code_consistency_across_operations(self):
        """测试不同操作间语言代码的一致性"""

        test_input = "zh_CN.GB2312"

        # 测试标准化一致性
        normalized1 = WordDataConverter.normalize_language_code(test_input)
        normalized2 = WordDataConverter.normalize_language_code(test_input)

        assert normalized1 == normalized2, "语言代码标准化不一致"

        # 测试在不同上下文中的使用
        ai_response = {
            'word': 'consistency_test',
            'phonetic': '/test/',
            'core_game': {'content': '一致性测试'},
            'game_boards': {},
            'etymology': {},
            'common_mistakes': {}
        }

        # 在AI响应转换中使用
        result1 = WordDataConverter.convert_ai_response_to_word(
            ai_response,
            language_code=test_input
        )

        # 在显示格式转换中使用（通过创建Word对象）
        word = Word(
            id=999,
            word="test",
            phonetic="/test/",
            part_of_speech="noun",
            translation="测试",
            is_golden=False,
            is_legacy_format=False,
            core_game_new={"content": "测试内容"},
            game_boards={},
            etymology_new={},
            common_mistakes_new={},
            memory_trick="测试技巧",
            source="test",
            language_code=test_input,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        result2 = WordDataConverter.get_word_display_format(word, 'auto')

        # 验证两种方式产生的语言代码一致
        assert result1["language_code"] == result2["language_code"], \
            "不同操作中的语言代码处理不一致"


class TestLanguageCodePerformance:
    """语言代码处理性能测试"""

    def test_normalization_performance(self):
        """测试语言代码标准化性能"""
        import time

        # 测试大量标准化的性能
        test_codes = [
            "zh_CN", "en_US", "zh-TW", "en-GB", "fr_FR", "de_DE",
            "zh_CN.GB2312", "en_US.UTF-8", "invalid_long_locale_code"
        ] * 1000  # 9000个测试用例

        start_time = time.time()
        for code in test_codes:
            WordDataConverter.normalize_language_code(code)
        end_time = time.time()

        # 验证性能在合理范围内（应该在秒内完成）
        execution_time = end_time - start_time
        assert execution_time < 2.0, f"语言代码标准化性能过慢: {execution_time}秒"

        # 平均每个标准化操作的时间
        avg_time = execution_time / len(test_codes)
        assert avg_time < 0.001, f"单个标准化操作时间过长: {avg_time}秒"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])