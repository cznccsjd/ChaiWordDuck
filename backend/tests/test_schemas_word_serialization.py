"""
测试Pydantic模型的JSON序列化和字段命名格式

验证API响应使用驼峰命名(camelCase)而不是蛇形命名(snake_case)
以及Unicode字符清理功能
"""
import json
from datetime import datetime
from typing import Dict, Any

import pytest

from app.schemas.word import (
    WordQueryResponse,
    WordByIdResponse,
    WordDetail,
    QueryLimitInfo,
    clean_invalid_unicode
)


class TestUnicodeCleaning:
    """测试Unicode字符清理功能"""

    def test_clean_invalid_unicode_with_valid_text(self):
        """测试清理有效Unicode文本"""
        valid_text = "Hello, 世界! This is valid text."
        result = clean_invalid_unicode(valid_text)
        assert result == valid_text

    def test_clean_invalid_unicode_with_invalid_surrogates(self):
        """测试清理包含无效代理对的文本"""
        # 包含无效代理对字符的文本
        text_with_surrogates = "Hello\udc80 world\udcff test"
        expected = "Hello world test"
        result = clean_invalid_unicode(text_with_surrogates)
        assert result == expected

    def test_clean_invalid_unicode_with_empty_string(self):
        """测试清理空字符串"""
        assert clean_invalid_unicode("") == ""
        assert clean_invalid_unicode(None) is None

    def test_clean_invalid_unicode_with_multiple_surrogates(self):
        """测试清理包含多个无效代理对的文本"""
        text = "start\udc80\udc99middle\udcffend"
        expected = "startmiddleend"
        result = clean_invalid_unicode(text)
        assert result == expected


