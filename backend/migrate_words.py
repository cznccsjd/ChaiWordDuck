#!/usr/bin/env python3
"""
单词数据迁移管理脚本

用于执行和管理words表的多语言Prompt支持迁移
"""
import argparse
import sys
import asyncio
from typing import Optional

from sqlalchemy.orm import Session
from app.core.database import get_db, engine
from app.services.word_migration_service import get_migration_service, WordMigrationService
from app.models.word_converter import WordDataConverter
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_migration(
    batch_size: int = 50,
    max_batches: Optional[int] = None,
    word_name: Optional[str] = None,
    golden_only: bool = False
) -> None:
    """
    执行数据迁移

    Args:
        batch_size: 批次大小
        max_batches: 最大批次数量
        word_name: 指定要迁移的单词名称
        golden_only: 是否只迁移黄金单词
    """
    db = next(get_db())
    migration_service = get_migration_service(db)

    try:
        # 显示迁移前统计
        stats = migration_service.get_migration_stats()
        logger.info("=== 迁移前统计 ===")
        logger.info(f"总单词数: {stats['total_words']}")
        logger.info(f"旧格式单词: {stats['legacy_words']}")
        logger.info(f"新格式单词: {stats['migrated_words']}")
        logger.info(f"迁移进度: {stats['migration_progress']}")

        if word_name:
            # 迁移指定单词
            logger.info(f"开始迁移单词: {word_name}")
            result = migration_service.migrate_word_by_name(word_name)
            if result:
                logger.info(f"成功迁移单词: {result.word}")
            else:
                logger.error(f"迁移失败或单词不存在: {word_name}")

        elif golden_only:
            # 只迁移黄金单词
            logger.info("开始迁移黄金手册单词...")
            result = migration_service.migrate_golden_words()
            logger.info(f"黄金单词迁移完成: {result}")

        else:
            # 批量迁移
            logger.info(f"开始批量迁移: batch_size={batch_size}, max_batches={max_batches}")
            result = migration_service.migrate_batch(batch_size, max_batches)
            logger.info(f"批量迁移完成: {result}")

        # 显示迁移后统计
        stats = migration_service.get_migration_stats()
        logger.info("=== 迁移后统计 ===")
        logger.info(f"总单词数: {stats['total_words']}")
        logger.info(f"旧格式单词: {stats['legacy_words']}")
        logger.info(f"新格式单词: {stats['migrated_words']}")
        logger.info(f"迁移进度: {stats['migration_progress']}")

    except Exception as e:
        logger.error(f"迁移过程中发生错误: {e}")
        raise
    finally:
        db.close()


def validate_migration() -> None:
    """验证迁移数据的完整性"""
    db = next(get_db())
    migration_service = get_migration_service(db)

    try:
        logger.info("开始验证迁移数据完整性...")
        result = migration_service.validate_migration_integrity()

        logger.info(f"=== 验证结果 ===")
        logger.info(f"检查的单词数: {result['total_words_checked']}")
        logger.info(f"有效迁移: {result['valid_migrations']}")
        logger.info(f"无效迁移: {result['invalid_migrations']}")

        if result['issues_found']:
            logger.warning("发现以下问题:")
            for issue in result['issues_found']:
                logger.warning(f"单词 ID {issue['word_id']} ({issue['word_name']}): {issue['issues']}")

        else:
            logger.info("所有验证通过，未发现问题")

    except Exception as e:
        logger.error(f"验证过程中发生错误: {e}")
        raise
    finally:
        db.close()


def estimate_migration() -> None:
    """估算迁移时间"""
    db = next(get_db())
    migration_service = get_migration_service(db)

    try:
        logger.info("开始估算迁移时间...")
        result = migration_service.estimate_migration_time()

        logger.info("=== 估算结果 ===")
        logger.info(f"预计总时间: {result['estimated_total_time_hours']:.2f} 小时")
        logger.info(f"预计批次数量: {result['estimated_batches']}")
        logger.info(f"样本单词数: {result['sample_words']}")
        logger.info(f"剩余待迁移单词: {result['legacy_words_remaining']}")

    except Exception as e:
        logger.error(f"估算过程中发生错误: {e}")
        raise
    finally:
        db.close()


def rollback_word(word_name: str) -> None:
    """回滚指定单词的迁移"""
    db = next(get_db())
    migration_service = get_migration_service(db)

    try:
        # 先查找单词ID
        from sqlalchemy import select
        from app.models.word import Word

        stmt = select(Word).where(Word.word == word_name)
        word = db.execute(stmt).scalar_one_or_none()

        if not word:
            logger.error(f"单词不存在: {word_name}")
            return

        logger.info(f"开始回滚单词: {word_name} (ID: {word.id})")
        success = migration_service.rollback_migration(word.id)

        if success:
            logger.info(f"成功回滚单词: {word_name}")
        else:
            logger.error(f"回滚失败: {word_name}")

    except Exception as e:
        logger.error(f"回滚过程中发生错误: {e}")
        raise
    finally:
        db.close()


def show_stats() -> None:
    """显示当前统计信息"""
    db = next(get_db())
    migration_service = get_migration_service(db)

    try:
        stats = migration_service.get_migration_stats()
        supported_langs = WordDataConverter.get_supported_languages()

        logger.info("=== 当前统计信息 ===")
        logger.info(f"总单词数: {stats['total_words']}")
        logger.info(f"旧格式单词: {stats['legacy_words']}")
        logger.info(f"新格式单词: {stats['migrated_words']}")
        logger.info(f"迁移进度: {stats['migration_progress']}")
        logger.info("")
        logger.info("=== 支持的语言 ===")
        for code, name in supported_langs.items():
            logger.info(f"{code}: {name}")

    except Exception as e:
        logger.error(f"获取统计信息时发生错误: {e}")
        raise
    finally:
        db.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="单词数据迁移管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # migrate命令
    migrate_parser = subparsers.add_parser('migrate', help='执行数据迁移')
    migrate_parser.add_argument('--batch-size', type=int, default=50, help='批次大小 (默认: 50)')
    migrate_parser.add_argument('--max-batches', type=int, help='最大批次数量')
    migrate_parser.add_argument('--word', type=str, help='迁移指定的单词')
    migrate_parser.add_argument('--golden-only', action='store_true', help='只迁移黄金手册单词')

    # validate命令
    validate_parser = subparsers.add_parser('validate', help='验证迁移数据完整性')

    # estimate命令
    estimate_parser = subparsers.add_parser('estimate', help='估算迁移时间')
    estimate_parser.add_argument('--sample-size', type=int, default=100, help='用于估算的样本大小 (默认: 100)')

    # rollback命令
    rollback_parser = subparsers.add_parser('rollback', help='回滚指定单词的迁移')
    rollback_parser.add_argument('word', type=str, help='要回滚的单词名称')

    # stats命令
    stats_parser = subparsers.add_parser('stats', help='显示当前统计信息')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == 'migrate':
            run_migration(
                batch_size=args.batch_size,
                max_batches=args.max_batches,
                word_name=args.word,
                golden_only=args.golden_only
            )
        elif args.command == 'validate':
            validate_migration()
        elif args.command == 'estimate':
            estimate_migration()
        elif args.command == 'rollback':
            rollback_word(args.word)
        elif args.command == 'stats':
            show_stats()
        else:
            logger.error(f"未知命令: {args.command}")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("用户中断操作")
        sys.exit(0)
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()