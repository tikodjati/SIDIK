"""honey-record lapis 4

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-09 10:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: str | Sequence[str] | None = '0003'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _persona_columns() -> list[sa.Column]:
    return [
        sa.Column('nrp', sa.String(length=32), nullable=False),
        sa.Column('nama', sa.String(length=128), nullable=False),
        sa.Column('pangkat', sa.String(length=64), nullable=False),
        sa.Column('satuan', sa.String(length=128), nullable=False),
        sa.Column('nik', sa.String(length=16), nullable=False),
        sa.Column('no_hp', sa.String(length=16), nullable=False),
        sa.Column('tanggal_lahir', sa.Date(), nullable=False),
    ]


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('personnel',
    sa.Column('id', sa.Integer(), nullable=False),
    *_persona_columns(),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nik'),
    sa.UniqueConstraint('no_hp'),
    sa.UniqueConstraint('nrp')
    )
    op.create_index(op.f('ix_personnel_satuan'), 'personnel', ['satuan'], unique=False)
    op.create_table('data_exports',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=32), nullable=False),
    sa.Column('satuan', sa.String(length=128), nullable=True),
    sa.Column('purpose', sa.String(length=256), nullable=False),
    sa.Column('row_count', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('honey_records',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('export_id', sa.Integer(), nullable=True),
    *_persona_columns(),
    sa.ForeignKeyConstraint(['export_id'], ['data_exports.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nik'),
    sa.UniqueConstraint('no_hp'),
    sa.UniqueConstraint('nrp')
    )
    op.create_index(
        op.f('ix_honey_records_export_id'), 'honey_records', ['export_id'], unique=False
    )
    op.create_table('public_corpora',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('label', sa.String(length=128), nullable=False),
    sa.Column('note', sa.String(length=256), nullable=False),
    sa.Column('entries', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('label')
    )
    op.create_table('corpus_fingerprints',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('corpus_id', sa.Integer(), nullable=False),
    sa.Column('fp', sa.String(length=64), nullable=False),
    sa.ForeignKeyConstraint(['corpus_id'], ['public_corpora.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('corpus_id', 'fp')
    )
    op.create_index(op.f('ix_corpus_fingerprints_fp'), 'corpus_fingerprints', ['fp'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_corpus_fingerprints_fp'), table_name='corpus_fingerprints')
    op.drop_table('corpus_fingerprints')
    op.drop_table('public_corpora')
    op.drop_index(op.f('ix_honey_records_export_id'), table_name='honey_records')
    op.drop_table('honey_records')
    op.drop_table('data_exports')
    op.drop_index(op.f('ix_personnel_satuan'), table_name='personnel')
    op.drop_table('personnel')