class TestWordQueryResponseSerialization:
    """测试WordQueryResponse的JSON序列化"""

    def test_field_names_camel_case_in_json(self):
        """测试JSON序列化时字段名使用驼峰命名"""
        # 创建测试数据
        now = datetime.now()
        response_data = {
            "id": 1,
            "word": "hello",
            "phonetic": "/həˈloʊ/",
            "part_of_speech": "interjection",
            "core_game": "核心游戏内容",
            "scenario_formal": "思辨场景内容",
            "scenario_casual": "生活场景内容",
            "etymology_breakdown": "词根拆解内容",
            "etymology_story": "词源故事内容",
            "common_mistakes": "常见错误内容",
            "memory_trick": "记忆技巧内容",
            "is_golden": True,
            "remaining_queries": 5
        }

        response = WordQueryResponse(**response_data)

        # 测试JSON序列化
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)

        # 验证字段名使用驼峰命名
        assert "partOfSpeech" in parsed
        assert "coreGame" in parsed
        assert "scenarioFormal" in parsed
        assert "scenarioCasual" in parsed
        assert "etymologyBreakdown" in parsed
        assert "etymologyStory" in parsed
        assert "commonMistakes" in parsed
        assert "memoryTrick" in parsed
        assert "isGolden" in parsed
        assert "remainingQueries" in parsed

        # 验证蛇形命名的字段不存在
        assert "part_of_speech" not in parsed
        assert "core_game" not in parsed
        assert "scenario_formal" not in parsed
        assert "etymology_breakdown" not in parsed

    def test_field_values_correct_after_serialization(self):
        """测试序列化后字段值保持正确"""
        response_data = {
            "id": 1,
            "word": "test",
            "phonetic": "/test/",
            "part_of_speech": "noun",
            "core_game": "测试核心游戏",
            "scenario_formal": "测试思辨场景",
            "scenario_casual": "测试生活场景",
            "etymology_breakdown": "测试词根拆解",
            "etymology_story": "测试词源故事",
            "common_mistakes": "测试常见错误",
            "memory_trick": "测试记忆技巧",
            "is_golden": False,
            "remaining_queries": 10
        }

        response = WordQueryResponse(**response_data)
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)

        # 验证字段值正确
        assert parsed["id"] == 1
        assert parsed["word"] == "test"
        assert parsed["phonetic"] == "/test/"
        assert parsed["partOfSpeech"] == "noun"
        assert parsed["coreGame"] == "测试核心游戏"
        assert parsed["scenarioFormal"] == "测试思辨场景"
        assert parsed["scenarioCasual"] == "测试生活场景"
        assert parsed["etymologyBreakdown"] == "测试词根拆解"
        assert parsed["etymologyStory"] == "测试词源故事"
        assert parsed["commonMistakes"] == "测试常见错误"
        assert parsed["memoryTrick"] == "测试记忆技巧"
        assert parsed["isGolden"] is False
        assert parsed["remainingQueries"] == 10

    def test_unicode_cleaning_in_validation(self):
        """测试字段验证时清理Unicode字符"""
        response_data = {
            "id": 1,
            "word": "test",
            "phonetic": "/test/",
            "part_of_speech": "noun",
            "core_game": "有效文本\udc80无效字符",  # 包含无效代理对
            "scenario_formal": "思辨场景\udcff测试",
            "scenario_casual": "生活场景测试",
            "etymology_breakdown": "词根拆解\udc99测试",
            "etymology_story": None,  # 可选字段为None
            "common_mistakes": "常见错误测试",
            "memory_trick": "记忆技巧\udc80测试",
            "is_golden": False,
            "remaining_queries": 10
        }

        response = WordQueryResponse(**response_data)

        # 验证Unicode字符被清理
        assert response.core_game == "有效文本无效字符"
        assert response.scenario_formal == "思辨场景测试"
        assert response.etymology_breakdown == "词根拆解测试"
        assert response.memory_trick == "记忆技巧测试"

        # 验证JSON序列化后也是清理后的内容
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["coreGame"] == "有效文本无效字符"
        assert parsed["scenarioFormal"] == "思辨场景测试"
        assert parsed["etymologyBreakdown"] == "词根拆解测试"
        assert parsed["memoryTrick"] == "记忆技巧测试"

    def test_model_dump_method_with_alias(self):
        """测试model_dump方法正确使用别名"""
        response_data = {
            "id": 1,
            "word": "test",
            "phonetic": "/test/",
            "part_of_speech": "noun",
            "core_game": "测试内容",
            "scenario_formal": "思辨场景",
            "scenario_casual": "生活场景",
            "etymology_breakdown": "词根拆解",
            "etymology_story": None,
            "common_mistakes": "常见错误",
            "memory_trick": "记忆技巧",
            "is_golden": True,
            "remaining_queries": 5
        }

        response = WordQueryResponse(**response_data)

        # 测试默认使用别名
        data_dict = response.model_dump()
        assert "partOfSpeech" in data_dict
        assert "coreGame" in data_dict
        assert "part_of_speech" not in data_dict
        assert "core_game" not in data_dict

        # 测试明确指定使用别名
        data_dict_with_alias = response.model_dump(by_alias=True)
        assert "partOfSpeech" in data_dict_with_alias
        assert "coreGame" in data_dict_with_alias

        # 测试不使用别名
        data_dict_no_alias = response.model_dump(by_alias=False)
        assert "part_of_speech" in data_dict_no_alias
        assert "core_game" in data_dict_no_alias
        assert "partOfSpeech" not in data_dict_no_alias
        assert "coreGame" not in data_dict_no_alias


