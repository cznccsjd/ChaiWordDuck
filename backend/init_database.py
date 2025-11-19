#!/usr/bin/env python3
"""
数据库初始化脚本

直接创建最新的数据库结构，跳过迁移步骤
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import engine, Base
from app.models import word, user, favorite, query_log, guest_query_log, ai_generation_log


async def init_database():
    """初始化数据库，创建所有表"""

    print("🚀 开始初始化数据库...")

    try:
        # 1. 删除所有现有表（如果存在）
        print("📋 删除现有表...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        # 2. 创建所有表
        print("🏗️  创建新表结构...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # 3. 创建额外的索引和约束
        print("🔧 创建额外索引和约束...")
        async with engine.begin() as conn:
            # 创建JSON字段的GIN索引（PostgreSQL特有）
            if os.getenv("PYTEST_CURRENT_TEST"):
                print("🧪 测试环境：跳过PostgreSQL特定索引")
            else:
                try:
                    # 检查是否为PostgreSQL
                    result = await conn.execute(text("SELECT version()"))
                    version = result.scalar()
                    if "PostgreSQL" in version:
                        print("📊 PostgreSQL环境：创建JSON字段的GIN索引")

                        # 为words表的JSON字段创建GIN索引
                        gin_indexes = [
                            "CREATE INDEX IF NOT EXISTS idx_words_core_game_new_gin ON words USING GIN (core_game_new)",
                            "CREATE INDEX IF NOT EXISTS idx_words_game_boards_gin ON words USING GIN (game_boards)",
                            "CREATE INDEX IF NOT EXISTS idx_words_etymology_new_gin ON words USING GIN (etymology_new)",
                            "CREATE INDEX IF NOT EXISTS idx_words_common_mistakes_new_gin ON words USING GIN (common_mistakes_new)",
                        ]

                        for index_sql in gin_indexes:
                            try:
                                await conn.execute(text(index_sql))
                                print(f"  ✅ 创建索引: {index_sql.split('idx_')[1].split(' ')[0]}")
                            except Exception as e:
                                print(f"  ⚠️  索引创建失败（可能已存在）: {e}")
                    else:
                        print(f"🗄️  非PostgreSQL环境：{version}")
                except Exception as e:
                    print(f"⚠️  数据库类型检测失败: {e}")

        # 4. 插入初始数据
        print("📝 插入初始数据...")
        await insert_initial_data(conn)

        print("✅ 数据库初始化完成！")

        # 5. 验证表结构
        print("🔍 验证表结构...")
        await verify_database_structure(conn)

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise


async def insert_initial_data(conn):
    """插入初始数据"""

    # 插入示例单词数据（如果需要）
    sample_words = [
        {
            'word': 'accommodation',
            'phonetic': '[əˌkɒməˈdeɪʃ(ə)n]',
            'part_of_speech': 'noun',
            'translation': '住宿；适应；和解',
            'language_code': 'zh',
            'core_game': '核心游戏内容：accommodation的记忆游戏',
            'scenario_formal': '正式场景：The hotel provides excellent accommodation for tourists.',
            'scenario_casual': '生活场景：我们需要找个住的地方。',
            'etymology_breakdown': 'ac(加强) + commod(适合) + ation(名词后缀)',
            'etymology_story': '词源故事：来自拉丁语accommodare，意为"使适应"。',
            'common_mistakes': '常见错误：不要忘记双写字母c和m',
            'memory_trick': '记忆技巧：ac-com-mode-ration（让适合的名词）',
            'is_golden': True,
            'source': 'ai',
            'prompt_version': 'v2.0',
            'is_legacy_format': False,
            'core_game_new': {'content': '核心游戏内容：accommodation的记忆游戏'},
            'game_boards': {
                'board_a_speculative': {'type': '棋盘A (思辨场)', 'name': '思辨场景', 'example': '正式场景：The hotel provides excellent accommodation for tourists.'},
                'board_b_life': {'type': '棋盘B (生活场)', 'name': '生活场景', 'example': '生活场景：我们需要找个住的地方。'}
            },
            'etymology_new': {
                'breakdown': {
                    'prefix': {'part': 'ac', 'meaning': '加强'},
                    'root': {'part': 'commod', 'meaning': '适合'},
                    'suffix': {'part': 'ation', 'meaning': '名词后缀'}
                },
                'story': '词源故事：来自拉丁语accommodare，意为"使适应"。'
            },
            'common_mistakes_new': {
                'warning': '常见错误：不要忘记双写字母c和m',
                'avoidance': '记忆技巧：ac-com-mode-ration（让适合的名词）'
            }
        }
    ]

    # 检查是否已有数据
    result = await conn.execute(text("SELECT COUNT(*) FROM words"))
    count = result.scalar()

    if count == 0:
        print("📝 插入示例单词数据...")

        # 手动构建插入语句，避免ORM映射问题
        insert_sql = """
        INSERT INTO words (
            word, phonetic, part_of_speech, translation, language_code,
            core_game, scenario_formal, scenario_casual, etymology_breakdown,
            etymology_story, common_mistakes, memory_trick, is_golden,
            source, prompt_version, is_legacy_format, core_game_new,
            game_boards, etymology_new, common_mistakes_new, created_at, updated_at
        ) VALUES (
            :word, :phonetic, :part_of_speech, :translation, :language_code,
            :core_game, :scenario_formal, :scenario_casual, :etymology_breakdown,
            :etymology_story, :common_mistakes, :memory_trick, :is_golden,
            :source, :prompt_version, :is_legacy_format, :core_game_new,
            :game_boards, :etymology_new, :common_mistakes_new,
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        """

        for word_data in sample_words:
            try:
                await conn.execute(text(insert_sql), word_data)
                print(f"  ✅ 插入单词: {word_data['word']}")
            except Exception as e:
                print(f"  ❌ 插入单词失败 {word_data['word']}: {e}")
    else:
        print(f"📝 数据库中已有 {count} 个单词，跳过示例数据插入")


async def verify_database_structure(conn):
    """验证数据库结构"""

    # 检查主要表是否存在
    tables = ['words', 'users', 'favorites', 'query_logs', 'guest_query_logs', 'ai_generation_logs']

    for table_name in tables:
        try:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table_name} LIMIT 1"))
            print(f"  ✅ 表 {table_name}: 存在")
        except Exception as e:
            print(f"  ❌ 表 {table_name}: 不存在或有问题 - {e}")

    # 检查words表的约束
    try:
        result = await conn.execute(text("""
            SELECT conname, consrc
            FROM pg_constraint
            WHERE conrelid = 'words'::regclass AND contype = 'c'
        """))
        constraints = result.fetchall()

        print("  🔍 words表约束:")
        for constraint_name, constraint_src in constraints:
            print(f"    - {constraint_name}: {constraint_src}")

    except Exception as e:
        print(f"  ⚠️  约束检查失败（可能不是PostgreSQL）: {e}")


async def main():
    """主函数"""
    print("=" * 60)
    print("🗄️  拆词鸭数据库初始化脚本")
    print("=" * 60)

    try:
        await init_database()
        print("\n🎉 数据库初始化成功完成！")
        print("🚀 现在可以启动应用了。")
    except Exception as e:
        print(f"\n💥 初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())