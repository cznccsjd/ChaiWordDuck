#!/usr/bin/env python3
"""
单词多语言迁移测试脚本

测试新的多语言Prompt支持和数据迁移功能
"""
import json
import pytest
from typing import Dict, Any

from app.core.database import get_db, engine
from app.models.word import Word
from app.models.word_converter import WordDataConverter
from app.services.word_migration_service import get_migration_service
from app.schemas.word import WordCreate, WordResponse


def test_word_converter_basic():
    """测试WordDataConverter基本功能"""
    print("=== 测试WordDataConverter基本功能 ===")

    # 测试支持的语言
    supported_langs = WordDataConverter.get_supported_languages()
    print(f"支持的语言数量: {len(supported_langs)}")
    assert 'en' in supported_langs
    assert 'zh_CN' in supported_langs

    # 测试语言验证
    assert WordDataConverter.validate_language_code('en') is True
    assert WordDataConverter.validate_language_code('zh_CN') is True
    assert WordDataConverter.validate_language_code('invalid') is False
    print("语言验证测试通过")

    # 测试AI响应转换
    ai_response = {
        "word": "test",
        "phonetic": "/test/",
        "translation": "测试",
        "part_of_speech": "noun",
        "core_game": {"content": "测试核心游戏"},
        "game_boards": {
            "board_a_speculative": {
                "type": "棋盘A (思辨场)",
                "name": "思辨场景",
                "example": "测试思辨示例"
            },
            "board_b_life": {
                "type": "棋盘B (生活场)",
                "name": "生活场景",
                "example": "测试生活示例"
            }
        },
        "etymology": {
            "breakdown": {
                "prefix": {"part": "", "meaning": ""},
                "root": {"part": "test", "meaning": "测试"},
                "suffix": {"part": "", "meaning": ""}
            },
            "story": "测试词源故事"
        },
        "common_mistakes": {
            "warning": "测试警告",
            "avoidance": "测试避免方法"
        },
        "memory_trick": "测试记忆技巧"
    }

    word_data = WordDataConverter.convert_ai_response_to_word(ai_response, 'zh_CN')
    assert word_data['word'] == 'test'
    assert word_data['translation'] == '测试'
    assert word_data['language_code'] == 'zh_CN'
    assert word_data['is_legacy_format'] is False
    print("AI响应转换测试通过")


def test_database_schema():
    """测试数据库schema扩展"""
    print("\n=== 测试数据库Schema扩展 ===")

    db = next(get_db())

    try:
        # 测试创建新格式单词
        new_word_data = {
            "word": "migration_test",
            "phonetic": "/test/",
            "part_of_speech": "noun",
            "core_game": "测试核心游戏",
            "scenario_formal": "测试思辨场景",
            "scenario_casual": "测试生活场景",
            "etymology_breakdown": "test-词根",
            "common_mistakes": "测试错误",
            "memory_trick": "测试技巧",
            "translation": "迁移测试",
            "language_code": "zh_CN",
            "prompt_version": "v2.0",
            "is_legacy_format": False,
            "core_game_new": {"content": "结构化核心游戏"},
            "game_boards": {
                "board_a_speculative": {"type": "思辨场", "name": "思辨", "example": "思辨示例"},
                "board_b_life": {"type": "生活场", "name": "生活", "example": "生活示例"}
            },
            "etymology_new": {
                "breakdown": {"prefix": {}, "root": {"part": "test", "meaning": "测试"}, "suffix": {}},
                "story": "测试故事"
            },
            "common_mistakes_new": {"warning": "警告", "avoidance": "避免方法"}
        }

        word = Word(**new_word_data)
        db.add(word)
        db.commit()
        db.refresh(word)

        # 验证数据保存
        assert word.word == "migration_test"
        assert word.language_code == "zh_CN"
        assert word.is_legacy_format is False
        assert word.core_game_new is not None
        assert isinstance(word.core_game_new, dict)

        # 测试向后兼容方法
        display_data = word.get_display_data()
        assert display_data['word'] == 'migration_test'
        assert display_data['language_code'] == 'zh_CN'
        assert display_data['is_legacy_format'] is False

        # 测试兼容性方法
        core_content = word.get_core_game_content()
        assert isinstance(core_content, str)

        game_boards = word.get_game_boards_data()
        assert isinstance(game_boards, dict)
        assert 'board_a_speculative' in game_boards

        etymology = word.get_etymology_data()
        assert isinstance(etymology, dict)
        assert 'breakdown' in etymology

        mistakes = word.get_common_mistakes_data()
        assert isinstance(mistakes, dict)
        assert 'warning' in mistakes

        print("数据库Schema扩展测试通过")

        # 清理测试数据
        db.delete(word)
        db.commit()

    finally:
        db.close()


