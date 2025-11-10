"""fix_language_code_constraint_inconsistency

Revision ID: 006_fix_language_code_constraint_inconsistency
Revises: 005_add_multilang_prompt_support
Create Date: 2025-11-08 15:00:00.000000

Fix language code constraint inconsistency between model definition and database:
- Update database constraint to use 2-character ISO 639-1 language codes ('zh' instead of 'zh_CN')
- Migrate existing data from 'zh_CN' to 'zh'
- Ensure consistency with application layer language code normalization
- Update default values to use 2-character codes

This fixes the check constraint violation error:
"new row for relation "words" violates check constraint "check_words_language_code""
"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = '006_fix_language_code_constraint_inconsistency'
down_revision: Union[str, None] = '005_add_multilang_prompt_support'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix language code constraint inconsistency"""

    # 1. First, drop the existing constraint
    op.drop_constraint('check_words_language_code', table_name='words', type_='check')

    # 2. Update existing data to use 2-character language codes
    connection = op.get_bind()

    # Migration mapping: 5-char codes to 2-char codes
    migration_query = """
    UPDATE words
    SET language_code = CASE
        WHEN language_code = 'zh_CN' THEN 'zh'
        WHEN language_code = 'zh-tw' THEN 'zh_TW'
        WHEN language_code = 'zh-TW' THEN 'zh_TW'
        WHEN language_code = 'en_US' THEN 'en'
        WHEN language_code = 'en-us' THEN 'en'
        WHEN language_code = 'en-GB' THEN 'en'
        WHEN language_code = 'en-gb' THEN 'en'
        ELSE language_code
    END
    WHERE language_code IN ('zh_CN', 'zh-tw', 'zh-TW', 'en_US', 'en-us', 'en-GB', 'en-gb');
    """

    connection.execute(text(migration_query))

    # 3. Update any remaining NULL language_code to use default 'zh'
    update_null_query = """
    UPDATE words
    SET language_code = 'zh'
    WHERE language_code IS NULL OR language_code = '';
    """

    connection.execute(text(update_null_query))

    # 4. Create the new constraint with 2-character language codes
    op.create_check_constraint(
        'check_words_language_code',
        'words',
        "language_code IN ('en', 'zh', 'zh_TW', 'ja', 'ko', 'fr', 'de', 'es', 'it', 'ru')"
    )

    # 5. Update server default for language_code to use 2-character code
    op.alter_column('words', 'language_code',
                   server_default=sa.text("'zh'"))

    # 6. Log the migration for audit purposes
    log_query = """
    INSERT INTO alembic_version (version_num)
    SELECT '006_fix_language_code_constraint_inconsistency'
    WHERE NOT EXISTS (SELECT 1 FROM alembic_version WHERE version_num = '006_fix_language_code_constraint_inconsistency');
    """

    try:
        connection.execute(text(log_query))
    except Exception:
        # Ignore duplicate entry errors
        pass


def downgrade() -> None:
    """Revert the language code constraint fix"""

    connection = op.get_bind()

    # 1. Drop the 2-character constraint
    op.drop_constraint('check_words_language_code', table_name='words', type_='check')

    # 2. Revert data migration: 2-char codes back to 5-char codes
    revert_query = """
    UPDATE words
    SET language_code = CASE
        WHEN language_code = 'zh' THEN 'zh_CN'
        WHEN language_code = 'zh_TW' THEN 'zh_TW'  # Keep as is
        WHEN language_code = 'en' THEN 'en_US'
        ELSE language_code
    END
    WHERE language_code IN ('zh', 'zh_TW', 'en');
    """

    connection.execute(text(revert_query))

    # 3. Recreate the original constraint with 5-character language codes
    op.create_check_constraint(
        'check_words_language_code',
        'words',
        "language_code IN ('en', 'zh_CN', 'zh_TW', 'ja', 'ko', 'fr', 'de', 'es', 'it', 'ru')"
    )

    # 4. Revert server default for language_code
    op.alter_column('words', 'language_code',
                   server_default=sa.text("'en'"))