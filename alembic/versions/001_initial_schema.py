"""initial_schema

Revision ID: 001
Revises: 
Create Date: 2026-08-23 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'audit_ledger',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('previous_hash', sa.String(), nullable=True),
        sa.Column('intent_id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False),
        sa.Column('recipient', sa.String(), nullable=False),
        sa.Column('model_risk_score', sa.Float(), nullable=True),
        sa.Column('decision', sa.String(), nullable=False),
        sa.Column('decision_reason', sa.String(), nullable=False),
        sa.Column('capability_jti', sa.String(), nullable=True),
        sa.Column('executed_tx_id', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_ledger_agent_id'), 'audit_ledger', ['agent_id'], unique=False)
    op.create_index('ix_audit_agent_timestamp', 'audit_ledger', ['agent_id', 'timestamp'], unique=False)
    op.create_index(op.f('ix_audit_ledger_capability_jti'), 'audit_ledger', ['capability_jti'], unique=True)
    op.create_index(op.f('ix_audit_ledger_decision'), 'audit_ledger', ['decision'], unique=False)
    op.create_index(op.f('ix_audit_ledger_id'), 'audit_ledger', ['id'], unique=False)
    op.create_index(op.f('ix_audit_ledger_intent_id'), 'audit_ledger', ['intent_id'], unique=True)
    op.create_index(op.f('ix_audit_ledger_previous_hash'), 'audit_ledger', ['previous_hash'], unique=False)
    op.create_index(op.f('ix_audit_ledger_timestamp'), 'audit_ledger', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_ledger_timestamp'), table_name='audit_ledger')
    op.drop_index(op.f('ix_audit_ledger_previous_hash'), table_name='audit_ledger')
    op.drop_index(op.f('ix_audit_ledger_intent_id'), table_name='audit_ledger')
    op.drop_index(op.f('ix_audit_ledger_id'), table_name='audit_ledger')
    op.drop_index(op.f('ix_audit_ledger_decision'), table_name='audit_ledger')
    op.drop_index(op.f('ix_audit_ledger_capability_jti'), table_name='audit_ledger')
    op.drop_index('ix_audit_agent_timestamp', table_name='audit_ledger')
    op.drop_index(op.f('ix_audit_ledger_agent_id'), table_name='audit_ledger')
    op.drop_table('audit_ledger')
