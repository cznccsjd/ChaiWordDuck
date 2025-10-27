"""merge multilang prompt and user language branches

Revision ID: 02c3300679fc
Revises: 006_add_word_language_unique_constraint, f14db0738bba
Create Date: 2025-10-28 00:26:09.152390

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '02c3300679fc'
down_revision: Union[str, None] = ('006_add_word_language_unique_constraint', 'f14db0738bba')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
