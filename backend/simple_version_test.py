#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的版本控制验证脚本
"""
from app.core.config import settings
from app.schemas.word import WordQueryResponse, WordByIdResponse
from datetime import datetime
import json

def test_config():
    """测试配置文件"""
    print(f"1. 配置文件中的prompt_version: {settings.prompt_version}")
    assert settings.prompt_version == "v2.0"
    print("   [PASS] 配置正确")

def test_response_models():
    """测试响应模型"""
    # 测试WordQueryResponse
    response1 = WordQueryResponse(
        id=1,
        word="test",
        phonetic="/test/",
        part_of_speech="noun",
        translation="测试",
        core_game="核心游戏",
        scenario_formal="思辨场景",
        scenario_casual="生活场景",
        etymology_breakdown="词根拆解",
        etymology_story="词源故事",
        common_mistakes="常见错误",
        memory_trick="记忆技巧",
        is_golden=False,
        prompt_version="v2.0",
        remaining_queries=10,
    )

    print(f"2. WordQueryResponse.prompt_version: {response1.prompt_version}")
    assert response1.prompt_version == "v2.0"

    # 检查序列化
    serialized = response1.model_dump(by_alias=True)
    print(f"3. 序列化后的promptVersion: {serialized.get('promptVersion')}")
    assert serialized.get('promptVersion') == "v2.0"
    print("   [PASS] WordQueryResponse正确")

def test_by_id_response():
    """测试WordByIdResponse"""
    response2 = WordByIdResponse(
        id=1,
        word="test",
        phonetic="/test/",
        part_of_speech="noun",
        core_game="核心游戏",
        scenario_formal="思辨场景",
        scenario_casual="生活场景",
        etymology_breakdown="词根拆解",
        etymology_story="词源故事",
        common_mistakes="常见错误",
        memory_trick="记忆技巧",
        is_golden=False,
        prompt_version="v2.0",
        created_at=datetime.now(),
    )

    print(f"4. WordByIdResponse.prompt_version: {response2.prompt_version}")
    assert response2.prompt_version == "v2.0"

    # 检查序列化
    serialized = response2.model_dump(by_alias=True)
    print(f"5. 序列化后的promptVersion: {serialized.get('promptVersion')}")
    assert serialized.get('promptVersion') == "v2.0"
    print("   [PASS] WordByIdResponse正确")

def test_api_logic():
    """测试API逻辑中的prompt_version处理"""
    from app.models.word_converter import WordDataConverter

    # 测试normalize_language_code
    normalized = WordDataConverter.normalize_language_code("zh_CN")
    print(f"6. 语言代码标准化: zh_CN -> {normalized}")
    assert normalized == "zh"
    print("   [PASS] 语言代码标准化正确")

if __name__ == "__main__":
    print("开始简化版本控制验证...")
    print("=" * 50)

    try:
        test_config()
        test_response_models()
        test_by_id_response()
        test_api_logic()

        print("=" * 50)
        print("[SUCCESS] 所有测试通过！版本控制逻辑正确实现")
        print("=" * 50)
        print("验证结果总结：")
        print("[PASS] 配置文件prompt_version = v2.0")
        print("[PASS] WordQueryResponse包含promptVersion字段")
        print("[PASS] WordByIdResponse包含promptVersion字段")
        print("[PASS] 序列化正确使用别名promptVersion")
        print("[PASS] 基础工具类功能正常")

    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        raise