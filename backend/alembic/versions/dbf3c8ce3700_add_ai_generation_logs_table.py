"""add ai_generation_logs table

Revision ID: dbf3c8ce3700
Revises: 004_guest_query_logs
Create Date: 2025-10-16 10:50:37.242037

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dbf3c8ce3700'
down_revision: Union[str, None] = '004_guest_query_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_generation_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='用户ID，游客为NULL'),
        sa.Column('ip_address', sa.String(50), nullable=False, comment='IP地址'),
        sa.Column('word', sa.String(100), nullable=False, comment='生成的单词'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='创建时间'),
    )
    op.create_index('idx_ai_gen_user_date', 'ai_generation_logs', ['user_id', 'created_at'])
    op.create_index('idx_ai_gen_ip_date', 'ai_generation_logs', ['ip_address', 'created_at'])


def downgrade() -> None:
    op.drop_table('ai_generation_logs')
