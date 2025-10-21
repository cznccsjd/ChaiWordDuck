#!/usr/bin/env python3
"""
Unicode数据清理脚本

用于清理数据库中包含无效Unicode代理对字符的单词数据
这些字符可能导致JSON序列化问题和前端响应截断
"""

import asyncio
import re
import sys
from typing import List, Tuple

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update

from app.core.config import settings
from app.core.logging import get_logger
from app.models.word import Word

logger = get_logger(__name__)


class UnicodeCleaner:
    """Unicode字符清理器"""

    # 无效代理对字符的正则表达式
    INVALID_SURROGATE_PATTERN = re.compile(r'[\udc80-\udfff]')

    @classmethod
    def clean_text(cls, text: str) -> str:
        """
        清理文本中的无效Unicode代理对字符

        Args:
            text: 原始文本

        Returns:
            str: 清理后的文本
        """
        if not text:
            return text

        # 移除无效的代理对字符
        cleaned = cls.INVALID_SURROGATE_PATTERN.sub('', text)

        # 记录清理统计
        if len(cleaned) != len(text):
            removed_count = len(text) - len(cleaned)
            logger.info(f"Cleaned {removed_count} invalid surrogate characters from text")

        return cleaned

    @classmethod
    def validate_text(cls, text: str) -> Tuple[bool, int]:
        """
        验证文本是否包含无效Unicode字符

        Args:
            text: 要验证的文本

        Returns:
            Tuple[bool, int]: (是否有效, 无效字符数量)
        """
        if not text:
            return True, 0

        invalid_chars = cls.INVALID_SURROGATE_PATTERN.findall(text)
        return len(invalid_chars) == 0, len(invalid_chars)


async def check_database_contamination() -> List[Tuple[int, str, List[str]]]:
    """
    检查数据库中的Unicode污染情况

    Returns:
        List[Tuple[int, str, List[str]]]: (单词ID, 单词, 污染字段列表)
    """
    logger.info("开始检查数据库Unicode污染情况...")

    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    contaminated_records = []
    text_fields = [
        'phonetic', 'part_of_speech', 'core_game', 'scenario_formal',
        'scenario_casual', 'etymology_breakdown', 'etymology_story',
        'common_mistakes', 'memory_trick'
    ]

    async with async_session() as session:
        # 获取所有单词记录
        result = await session.execute(select(Word))
        words = result.scalars().all()

        logger.info(f"检查 {len(words)} 条单词记录...")

        for word in words:
            contaminated_fields = []

            for field in text_fields:
                text_value = getattr(word, field, None)
                if text_value:
                    is_valid, invalid_count = UnicodeCleaner.validate_text(text_value)
                    if not is_valid:
                        contaminated_fields.append(field)
                        logger.warning(
                            f"发现污染数据 - Word: {word.word}, Field: {field}, "
                            f"Invalid chars: {invalid_count}"
                        )

            if contaminated_fields:
                contaminated_records.append((word.id, word.word, contaminated_fields))

    await engine.dispose()

    logger.info(f"检查完成，发现 {len(contaminated_records)} 条污染记录")
    return contaminated_records


async def clean_database_data(dry_run: bool = True) -> List[int]:
    """
    清理数据库中的Unicode污染数据

    Args:
        dry_run: 是否为试运行模式（不实际修改数据）

    Returns:
        List[int]: 清理的记录ID列表
    """
    logger.info(f"开始清理数据库Unicode数据 (试运行: {dry_run})...")

    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    cleaned_record_ids = []
    text_fields = [
        'phonetic', 'part_of_speech', 'core_game', 'scenario_formal',
        'scenario_casual', 'etymology_breakdown', 'etymology_story',
        'common_mistakes', 'memory_trick'
    ]

    async with async_session() as session:
        # 获取所有单词记录
        result = await session.execute(select(Word))
        words = result.scalars().all()

        for word in words:
            needs_update = False
            update_data = {}

            for field in text_fields:
                text_value = getattr(word, field, None)
                if text_value:
                    cleaned_value = UnicodeCleaner.clean_text(text_value)
                    if cleaned_value != text_value:
                        update_data[field] = cleaned_value
                        needs_update = True

                        logger.info(
                            f"清理字段 - Word: {word.word}, Field: {field}, "
                            f"Original length: {len(text_value)}, "
                            f"Cleaned length: {len(cleaned_value)}"
                        )

            if needs_update:
                if not dry_run:
                    # 实际更新数据库
                    await session.execute(
                        update(Word)
                        .where(Word.id == word.id)
                        .values(**update_data)
                    )
                    await session.commit()
                    logger.info(f"已更新记录: Word ID {word.id} ({word.word})")

                cleaned_record_ids.append(word.id)

    await engine.dispose()

    logger.info(f"清理完成，{'试运行模式 - ' if dry_run else ''}处理了 {len(cleaned_record_ids)} 条记录")
    return cleaned_record_ids


async def verify_cleanup():
    """验证清理结果"""
    logger.info("开始验证清理结果...")

    contaminated_records = await check_database_contamination()

    if contaminated_records:
        logger.error(f"验证失败，仍有 {len(contaminated_records)} 条污染记录")
        for word_id, word_text, fields in contaminated_records:
            logger.error(f"  - Word ID {word_id} ({word_text}): {', '.join(fields)}")
        return False
    else:
        logger.info("验证成功！数据库已无Unicode污染数据")
        return True


async def main():
    """主函数"""
    print("拆词鸭 - Unicode数据清理工具")
    print("=" * 50)

    try:
        # 步骤1：检查污染情况
        print("\n步骤1：检查数据库Unicode污染情况...")
        contaminated_records = await check_database_contamination()

        if not contaminated_records:
            print("数据库中没有发现Unicode污染数据，无需清理")
            return

        print(f"发现 {len(contaminated_records)} 条污染记录：")
        for word_id, word_text, fields in contaminated_records[:5]:  # 只显示前5条
            print(f"  - Word ID {word_id} ({word_text}): {', '.join(fields)}")

        if len(contaminated_records) > 5:
            print(f"  ... 还有 {len(contaminated_records) - 5} 条记录")

        # 步骤2：试运行清理
        print("\n步骤2：试运行清理（不修改数据）...")
        dry_run_results = await clean_database_data(dry_run=True)
        print(f"试运行将处理 {len(dry_run_results)} 条记录")

        # 步骤3：确认执行
        confirm = input("\n是否执行实际数据清理？(y/N): ").lower().strip()

        if confirm in ['y', 'yes']:
            print("\n步骤3：执行实际数据清理...")
            actual_results = await clean_database_data(dry_run=False)
            print(f"已清理 {len(actual_results)} 条记录")

            # 步骤4：验证结果
            print("\n步骤4：验证清理结果...")
            success = await verify_cleanup()

            if success:
                print("数据清理完成并验证成功！")
            else:
                print("清理验证失败，请检查日志")
                sys.exit(1)
        else:
            print("用户取消操作，未执行实际清理")

    except Exception as e:
        logger.error(f"清理过程中发生错误: {e}", exc_info=True)
        print(f"清理失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())