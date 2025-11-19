#!/usr/bin/env python3
"""
Fixed database initialization script
"""
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Direct database configuration
DATABASE_URL = "postgresql+asyncpg://chaiword_user:chaiword_password@localhost:5432/chaiword_db"

# Create engine with correct credentials
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
)

# Base class for models
Base = declarative_base()


# Import model definitions after creating engine
from app.models import word, user, favorite, query_log, guest_query_log, ai_generation_log


async def test_connection():
    """Test database connection"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"Successfully connected to database: {version}")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


async def init_database():
    """Initialize database, create all tables"""

    print("Starting database initialization...")

    # Test connection first
    if not await test_connection():
        raise Exception("Cannot connect to database")

    try:
        # 1. Drop all existing tables (if any)
        print("Dropping existing tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        # 2. Create all tables
        print("Creating new table structure...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # 3. Verify tables were created
        print("Verifying table creation...")
        async with engine.begin() as conn:
            await verify_tables(conn)

        # 4. Insert sample data
        print("Inserting sample data...")
        async with engine.begin() as conn:
            await insert_sample_data(conn)

        # 5. Create additional indexes
        print("Creating additional indexes...")
        async with engine.begin() as conn:
            await create_additional_indexes(conn)

        print("Database initialization completed successfully!")

    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise


async def verify_tables(conn):
    """Verify that tables were created successfully"""

    tables_to_check = [
        'words', 'users', 'favorites', 'query_logs',
        'guest_query_logs', 'ai_generation_logs'
    ]

    for table_name in tables_to_check:
        try:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
            print(f"  Table '{table_name}': OK (rows: {count})")
        except Exception as e:
            print(f"  Table '{table_name}': ERROR - {e}")


async def create_additional_indexes(conn):
    """Create additional indexes for JSON fields"""

    try:
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
                print(f"  Created GIN index: {index_sql.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                print(f"  Index creation failed (may already exist): {e}")

    except Exception as e:
        print(f"Additional index creation failed: {e}")


async def insert_sample_data(conn):
    """Insert sample data for testing"""

    # Check if words table is empty
    result = await conn.execute(text("SELECT COUNT(*) FROM words"))
    count = result.scalar()

    if count == 0:
        print("Inserting sample word data...")

        # Insert sample word with correct language code
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

        # Insert another sample with English
        insert_sql_en = """
        INSERT INTO words (
            word, phonetic, part_of_speech, translation, language_code,
            core_game, scenario_formal, scenario_casual, etymology_breakdown,
            etymology_story, common_mistakes, memory_trick, is_golden,
            source, prompt_version, is_legacy_format, created_at, updated_at
        ) VALUES (
            'spring', '/sprɪŋ/', 'n.', '春天', 'en',
            '核心游戏：spring的季节变化',
            'Formal: Spring brings new life to nature.',
            'Casual: I love spring weather!',
            '来自古英语 springan',
            '词源：表示跳跃、涌出的意思',
            '发音注意：不是spr-ing，而是/sprɪŋ/',
            '记忆：spring = s + ring，联想季节的环环相扣',
            false, 'ai', 'v2.0', false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        """

        try:
            await conn.execute(text(insert_sql_en))
            print("  Inserted sample word: spring")
        except Exception as e:
            print(f"  Failed to insert sample word: {e}")

    else:
        print(f"Words table already has {count} rows, skipping sample data")


async def cleanup():
    """Clean up database connections"""
    await engine.dispose()


async def main():
    """Main function"""
    print("=" * 60)
    print("ChaiWord Duck Database Initialization Script (Fixed)")
    print("=" * 60)

    try:
        await init_database()
        print("\nDatabase initialization completed successfully!")
        print("You can now start the application.")
    except Exception as e:
        print(f"\nInitialization failed: {e}")
        sys.exit(1)
    finally:
        await cleanup()


if __name__ == "__main__":
    asyncio.run(main())