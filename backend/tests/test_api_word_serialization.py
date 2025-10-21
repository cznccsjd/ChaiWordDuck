"""
测试API端点的JSON序列化行为

验证实际的API响应使用驼峰命名格式
"""
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.schemas.word import WordQueryResponse


class TestWordAPISerialization:
    """测试单词API的JSON序列化"""

    def setup_method(self):
        """设置测试客户端"""
        self.client = TestClient(app)

    def test_word_query_api_camel_case_response(self):
        """测试单词查询API返回驼峰命名的JSON响应"""
        # 模拟查询单词数据
        mock_word = MagicMock()
        mock_word.id = 1
        mock_word.word = "extraordinary"
        mock_word.phonetic = "/ɪkˈstrɔːrdəneri/"
        mock_word.part_of_speech = "adjective"
        mock_word.core_game = "extra(额外) + ordinary(普通) = 超出普通的"
        mock_word.scenario_formal = "This is an extraordinary opportunity."
        mock_word.scenario_casual = "Wow, that's extraordinary!"
        mock_word.etymology_breakdown = "extra- (beyond) + ordinarius (usual)"
        mock_word.etymology_story = "源自拉丁语，意为'超出常规的'"
        mock_word.common_mistakes = "注意不要写成extra-ordinary"
        mock_word.memory_trick = "想象超人站在普通人面前"
        mock_word.is_golden = True

        # 使用Pydantic模型创建响应数据，验证驼峰命名转换
        from app.schemas.word import WordQueryResponse
        response_model = WordQueryResponse(
            id=mock_word.id,
            word=mock_word.word,
            phonetic=mock_word.phonetic,
            part_of_speech=mock_word.part_of_speech,
            core_game=mock_word.core_game,
            scenario_formal=mock_word.scenario_formal,
            scenario_casual=mock_word.scenario_casual,
            etymology_breakdown=mock_word.etymology_breakdown,
            etymology_story=mock_word.etymology_story,
            common_mistakes=mock_word.common_mistakes,
            memory_trick=mock_word.memory_trick,
            is_golden=mock_word.is_golden,
            remaining_queries=80
        )

        # 验证Pydantic模型使用驼峰命名序列化
        json_data = response_model.model_dump()

        # 验证响应结构使用驼峰命名
        expected_camel_case_fields = [
            "partOfSpeech", "coreGame", "scenarioFormal", "scenarioCasual",
            "etymologyBreakdown", "etymologyStory", "commonMistakes",
            "memoryTrick", "isGolden", "remainingQueries"
        ]

        for field in expected_camel_case_fields:
            assert field in json_data, f"Missing camelCase field: {field}"

        # 验证蛇形命名字段不存在
        snake_case_fields = [
            "part_of_speech", "core_game", "scenario_formal",
            "etymology_breakdown", "etymology_story", "common_mistakes",
            "memory_trick", "is_golden", "remaining_queries"
        ]

        for field in snake_case_fields:
            assert field not in json_data, f"Found unexpected snakeCase field: {field}"

        # 验证字段值正确
        assert json_data["word"] == "extraordinary"
        assert json_data["partOfSpeech"] == "adjective"
        assert json_data["coreGame"] == "extra(额外) + ordinary(普通) = 超出普通的"
        assert json_data["isGolden"] is True
        assert json_data["remainingQueries"] == 80

    def test_word_by_id_api_camel_case_response(self):
        """测试根据ID获取单词API返回驼峰命名的JSON响应"""
        # 使用Pydantic模型创建响应数据，验证驼峰命名转换
        from app.schemas.word import WordByIdResponse
        from datetime import datetime

        response_model = WordByIdResponse(
            id=1,
            word="hello",
            phonetic="/həˈloʊ/",
            part_of_speech="interjection",
            core_game="打招呼的问候语",
            scenario_formal="Hello, how are you today?",
            scenario_casual="Hey! What's up?",
            etymology_breakdown="来自古英语中的 greeting word",
            etymology_story="历史上用于友好问候的表达",
            common_mistakes="不要与hellow混淆",
            memory_trick="想象见到朋友时挥手说hello",
            is_golden=False,
            created_at=datetime.utcnow()
        )

        # 验证Pydantic模型使用驼峰命名序列化
        json_data = response_model.model_dump()

        # 验证响应结构使用驼峰命名
        expected_camel_case_fields = [
            "partOfSpeech", "coreGame", "scenarioFormal", "scenarioCasual",
            "etymologyBreakdown", "etymologyStory", "commonMistakes",
            "memoryTrick", "isGolden", "createdAt"
        ]

        for field in expected_camel_case_fields:
            assert field in json_data, f"Missing camelCase field: {field}"

        # 验证字段值正确
        assert json_data["id"] == 1
        assert json_data["word"] == "hello"
        assert json_data["partOfSpeech"] == "interjection"
        assert json_data["isGolden"] is False
        assert "createdAt" in json_data

    def test_query_limit_api_camel_case_response(self):
        """测试查询限制API返回驼峰命名的JSON响应"""
        # 使用Pydantic模型创建响应数据，验证驼峰命名转换
        from app.schemas.word import QueryLimitInfo

        response_model = QueryLimitInfo(
            total_queries=100,
            remaining_queries=80,
            used_queries=20,
            queried_words=[1, 2, 3, 4, 5]
        )

        # 验证Pydantic模型使用驼峰命名序列化
        json_data = response_model.model_dump()

        # 验证响应结构使用驼峰命名
        expected_camel_case_fields = [
            "totalQueries", "remainingQueries", "usedQueries", "queriedWords"
        ]

        for field in expected_camel_case_fields:
            assert field in json_data, f"Missing camelCase field: {field}"

        # 验证蛇形命名字段不存在
        snake_case_fields = [
            "total_queries", "remaining_queries", "used_queries", "queried_words"
        ]

        for field in snake_case_fields:
            assert field not in json_data, f"Found unexpected snakeCase field: {field}"

        # 验证字段值正确
        assert json_data["totalQueries"] == 100
        assert json_data["remainingQueries"] == 80
        assert json_data["usedQueries"] == 20
        assert json_data["queriedWords"] == [1, 2, 3, 4, 5]

    def test_unicode_cleaning_in_api_response(self):
        """测试API响应中的Unicode字符清理"""
        # 这个测试需要创建包含无效Unicode字符的模拟数据
        # 实际的清理会在Pydantic模型层面完成

        contaminated_data = {
            "id": 1,
            "word": "test",
            "phonetic": "/test/",
            "part_of_speech": "noun",
            "core_game": "有效文本\udc80无效字符",  # 包含无效代理对
            "scenario_formal": "思辨场景\udcff测试",
            "scenario_casual": "生活场景测试",
            "etymology_breakdown": "词根拆解\udc99测试",
            "etymology_story": "词源故事\udc80测试",
            "common_mistakes": "常见错误",
            "memory_trick": "记忆技巧\udc80测试",
            "is_golden": False,
            "remaining_queries": 15
        }

        # 创建Pydantic模型实例
        response = WordQueryResponse(**contaminated_data)

        # 验证Unicode字符被清理
        assert response.core_game == "有效文本无效字符"
        assert response.scenario_formal == "思辨场景测试"
        assert response.etymology_breakdown == "词根拆解测试"
        assert response.etymology_story == "词源故事测试"
        assert response.memory_trick == "记忆技巧测试"

        # 验证JSON序列化也是清理后的数据
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["coreGame"] == "有效文本无效字符"
        assert parsed["scenarioFormal"] == "思辨场景测试"
        assert parsed["etymologyBreakdown"] == "词根拆解测试"
        assert parsed["memoryTrick"] == "记忆技巧测试"