class TestWordByIdResponseSerialization:
    """测试WordByIdResponse的JSON序列化"""

    def test_field_names_camel_case_in_json(self):
        """测试JSON序列化时字段名使用驼峰命名"""
        now = datetime.now()
        response_data = {
            "id": 1,
            "word": "hello",
            "phonetic": "/həˈloʊ/",
            "part_of_speech": "interjection",
            "core_game": "核心游戏内容",
            "scenario_formal": "思辨场景内容",
            "scenario_casual": "生活场景内容",
            "etymology_breakdown": "词根拆解内容",
            "etymology_story": "词源故事内容",
            "common_mistakes": "常见错误内容",
            "memory_trick": "记忆技巧内容",
            "is_golden": True,
            "created_at": now
        }

        response = WordByIdResponse(**response_data)

        # 测试JSON序列化
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)

        # 验证字段名使用驼峰命名
        assert "partOfSpeech" in parsed
        assert "coreGame" in parsed
        assert "scenarioFormal" in parsed
        assert "scenarioCasual" in parsed
        assert "etymologyBreakdown" in parsed
        assert "etymologyStory" in parsed
        assert "commonMistakes" in parsed
        assert "memoryTrick" in parsed
        assert "isGolden" in parsed
        assert "createdAt" in parsed

        # 验证蛇形命名的字段不存在
        assert "part_of_speech" not in parsed
        assert "core_game" not in parsed
        assert "created_at" not in parsed

    def test_datetime_serialization(self):
        """测试datetime字段序列化"""
        now = datetime(2024, 1, 15, 10, 30, 45)
        response_data = {
            "id": 1,
            "word": "test",
            "phonetic": "/test/",
            "part_of_speech": "noun",
            "core_game": "测试内容",
            "scenario_formal": "思辨场景",
            "scenario_casual": "生活场景",
            "etymology_breakdown": "词根拆解",
            "etymology_story": None,
            "common_mistakes": "常见错误",
            "memory_trick": "记忆技巧",
            "is_golden": False,
            "created_at": now
        }

        response = WordByIdResponse(**response_data)
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)

        # 验证datetime被正确序列化为ISO格式
        assert parsed["createdAt"] == "2024-01-15T10:30:45"

    def test_unicode_cleaning_in_word_by_id(self):
        """测试WordByIdResponse中的Unicode清理"""
        response_data = {
            "id": 1,
            "word": "test",
            "phonetic": "/test/",
            "part_of_speech": "noun",
            "core_game": "测试\udc80内容",
            "scenario_formal": "思辨\udcff场景",
            "scenario_casual": "生活场景",
            "etymology_breakdown": "词根\udc99拆解",
            "etymology_story": None,
            "common_mistakes": "常见错误",
            "memory_trick": "记忆\udc80技巧",
            "is_golden": False,
            "created_at": datetime.now()
        }

        response = WordByIdResponse(**response_data)

        # 验证Unicode字符被清理
        assert response.core_game == "测试内容"
        assert response.scenario_formal == "思辨场景"
        assert response.etymology_breakdown == "词根拆解"
        assert response.memory_trick == "记忆技巧"


class TestWordDetailSerialization:
    """测试WordDetail的JSON序列化"""

    def test_word_detail_serialization(self):
        """测试WordDetail的JSON序列化"""
        now = datetime.now()
        response_data = {
            "id": 1,
            "word": "test",
            "phonetic": "/test/",
            "part_of_speech": "noun",
            "core_game": "测试内容",
            "scenario_formal": "思辨场景",
            "scenario_casual": "生活场景",
            "etymology_breakdown": "词根拆解",
            "etymology_story": "词源故事",
            "common_mistakes": "常见错误",
            "memory_trick": "记忆技巧",
            "is_golden": True,
            "created_at": now
        }

        detail = WordDetail(**response_data)
        json_str = detail.model_dump_json()
        parsed = json.loads(json_str)

        # 验证字段名使用驼峰命名
        assert "partOfSpeech" in parsed
        assert "coreGame" in parsed
        assert "isGolden" in parsed
        assert "createdAt" in parsed


