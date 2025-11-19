#!/usr/bin/env python3
"""
Simple database initialization script

Creates the latest database structure directly, skipping migrations
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import engine, Base
from app.models import word, user, favorite, query_log, guest_query_log, ai_generation_log


async def init_database():
    """Initialize database, create all tables"""

    print("Starting database initialization...")

    try:
        # 1. Drop all existing tables (if any)
        print("Dropping existing tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        # 2. Create all tables
        print("Creating new table structure...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # 3. Create additional indexes and constraints
        print("Creating additional indexes and constraints...")
        await create_additional_indexes(conn)

        # 4. Insert initial data
        print("Inserting initial data...")
        await insert_initial_data(conn)

        print("Database initialization completed successfully!")

        # 5. Verify table structure
        print("Verifying table structure...")
        await verify_database_structure(conn)

    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise


async def create_additional_indexes(conn):
    """Create additional indexes for better performance"""

    try:
        # Check if PostgreSQL
        result = await conn.execute(text("SELECT version()"))
        version = result.scalar()

        if "PostgreSQL" in version:
            print("PostgreSQL environment: creating GIN indexes for JSON fields")

            # Create GIN indexes for words table JSON fields
            gin_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_words_core_game_new_gin ON words USING GIN (core_game_new)",
                "CREATE INDEX IF NOT EXISTS idx_words_game_boards_gin ON words USING GIN (game_boards)",
                "CREATE INDEX IF NOT EXISTS idx_words_etymology_new_gin ON words USING GIN (etymology_new)",
                "CREATE INDEX IF NOT EXISTS idx_words_common_mistakes_new_gin ON words USING GIN (common_mistakes_new)",
            ]

            for index_sql in gin_indexes:
                try:
                    await conn.execute(text(index_sql))
                    print(f"  Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
                except Exception as e:
                    print(f"  Index creation failed (may already exist): {e}")
        else:
            print(f"Non-PostgreSQL environment: {version}")

    except Exception as e:
        print(f"Database type detection failed: {e}")


async def insert_initial_data(conn):
    """Insert initial data"""

    # Check if data already exists
    result = await conn.execute(text("SELECT COUNT(*) FROM words"))
    count = result.scalar()

    if count == 0:
        print("Inserting sample word data...")

        # Insert sample word using direct SQL
        insert_sql = """
        INSERT INTO words (
            word, phonetic, part_of_speech, translation, language_code,
            core_game, scenario_formal, scenario_casual, etymology_breakdown,
            etymology_story, common_mistakes, memory_trick, is_golden,
            source, prompt_version, is_legacy_format, created_at, updated_at
        ) VALUES (
            'accommodation', '[əˌkɒməˈdeɪʃ(ə)n]', 'noun', '住宿；适应；和解', 'zh',
            '核心游戏内容：accommodation的记忆游戏',
            '正式场景：The hotel provides excellent accommodation for tourists.',
            '生活场景：我们需要找个住的地方。',
            'ac(加强) + commod(适合) + ation(名词后缀)',
            '词源故事：来自拉丁语accommodare，意为"使适应"。',
            '常见错误：不要忘记双写字母c和m',
            '记忆技巧：ac-com-mode-ration（让适合的名词）',
            true, 'ai', 'v2.0', false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        """

        try:
            await conn.execute(text(insert_sql))
            print("  Inserted sample word: accommodation")
        except Exception as e:
            print(f"  Failed to insert sample word: {e}")
    else:
        print(f"Database already has {count} words, skipping sample data insertion")


async def verify_database_structure(conn):
    """Verify database structure"""

    # Check if main tables exist
    tables = ['words', 'users', 'favorites', 'query_logs', 'guest_query_logs', 'ai_generation_logs']

    for table_name in tables:
        try:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table_name} LIMIT 1"))
            print(f"  Table {table_name}: exists")
        except Exception as e:
            print(f"  Table {table_name}: does not exist or has issues - {e}")

    # Check constraints on words table
    try:
        result = await conn.execute(text("""
            SELECT conname, consrc
            FROM pg_constraint
            WHERE conrelid = 'words'::regclass AND contype = 'c'
        """))
        constraints = result.fetchall()

        print("  Constraints on words table:")
        for constraint_name, constraint_src in constraints:
            print(f"    - {constraint_name}: {constraint_src}")

    except Exception as e:
        print(f"  Constraint check failed (may not be PostgreSQL): {e}")


async def main():
    """Main function"""
    print("=" * 60)
    print("ChaiWord Duck Database Initialization Script")
    print("=" * 60)

    try:
        await init_database()
        print("\nDatabase initialization completed successfully!")
        print("You can now start the application.")
    except Exception as e:
        print(f"\nInitialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())