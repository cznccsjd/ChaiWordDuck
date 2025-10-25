"""Prompt向后兼容层测试"""

import pytest
import warnings
from unittest.mock import patch, MagicMock

from app.prompts import legacy
from app.prompts.legacy import (
    get_word_generation_prompt,
    get_prompt_with_metadata,
    WORD_GENERATION_PROMPT
)
from app.prompts.manager import PromptManager


class TestLegacyCompatibility:
    """向后兼容层测试类"""

    def test_word_generation_prompt_constant_exists(self):
        """测试原有常量存在"""
        assert hasattr(legacy, 'WORD_GENERATION_PROMPT')
        assert isinstance(WORD_GENERATION_PROMPT, str)
        assert len(WORD_GENERATION_PROMPT) > 0
        assert '{word}' in WORD_GENERATION_PROMPT

    def test_get_word_generation_prompt_function_exists(self):
        """测试原有函数存在"""
        assert hasattr(legacy, 'get_word_generation_prompt')
        assert callable(get_word_generation_prompt)

    def test_get_word_generation_prompt_deprecation_warning(self):
        """测试弃用警告"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            result = get_word_generation_prompt("test")

            # 验证警告
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()

    @patch('app.prompts.legacy.get_prompt_manager')
    def test_get_word_generation_prompt_success(self, mock_get_manager):
        """测试成功获取Prompt"""
        # Mock PromptManager
        mock_manager = MagicMock()
        mock_get_manager.return_value = mock_manager

        system_prompt = "System prompt"
        user_prompt = "User prompt for word example"  # 已经格式化的结果
        mock_manager.render_prompt.return_value = (system_prompt, user_prompt)

        result = get_word_generation_prompt("example")

        # 验证调用
        mock_manager.render_prompt.assert_called_once_with(
            word="example",
            language="zh_CN",
            provider="gemini"
        )

        # 验证返回值 (legacy函数直接返回用户提示词)
        assert result == user_prompt

    @patch('app.prompts.legacy.get_prompt_manager')
    def test_get_word_generation_prompt_manager_failure_fallback(self, mock_get_manager):
        """测试PromptManager失败时的降级策略"""
        # Mock PromptManager抛出异常
        mock_get_manager.side_effect = Exception("Manager failed")

        result = get_word_generation_prompt("example")

        # 应该降级到原有模板
        expected = WORD_GENERATION_PROMPT.replace("{word}", "example")
        assert result == expected

    def test_get_prompt_with_metadata_success(self):
        """测试成功获取带元数据的Prompt"""
        result = get_prompt_with_metadata("test")

        assert isinstance(result, dict)
        assert "system_prompt" in result
        assert "user_prompt" in result
        assert "language" in result
        assert "provider" in result
        assert "word" in result
        assert "generated_by" in result

        # 验证内容
        assert result["word"] == "test"
        assert result["language"] == "zh_CN"
        assert result["provider"] == "gemini"
        assert "test" in result["user_prompt"]

    @patch('app.prompts.legacy.get_prompt_manager')
    def test_get_prompt_with_metadata_manager_failure(self, mock_get_manager):
        """测试PromptManager失败时的元数据降级策略"""
        # Mock PromptManager抛出异常
        mock_get_manager.side_effect = Exception("Manager failed")

        result = get_prompt_with_metadata("test")

        assert isinstance(result, dict)
        assert result["generated_by"] == "LegacyFallback"
        assert "error" in result
        assert result["word"] == "test"

        # 验证降级内容
        assert result["user_prompt"] == WORD_GENERATION_PROMPT.replace("{word}", "test")

    def test_metadata_structure(self):
        """测试元数据结构"""
        result = get_prompt_with_metadata("structure_test")

        required_fields = [
            "system_prompt",
            "user_prompt",
            "language",
            "provider",
            "word",
            "generated_by"
        ]

        for field in required_fields:
            assert field in result, f"Missing field: {field}"

        # 验证数据类型
        assert isinstance(result["system_prompt"], str)
        assert isinstance(result["user_prompt"], str)
        assert isinstance(result["language"], str)
        assert isinstance(result["provider"], str)
        assert isinstance(result["word"], str)
        assert isinstance(result["generated_by"], str)

    def test_prompt_content_quality(self):
        """测试Prompt内容质量"""
        word = "accommodation"
        result = get_prompt_with_metadata(word)

        # 验证系统提示词
        assert len(result["system_prompt"]) > 10
        assert "专家" in result["system_prompt"] or "expert" in result["system_prompt"]

        # 验证用户提示词
        assert len(result["user_prompt"]) > 100  # 应该是完整的模板
        assert word in result["user_prompt"]
        assert "维特根斯坦" in result["user_prompt"] or "Wittgenstein" in result["user_prompt"]

    def test_multiple_calls_consistency(self):
        """测试多次调用的一致性"""
        word = "consistency_test"

        result1 = get_word_generation_prompt(word)
        result2 = get_word_generation_prompt(word)

        assert result1 == result2

        metadata1 = get_prompt_with_metadata(word)
        metadata2 = get_prompt_with_metadata(word)

        # 元数据可能包含时间戳等信息，所以只比较核心内容
        assert metadata1["system_prompt"] == metadata2["system_prompt"]
        assert metadata1["user_prompt"] == metadata2["user_prompt"]
        assert metadata1["language"] == metadata2["language"]
        assert metadata1["provider"] == metadata2["provider"]
        assert metadata1["word"] == metadata2["word"]

    @patch('app.prompts.legacy.logger')
    def test_logging_behavior(self, mock_logger):
        """测试日志记录行为"""
        # 测试成功情况
        get_word_generation_prompt("logging_test")

        # 验证信息日志
        mock_logger.info.assert_called()

        # 重置mock
        mock_logger.reset_mock()

        # 测试失败情况
        with patch('app.prompts.legacy.get_prompt_manager') as mock_get_manager:
            mock_get_manager.side_effect = Exception("Test error")

            get_word_generation_prompt("error_test")

            # 验证警告日志
            mock_logger.warning.assert_called()

    def test_backward_compatibility_import(self):
        """测试向后兼容的导入"""
        # 测试从主模块导入
        from app.prompts import (
            get_word_generation_prompt as imported_get_prompt,
            WORD_GENERATION_PROMPT as imported_prompt
        )

        assert callable(imported_get_prompt)
        assert isinstance(imported_prompt, str)

        # 测试功能正常
        result = imported_get_prompt("test_import")
        assert "test_import" in result

    def test_constant_format_matches_expected(self):
        """测试常量格式符合预期"""
        # 验证关键结构存在
        expected_sections = [
            "核心游戏：这是什么",
            "游戏棋盘：它在哪两种",
            "游戏溯源与拆解",
            "犯规警告：常见的",
            "通关秘籍：一招制胜"
        ]

        for section in expected_sections:
            assert section in WORD_GENERATION_PROMPT

        # 验证JSON结构示例存在
        assert "```json" in WORD_GENERATION_PROMPT
        assert "word" in WORD_GENERATION_PROMPT
        assert "phonetic" in WORD_GENERATION_PROMPT
        assert "core_game" in WORD_GENERATION_PROMPT

    def test_error_handling(self):
        """测试错误处理"""
        # 测试空单词
        result = get_word_generation_prompt("")
        assert isinstance(result, str)
        assert "" in result  # 模板应该正确处理空字符串

        # 测试特殊字符单词
        special_word = "test-word_123"
        result = get_word_generation_prompt(special_word)
        assert special_word in result

        # 测试非常长的单词
        long_word = "p" * 100
        result = get_word_generation_prompt(long_word)
        assert long_word in result