class TestQueryLimitInfoSerialization:
    """测试QueryLimitInfo的JSON序列化"""

    def test_query_limit_info_serialization(self):
        """测试QueryLimitInfo的JSON序列化"""
        response_data = {
            "total_queries": 100,
            "remaining_queries": 80,
            "used_queries": 20,
            "queried_words": [1, 2, 3, 4, 5]
        }

        limit_info = QueryLimitInfo(**response_data)
        json_str = limit_info.model_dump_json()
        parsed = json.loads(json_str)

        # 验证字段名使用驼峰命名
        assert "totalQueries" in parsed
        assert "remainingQueries" in parsed
        assert "usedQueries" in parsed
        assert "queriedWords" in parsed

        # 验证字段值正确
        assert parsed["totalQueries"] == 100
        assert parsed["remainingQueries"] == 80
        assert parsed["usedQueries"] == 20
        assert parsed["queriedWords"] == [1, 2, 3, 4, 5]

    def test_query_limit_info_model_dump_methods(self):
        """测试QueryLimitInfo的不同序列化方法"""
        response_data = {
            "total_queries": 50,
            "remaining_queries": 30,
            "used_queries": 20,
            "queried_words": [1, 2, 3]
        }

        limit_info = QueryLimitInfo(**response_data)

        # 测试默认使用别名
        data_dict = limit_info.model_dump()
        assert "totalQueries" in data_dict
        assert "total_queries" not in data_dict

        # 测试明确指定不使用别名
        data_dict_no_alias = limit_info.model_dump(by_alias=False)
        assert "total_queries" in data_dict_no_alias
        assert "totalQueries" not in data_dict_no_alias


class TestIntegrationWithRealWorldData:
    """集成测试：模拟真实世界数据"""

    def test_complete_word_response_serialization_flow(self):
        """测试完整的单词响应序列化流程"""
        # 模拟真实的单词数据
        word_data = {
            "id": 123,
            "word": "extraordinary",
            "phonetic": "/ɪkˈstrɔːrdəneri/",
            "part_of_speech": "adjective",
            "core_game": "extra(额外) + ordinary(普通) = 超出普通的",
            "scenario_formal": "This is an extraordinary opportunity for research.",
            "scenario_casual": "Wow, that's extraordinary!",
            "etymology_breakdown": "extra- (beyond) + ordinarius (usual)",
            "etymology_story": "源自拉丁语，意为'超出常规的'",
            "common_mistakes": "注意不要写成extra-ordinary",
            "memory_trick": "想象一个超人(extra)站在普通(ordinary)人面前",
            "is_golden": True,
            "remaining_queries": 7
        }

        response = WordQueryResponse(**word_data)

        # 测试JSON序列化
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)

        # 验证所有关键字段都正确序列化
        expected_camel_case_fields = [
            "partOfSpeech", "coreGame", "scenarioFormal", "scenarioCasual",
            "etymologyBreakdown", "etymologyStory", "commonMistakes",
            "memoryTrick", "isGolden", "remainingQueries"
        ]

        for field in expected_camel_case_fields:
            assert field in parsed, f"Missing field: {field}"

        # 验证数据完整性
        assert parsed["word"] == "extraordinary"
        assert parsed["isGolden"] is True
        assert parsed["remainingQueries"] == 7
        assert "extra(额外) + ordinary(普通)" in parsed["coreGame"]

    def test_unicode_contaminated_data_cleaning(self):
        """测试被Unicode污染的数据清理"""
        contaminated_data = {
            "id": 456,
            "word": "test",
            "phonetic": None,
            "part_of_speech": "verb",
            "core_game": "测试内容\udc80\udc99",
            "scenario_formal": "思辨场景\udcff测试",
            "scenario_casual": "生活场景\udc80",
            "etymology_breakdown": "词根拆解\udc99\udcff内容",
            "etymology_story": "词源故事\udc80测试",
            "common_mistakes": "常见错误",
            "memory_trick": "记忆技巧\udc80\udcff",
            "is_golden": False,
            "remaining_queries": 15
        }

        response = WordQueryResponse(**contaminated_data)

        # 验证数据被清理
        assert response.core_game == "测试内容"
        assert response.scenario_formal == "思辨场景测试"
        assert response.scenario_casual == "生活场景"
        assert response.etymology_breakdown == "词根拆解内容"
        assert response.etymology_story == "词源故事测试"
        assert response.memory_trick == "记忆技巧"

        # 验证JSON序列化也是清理后的数据
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["coreGame"] == "测试内容"
        assert parsed["scenarioFormal"] == "思辨场景测试"
        assert parsed["etymologyBreakdown"] == "词根拆解内容"
        assert parsed["memoryTrick"] == "记忆技巧"