def test_legacy_to_new_format():
    """测试旧格式到新格式转换"""
    print("\n=== 测试旧格式到新格式转换 ===")

    db = next(get_db())

    try:
        # 创建旧格式单词
        legacy_word_data = {
            "word": "legacy_test",
            "phonetic": "/test/",
            "part_of_speech": "noun",
            "core_game": "旧格式核心游戏",
            "scenario_formal": "旧格式思辨场景",
            "scenario_casual": "旧格式生活场景",
            "etymology_breakdown": "legacy-词根",
            "etymology_story": "旧格式故事",
            "common_mistakes": "旧格式错误",
            "memory_trick": "旧格式技巧",
            "source": "test"
        }

        word = Word(**legacy_word_data)
        word.is_legacy_format = True  # 确保标记为旧格式
        db.add(word)
        db.commit()
        db.refresh(word)

        # 测试转换
        converter = WordDataConverter()
        new_format = converter.legacy_to_new_format(word)

        assert new_format['word'] == 'legacy_test'
        assert new_format['is_legacy_format'] is True
        assert new_format['language_code'] == 'en'  # 默认语言
        assert isinstance(new_format['core_game'], dict)
        assert isinstance(new_format['game_boards'], dict)
        assert isinstance(new_format['etymology'], dict)
        assert isinstance(new_format['common_mistakes'], dict)

        print("旧格式转换测试通过")

        # 清理测试数据
        db.delete(word)
        db.commit()

    finally:
        db.close()


def test_migration_service():
    """测试迁移服务"""
    print("\n=== 测试迁移服务 ===")

    db = next(get_db())
    migration_service = get_migration_service(db)

    try:
        # 创建测试数据（旧格式）
        test_words = [
            {
                "word": "migration_test_1",
                "phonetic": "/test1/",
                "core_game": "测试核心游戏1",
                "scenario_formal": "测试思辨场景1",
                "scenario_casual": "测试生活场景1",
                "etymology_breakdown": "test1-词根",
                "common_mistakes": "测试错误1",
                "memory_trick": "测试技巧1",
                "source": "test"
            },
            {
                "word": "migration_test_2",
                "phonetic": "/test2/",
                "core_game": "测试核心游戏2",
                "scenario_formal": "测试思辨场景2",
                "scenario_casual": "测试生活场景2",
                "etymology_breakdown": "test2-词根",
                "common_mistakes": "测试错误2",
                "memory_trick": "测试技巧2",
                "source": "test"
            }
        ]

        words = []
        for word_data in test_words:
            word = Word(**word_data)
            word.is_legacy_format = True
            db.add(word)
            words.append(word)

        db.commit()
        db.refresh_all()

        # 获取迁移前统计
        stats_before = migration_service.get_migration_stats()
        print(f"迁移前统计: {stats_before}")

        # 迁移单个单词
        word_to_migrate = words[0]
        result = migration_service.migrate_single_word(word_to_migrate.id)
        assert result is not None
        assert result.is_legacy_format is False

        # 批量迁移剩余单词
        batch_result = migration_service.migrate_batch(batch_size=10)
        print(f"批量迁移结果: {batch_result}")
        assert batch_result['total_migrated'] > 0

        # 获取迁移后统计
        stats_after = migration_service.get_migration_stats()
        print(f"迁移后统计: {stats_after}")
        assert stats_after['migrated_words'] > stats_before['migrated_words']

        # 验证迁移完整性
        validation_result = migration_service.validate_migration_integrity()
        print(f"验证结果: {validation_result}")
        assert validation_result['invalid_migrations'] == 0

        print("迁移服务测试通过")

        # 清理测试数据
        for word in words:
            db.delete(word)
        db.commit()

    finally:
        db.close()


def test_api_compatibility():
    """测试API兼容性"""
    print("\n=== 测试API兼容性 ===")

    db = next(get_db())

    try:
        # 创建新格式单词
        new_word_data = {
            "word": "api_test",
            "phonetic": "/api-test/",
            "part_of_speech": "noun",
            "core_game": "API测试核心游戏",
            "scenario_formal": "API测试思辨场景",
            "scenario_casual": "API测试生活场景",
            "etymology_breakdown": "api-test-词根",
            "common_mistakes": "API测试错误",
            "memory_trick": "API测试技巧",
            "translation": "API测试",
            "language_code": "zh_CN",
            "prompt_version": "v2.0",
            "is_legacy_format": False,
            "core_game_new": {"content": "结构化API核心游戏"},
            "game_boards": {
                "board_a_speculative": {"type": "思辨场", "name": "API思辨", "example": "API思辨示例"},
                "board_b_life": {"type": "生活场", "name": "API生活", "example": "API生活示例"}
            },
            "etymology_new": {
                "breakdown": {"prefix": {}, "root": {"part": "api", "meaning": "API"}, "suffix": {}},
                "story": "API测试故事"
            },
            "common_mistakes_new": {"warning": "API警告", "avoidance": "API避免方法"}
        }

        word = Word(**new_word_data)
        db.add(word)
        db.commit()
        db.refresh(word)

        # 测试API格式转换
        api_dict_new_format = word.to_api_dict(include_legacy_fields=False)
        assert 'core_game' in api_dict_new_format
        assert 'game_boards' in api_dict_new_format
        assert 'core_game_content' not in api_dict_new_format  # 不包含向后兼容字段

        api_dict_legacy = word.to_api_dict(include_legacy_fields=True)
        assert 'core_game' in api_dict_legacy
        assert 'game_boards' in api_dict_legacy
        assert 'core_game_content' in api_dict_legacy  # 包含向后兼容字段
        assert 'scenario_formal' in api_dict_legacy

        print("API兼容性测试通过")

        # 清理测试数据
        db.delete(word)
        db.commit()

    finally:
        db.close()


def run_all_tests():
    """运行所有测试"""
    print("开始运行多语言迁移测试...")

    try:
        test_word_converter_basic()
        test_database_schema()
        test_legacy_to_new_format()
        test_migration_service()
        test_api_compatibility()

        print("\n🎉 所有测试通过！多语言Prompt支持扩展方案验证成功。")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()