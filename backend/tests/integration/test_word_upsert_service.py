"""
单词数据更新插入服务测试

测试新的UPSERT操作，确保正确处理单词的创建和更新逻辑
"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.models.user import User
from app.models.word import Word
from app.services.word_upsert_service import get_word_upsert_service
from app.services.ai.base import WordManualData, GameBoard, EtymologyBreakdown, CoreGame, GameBoards, CommonMistakes


class TestWordUpsertService:
    """单词数据更新插入服务测试"""

    @pytest.fixture
    def sample_ai_response_data(self):
        """模拟AI响应数据"""
        return {
            "word": "test_word",
            "phonetic": "[test]",
            "translation": "测试单词",
            "part_of_speech": "noun",
            "core_game": {
                "content": "这是一个核心游戏内容",
                "difficulty": "medium"
            },
            "game_boards": {
                "board_a_speculative": {
                    "type": "棋盘A (思辨场)",
                    "name": "学术论坛",
                    "example": "学术场景示例"
                },
                "board_b_life": {
                    "type": "棋盘B (生活场)",
                    "name": "生活场景",
                    "example": "生活场景示例"
                }
            },
            "etymology": {
                "breakdown": {
                    "prefix": {"part": "test-", "meaning": "测试前缀"},
                    "root": {"part": "word", "meaning": "词根"},
                    "suffix": {"part": "", "meaning": ""}
                },
                "story": "词源故事"
            },
            "common_mistakes": {
                "warning": "常见错误警告",
                "avoidance": "避免方法"
            }
        }

    async def test_upsert_create_new_word(
        self, test_db: AsyncSession, sample_ai_response_data
    ):
        """测试创建新单词"""
        upsert_service = await get_word_upsert_service(test_db)

        # 执行upsert操作（应该创建新记录）
        word, was_created = await upsert_service.upsert_word(
            word_text="test_word",
            ai_response_data=sample_ai_response_data,
            language_code="zh_CN",
            source="ai"
        )

        # 验证创建成功
        assert was_created is True
        assert word.word == "test_word"
        assert word.language_code == "zh_CN"
        assert word.source == "ai"
        assert word.translation == "测试单词"
        assert word.core_game_new is not None
        assert word.game_boards is not None
        assert word.is_legacy_format is False  # 应该是新格式

        # 验证JSONB字段正确存储
        assert word.core_game_new["content"] == "这是一个核心游戏内容"
        assert word.game_boards["board_a_speculative"]["name"] == "学术论坛"

    async def test_upsert_update_existing_word(
        self, test_db: AsyncSession, sample_ai_response_data
    ):
        """测试更新现有单词"""
        upsert_service = await get_word_upsert_service(test_db)

        # 1. 先创建一个单词
        word, was_created = await upsert_service.upsert_word(
            word_text="update_test",
            ai_response_data={
                "word": "update_test",
                "translation": "原始翻译"
            },
            language_code="zh_CN",
            source="ai"
        )
        assert was_created is True
        original_id = word.id

        # 2. 更新同一个单词（使用相同AI数据）
        updated_ai_data = sample_ai_response_data.copy()
        updated_ai_data["word"] = "update_test"
        updated_ai_data["translation"] = "更新后的翻译"

        updated_word, was_updated = await upsert_service.upsert_word(
            word_text="update_test",
            ai_response_data=updated_ai_data,
            language_code="zh_CN",
            source="ai"
        )

        # 验证更新逻辑
        assert was_updated is False  # 返回的是否为新创建，不是是否被更新
        assert updated_word.id == original_id  # 应该是同一个记录
        assert updated_word.translation == "更新后的翻译"  # 翻译应该被更新

    async def test_upsert_different_language_versions(
        self, test_db: AsyncSession, sample_ai_response_data
    ):
        """测试同一单词的不同语言版本"""
        upsert_service = await get_word_upsert_service(test_db)

        # 1. 创建中文版本
        zh_word, zh_created = await upsert_service.upsert_word(
            word_text="multilang_test",
            ai_response_data={**sample_ai_response_data, "translation": "中文翻译"},
            language_code="zh_CN",
            source="ai"
        )

        # 2. 创建英文版本
        en_word, en_created = await upsert_service.upsert_word(
            word_text="multilang_test",
            ai_response_data={**sample_ai_response_data, "translation": "English translation"},
            language_code="en",
            source="ai"
        )

        # 验证创建了两个不同记录
        assert zh_created is True
        assert en_created is True
        assert zh_word.id != en_word.id
        assert zh_word.language_code == "zh_CN"
        assert en_word.language_code == "en"
        assert zh_word.translation == "中文翻译"
        assert en_word.translation == "English translation"

    async def test_get_word_with_fallback(
        self, test_db: AsyncSession, sample_ai_response_data
    ):
        """测试单词查询降级机制"""
        upsert_service = await get_word_upsert_service(test_db)

        # 1. 创建英文版本的单词
        en_word, _ = await upsert_service.upsert_word(
            word_text="fallback_test",
            ai_response_data={**sample_ai_response_data, "translation": "English version"},
            language_code="en",
            source="ai"
        )

        # 2. 查询中文版本（应该降级到英文版本）
        found_word = await upsert_service.get_word_with_fallback(
            "fallback_test", "zh_CN"
        )

        # 应该找到英文版本作为降级
        assert found_word is not None
        assert found_word.id == en_word.id
        assert found_word.language_code == "en"

    async def test_should_update_word_data(
        self, test_db: AsyncSession, sample_ai_response_data
    ):
        """测试单词数据更新判断逻辑"""
        upsert_service = await get_word_upsert_service(test_db)

        # 1. 创建旧格式单词
        legacy_word_data = {
            "word": "legacy_test",
            "translation": "旧格式单词"
        }

        # 直接创建旧格式的单词（模拟）
        legacy_word = Word(
            word="legacy_test",
            language_code="zh_CN",
            translation="旧格式单词",
            is_legacy_format=True,
            core_game="旧格式内容",
            scenario_formal="思辨场景",
            scenario_casual="生活场景",
            etymology_breakdown="词根拆解",
            common_mistakes="常见错误",
            memory_trick="记忆技巧",
            source="ai"
        )
        async_session.add(legacy_word)
        await async_session.commit()
        await async_session.refresh(legacy_word)

        # 2. 测试是否需要更新
        should_update = await upsert_service.should_update_word_data(
            legacy_word, "zh_CN"
        )
        assert should_update is True  # 旧格式应该需要更新

        # 3. 创建新格式单词
        new_format_word, _ = await upsert_service.upsert_word(
            word_text="new_format_test",
            ai_response_data=sample_ai_response_data,
            language_code="zh_CN",
            source="ai"
        )

        # 4. 测试新格式单词是否需要更新
        should_update_new = await upsert_service.should_update_word_data(
            new_format_word, "zh_CN"
        )
        assert should_update_new is False  # 新格式应该不需要更新

    async def test_get_word_statistics(
        self, test_db: AsyncSession, sample_ai_response_data
    ):
        """测试单词统计功能"""
        upsert_service = await get_word_upsert_service(test_db)

        # 创建多个测试单词
        await upsert_service.upsert_word(
            word_text="stats_test_1",
            ai_response_data=sample_ai_response_data,
            language_code="zh_CN",
            source="ai"
        )

        await upsert_service.upsert_word(
            word_text="stats_test_2",
            ai_response_data=sample_ai_response_data,
            language_code="en",
            source="ai"
        )

        # 创建黄金手册单词
        golden_data = sample_ai_response_data.copy()
        golden_ai_data = WordManualData(**golden_data)

        golden_word_dict = WordDataConverter.convert_ai_response_to_word(
            golden_ai_data.model_dump(), "zh_CN", "manual"
        )
        golden_word = Word(**golden_word_dict, is_golden=True)
        async_session.add(golden_word)
        await async_session.commit()

        # 获取统计信息
        stats = await upsert_service.get_word_statistics()

        # 验证统计信息
        assert "total_words" in stats
        assert "by_language" in stats
        assert "format_stats" in stats
        assert "golden_stats" in stats

        assert stats["total_words"] >= 3
        assert "zh_CN" in stats["by_language"]
        assert "en" in stats["by_language"]
        assert stats["by_language"]["zh_CN"] >= 2
        assert stats["by_language"]["en"] >= 1