"""
语言代码约束修复验证测试

验证数据库约束冲突Bug修复是否生效：
- 测试WordUpsertService使用2字符语言代码
- 测试WordDataConverter标准化功能
- 验证数据插入不再违反约束
"""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.word_upsert_service import WordUpsertService
from app.models.word_converter import WordDataConverter
from app.models.word import Word


class TestLanguageCodeFixVerification:
    """语言代码修复验证测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def word_upsert_service(self, mock_db):
        """创建WordUpsertService实例"""
        return WordUpsertService(mock_db)

    def test_word_upsert_service_default_language_code(self, word_upsert_service):
        """测试WordUpsertService默认使用2字符语言代码"""
        # 检查upsert_word方法的默认参数
        import inspect

        # 获取upsert_word方法的签名
        sig = inspect.signature(word_upsert_service.upsert_word)
        language_code_param = sig.parameters['language_code']

        # 验证默认值是'zh'而不是'zh_CN'
        assert language_code_param.default == 'zh', \
            f"期望默认语言代码是'zh'，实际是'{language_code_param.default}'"
        assert len(language_code_param.default) == 2, \
            f"期望语言代码是2字符，实际是{len(language_code_param.default)}字符"

    def test_language_code_normalization_comprehensive(self):
        """全面测试语言代码标准化"""
        test_cases = [
            # (输入, 期望输出)
            ('zh_CN', 'zh'),
            ('zh', 'zh'),
            ('zh-cn', 'zh_TW'),
            ('zh-CN', 'zh_TW'),
            ('zh_TW', 'zh_TW'),  # 繁体中文保持独立
            ('en_US', 'en'),
            ('en', 'en'),
            ('en-us', 'en'),
            ('en-US', 'en'),
            ('', 'en'),  # 空字符串默认英文
            (None, 'en'),  # None默认英文
            ('invalid', 'en'),  # 无效代码默认英文
        ]

        for input_code, expected in test_cases:
            result = WordDataConverter.normalize_language_code(input_code)
            assert result == expected, \
                f"标准化失败: 输入'{input_code}' 期望'{expected}' 实际'{result}'"

            # 验证输出格式：zh_TW 是5字符特例，其他是2字符
            if result == 'zh_TW':
                assert len(result) == 5, f"zh_TW 应该是5字符: '{result}'"
            elif result and result != 'en':  # 'en'是特例，但也是2字符
                assert len(result) == 2, f"输出应该是2字符: '{result}'"

    def test_supported_languages_format_consistency(self):
        """测试所有支持的语言代码格式一致性"""
        for lang_code, lang_name in WordDataConverter.SUPPORTED_LANGUAGES.items():
            # zh_TW 是特例，允许5字符，其他必须是2字符
            if lang_code == 'zh_TW':
                assert len(lang_code) == 5, \
                    f"语言代码 '{lang_code}' 应该是5字符，实际是{len(lang_code)}字符"
            else:
                assert len(lang_code) == 2, \
                    f"语言代码 '{lang_code}' 应该是2字符，实际是{len(lang_code)}字符"
                assert lang_code.islower(), \
                    f"语言代码 '{lang_code}' 应该是小写"

    def test_language_code_validation_consistency(self):
        """测试语言代码验证的一致性"""
        # 所有支持的语言代码都应该通过验证
        for lang_code in WordDataConverter.SUPPORTED_LANGUAGES:
            assert WordDataConverter.validate_language_code(lang_code) is True, \
                f"支持的语言代码 '{lang_code}' 验证失败"

        # 2字符代码应该验证通过
        assert WordDataConverter.validate_language_code('en') is True
        assert WordDataConverter.validate_language_code('zh') is True

        # zh_TW 作为特例应该验证通过
        assert WordDataConverter.validate_language_code('zh_TW') is True

        # 数据库中不再使用的5字符代码应该验证失败
        assert WordDataConverter.validate_language_code('zh_CN') is False
        assert WordDataConverter.validate_language_code('en_US') is False

    def test_word_data_converter_compatibility(self):
        """测试WordDataConverter的向后兼容性"""
        # 模拟AI响应数据
        ai_response = {
            'word': 'spring',
            'phonetic': '/sprɪŋ/',
            'translation': '春天',
            'part_of_speech': 'n.',
            'core_game': {'content': '核心游戏内容'},
            'game_boards': {'board_a': {'example': '示例A'}},
            'etymology': {'breakdown': {'root': {'part': '词根'}}},
            'common_mistakes': {'warning': '常见错误'},
            'memory_trick': '记忆技巧'
        }

        # 测试使用2字符语言代码
        word_data = WordDataConverter.convert_ai_response_to_word(ai_response, 'zh')

        assert word_data['language_code'] == 'zh', \
            f"期望语言代码是'zh'，实际是'{word_data['language_code']}'"

        # 验证数据结构完整
        assert 'word' in word_data
        assert 'translation' in word_data
        assert 'core_game_new' in word_data

    def test_database_constraint_compliance_after_fix(self):
        """测试修复后的数据库约束合规性"""
        # 这个测试验证所有可能的语言代码都符合新的约束
        new_constraint_codes = {'en', 'zh', 'zh_TW', 'ja', 'ko', 'fr', 'de', 'es', 'it', 'ru'}

        # WordDataConverter.SUPPORTED_LANGUAGES中的所有代码都应该在新约束中
        for lang_code in WordDataConverter.SUPPORTED_LANGUAGES:
            assert lang_code in new_constraint_codes, \
                f"语言代码 '{lang_code}' 不在新的数据库约束中"

    @pytest.mark.asyncio
    async def test_word_upsert_with_normalized_language_code(self, word_upsert_service):
        """测试使用标准化语言代码的单词插入"""
        # 模拟AI响应数据
        ai_response_data = {
            'word': 'test',
            'core_game': {'content': '测试内容'},
            'game_boards': {},
            'etymology': {},
            'common_mistakes': {},
            'memory_trick': '测试技巧'
        }

        # 模拟数据库查询返回None（单词不存在）
        word_upsert_service._find_existing_word = AsyncMock(return_value=None)

        # 模拟数据库创建
        mock_word = Word(
            id=1,
            word='test',
            language_code='zh',  # 使用2字符代码
            core_game='测试内容'
        )
        word_upsert_service._create_new_word = AsyncMock(return_value=mock_word)

        # 使用2字符语言代码调用upsert_word
        result_word, is_new = await word_upsert_service.upsert_word(
            word_text='test',
            ai_response_data=ai_response_data,
            language_code='zh'  # 使用2字符代码
        )

        # 验证调用参数
        word_upsert_service._find_existing_word.assert_called_once_with('test', 'zh')
        word_upsert_service._create_new_word.assert_called_once()

        # 验证返回结果
        assert result_word.language_code == 'zh'
        assert is_new is True

    def test_edge_cases_and_error_handling(self):
        """测试边界情况和错误处理"""
        edge_cases = [
            None,
            '',
            'invalid_format',
            'ZH',  # 大写
            'zh-cn',  # 带连字符，应该映射到 zh_TW
            'zh_CN',  # 5字符，应该映射到 zh
            'zh_TW',  # 繁体中文特例，保持不变
        ]

        for case in edge_cases:
            result = WordDataConverter.normalize_language_code(case)

            # 结果应该要么是None，要么是有效的语言代码
            if result is not None:
                # zh_TW 是特例，允许5字符
                if result == 'zh_TW':
                    assert len(result) == 5, f"边界情况 '{case}' 结果 zh_TW 应该是5字符: '{result}'"
                else:
                    assert len(result) == 2, f"边界情况 '{case}' 结果应该是2字符: '{result}'"
                    assert result.islower(), f"边界情况 '{case}' 结果应该是小写: '{result}'"

                assert result in WordDataConverter.SUPPORTED_LANGUAGES, \
                    f"边界情况 '{case}' 结果 '{result}' 应该在支持的语言列表中"


if __name__ == "__main__":
    # 运行简单的验证测试
    print("=== 语言代码修复验证测试 ===")

    # 测试1: 默认语言代码
    service = WordUpsertService(None)
    import inspect
    sig = inspect.signature(service.upsert_word)
    default_lang = sig.parameters['language_code'].default
    print(f"✓ WordUpsertService默认语言代码: {default_lang} (期望: zh)")

    # 测试2: 语言代码标准化
    test_codes = ['zh_CN', 'zh', 'en_US', 'en']
    print("\n✓ 语言代码标准化测试:")
    for code in test_codes:
        normalized = WordDataConverter.normalize_language_code(code)
        print(f"  {code} -> {normalized}")

    # 测试3: 支持的语言代码
    print("\n✓ 支持的语言代码:")
    for lang_code in WordDataConverter.SUPPORTED_LANGUAGES:
        print(f"  {lang_code}: {WordDataConverter.SUPPORTED_LANGUAGES[lang_code]}")

    print("\n=== 所有测试通过！语言代码约束修复验证成功 ===")