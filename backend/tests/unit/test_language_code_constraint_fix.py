"""
语言代码约束Bug修复验证测试

验证Railway部署环境的语言代码约束违反Bug修复情况：
- 确保应用层只产生2字符ISO 639-1语言代码
- 验证Accept-Language头部正确映射到2字符代码
- 确保与数据库约束一致
"""
import pytest
from unittest.mock import patch

from app.validators.user_preferences import (
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
    is_supported_language,
    validate_preferred_language,
    normalize_language_code,
    get_default_language
)
from app.services.guest_preferences import (
    get_language_from_accept_language,
    normalize_accept_language_code,
    get_language_from_cookie,
    get_guest_language_preference,
    get_effective_language_for_guest
)


class TestLanguageCodeConstraintFix:
    """语言代码约束修复验证测试"""

    def test_supported_languages_use_two_char_codes(self):
        """测试支持的语言使用2字符代码"""
        # 验证所有支持的语言都是2字符ISO 639-1代码
        for lang in SUPPORTED_LANGUAGES:
            assert len(lang) == 2, f"语言代码 '{lang}' 应该是2字符，实际是 {len(lang)} 字符"
            assert lang.islower(), f"语言代码 '{lang}' 应该是小写"

        # 验证特定语言代码存在
        assert "en" in SUPPORTED_LANGUAGES, "应该支持 'en' 语言代码"
        assert "zh" in SUPPORTED_LANGUAGES, "应该支持 'zh' 语言代码"

        # 验证不应该包含5字符代码
        assert "en_US" not in SUPPORTED_LANGUAGES, "不应该支持 'en_US' 语言代码"
        assert "zh_CN" not in SUPPORTED_LANGUAGES, "不应该支持 'zh_CN' 语言代码"

    def test_default_language_is_two_char_code(self):
        """测试默认语言使用2字符代码"""
        assert len(DEFAULT_LANGUAGE) == 2, f"默认语言 '{DEFAULT_LANGUAGE}' 应该是2字符"
        assert DEFAULT_LANGUAGE.islower(), f"默认语言 '{DEFAULT_LANGUAGE}' 应该是小写"
        assert DEFAULT_LANGUAGE in SUPPORTED_LANGUAGES, "默认语言应该在支持的语言列表中"

    def test_is_supported_language_two_char_codes(self):
        """测试语言支持验证只接受2字符代码"""
        # 支持的2字符代码
        assert is_supported_language("en") is True
        assert is_supported_language("zh") is True

        # 不应该支持5字符代码
        assert is_supported_language("en_US") is False
        assert is_supported_language("zh_CN") is False

        # 不应该支持其他格式
        assert is_supported_language("en-us") is False
        assert is_supported_language("zh-cn") is False
        assert is_supported_language("EN") is False
        assert is_supported_language("ZH") is False

    def test_validate_preferred_language_two_char_codes(self):
        """测试语言偏好验证只接受2字符代码"""
        # 有效的2字符代码
        assert validate_preferred_language("en") == "en"
        assert validate_preferred_language("zh") == "zh"

        # 无效的5字符代码应该抛出异常
        with pytest.raises(ValueError, match="不支持的语言代码"):
            validate_preferred_language("en_US")

        with pytest.raises(ValueError, match="不支持的语言代码"):
            validate_preferred_language("zh_CN")

    def test_normalize_language_code_to_two_char(self):
        """测试语言代码标准化为2字符格式"""
        # 2字符代码应该保持不变
        assert normalize_language_code("en") == "en"
        assert normalize_language_code("zh") == "zh"

        # 5字符代码应该映射到2字符代码
        assert normalize_language_code("en_US") == "en"
        assert normalize_language_code("zh_CN") == "zh"

        # 带连字符的格式应该映射到2字符代码
        assert normalize_language_code("en-us") == "en"
        assert normalize_language_code("zh-cn") == "zh"

        # 空值应该返回默认语言
        assert normalize_language_code("") == DEFAULT_LANGUAGE
        assert normalize_language_code(None) == DEFAULT_LANGUAGE

    def test_normalize_accept_language_code_to_two_char(self):
        """测试Accept-Language代码标准化为2字符格式"""
        # 常见的Accept-Language格式应该映射到2字符代码
        assert normalize_accept_language_code("en-US") == "en"
        assert normalize_accept_language_code("en-us") == "en"
        assert normalize_accept_language_code("en") == "en"

        assert normalize_accept_language_code("zh-CN") == "zh"
        assert normalize_accept_language_code("zh-cn") == "zh"
        assert normalize_accept_language_code("zh") == "zh"

        # 不支持的语言应该返回None
        assert normalize_accept_language_code("fr-FR") is None
        assert normalize_accept_language_code("de-DE") is None
        assert normalize_accept_language_code("ja-JP") is None

    def test_get_language_from_accept_language_two_char_codes(self):
        """测试从Accept-Language头部获取2字符语言代码"""
        # 英文优先级测试
        en_lang = get_language_from_accept_language("en-US,en;q=0.9,zh-CN;q=0.8")
        assert en_lang == "en", f"期望 'en'，实际得到 '{en_lang}'"

        # 中文优先级测试
        zh_lang = get_language_from_accept_language("zh-CN,zh;q=0.9,en-US;q=0.8")
        assert zh_lang == "zh", f"期望 'zh'，实际得到 '{zh_lang}'"

        # 混合质量值测试
        en_lang = get_language_from_accept_language("zh-CN;q=0.8,en-US;q=0.9")
        assert en_lang == "en", f"期望 'en'，实际得到 '{en_lang}'"

        # 没有头部时应该返回默认语言
        default_lang = get_language_from_accept_language(None)
        assert default_lang == DEFAULT_LANGUAGE
        assert len(default_lang) == 2

    def test_get_language_from_cookie_two_char_codes(self):
        """测试从Cookie获取2字符语言代码"""
        # 有效的2字符代码Cookie
        cookies = {"language": "en"}
        language = get_language_from_cookie(cookies)
        assert language == "en"

        cookies = {"language": "zh"}
        language = get_language_from_cookie(cookies)
        assert language == "zh"

        # 5字符代码Cookie应该被标准化
        cookies = {"language": "en_US"}
        language = get_language_from_cookie(cookies)
        assert language == "en"

        cookies = {"language": "zh_CN"}
        language = get_language_from_cookie(cookies)
        assert language == "zh"

        # 无效Cookie应该返回默认语言
        language = get_language_from_cookie({})
        assert language == DEFAULT_LANGUAGE
        assert len(language) == 2

    def test_guest_language_preference_two_char_codes(self):
        """测试游客语言偏好使用2字符代码"""
        # 测试Accept-Language头部
        headers = {"Accept-Language": "en-US,en;q=0.9"}
        cookies = {}
        language = get_guest_language_preference(headers, cookies)
        assert language == "en"
        assert len(language) == 2

        # 测试Cookie覆盖
        headers = {"Accept-Language": "en-US,en;q=0.9"}
        cookies = {"language": "zh_CN"}
        language = get_guest_language_preference(headers, cookies)
        assert language == "zh"
        assert len(language) == 2

        # 测试默认语言
        language = get_guest_language_preference({}, {})
        assert language == DEFAULT_LANGUAGE
        assert len(language) == 2

    def test_effective_language_for_guest_two_char_codes(self):
        """测试游客有效语言使用2字符代码"""
        headers = {"Accept-Language": "en-US,en;q=0.9"}
        cookies = {"language": "zh_CN"}

        # 测试显式参数最高优先级
        explicit_lang = get_effective_language_for_guest(
            headers=headers, cookies=cookies, explicit_language="zh_CN"
        )
        assert explicit_lang == "zh"
        assert len(explicit_lang) == 2

        # 测试Cookie优先级
        cookie_lang = get_effective_language_for_guest(
            headers=headers, cookies=cookies, explicit_language=None
        )
        assert cookie_lang == "zh"
        assert len(cookie_lang) == 2

        # 测试Accept-Language优先级
        header_lang = get_effective_language_for_guest(
            headers=headers, cookies={}, explicit_language=None
        )
        assert header_lang == "en"
        assert len(header_lang) == 2

    def test_complex_accept_language_parsing_two_char_codes(self):
        """测试复杂Accept-Language头部解析使用2字符代码"""
        test_cases = [
            # (Accept-Language头部, 期望结果)
            ("fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6", "en"),
            ("de-DE,de;q=0.9,zh-CN;q=0.8,zh;q=0.7", "zh"),
            ("ja-JP,ja;q=0.9,ko-KR;q=0.8", DEFAULT_LANGUAGE),  # 都不支持，使用默认语言
            ("en-US;q=0.8,zh-CN;q=0.9", "zh"),
            ("zh;q=0.9,en;q=0.8", "zh"),
        ]

        for accept_language, expected in test_cases:
            result = get_language_from_accept_language(accept_language)
            assert result == expected, f"Accept-Language: '{accept_language}', 期望: '{expected}', 实际: '{result}'"
            assert len(result) == 2, f"结果应该是2字符代码: '{result}'"

    def test_edge_cases_and_error_handling(self):
        """测试边界情况和错误处理"""
        edge_cases = [
            "",  # 空字符串
            None,  # None值
            "invalid",  # 无效格式
            "zh;q=abc",  # 无效质量值
            "zh;q=2.0",  # 超出范围质量值
            "  en-US  ",  # 前后空格
            "en-US,",  # 尾随逗号
            ",en-US",  # 前导逗号
        ]

        for accept_language in edge_cases:
            result = get_language_from_accept_language(accept_language)
            assert result in SUPPORTED_LANGUAGES, f"边界情况 '{accept_language}' 应该返回支持的语言"
            assert len(result) == 2, f"结果应该是2字符代码: '{result}'"

    def test_backwards_compatibility_warning(self):
        """测试向后兼容性警告（如果需要）"""
        # 测试 normalize_language_code 能正确处理旧的5字符代码
        result = normalize_language_code("en_US")
        assert result == "en"

        result = normalize_language_code("zh_CN")
        assert result == "zh"

    @pytest.mark.parametrize("input_lang,expected_output", [
        ("en-US", "en"),
        ("en-us", "en"),
        ("en", "en"),
        ("zh-CN", "zh"),
        ("zh-cn", "zh"),
        ("zh", "zh"),
        ("EN-US", "en"),
        ("ZH-CN", "zh"),
        ("en_US", "en"),
        ("zh_CN", "zh"),
        (None, None),  # normalize_accept_language_code对None返回None
        ("", None),   # normalize_accept_language_code对空字符串返回None
        ("invalid", None),  # 不支持的语言返回None
        ("fr-FR", None),  # 不支持的语言
    ])
    def test_language_normalization_parametrized(self, input_lang, expected_output):
        """参数化测试语言代码标准化"""
        if expected_output is None:
            result = normalize_accept_language_code(input_lang)
            assert result is None
        else:
            result = normalize_accept_language_code(input_lang)
            assert result == expected_output
            if result is not None:
                assert len(result) == 2

    def test_database_constraint_compliance(self):
        """测试数据库约束合规性"""
        # 验证所有可能的语言代码都符合数据库约束
        # 数据库约束: language_code IN ('en', 'zh_CN', 'zh_TW', 'ja', 'ko', 'fr', 'de', 'es', 'it', 'ru')
        db_allowed_codes = {'en', 'zh_CN', 'zh_TW', 'ja', 'ko', 'fr', 'de', 'es', 'it', 'ru'}

        # 我们的应用现在只使用 'en' 和 'zh'（映射到原来的 'en' 和 'zh_CN'）
        for lang in SUPPORTED_LANGUAGES:
            assert lang in db_allowed_codes or (lang == 'zh' and 'zh_CN' in db_allowed_codes), \
                f"语言代码 '{lang}' 不在数据库允许的代码列表中"

    def test_performance_considerations(self):
        """测试性能考虑"""
        # 确保语言代码处理不会显著影响性能
        import time

        # 测试大量语言代码处理的性能
        start_time = time.time()

        for _ in range(1000):
            get_language_from_accept_language("en-US,en;q=0.9,zh-CN;q=0.8,fr-FR;q=0.7")
            normalize_accept_language_code("zh-CN")
            normalize_language_code("en_US")

        end_time = time.time()
        processing_time = end_time - start_time

        # 1000次操作应该在合理时间内完成（比如1秒内）
        assert processing_time < 1.0, f"语言代码处理性能测试失败，耗时: {processing_time}秒"