"""suar pelacak (canary beacon) lapis 1

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-13 18:45:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0006'
down_revision: str | Sequence[str] | None = '0005'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Buat tabel beacon_hits."""
    op.create_table(
        'beacon_hits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('copy_id', sa.BigInteger(), nullable=False),
        sa.Column('ip_address', sa.String(length=64), nullable=False),
        sa.Column('user_agent', sa.String(length=512), nullable=True),
        sa.Column('referer', sa.String(length=256), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['copy_id'], ['copies.copy_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_beacon_hits_copy_id'), 'beacon_hits', ['copy_id'], unique=False)


def downgrade() -> None:
    """Hapus tabel beacon_hits."""
    op.drop_index(op.f('ix_beacon_hits_copy_id'), table_name='beacon_hits')
    op.drop_table('beacon_hits')
