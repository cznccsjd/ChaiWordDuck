"""add_multilang_prompt_support

Revision ID: 005_add_multilang_prompt_support
Revises: c83b80768b59
Create Date: 2025-10-26 10:00:00.000000

Add support for multilang prompt system with hybrid storage strategy:
- Add new fields for simple data (VARCHAR/TEXT)
- Add JSONB fields for complex nested structures
- Keep existing fields for backward compatibility
- Add migration logic for existing data
- Add optimized indexes and constraints

New Fields:
- translation: VARCHAR(500) - word translation
- language_code: VARCHAR(10) - language identifier (en, zh_CN, etc.)
- core_game_new: JSONB - structured core game data
- game_boards: JSONB - structured game boards data
- etymology_new: JSONB - structured etymology data
- common_mistakes_new: JSONB - structured common mistakes data
- prompt_version: VARCHAR(20) - track which prompt version was used
- is_legacy_format: BOOLEAN - mark records using old format
"""
from typing import Sequence, Union
import json
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_add_multilang_prompt_support'
down_revision: Union[str, None] = 'c83b80768b59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add multilang prompt support fields to words table"""

    # 1. Add new simple fields
    op.add_column('words', sa.Column('translation', sa.String(length=500), nullable=True))
    op.add_column('words', sa.Column('language_code', sa.String(length=10), nullable=True, server_default='en'))
    op.add_column('words', sa.Column('prompt_version', sa.String(length=20), nullable=True, server_default='v1.0'))
    op.add_column('words', sa.Column('is_legacy_format', sa.Boolean(), nullable=False, server_default=sa.text("'true'")))

    # 2. Add new JSONB fields for structured data
    op.add_column('words', sa.Column('core_game_new', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('words', sa.Column('game_boards', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('words', sa.Column('etymology_new', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('words', sa.Column('common_mistakes_new', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # 3. Add constraints for language codes
    op.create_check_constraint(
        'check_words_language_code',
        'words',
        "language_code IN ('en', 'zh_CN', 'zh_TW', 'ja', 'ko', 'fr', 'de', 'es', 'it', 'ru')"
    )

    # 4. Add indexes for performance
    op.create_index('idx_words_language_code', 'words', ['language_code'])
    op.create_index('idx_words_prompt_version', 'words', ['prompt_version'])
    op.create_index('idx_words_is_legacy_format', 'words', ['is_legacy_format'])

    # 5. Create GIN indexes for JSONB fields to optimize queries
    op.create_index('idx_words_core_game_new_gin', 'words', ['core_game_new'], postgresql_using='gin')
    op.create_index('idx_words_game_boards_gin', 'words', ['game_boards'], postgresql_using='gin')
    op.create_index('idx_words_etymology_new_gin', 'words', ['etymology_new'], postgresql_using='gin')
    op.create_index('idx_words_common_mistakes_new_gin', 'words', ['common_mistakes_new'], postgresql_using='gin')

    # 6. Migrate existing data to new format
    connection = op.get_bind()

    # Update existing records with legacy format marker and structured data
    migration_query = """
    UPDATE words
    SET
        language_code = CASE
            WHEN translation LIKE '%中文%' OR translation LIKE '%译文%' THEN 'zh_CN'
            ELSE 'en'
        END,
        core_game_new = jsonb_build_object('content', core_game),
        game_boards = jsonb_build_object(
            'board_a_speculative', jsonb_build_object(
                'type', '棋盘A (思辨场)',
                'name', '思辨场景',
                'example', scenario_formal
            ),
            'board_b_life', jsonb_build_object(
                'type', '棋盘B (生活场)',
                'name', '生活场景',
                'example', scenario_casual
            )
        ),
        etymology_new = jsonb_build_object(
            'breakdown', jsonb_build_object(
                'prefix', jsonb_build_object('part', '', 'meaning', ''),
                'root', jsonb_build_object('part', etymology_breakdown, 'meaning', '词根拆解'),
                'suffix', jsonb_build_object('part', '', 'meaning', '')
            ),
            'story', COALESCE(etymology_story, '')
        ),
        common_mistakes_new = jsonb_build_object(
            'warning', common_mistakes,
            'avoidance', memory_trick
        ),
        prompt_version = 'v1.0'
    WHERE is_legacy_format = true;
    """

    connection.execute(migration_query)

    # 7. Add default translation for golden handbook words
    golden_words_translation = {
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

    for word, translation in golden_words_translation.items():
        update_query = f"""
        UPDATE words
        SET translation = '{translation}', language_code = 'zh_CN'
        WHERE word = '{word}' AND source = 'manual'
        """
        connection.execute(update_query)


def downgrade() -> None:
    """Remove multilang prompt support fields"""

    # Drop indexes first
    op.drop_index('idx_words_common_mistakes_new_gin', table_name='words')
    op.drop_index('idx_words_etymology_new_gin', table_name='words')
    op.drop_index('idx_words_game_boards_gin', table_name='words')
    op.drop_index('idx_words_core_game_new_gin', table_name='words')
    op.drop_index('idx_words_is_legacy_format', table_name='words')
    op.drop_index('idx_words_prompt_version', table_name='words')
    op.drop_index('idx_words_language_code', table_name='words')

    # Drop constraints
    op.drop_constraint('check_words_language_code', table_name='words', type_='check')

    # Drop new columns
    op.drop_column('words', 'common_mistakes_new')
    op.drop_column('words', 'etymology_new')
    op.drop_column('words', 'game_boards')
    op.drop_column('words', 'core_game_new')
    op.drop_column('words', 'is_legacy_format')
    op.drop_column('words', 'prompt_version')
    op.drop_column('words', 'language_code')
    op.drop_column('words', 'translation')