"""
单词数据更新插入服务

实现智能的UPSERT操作，解决重复数据存储问题
支持同一单词的多语言版本管理和数据格式升级
"""
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from sqlalchemy import select, and_, func

from app.models.word import Word
from app.models.word_converter import WordDataConverter
from app.core.logging import get_logger, log_with_context

logger = get_logger(__name__)


class WordUpsertService:
    """单词数据更新插入服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_word(
        self,
        word_text: str,
        ai_response_data: Dict[str, Any],
        language_code: str = "zh",
        source: str = "ai",
        prompt_version: str = None  # 将在方法内部使用配置值
    ) -> Tuple[Word, bool]:
        """
        智能插入或更新单词数据

        Args:
            word_text: 单词文本
            ai_response_data: AI响应的原始数据
            language_code: 语言代码
            source: 数据来源
            prompt_version: Prompt版本

        Returns:
            Tuple[Word, bool]: (单词对象, 是否为新创建)

        策略：
        1. 查找现有记录 (word + language_code)
        2. 存在 → 智能合并更新
        3. 不存在 → 创建新记录
        """
        # 如果未提供prompt_version，使用配置中的默认值
        if prompt_version is None:
            prompt_version = settings.prompt_version

        log_with_context(
            logger, "info", "Starting word upsert operation",
            word=word_text, language=language_code, source=source, prompt_version=prompt_version
        )

        # 1. 查找现有记录
        existing_word = await self._find_existing_word(word_text, language_code)

        if existing_word:
            # 2. 更新现有记录
            updated_word, was_updated = await self._update_existing_word(
                existing_word, ai_response_data, prompt_version
            )

            log_with_context(
                logger, "info", "Word update completed",
                word=word_text, language=language_code,
                was_updated=was_updated, word_id=updated_word.id
            )

            return updated_word, False
        else:
            # 3. 创建新记录
            created_word = await self._create_new_word(
                word_text, ai_response_data, language_code, source, prompt_version
            )

            log_with_context(
                logger, "info", "New word created",
                word=word_text, language=language_code,
                word_id=created_word.id
            )

            return created_word, True

    async def _find_existing_word(
        self, word_text: str, language_code: str
    ) -> Optional[Word]:
        """查找现有单词记录"""
        result = await self.db.execute(
            select(Word)
            .where(and_(
                Word.word == word_text,
                Word.language_code == language_code
            ))
        )
        return result.scalar_one_or_none()

    async def _update_existing_word(
        self, existing_word: Word, ai_response_data: Dict[str, Any], prompt_version: str
    ) -> Tuple[Word, bool]:
        """
        智能更新现有单词记录

        策略：
        1. 保留已有黄金手册状态
        2. 补充缺失的新格式字段
        3. 更新Prompt版本和时间戳
        4. 保持向后兼容性
        """
        was_updated = False

        # 转换AI数据为标准格式
        standard_data = WordDataConverter.convert_ai_response_to_word(
            ai_response_data, existing_word.language_code, "update"
        )

        # 1. 更新基本字段（如果为空或版本过时）
        if not existing_word.phonetic and standard_data.get("phonetic"):
            existing_word.phonetic = standard_data["phonetic"]
            was_updated = True

        if not existing_word.part_of_speech and standard_data.get("part_of_speech"):
            existing_word.part_of_speech = standard_data["part_of_speech"]
            was_updated = True

        # 2. 更新翻译字段（优先使用AI新生成的）
        if standard_data.get("translation") and standard_data["translation"] != existing_word.translation:
            existing_word.translation = standard_data["translation"]
            was_updated = True

        # 3. 补充新格式字段（如果缺失）
        new_format_fields = [
            ("core_game_new", "core_game"),
            ("game_boards", "game_boards"),
            ("etymology_new", "etymology"),
            ("common_mistakes_new", "common_mistakes")
        ]

        for new_field, legacy_field in new_format_fields:
            if not getattr(existing_word, new_field) and standard_data.get(new_field):
                setattr(existing_word, new_field, standard_data[new_field])
                was_updated = True

        # 4. 标记为新格式（如果所有新字段都已填充）
        if (existing_word.core_game_new and existing_word.game_boards and
            existing_word.etymology_new and existing_word.common_mistakes_new and
            existing_word.is_legacy_format):

            existing_word.is_legacy_format = False
            was_updated = True
            log_with_context(
                logger, "info", "Word migrated to new format",
                word=existing_word.word, language=existing_word.language_code
            )

        # 5. 更新元数据
        if was_updated:
            existing_word.updated_at = datetime.utcnow()
            existing_word.prompt_version = prompt_version

        await self.db.commit()
        await self.db.refresh(existing_word)

        return existing_word, was_updated

    async def _create_new_word(
        self,
        word_text: str,
        ai_response_data: Dict[str, Any],
        language_code: str,
        source: str,
        prompt_version: str
    ) -> Word:
        """创建新的单词记录"""
        # 转换AI数据为数据库格式
        word_data = WordDataConverter.convert_ai_response_to_word(
            ai_response_data, language_code, source
        )

        # 设置基本字段
        # 使用转换后的语言代码，确保符合数据库约束
        db_language_code = WordDataConverter.normalize_language_code(language_code)

        word_data.update({
            "word": word_text,
            "language_code": db_language_code,
            "source": source,
            "prompt_version": prompt_version,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

        new_word = Word(**word_data)
        self.db.add(new_word)
        await self.db.commit()
        await self.db.refresh(new_word)

        return new_word

    async def get_word_with_fallback(
        self,
        word_text: str,
        preferred_language: str = "zh_CN"
    ) -> Optional[Word]:
        """
        智能单词查询，支持语言降级

        优先级：
        1. 指定语言的单词
        2. 英文原版单词
        3. 任何可用的版本
        """
        log_with_context(
            logger, "info", "Querying word with fallback",
            word=word_text, preferred_language=preferred_language
        )

        # 1. 首选：指定语言
        word = await self._find_existing_word(word_text, preferred_language)
        if word:
            return word

        # 2. 备选：英文原版
        word = await self._find_existing_word(word_text, "en")
        if word:
            log_with_context(
                logger, "info", "Using English fallback for word",
                word=word_text, fallback_language="en"
            )
            return word

        # 3. 兜底：任何可用版本（优先黄金手册）
        result = await self.db.execute(
            select(Word)
            .where(Word.word == word_text)
            .order_by(
                Word.is_golden.desc(),
                Word.language_code.asc()  # 优先返回语言代码较小的版本
            )
        )
        word = result.scalar_one_or_none()

        if word:
            log_with_context(
                logger, "info", "Using any available version for word",
                word=word_text, found_language=word.language_code,
                is_golden=word.is_golden
            )

        return word

    async def should_update_word_data(
        self, word: Word, preferred_language: str
    ) -> bool:
        """
        检查是否需要更新单词数据

        判断标准：
        1. 语言不匹配（需要补充新语言版本）
        2. 数据格式过时（仍为legacy格式）
        3. 新格式字段缺失（部分迁移）
        4. Prompt版本过时
        """
        # 1. 语言不匹配
        if word.language_code != preferred_language and preferred_language != "auto":
            return True

        # 2. 数据格式过时
        if word.is_legacy_format:
            return True

        # 3. 新格式字段缺失
        new_format_fields = [
            word.core_game_new, word.game_boards,
            word.etymology_new, word.common_mistakes_new
        ]
        if not all(new_format_fields):
            return True

        # 4. Prompt版本过时（可根据需要配置）
        if word.prompt_version and word.prompt_version < "v1.0":
            return True

        return False

    async def get_word_statistics(self) -> Dict[str, Any]:
        """获取单词数据统计信息"""
        stats = {}

        # 总单词数
        result = await self.db.execute(select(Word).count())
        stats["total_words"] = result.scalar()

        # 按语言分组统计
        result = await self.db.execute(
            select(Word.language_code, func.count(Word.id))
            .group_by(Word.language_code)
        )
        stats["by_language"] = dict(result.all())

        # 新旧格式统计
        result = await self.db.execute(
            select(Word.is_legacy_format, func.count(Word.id))
            .group_by(Word.is_legacy_format)
        )
        legacy_stats = dict(result.all())
        stats["format_stats"] = {
            "legacy": legacy_stats.get(True, 0),
            "new_format": legacy_stats.get(False, 0)
        }

        # 黄金手册统计
        result = await self.db.execute(
            select(Word.is_golden, func.count(Word.id))
            .group_by(Word.is_golden)
        )
        golden_stats = dict(result.all())
        stats["golden_stats"] = {
            "golden": golden_stats.get(True, 0),
            "regular": golden_stats.get(False, 0)
        }

        return stats


# 便捷函数
async def get_word_upsert_service(db: AsyncSession) -> WordUpsertService:
    """获取单词更新插入服务实例"""
    return WordUpsertService(db)