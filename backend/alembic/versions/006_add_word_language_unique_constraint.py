"""add_word_language_unique_constraint

Revision ID: 006_add_word_language_unique_constraint
Revises: 005_add_multilang_prompt_support
Create Date: 2025-10-26 15:50:00.000000

Add unique constraint for (word, language_code) combination to enable proper UPSERT operations:
- Add composite unique constraint on word + language_code
- Clean up duplicate data (keep newest version)
- Create performance indexes for word lookup
- Enable efficient multi-language word management
"""

from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = '006_add_word_language_unique_constraint'
down_revision: Union[str, None] = '005_add_multilang_prompt_support'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add word+language unique constraint and optimize table structure"""

    # 1. Clean up duplicate data first
    # Keep the newest version for each word+language combination
    cleanup_query = """
    WITH ranked_words AS (
        SELECT
            id,
            word,
            language_code,
            ROW_NUMBER() OVER (
                PARTITION BY word, language_code
                ORDER BY
                    CASE WHEN is_golden = true THEN 1 ELSE 2 END,
                    updated_at DESC,
                    id DESC
            ) as rn
        FROM words
    ),
    duplicates_to_delete AS (
        SELECT id FROM ranked_words WHERE rn > 1
    )
    DELETE FROM words WHERE id IN (SELECT id FROM duplicates_to_delete);
    """

    op.execute(text(cleanup_query))

    # 2. Remove existing word unique constraint if it exists
    conn = op.get_bind()
    # Check if constraint exists and drop it
    check_constraint_query = """
    SELECT conname FROM pg_constraint
    WHERE conrelid = 'words'::regclass
    AND contype = 'u'
    AND conname = 'uk_words_word'
    """
    result = conn.execute(text(check_constraint_query)).scalar()
    if result:
        op.drop_constraint('uk_words_word', 'words', type_='unique')

    # 3. Add new composite unique constraint
    op.create_unique_constraint(
        'uk_words_word_lang',
        'words',
        ['word', 'language_code']
    )

    # 4. Create performance indexes
    # Primary query index
    op.create_index(
        'idx_words_word_lang',
        'words',
        ['word', 'language_code']
    )

    # Index for golden handbook queries
    op.create_index(
        'idx_words_word_lang_golden',
        'words',
        ['word', 'language_code', 'is_golden']
    )

    # Index for language-specific queries
    op.create_index(
        'idx_words_language_code',
        'words',
        ['language_code']
    )

    # 5. Add indexes for new JSONB fields to support efficient querying
    # GIN index for partial match in JSONB fields
    op.create_index(
        'idx_words_core_game_new_partial',
        'words',
        ['core_game_new'],
        postgresql_using='gin',
        postgresql_where=sa.text("core_game_new IS NOT NULL")
    )

    op.create_index(
        'idx_words_game_boards_partial',
        'words',
        ['game_boards'],
        postgresql_using='gin',
        postgresql_where=sa.text("game_boards IS NOT NULL")
    )

    # 6. Add table comment for documentation
    op.execute(text("""
        COMMENT ON TABLE words IS '单词表 - 支持多语言和混合存储格式
        - word + language_code: 唯一约束，支持同一单词多语言版本
        - is_legacy_format: 标识数据格式类型 (true=旧格式, false=新格式)
        - JSONB字段: 存储嵌套的复杂结构化数据
        - 旧格式字段: 保持向后兼容性
        '
    """))

    # 7. Log migration completion
    op.execute(text("""
        INSERT INTO alembic_version (version_num, created_at)
        VALUES ('006_add_word_language_unique_constraint', CURRENT_TIMESTAMP)
        ON CONFLICT (version_num) DO NOTHING;
    """))


def downgrade() -> None:
    """Remove word+language unique constraint and related indexes"""

    # Drop new indexes first
    op.drop_index('idx_words_core_game_new_partial', table_name='words')
    op.drop_index('idx_words_game_boards_partial', table_name='words')
    op.drop_index('idx_words_language_code', table_name='words')
    op.drop_index('idx_words_word_lang_golden', table_name='words')
    op.drop_index('idx_words_word_lang', table_name='words')

    # Drop composite unique constraint
    op.drop_constraint('uk_words_word_lang', 'words', type_='unique')

    # Recreate old word unique constraint
    op.create_unique_constraint('uk_words_word', 'words', ['word'])

    # Remove table comment
    op.execute(text("COMMENT ON TABLE words IS NULL"))