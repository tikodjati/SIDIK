"""persetujuan ganda salinan

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-09 15:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0005'
down_revision: str | Sequence[str] | None = '0004'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema. Salinan lama dianggap sudah terbit (ISSUED)."""
    op.add_column('copies', sa.Column(
        'status', sa.String(length=16), nullable=False, server_default='ISSUED'
    ))
    op.add_column('copies', sa.Column('requested_by', sa.String(length=32), nullable=True))
    op.add_column('copies', sa.Column('approved_by', sa.String(length=32), nullable=True))
    op.add_column('copies', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('copies', 'approved_at')
    op.drop_column('copies', 'approved_by')
    op.drop_column('copies', 'requested_by')
    op.drop_column('copies', 'status')
