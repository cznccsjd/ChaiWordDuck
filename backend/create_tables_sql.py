#!/usr/bin/env python3
"""
Create tables using direct SQL
"""
import asyncio
import sys

DATABASE_URL = "postgresql+asyncpg://chaiword_user:chaiword_password@localhost:5432/chaiword_db"

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

engine = create_async_engine(DATABASE_URL, echo=True)


async def create_tables():
    """Create tables using direct SQL"""

    print("Creating tables using direct SQL...")

    # Words table
    create_words_sql = """
    CREATE TABLE IF NOT EXISTS words (
        id SERIAL PRIMARY KEY,
        word VARCHAR(100) NOT NULL UNIQUE,
        phonetic VARCHAR(200),
        part_of_speech VARCHAR(255),
        translation VARCHAR(500),
        language_code VARCHAR(10) DEFAULT 'zh',
        prompt_version VARCHAR(20) DEFAULT 'v1.0',
        is_legacy_format BOOLEAN DEFAULT true,
        core_game TEXT NOT NULL,
        scenario_formal TEXT NOT NULL,
        scenario_casual TEXT NOT NULL,
        etymology_breakdown TEXT NOT NULL,
        etymology_story TEXT,
        common_mistakes TEXT NOT NULL,
        memory_trick TEXT NOT NULL,
        is_golden BOOLEAN DEFAULT false,
        source VARCHAR(50) DEFAULT 'ai',
        core_game_new JSONB,
        game_boards JSONB,
        etymology_new JSONB,
        common_mistakes_new JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create indexes
    CREATE INDEX IF NOT EXISTS idx_words_word ON words(word);
    CREATE INDEX IF NOT EXISTS idx_words_is_golden ON words(is_golden);
    CREATE INDEX IF NOT EXISTS idx_words_language_code ON words(language_code);
    CREATE INDEX IF NOT EXISTS idx_words_prompt_version ON words(prompt_version);
    CREATE INDEX IF NOT EXISTS idx_words_is_legacy_format ON words(is_legacy_format);

    -- Create GIN indexes for JSON fields
    CREATE INDEX IF NOT EXISTS idx_words_core_game_new_gin ON words USING GIN (core_game_new);
    CREATE INDEX IF NOT EXISTS idx_words_game_boards_gin ON words USING GIN (game_boards);
    CREATE INDEX IF NOT EXISTS idx_words_etymology_new_gin ON words USING GIN (etymology_new);
    CREATE INDEX IF NOT EXISTS idx_words_common_mistakes_new_gin ON words USING GIN (common_mistakes_new);

    -- Create constraints
    ALTER TABLE words ADD CONSTRAINT check_word_source
        CHECK (source IN ('ai', 'manual'));

    ALTER TABLE words ADD CONSTRAINT check_words_language_code
        CHECK (language_code IN ('en', 'zh', 'zh_TW', 'ja', 'ko', 'fr', 'de', 'es', 'it', 'ru'));
    """

    # Users table
    create_users_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL UNIQUE,
        hashed_password VARCHAR(255) NOT NULL,
        is_active BOOLEAN DEFAULT true,
        is_premium BOOLEAN DEFAULT false,
        daily_query_count INTEGER DEFAULT 0,
        preferred_language VARCHAR(10) DEFAULT 'zh',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
    CREATE INDEX IF NOT EXISTS idx_users_is_premium ON users(is_premium);
    """

    # Favorites table
    create_favorites_sql = """
    CREATE TABLE IF NOT EXISTS favorites (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, word_id)
    );

    CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id);
    CREATE INDEX IF NOT EXISTS idx_favorites_word_id ON favorites(word_id);
    """

    # Query logs table
    create_query_logs_sql = """
    CREATE TABLE IF NOT EXISTS query_logs (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        word_text VARCHAR(100) NOT NULL,
        ip_address INET,
        user_agent TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_query_logs_user_id ON query_logs(user_id);
    CREATE INDEX IF NOT EXISTS idx_query_logs_word_text ON query_logs(word_text);
    CREATE INDEX IF NOT EXISTS idx_query_logs_created_at ON query_logs(created_at);
    """

    # Guest query logs table
    create_guest_query_logs_sql = """
    CREATE TABLE IF NOT EXISTS guest_query_logs (
        id SERIAL PRIMARY KEY,
        word_text VARCHAR(100) NOT NULL,
        ip_address INET NOT NULL,
        user_agent TEXT,
        session_id VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_guest_query_logs_ip_address ON guest_query_logs(ip_address);
    CREATE INDEX IF NOT EXISTS idx_guest_query_logs_word_text ON guest_query_logs(word_text);
    CREATE INDEX IF NOT EXISTS idx_guest_query_logs_session_id ON guest_query_logs(session_id);
    CREATE INDEX IF NOT EXISTS idx_guest_query_logs_created_at ON guest_query_logs(created_at);
    """

    # AI generation logs table
    create_ai_generation_logs_sql = """
    CREATE TABLE IF NOT EXISTS ai_generation_logs (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        word_text VARCHAR(100) NOT NULL,
        prompt_template VARCHAR(100),
        ai_provider VARCHAR(50),
        model_name VARCHAR(100),
        response_time_ms INTEGER,
        tokens_used INTEGER,
        success BOOLEAN DEFAULT false,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_ai_generation_logs_user_id ON ai_generation_logs(user_id);
    CREATE INDEX IF NOT EXISTS idx_ai_generation_logs_word_text ON ai_generation_logs(word_text);
    CREATE INDEX IF NOT EXISTS idx_ai_generation_logs_ai_provider ON ai_generation_logs(ai_provider);
    CREATE INDEX IF NOT EXISTS idx_ai_generation_logs_success ON ai_generation_logs(success);
    CREATE INDEX IF NOT EXISTS idx_ai_generation_logs_created_at ON ai_generation_logs(created_at);
    """

    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.execute(text(create_words_sql))
            print("Created words table")

            await conn.execute(text(create_users_sql))
            print("Created users table")

            await conn.execute(text(create_favorites_sql))
            print("Created favorites table")

            await conn.execute(text(create_query_logs_sql))
            print("Created query_logs table")

            await conn.execute(text(create_guest_query_logs_sql))
            print("Created guest_query_logs table")

            await conn.execute(text(create_ai_generation_logs_sql))
            print("Created ai_generation_logs table")

        print("All tables created successfully!")

        # Insert sample data
        await insert_sample_data()

    except Exception as e:
        print(f"Error creating tables: {e}")
        raise


async def insert_sample_data():
    """Insert sample data"""

    print("Inserting sample data...")

    insert_sql = """
    INSERT INTO words (
        word, phonetic, part_of_speech, translation, language_code,
        core_game, scenario_formal, scenario_casual, etymology_breakdown,
        etymology_story, common_mistakes, memory_trick, is_golden,
        source, prompt_version, is_legacy_format
    ) VALUES
    (
        'accommodation', '[əˌkɒməˈdeɪʃ(ə)n]', 'noun', '住宿；适应；和解', 'zh',
        '核心游戏内容：accommodation的记忆游戏',
        '正式场景：The hotel provides excellent accommodation for tourists.',
        '生活场景：我们需要找个住的地方。',
        'ac(加强) + commod(适合) + ation(名词后缀)',
        '词源故事：来自拉丁语accommodare，意为"使适应"。',
        '常见错误：不要忘记双写字母c和m',
        '记忆技巧：ac-com-mode-ration（让适合的名词）',
        true, 'ai', 'v2.0', false
    ),
    (
        'spring', '/sprɪŋ/', 'n.', '春天', 'en',
        '核心游戏：spring的季节变化',
        'Formal: Spring brings new life to nature.',
        'Casual: I love spring weather!',
        '来自古英语 springan',
        '词源：表示跳跃、涌出的意思',
        '发音注意：不是spr-ing，而是/sprɪŋ/',
        '记忆：spring = s + ring，联想季节的环环相扣',
        false, 'ai', 'v2.0', false
    )
    ON CONFLICT (word) DO NOTHING;
    """

    try:
        async with engine.begin() as conn:
            result = await conn.execute(text(insert_sql))
            print(f"Inserted {result.rowcount} sample words")

    except Exception as e:
        print(f"Error inserting sample data: {e}")


async def verify_tables():
    """Verify tables exist"""

    print("Verifying tables...")

    tables = ['words', 'users', 'favorites', 'query_logs', 'guest_query_logs', 'ai_generation_logs']

    for table in tables:
        try:
            async with engine.begin() as conn:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  {table}: {count} rows")
        except Exception as e:
            print(f"  {table}: ERROR - {e}")


async def main():
    """Main function"""
    print("=" * 60)
    print("Creating tables with direct SQL")
    print("=" * 60)

    try:
        await create_tables()
        await verify_tables()
        print("\nDatabase setup completed successfully!")
    except Exception as e:
        print(f"\nSetup failed: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())