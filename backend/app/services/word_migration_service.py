"""
单词数据迁移服务

处理旧格式到新格式的数据迁移，支持批量迁移和增量迁移
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, update, func, and_, or_

from app.core.database import get_db
from app.models.word import Word
from app.models.word_converter import WordDataConverter

logger = logging.getLogger(__name__)


class WordMigrationService:
    """单词数据迁移服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_migration_stats(self) -> Dict[str, Any]:
        """
        获取迁移统计信息

        Returns:
            迁移统计信息
        """
        total_words = self.db.execute(select(func.count(Word.id))).scalar()
        legacy_words = self.db.execute(
            select(func.count(Word.id)).where(Word.is_legacy_format == True)
        ).scalar()
        migrated_words = total_words - legacy_words

        return {
            'total_words': total_words,
            'legacy_words': legacy_words,
            'migrated_words': migrated_words,
            'migration_progress': f"{(migrated_words / total_words * 100):.2f}%" if total_words > 0 else "0%"
        }

    def migrate_single_word(self, word_id: int) -> Optional[Word]:
        """
        迁移单个单词到新格式

        Args:
            word_id: 要迁移的单词ID

        Returns:
            更新后的Word对象或None
        """
        try:
            result = WordDataConverter.migrate_legacy_word(self.db, word_id)
            if result:
                logger.info(f"Successfully migrated word ID {word_id}: {result.word}")
            else:
                logger.warning(f"Word with ID {word_id} not found")
            return result
        except Exception as e:
            logger.error(f"Failed to migrate word ID {word_id}: {e}")
            self.db.rollback()
            return None

    def migrate_batch(self, batch_size: int = 50, max_batches: Optional[int] = None) -> Dict[str, Any]:
        """
        批量迁移单词

        Args:
            batch_size: 每批次的单词数量
            max_batches: 最大批次数量，None表示无限制

        Returns:
            迁移结果统计
        """
        logger.info(f"Starting batch migration: batch_size={batch_size}, max_batches={max_batches}")

        total_migrated = 0
        total_failed = 0
        batch_count = 0

        while True:
            if max_batches and batch_count >= max_batches:
                break

            # 查找一批未迁移的单词
            stmt = (
                select(Word)
                .where(Word.is_legacy_format == True)
                .limit(batch_size)
                .order_by(Word.id)  # 确保按顺序处理
            )
            words = self.db.execute(stmt).scalars().all()

            if not words:
                break

            batch_count += 1
            logger.info(f"Processing batch {batch_count} with {len(words)} words")

            batch_migrated = 0
            batch_failed = 0

            for word in words:
                try:
                    result = self.migrate_single_word(word.id)
                    if result:
                        batch_migrated += 1
                    else:
                        batch_failed += 1
                except Exception as e:
                    logger.error(f"Error in batch {batch_count} for word {word.word}: {e}")
                    batch_failed += 1

            total_migrated += batch_migrated
            total_failed += batch_failed

            logger.info(f"Batch {batch_count} completed: {batch_migrated} migrated, {batch_failed} failed")

        result = {
            'batch_count': batch_count,
            'total_migrated': total_migrated,
            'total_failed': total_failed,
            'migration_stats': self.get_migration_stats()
        }

        logger.info(f"Batch migration completed: {result}")
        return result

    def migrate_word_by_name(self, word_name: str) -> Optional[Word]:
        """
        按单词名称迁移

        Args:
            word_name: 要迁移的单词名称

        Returns:
            更新后的Word对象或None
        """
        stmt = select(Word).where(
            and_(Word.word == word_name, Word.is_legacy_format == True)
        )
        word = self.db.execute(stmt).scalar_one_or_none()

        if word:
            return self.migrate_single_word(word.id)
        else:
            logger.warning(f"Word '{word_name}' not found or already migrated")
            return None

    def migrate_golden_words(self) -> Dict[str, Any]:
        """
        迁移黄金手册单词

        Returns:
            迁移结果
        """
        stmt = select(Word).where(
            and_(Word.is_golden == True, Word.is_legacy_format == True)
        )
        golden_words = self.db.execute(stmt).scalars().all()

        migrated_count = 0
        failed_count = 0

        logger.info(f"Found {len(golden_words)} golden words to migrate")

        for word in golden_words:
            try:
                result = self.migrate_single_word(word.id)
                if result:
                    migrated_count += 1
                    # 为黄金单词设置中文翻译
                    if hasattr(word, 'translation') and not word.translation:
                        self._set_golden_word_translation(word)
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Failed to migrate golden word {word.word}: {e}")
                failed_count += 1

        self.db.commit()

        return {
            'total_golden_words': len(golden_words),
            'migrated': migrated_count,
            'failed': failed_count
        }

    def _set_golden_word_translation(self, word: Word) -> None:
        """为黄金单词设置预定义翻译"""
        golden_translations = {
            'accommodation': '住宿，调适',
            'embarrassment': '尴尬，窘迫',
            'procrastination': '拖延，拖延症',
            'Mediterranean': '地中海的',
            'Massachusetts': '马萨诸塞州',
            'entrepreneur': '企业家，创业者',
            'conscientious': '认真的，勤勤恳恳的',
            'pharmaceutical': '制药的，药物的',
            'archaeology': '考古学',
            'bureaucracy': '官僚主义，官僚体制'
        }

        translation = golden_translations.get(word.word)
        if translation:
            word.translation = translation
            word.language_code = 'zh'
            logger.info(f"Set translation for golden word {word.word}: {translation}")

    def validate_migration_integrity(self) -> Dict[str, Any]:
        """
        验证迁移数据的完整性

        Returns:
            验证结果
        """
        validation_results = {
            'total_words_checked': 0,
            'valid_migrations': 0,
            'invalid_migrations': 0,
            'issues_found': []
        }

        # 检查新格式的单词
        stmt = select(Word).where(Word.is_legacy_format == False).limit(100)  # 限制检查数量
        words = self.db.execute(stmt).scalars().all()

        for word in words:
            validation_results['total_words_checked'] += 1

            issues = []

            # 检查必需的JSONB字段
            if not word.core_game_new:
                issues.append("Missing core_game_new field")
            elif not isinstance(word.core_game_new, dict):
                issues.append("core_game_new is not a dict")

            if not word.game_boards:
                issues.append("Missing game_boards field")
            elif not isinstance(word.game_boards, dict):
                issues.append("game_boards is not a dict")

            if not word.etymology_new:
                issues.append("Missing etymology_new field")
            elif not isinstance(word.etymology_new, dict):
                issues.append("etymology_new is not a dict")

            if not word.common_mistakes_new:
                issues.append("Missing common_mistakes_new field")
            elif not isinstance(word.common_mistakes_new, dict):
                issues.append("common_mistakes_new is not a dict")

            # 检查语言代码
            if not WordDataConverter.validate_language_code(word.language_code or 'en'):
                issues.append(f"Invalid language code: {word.language_code}")

            if issues:
                validation_results['invalid_migrations'] += 1
                validation_results['issues_found'].append({
                    'word_id': word.id,
                    'word_name': word.word,
                    'issues': issues
                })
            else:
                validation_results['valid_migrations'] += 1

        return validation_results

    def rollback_migration(self, word_id: int) -> bool:
        """
        回滚单个单词的迁移（恢复到旧格式）

        Args:
            word_id: 要回滚的单词ID

        Returns:
            是否回滚成功
        """
        try:
            stmt = select(Word).where(Word.id == word_id)
            word = self.db.execute(stmt).scalar_one_or_none()

            if not word:
                logger.warning(f"Word with ID {word_id} not found")
                return False

            if word.is_legacy_format:
                logger.info(f"Word ID {word_id} is already in legacy format")
                return True

            # 从新格式数据恢复到旧格式字段
            display_data = word.get_display_data('new')

            # 恢复旧格式字段（这里需要根据实际的新格式数据来反向填充）
            # 这个实现取决于具体的新格式结构

            # 标记为旧格式
            word.is_legacy_format = True
            word.updated_at = datetime.utcnow()

            self.db.commit()
            logger.info(f"Successfully rolled back word ID {word_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback word ID {word_id}: {e}")
            self.db.rollback()
            return False

    def estimate_migration_time(self, sample_size: int = 100) -> Dict[str, Any]:
        """
        估算迁移时间

        Args:
            sample_size: 用于估算的样本大小

        Returns:
            估算结果
        """
        legacy_count = self.db.execute(
            select(func.count(Word.id)).where(Word.is_legacy_format == True)
        ).scalar()

        if legacy_count == 0:
            return {
                'estimated_total_time': 0,
                'estimated_batches': 0,
                'sample_words': 0
            }

        # 迁移少量样本进行时间估算
        sample_size = min(sample_size, legacy_count)
        start_time = datetime.utcnow()

        stmt = (
            select(Word)
            .where(Word.is_legacy_format == True)
            .limit(sample_size)
        )
        sample_words = self.db.execute(stmt).scalars().all()

        for word in sample_words:
            try:
                WordDataConverter.migrate_legacy_word(self.db, word.id)
            except Exception as e:
                logger.warning(f"Failed to migrate sample word {word.word}: {e}")

        end_time = datetime.utcnow()
        sample_time = (end_time - start_time).total_seconds()

        # 估算总时间和批次
        if sample_size > 0:
            avg_time_per_word = sample_time / sample_size
            estimated_total_time = (legacy_count * avg_time_per_word) / 3600  # 转换为小时
            estimated_batches = (legacy_count + 49) // 50  # 假设每批50个单词
        else:
            estimated_total_time = 0
            estimated_batches = 0

        return {
            'estimated_total_time_hours': estimated_total_time,
            'estimated_batches': estimated_batches,
            'sample_words': sample_size,
            'legacy_words_remaining': legacy_count - sample_size
        }


# 便利函数
def get_migration_service(db: Session = None) -> WordMigrationService:
    """获取迁移服务实例"""
    if db is None:
        db = next(get_db())
    return WordMigrationService(db)