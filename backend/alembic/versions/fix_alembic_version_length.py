"""fix_alembic_version_length

Revision ID: fix_alembic_version_length
Revises: 005_add_multilang_prompt_support
Create Date: 2025-10-28 00:00:00.000000

Fix alembic_version table version_num field length limitation:
- Extend version_num from VARCHAR(32) to VARCHAR(64)
- Allow longer descriptive revision IDs
- Prevent future length constraint violations
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'fix_alembic_version_length'
down_revision: Union[str, None] = '005_add_multilang_prompt_support'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Extend alembic_version.version_num field to VARCHAR(64)"""

    # Check if the version_num field needs extension
    conn = op.get_bind()

    # Get current column info
    check_query = """
    SELECT character_maximum_length
    FROM information_schema.columns
    WHERE table_name = 'alembic_version'
    AND column_name = 'version_num'
    """
    current_length = conn.execute(text(check_query)).scalar()

    if current_length and current_length < 64:
        # First, ensure we're at the correct version before modifying
        # This prevents accidentally applying this fix when we're already at a newer version
        version_check = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()

        if version_check == '005_add_multilang_prompt_support':
            # Modify the version_num column to extend the length
            op.alter_column(
                'alembic_version',
                'version_num',
                existing_type=sa.VARCHAR(length=32),
                type_=sa.VARCHAR(length=64),
                existing_nullable=False
            )

            # Add comment for documentation
            op.execute(text("""
                COMMENT ON TABLE alembic_version IS 'Alembic migration tracking table - version_num extended to support longer descriptive revision IDs'
            """))

            print("✅ Successfully extended alembic_version.version_num to VARCHAR(64)")
        else:
            raise Exception(f"Cannot apply fix: current database version is {version_check}, expected 005_add_multilang_prompt_support")
    else:
        print("ℹ️  alembic_version.version_num is already extended or has sufficient length")


def downgrade() -> None:
    """Revert alembic_version.version_num field back to VARCHAR(32)"""

    # Check current state before reverting
    conn = op.get_bind()
    version_check = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()

    # Only allow downgrade if we're at the fix version
    if version_check == 'fix_alembic_version_length':
        # Revert the version_num column back to original length
        op.alter_column(
            'alembic_version',
            'version_num',
            existing_type=sa.VARCHAR(length=64),
            type_=sa.VARCHAR(length=32),
            existing_nullable=False
        )

        # Remove table comment
        op.execute(text("COMMENT ON TABLE alembic_version IS NULL"))

        print("✅ Successfully reverted alembic_version.version_num to VARCHAR(32)")
    else:
        raise Exception(f"Cannot revert: current database version is {version_check}, expected fix_alembic_version_length")