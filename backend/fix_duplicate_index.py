#!/usr/bin/env python3
"""
数据库重复索引修复脚本

解决 alembic 迁移中的 idx_words_language_code 重复索引问题
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到sys.path
sys.path.append(str(Path(__file__).resolve().parents[0]))

from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def check_duplicate_indexes():
    """检查重复索引"""
    global engine

    try:
        async with engine.connect() as conn:
            # 检查是否存在重复的idx_words_language_code索引
            query = text("""
                SELECT indexname, indexdef, schemaname
                FROM pg_indexes
                WHERE tablename = 'words'
                AND indexname = 'idx_words_language_code'
                ORDER BY indexname
            """)

            result = await conn.execute(query)
            indexes = result.fetchall()

            logger.info(f"找到 {len(indexes)} 个 'idx_words_language_code' 索引:")
            for idx in indexes:
                logger.info(f"  - {idx.indexname} in schema {idx.schemaname}")
                logger.info(f"    Definition: {idx.indexdef}")

            return len(indexes) > 1

    except Exception as e:
        logger.error(f"检查索引时发生错误: {e}")
        return False
    finally:
        await engine.dispose()


async def get_current_alembic_version():
    """获取当前alembic版本"""
    global engine

    try:
        async with engine.connect() as conn:
            query = text("SELECT version_num FROM alembic_version")
            result = await conn.execute(query)
            version = result.scalar()
            logger.info(f"当前alembic版本: {version}")
            return version
    except Exception as e:
        logger.error(f"获取alembic版本时发生错误: {e}")
        return None
    finally:
        await engine.dispose()


async def fix_duplicate_index():
    """修复重复索引问题"""
    global engine

    try:
        async with engine.begin() as conn:
            # 删除重复索引（如果存在多个）
            logger.info("正在检查并删除重复的索引...")

            # 检查索引存在情况
            check_query = text("""
                SELECT COUNT(*) as count
                FROM pg_indexes
                WHERE tablename = 'words'
                AND indexname = 'idx_words_language_code'
            """)

            result = await conn.execute(check_query)
            count = result.scalar()

            if count > 1:
                logger.warning(f"发现 {count} 个重复索引，开始清理...")
                # 删除索引（PostgreSQL允许重复删除，会报错但不会停止）
                drop_query = text("DROP INDEX IF EXISTS idx_words_language_code")
                await conn.execute(drop_query)
                logger.info("已删除重复索引")

                # 重新创建索引
                create_query = text("CREATE INDEX idx_words_language_code ON words (language_code)")
                await conn.execute(create_query)
                logger.info("已重新创建索引")

            elif count == 1:
                logger.info("索引已存在且唯一，无需修复")
            else:
                logger.info("索引不存在，将创建新索引")
                create_query = text("CREATE INDEX idx_words_language_code ON words (language_code)")
                await conn.execute(create_query)
                logger.info("已创建索引")

            await conn.commit()
            return True

    except Exception as e:
        logger.error(f"修复索引时发生错误: {e}")
        return False
    finally:
        await engine.dispose()


async def set_alembic_version(version: str):
    """设置alembic版本"""
    global engine

    try:
        async with engine.begin() as conn:
            # 更新alembic版本
            query = text("""
                INSERT INTO alembic_version (version_num)
                VALUES (:version)
                ON CONFLICT (version_num)
                DO UPDATE SET version_num = EXCLUDED.version_num
            """)
            await conn.execute(query, {"version": version})
            await conn.commit()
            logger.info(f"已设置alembic版本为: {version}")
            return True
    except Exception as e:
        logger.error(f"设置alembic版本时发生错误: {e}")
        return False
    finally:
        await engine.dispose()


async def main():
    """主修复流程"""
    logger.info("开始数据库迁移修复流程...")

    # 1. 检查数据库连接
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✓ 数据库连接正常")
    except Exception as e:
        logger.error(f"✗ 数据库连接失败: {e}")
        logger.error("请检查数据库服务是否运行以及连接配置是否正确")
        return False

    # 2. 检查当前alembic版本
    current_version = await get_current_alembic_version()
    if not current_version:
        logger.error("无法获取当前alembic版本，请检查alembic_version表")
        return False

    # 3. 检查重复索引
    has_duplicates = await check_duplicate_indexes()

    # 4. 修复重复索引
    if has_duplicates:
        success = await fix_duplicate_index()
        if not success:
            logger.error("修复索引失败")
            return False

    # 5. 根据当前版本设置正确的alembic版本
    # 如果当前版本停留在005，设置为006；如果已经是006，保持不变
    if current_version == '005_add_multilang_prompt_support':
        target_version = '006_add_word_language_unique_constraint'
        logger.info(f"需要将alembic版本从 {current_version} 更新到 {target_version}")
        success = await set_alembic_version(target_version)
        if not success:
            logger.error("设置alembic版本失败")
            return False
    elif current_version == '006_add_word_language_unique_constraint':
        logger.info("alembic版本已是最新的，无需更新")
    else:
        logger.warning(f"当前版本 {current_version} 不是预期版本，请手动检查")

    logger.info("✓ 数据库迁移修复完成！")
    logger.info("现在可以运行以下命令继续:")
    logger.info("  pdm run alembic current")
    logger.info("  pdm run alembic upgrade head")

    return True


if __name__ == "__main__":
    # 运行修复脚本
    success = asyncio.run(main())
    if not success:
        sys.exit(1)