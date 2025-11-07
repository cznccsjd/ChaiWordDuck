#!/usr/bin/env python3
"""
版本控制逻辑和降级机制验证脚本

全面测试API路由中的版本控制逻辑是否正确实现
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.schemas.word import WordQueryResponse, WordByIdResponse
from app.models.word import Word
from app.models.word_converter import WordDataConverter
from datetime import datetime
import json


def test_word_data_converter_legacy_format_prompt_version():
    """测试WordDataConverter在处理旧格式数据时的prompt_version逻辑"""

    # 创建旧格式的Word对象（没有prompt_version字段）
    mock_word = Mock(spec=Word)
    mock_word.id = 13
    mock_word.word = "hello"
    mock_word.phonetic = "/həˈloʊ/"
    mock_word.part_of_speech = "interjection"
    mock_word.translation = "你好"
    mock_word.is_golden = False
    mock_word.is_legacy_format = True  # 旧格式标记
    mock_word.core_game = "核心游戏内容"
    mock_word.scenario_formal = "思辨场景"
    mock_word.scenario_casual = "生活场景"
    mock_word.etymology_breakdown = "词根拆解"
    mock_word.etymology_story = "词源故事"
    mock_word.common_mistakes = "犯规警告"
    mock_word.memory_trick = "通关秘籍"
    mock_word.created_at = datetime.now()
    mock_word.updated_at = datetime.now()

    # 模拟没有prompt_version字段的情况
    # 设置language_code为字符串，避免Mock对象的问题
    mock_word.language_code = "zh"
    # Mock对象没有del属性，我们直接模拟getattr返回None
    original_getattr = getattr
    def mock_getattr(obj, name, default=None):
        if name == 'prompt_version':
            return None  # 模拟没有prompt_version字段
        return original_getattr(obj, name, default)

    import builtins
    builtins.getattr = mock_getattr

    # 测试legacy_to_new_format转换
    result = WordDataConverter.legacy_to_new_format(mock_word)

    # 验证默认值设置
    assert "prompt_version" in result
    assert result["prompt_version"] == "v1.0"  # 应该使用默认值


def test_word_data_converter_new_format_prompt_version():
    """测试WordDataConverter在处理新格式数据时的prompt_version逻辑"""

    # 创建新格式的Word对象（有prompt_version字段）
    mock_word = Mock(spec=Word)
    mock_word.id = 13
    mock_word.word = "hello"
    mock_word.phonetic = "/həˈloʊ/"
    mock_word.part_of_speech = "interjection"
    mock_word.translation = "你好"
    mock_word.is_golden = False
    mock_word.is_legacy_format = False  # 新格式标记
    mock_word.prompt_version = "v2.0"  # 有明确的版本
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
    mock_word.created_at = datetime.now()
    mock_word.updated_at = datetime.now()

    # 测试get_word_display_format
    result = WordDataConverter.get_word_display_format(mock_word, 'auto')

    # 验证prompt_version正确传递
    assert "prompt_version" in result
    assert result["prompt_version"] == "v2.0"


def test_config_prompt_version_settings():
    """测试配置文件中的prompt_version设置"""

    from app.core.config import settings

    # 验证配置中的prompt_version设置为v2.0
    assert hasattr(settings, 'prompt_version')
    assert settings.prompt_version == "v2.0", f"Expected v2.0, got {settings.prompt_version}"


def test_api_response_schema_includes_prompt_version():
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


def test_word_model_default_prompt_version():
    """测试Word模型的默认prompt_version设置"""

    from app.models.word import Word
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # 测试模型定义中的默认值
    word_table = Word.__table__
    prompt_version_column = word_table.c.prompt_version

    # 验证server_default设置为v1.0
    assert prompt_version_column.server_default is not None
    # PostgreSQL的server_default可能包含引号，所以我们检查是否包含v1.0
    assert "v1.0" in str(prompt_version_column.server_default.arg)


def test_version_fallback_logic():
    """测试版本降级逻辑"""

    # 模拟不同版本的数据
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
        }
    ]

    for case in test_cases:
        mock_word = Mock(spec=Word)
        for key, value in case["word_data"].items():
            setattr(mock_word, key, value)

        # 如果没有设置is_legacy_format，默认为True
        if not hasattr(mock_word, 'is_legacy_format'):
            mock_word.is_legacy_format = True

        # 添加必需的属性
        if not hasattr(mock_word, 'created_at'):
            mock_word.created_at = datetime.now()
        if not hasattr(mock_word, 'updated_at'):
            mock_word.updated_at = datetime.now()

        # 使用转换器处理
        if mock_word.is_legacy_format:
            result = WordDataConverter.legacy_to_new_format(mock_word)
        else:
            result = WordDataConverter.get_word_display_format(mock_word, 'auto')

        # 验证版本
        assert result.get("prompt_version") == case["expected_version"], \
            f"测试用例 {case['name']} 失败: 期望 {case['expected_version']}, 实际 {result.get('prompt_version')}"


if __name__ == "__main__":
    print("开始版本控制逻辑和降级机制验证...")

    try:
        test_word_data_converter_legacy_format_prompt_version()
        print("[PASS] 旧格式数据prompt_version处理测试通过")

        test_word_data_converter_new_format_prompt_version()
        print("[PASS] 新格式数据prompt_version处理测试通过")

        test_config_prompt_version_settings()
        print("[PASS] 配置文件prompt_version设置测试通过")

        test_api_response_schema_includes_prompt_version()
        print("[PASS] API响应schema prompt_version字段测试通过")

        test_word_model_default_prompt_version()
        print("[PASS] Word模型默认prompt_version测试通过")

        test_version_fallback_logic()
        print("[PASS] 版本降级逻辑测试通过")

        print("\n[SUCCESS] 所有版本控制逻辑测试通过！✅")
        print("=" * 60)
        print("验证结果总结：")
        print("1. ✅ API响应包含promptVersion字段")
        print("2. ✅ 配置文件prompt_version设置为v2.0")
        print("3. ✅ 旧格式数据默认使用v1.0")
        print("4. ✅ 新格式数据正确传递版本信息")
        print("5. ✅ 版本降级逻辑工作正常")
        print("6. ✅ 数据库模型默认值设置正确")
        print("=" * 60)

    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        raise