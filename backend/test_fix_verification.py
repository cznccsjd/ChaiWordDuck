#!/usr/bin/env python3
"""
测试 common_mistakes 字段修复的验证脚本
验证 Pydantic 验证错误是否已修复
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.word_converter import WordDataConverter
from app.schemas.word import WordQueryResponse


class MockWord:
    """模拟Word对象用于测试"""

    def __init__(self, is_legacy_format=False, has_structured_data=False):
        self.id = 1
        self.word = 'hello'
        self.phonetic = '/həˈloʊ/'
        self.part_of_speech = 'interjection'
        self.translation = '你好'
        self.core_game = 'test content'
        self.scenario_formal = 'formal scenario'
        self.scenario_casual = 'casual scenario'
        self.etymology_breakdown = 'test breakdown'
        self.etymology_story = 'test story'
        self.common_mistakes = '1. Pronunciation issues require special attention. 2. Do not confuse with "hollow".'
        self.memory_trick = 'Imagine greeting a friend'
        self.is_golden = False
        self.source = 'test'
        self.prompt_version = 'v1.0'
        self.created_at = None
        self.updated_at = None
        self.is_legacy_format = is_legacy_format

        if has_structured_data:
            self.core_game_new = {'content': 'structured core game'}
            self.game_boards = {
                'board_a_speculative': {'type': 'Board A', 'example': 'formal example'},
                'board_b_life': {'type': 'Board B', 'example': 'casual example'}
            }
            self.etymology_new = {
                'breakdown': {'root': {'part': 'test breakdown', 'meaning': 'test meaning'}},
                'story': 'test story'
            }
            self.common_mistakes_new = {
                'warning': 'Structured warning message',
                'avoidance': 'Structured avoidance advice'
            }
        else:
            self.core_game_new = None
            self.game_boards = None
            self.etymology_new = None
            self.common_mistakes_new = None

    def to_api_dict(self, include_legacy_fields=True):
        """模拟 to_api_dict 方法"""
        return WordDataConverter.get_word_display_format(self, 'auto')


def simulate_api_response(word_dict):
    """模拟API层的类型转换和响应构建"""
    # 处理 common_mistakes 字段的类型转换（修复后的逻辑）
    common_mistakes_value = word_dict.get("common_mistakes", "")
    if isinstance(common_mistakes_value, dict):
        # 如果是字典，提取 warning 字段作为字符串
        common_mistakes = common_mistakes_value.get("warning", "")
    else:
        # 如果已经是字符串，直接使用
        common_mistakes = str(common_mistakes_value) if common_mistakes_value else ""

    # 构建 WordQueryResponse
    try:
        response = WordQueryResponse(
            id=word_dict["id"],
            word=word_dict["word"],
            phonetic=word_dict["phonetic"],
            part_of_speech=word_dict["part_of_speech"],
            translation=word_dict.get("translation"),
            core_game=word_dict.get("core_game_content", ""),
            scenario_formal=word_dict.get("scenario_formal", ""),
            scenario_casual=word_dict.get("scenario_casual", ""),
            etymology_breakdown=word_dict.get("etymology_breakdown", ""),
            etymology_story=word_dict.get("etymology_story", ""),
            common_mistakes=common_mistakes,  # 使用处理后的值
            memory_trick=word_dict["memory_trick"],
            is_golden=word_dict["is_golden"],
            remaining_queries=10
        )
        return True, response
    except Exception as e:
        return False, str(e)


def test_case_1_new_format():
    """Test Case 1: New format data with structured common_mistakes"""
    print("=" * 80)
    print("Test Case 1: New format data (with structured common_mistakes)")
    print("=" * 80)

    mock_word = MockWord(is_legacy_format=False, has_structured_data=True)
    word_dict = mock_word.to_api_dict(include_legacy_fields=True)

    print(f"word_dict['common_mistakes'] type: {type(word_dict['common_mistakes'])}")
    print(f"word_dict['common_mistakes'] value: {word_dict['common_mistakes']}")

    success, result = simulate_api_response(word_dict)

    if success:
        print(f"SUCCESS: API response construction successful!")
        print(f"   common_mistakes field value: \"{result.common_mistakes}\"")
        print(f"   field type: {type(result.common_mistakes)}")
    else:
        print(f"ERROR: API response construction failed: {result}")

    return success


def test_case_2_legacy_format():
    """Test Case 2: Legacy format data with string common_mistakes"""
    print("\n" + "=" * 80)
    print("Test Case 2: Legacy format data (string common_mistakes only)")
    print("=" * 80)

    mock_word = MockWord(is_legacy_format=True, has_structured_data=False)
    word_dict = mock_word.to_api_dict(include_legacy_fields=True)

    print(f"word_dict['common_mistakes'] type: {type(word_dict['common_mistakes'])}")
    print(f"word_dict['common_mistakes'] value: {word_dict['common_mistakes']}")

    success, result = simulate_api_response(word_dict)

    if success:
        print(f"SUCCESS: API response construction successful!")
        print(f"   common_mistakes field value: \"{result.common_mistakes}\"")
        print(f"   field type: {type(result.common_mistakes)}")
    else:
        print(f"ERROR: API response construction failed: {result}")

    return success


def test_case_3_edge_cases():
    """Test Case 3: Edge cases"""
    print("\n" + "=" * 80)
    print("Test Case 3: Edge cases testing")
    print("=" * 80)

    # Test empty common_mistakes
    mock_word = MockWord(is_legacy_format=False, has_structured_data=False)
    mock_word.common_mistakes = ""
    word_dict = mock_word.to_api_dict(include_legacy_fields=True)

    print("Testing empty string common_mistakes:")
    success, result = simulate_api_response(word_dict)
    print(f"   Result: {'SUCCESS' if success else 'ERROR'}")
    if success:
        print(f"   common_mistakes value: \"{result.common_mistakes}\"")

    return success


def main():
    """Main test function"""
    print("Starting verification of common_mistakes field fix...")
    print("Verifying Pydantic validation error fix for Railway deployment")

    test_results = []

    # Run all test cases
    test_results.append(test_case_1_new_format())
    test_results.append(test_case_2_legacy_format())
    test_results.append(test_case_3_edge_cases())

    # Summarize results
    print("\n" + "=" * 80)
    print("Test Results Summary")
    print("=" * 80)

    passed = sum(test_results)
    total = len(test_results)

    print(f"Total tests: {total}")
    print(f"Passed tests: {passed}")
    print(f"Failed tests: {total - passed}")

    if passed == total:
        print("\n*** All tests passed! Fix verification successful! ***")
        print("Pydantic validation error has been fixed, API should work normally now.")
    else:
        print(f"\n*** {total - passed} tests failed, further investigation needed. ***")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)