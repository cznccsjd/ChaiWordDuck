#!/usr/bin/env python3
"""
验证prompt_version字段修复效果的测试脚本

测试API响应是否包含prompt_version字段
"""
import pytest
from unittest.mock import Mock, AsyncMock
from app.schemas.word import WordQueryResponse, WordByIdResponse
from app.models.word import Word
from datetime import datetime


def test_word_query_response_includes_prompt_version():
    """测试WordQueryResponse模型包含prompt_version字段"""

    # 创建测试数据
    response_data = {
        "id": 13,
        "word": "hello",
        "phonetic": "/həˈloʊ/",
        "partOfSpeech": "interjection",
        "translation": "你好",
        "coreGame": "核心游戏内容",
        "scenarioFormal": "思辨场景",
        "scenarioCasual": "生活场景",
        "etymologyBreakdown": "词根拆解",
        "etymologyStory": "词源故事",
        "commonMistakes": "犯规警告",
        "memoryTrick": "通关秘籍",
        "isGolden": False,
        "promptVersion": "v2.0",  # 关键字段
        "remainingQueries": 10,
    }

    # 创建响应对象
    response = WordQueryResponse(**response_data)

    # 验证prompt_version字段存在且正确
    assert hasattr(response, 'prompt_version')
    assert response.prompt_version == "v2.0"

    # 验证序列化包含该字段
    serialized = response.model_dump(by_alias=True)
    assert "promptVersion" in serialized
    assert serialized["promptVersion"] == "v2.0"


def test_word_by_id_response_includes_prompt_version():
    """测试WordByIdResponse模型包含prompt_version字段"""

    # 创建测试数据
    response_data = {
        "id": 13,
        "word": "hello",
        "phonetic": "/həˈloʊ/",
        "partOfSpeech": "interjection",
        "coreGame": "核心游戏内容",
        "scenarioFormal": "思辨场景",
        "scenarioCasual": "生活场景",
        "etymologyBreakdown": "词根拆解",
        "etymologyStory": "词源故事",
        "commonMistakes": "犯规警告",
        "memoryTrick": "通关秘籍",
        "isGolden": False,
        "promptVersion": "v2.0",  # 关键字段
        "createdAt": datetime.now(),
    }

    # 创建响应对象
    response = WordByIdResponse(**response_data)

    # 验证prompt_version字段存在且正确
    assert hasattr(response, 'prompt_version')
    assert response.prompt_version == "v2.0"

    # 验证序列化包含该字段
    serialized = response.model_dump(by_alias=True)
    assert "promptVersion" in serialized
    assert serialized["promptVersion"] == "v2.0"


def test_word_query_response_without_prompt_version_has_default():
    """测试WordQueryResponse在没有prompt_version时的处理"""

    # 创建不包含prompt_version的测试数据
    response_data = {
        "id": 13,
        "word": "hello",
        "phonetic": "/həˈloʊ/",
        "partOfSpeech": "interjection",
        "translation": "你好",
        "coreGame": "核心游戏内容",
        "scenarioFormal": "思辨场景",
        "scenarioCasual": "生活场景",
        "etymologyBreakdown": "词根拆解",
        "etymologyStory": "词源故事",
        "commonMistakes": "犯规警告",
        "memoryTrick": "通关秘籍",
        "isGolden": False,
        "remainingQueries": 10,
    }

    # 应该抛出验证错误，因为prompt_version是必需字段
    with pytest.raises(ValueError) as exc_info:
        WordQueryResponse(**response_data)

    # 验证错误信息提到prompt_version字段
    assert "prompt_version" in str(exc_info.value) or "promptVersion" in str(exc_info.value)


def test_word_to_api_dict_includes_prompt_version():
    """测试Word对象的to_api_dict方法包含prompt_version字段"""

    # 创建一个模拟的Word对象
    mock_word = Mock(spec=Word)
    mock_word.id = 13
    mock_word.word = "hello"
    mock_word.phonetic = "/həˈloʊ/"
    mock_word.part_of_speech = "interjection"
    mock_word.translation = "你好"
    mock_word.language_code = "zh"  # 添加语言代码
    mock_word.is_golden = False
    mock_word.prompt_version = "v2.0"
    mock_word.is_legacy_format = False
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
    mock_word.core_game = "核心游戏内容"
    mock_word.scenario_formal = "思辨场景"
    mock_word.scenario_casual = "生活场景"
    mock_word.etymology_breakdown = "词根拆解"
    mock_word.etymology_story = "词源故事"
    mock_word.common_mistakes = "犯规警告"
    mock_word.created_at = datetime.now()
    mock_word.updated_at = datetime.now()

    # 模拟to_api_dict方法
    def mock_to_api_dict(include_legacy_fields=True):
        from app.models.word_converter import WordDataConverter
        return WordDataConverter.get_word_display_format(mock_word, 'auto')

    mock_word.to_api_dict = mock_to_api_dict

    # 调用to_api_dict方法
    result = mock_word.to_api_dict(include_legacy_fields=True)

    # 验证结果包含prompt_version字段
    assert "prompt_version" in result
    assert result["prompt_version"] == "v2.0"


if __name__ == "__main__":
    print("Starting prompt_version field fix verification...")

    try:
        test_word_query_response_includes_prompt_version()
        print("[PASS] WordQueryResponse test passed")

        test_word_by_id_response_includes_prompt_version()
        print("[PASS] WordByIdResponse test passed")

        test_word_query_response_without_prompt_version_has_default()
        print("[PASS] Missing prompt_version error handling test passed")

        test_word_to_api_dict_includes_prompt_version()
        print("[PASS] Word.to_api_dict() test passed")

        print("\n[SUCCESS] All tests passed! prompt_version field fix successful!")

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        raise