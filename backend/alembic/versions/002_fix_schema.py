"""Fix database schema inconsistencies and add guest_sessions table

Revision ID: 002_fix_schema
Revises: 001_initial
Create Date: 2025-10-15 12:00:00.000000

Fixes Bug #1: Database migration script inconsistencies with ORM models
- Remove incorrect fields from users table
- Add missing fields to users table
- Create guest_sessions table
- Add proper indexes and constraints
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_fix_schema'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix schema to match ORM models"""

    # 1. Fix users table - remove incorrect fields
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'subscription_expires_at')
    op.drop_column('users', 'is_active')

    # 2. Rename field to match ORM model
    op.alter_column('users', 'is_email_verified', new_column_name='email_verified')

    # 3. Add missing field
    op.add_column('users', sa.Column('membership_expires_at', sa.DateTime(), nullable=True))

    # 4. Fix membership_tier column length and add CHECK constraint
    op.alter_column('users', 'membership_tier',
                    type_=sa.String(length=20),
                    existing_type=sa.String(length=50),
                    nullable=False,
                    server_default='free')

    op.create_check_constraint(
        'check_membership_tier',
        'users',
        "membership_tier IN ('free', 'premium')"
    )

    # 5. Add index for membership queries
    op.create_index('idx_users_membership', 'users', ['membership_tier', 'membership_expires_at'])

    # 6. Add index for token expiration queries
    op.create_index('idx_token_expires', 'password_reset_tokens', ['expires_at', 'is_used'])

    # 7. Create guest_sessions table
    op.create_table(
        'guest_sessions',
        sa.Column('guest_id', sa.String(length=36), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('user_agent_hash', sa.String(length=64), nullable=False),
        sa.Column('last_query_date', sa.DateTime(), nullable=False),
        sa.Column('query_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('guest_id')
    )

    # 8. Create indexes for guest_sessions
    op.create_index('idx_guest_last_query', 'guest_sessions', ['last_query_date'])
    op.create_index('idx_guest_ip', 'guest_sessions', ['ip_address', 'user_agent_hash'])
    op.create_index('idx_guest_created', 'guest_sessions', ['created_at'])


def downgrade() -> None:
    """Revert schema changes"""

    # Drop guest_sessions table
    op.drop_index('idx_guest_created', table_name='guest_sessions')
    op.drop_index('idx_guest_ip', table_name='guest_sessions')
    op.drop_index('idx_guest_last_query', table_name='guest_sessions')
    op.drop_table('guest_sessions')

    # Drop new indexes
    op.drop_index('idx_token_expires', table_name='password_reset_tokens')
    op.drop_index('idx_users_membership', table_name='users')

    # Drop CHECK constraint
    op.drop_constraint('check_membership_tier', 'users', type_='check')

    # Revert users table changes
    op.drop_column('users', 'membership_expires_at')

    op.alter_column('users', 'email_verified', new_column_name='is_email_verified')

    op.alter_column('users', 'membership_tier',
                    type_=sa.String(length=50),
                    existing_type=sa.String(length=20))

    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('users', sa.Column('subscription_expires_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('subscription_status', sa.String(length=50), nullable=True))
