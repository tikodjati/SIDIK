"""tabel awal registri dan ledger

Revision ID: 0001
Revises: 
Create Date: 2026-11-01 16:38:43.533715

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('documents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nomor', sa.String(length=64), nullable=False),
    sa.Column('judul', sa.String(length=256), nullable=False),
    sa.Column('klasifikasi', sa.String(length=32), nullable=False),
    sa.Column('template', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nomor')
    )
    op.create_table('ledger_entries',
    sa.Column('seq', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('prev_hash', sa.String(length=64), nullable=False),
    sa.Column('entry_hash', sa.String(length=64), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('signature', sa.String(length=128), nullable=False),
    sa.Column('key_id', sa.String(length=16), nullable=False),
    sa.PrimaryKeyConstraint('seq'),
    sa.UniqueConstraint('entry_hash'),
    sa.UniqueConstraint('prev_hash')
    )
    op.create_table('recipients',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nrp', sa.String(length=32), nullable=False),
    sa.Column('nama', sa.String(length=128), nullable=False),
    sa.Column('pangkat', sa.String(length=64), nullable=False),
    sa.Column('jabatan', sa.String(length=128), nullable=False),
    sa.Column('satuan', sa.String(length=128), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nrp')
    )
    op.create_table('copies',
    sa.Column('copy_id', sa.BigInteger(), autoincrement=False, nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('recipient_id', sa.Integer(), nullable=False),
    sa.Column('issued_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
    sa.ForeignKeyConstraint(['recipient_id'], ['recipients.id'], ),
    sa.PrimaryKeyConstraint('copy_id'),
    sa.UniqueConstraint('document_id', 'recipient_id')
    )
    if op.get_bind().dialect.name == "postgresql":
        # Buku besar append-only di level DB: UPDATE/DELETE/TRUNCATE ditolak. Pemilik DB masih bisa
        # melepas trigger; karena itu integritas dijamin juga oleh hash chain + tanda tangan.
        op.execute(
            """
            CREATE FUNCTION ledger_entries_immutable() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'ledger_entries bersifat append-only';
            END;
            $$ LANGUAGE plpgsql
            """
        )
        op.execute(
            "CREATE TRIGGER ledger_entries_no_change BEFORE UPDATE OR DELETE ON ledger_entries "
            "FOR EACH ROW EXECUTE FUNCTION ledger_entries_immutable()"
        )
        op.execute(
            "CREATE TRIGGER ledger_entries_no_truncate BEFORE TRUNCATE ON ledger_entries "
            "FOR EACH STATEMENT EXECUTE FUNCTION ledger_entries_immutable()"
        )


def downgrade() -> None:
    """Downgrade schema."""
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS ledger_entries_no_truncate ON ledger_entries")
        op.execute("DROP TRIGGER IF EXISTS ledger_entries_no_change ON ledger_entries")
        op.execute("DROP FUNCTION IF EXISTS ledger_entries_immutable()")
    op.drop_table('copies')
    op.drop_table('recipients')
    op.drop_table('ledger_entries')
    op.drop_table('documents')
