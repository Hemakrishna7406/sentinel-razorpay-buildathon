"""add audit integrity fields

Revision ID: 002
Revises: 001
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_ledger", sa.Column("behavioral_risk_score", sa.Float(), nullable=True))
    op.add_column("audit_ledger", sa.Column("semantic_risk_score", sa.Float(), nullable=True))
    op.add_column("audit_ledger", sa.Column("fusion_disagreement", sa.String(), nullable=True))
    op.add_column("audit_ledger", sa.Column("record_hash", sa.String(), nullable=True))
    op.create_index("ix_audit_ledger_record_hash", "audit_ledger", ["record_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_audit_ledger_record_hash", table_name="audit_ledger")
    op.drop_column("audit_ledger", "record_hash")
    op.drop_column("audit_ledger", "fusion_disagreement")
    op.drop_column("audit_ledger", "semantic_risk_score")
    op.drop_column("audit_ledger", "behavioral_risk_score")
