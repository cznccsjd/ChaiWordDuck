"""add guest query logs table

Revision ID: 004_guest_query_logs
Revises: 003_words_and_favorites
Create Date: 2025-10-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_guest_query_logs'
down_revision: Union[str, None] = '003_words_and_favorites'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级：创建guest_query_logs表"""
    # 创建游客查询日志表
    op.create_table(
        'guest_query_logs',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('identifier', sa.String(length=255), nullable=False, comment='游客标识符（IP地址）'),
        sa.Column('word_id', sa.Integer(), nullable=False, comment='查询的单词ID'),
        sa.Column('query_date', sa.Date(), nullable=False, comment='查询日期'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='创建时间'),
        sa.ForeignKeyConstraint(['word_id'], ['words.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='游客查询日志表',
    )

    # 创建索引：优化按identifier和date查询
    op.create_index(
        'idx_guest_identifier_date',
        'guest_query_logs',
        ['identifier', 'query_date'],
        unique=False,
    )

    # 创建唯一索引：防止同一游客同一天查询同一单词重复记录
    op.create_index(
        'uk_guest_word_date',
        'guest_query_logs',
        ['identifier', 'word_id', 'query_date'],
        unique=True,
    )


def downgrade() -> None:
    """降级：删除guest_query_logs表"""
    # 删除索引
    op.drop_index('uk_guest_word_date', table_name='guest_query_logs')
    op.drop_index('idx_guest_identifier_date', table_name='guest_query_logs')

    # 删除表
    op.drop_table('guest_query_logs')
