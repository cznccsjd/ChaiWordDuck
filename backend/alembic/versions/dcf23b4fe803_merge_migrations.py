"""merge migrations

Revision ID: dcf23b4fe803
Revises: 006_fix_language_code_constraint_inconsistency, 02c3300679fc
Create Date: 2025-11-08 09:43:18.613675

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dcf23b4fe803'
down_revision: Union[str, None] = ('006_fix_language_code_constraint_inconsistency', '02c3300679fc')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
