"""honey-token lapis 3

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-08 10:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: str | Sequence[str] | None = '0002'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('honey_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('copy_id', sa.BigInteger(), nullable=False),
    sa.Column('token_index', sa.Integer(), nullable=False),
    sa.Column('value', sa.String(length=32), nullable=False),
    sa.Column('digits', sa.String(length=32), nullable=False),
    sa.ForeignKeyConstraint(['copy_id'], ['copies.copy_id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('copy_id', 'token_index'),
    sa.UniqueConstraint('digits')
    )
    op.create_index(op.f('ix_honey_tokens_copy_id'), 'honey_tokens', ['copy_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_honey_tokens_copy_id'), table_name='honey_tokens')
    op.drop_table('honey_tokens')
