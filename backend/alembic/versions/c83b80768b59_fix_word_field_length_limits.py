"""fix_word_field_length_limits

Revision ID: c83b80768b59
Revises: dbf3c8ce3700
Create Date: 2025-10-21 01:49:05.589362

Fixes field length limits in words and users tables to accommodate
AI-generated content and extended metadata.

Changes:
- words.part_of_speech: String(20) -> String(255)
- words.source: String(20) -> String(50)
- words.phonetic: String(50) -> String(200)
- users.membership_tier: String(20) -> String(50)

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c83b80768b59'
down_revision: Union[str, None] = 'dbf3c8ce3700'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Increase field length limits to accommodate AI-generated content"""

    # Update words table fields
    op.alter_column('words', 'part_of_speech',
                   existing_type=sa.String(length=20),
                   type_=sa.String(length=255),
                   existing_nullable=True)

    op.alter_column('words', 'phonetic',
                   existing_type=sa.String(length=50),
                   type_=sa.String(length=200),
                   existing_nullable=True)

    op.alter_column('words', 'source',
                   existing_type=sa.String(length=20),
                   type_=sa.String(length=50),
                   existing_nullable=False)

    # Update users table fields
    op.alter_column('users', 'membership_tier',
                   existing_type=sa.String(length=20),
                   type_=sa.String(length=50),
                   existing_nullable=False)


def downgrade() -> None:
    """Revert field length limits to original values"""

    # Revert words table fields
    op.alter_column('words', 'part_of_speech',
                   existing_type=sa.String(length=255),
                   type_=sa.String(length=20),
                   existing_nullable=True)

    op.alter_column('words', 'phonetic',
                   existing_type=sa.String(length=200),
                   type_=sa.String(length=50),
                   existing_nullable=True)

    op.alter_column('words', 'source',
                   existing_type=sa.String(length=50),
                   type_=sa.String(length=20),
                   existing_nullable=False)

    # Revert users table fields
    op.alter_column('users', 'membership_tier',
                   existing_type=sa.String(length=50),
                   type_=sa.String(length=20),
                   existing_nullable=False)
