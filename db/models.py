"""
Sentinel — Database Schema

SQLAlchemy ORM models for the audit ledger.
PostgreSQL is the durable source of truth for all decisions.
"""

import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class AuditRecord(Base):
    """Immutable ledger of all evaluated intents and their decisions."""
    __tablename__ = "audit_ledger"

    # Sequence ID provides strict global ordering of audit events
    id = Column(Integer, primary_key=True, index=True)
    
    # Audit chain ordering
    previous_hash = Column(String, nullable=True, index=True)
    record_hash = Column(String, nullable=False, unique=True, index=True)
    
    # Intent identity
    intent_id = Column(String, unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    
    # Payload details
    agent_id = Column(String, index=True, nullable=False)
    action_type = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String, nullable=False)
    recipient = Column(String, nullable=False)
    
    # ML and Policy outputs
    model_risk_score = Column(Float, nullable=True) # Final fused risk
    behavioral_risk_score = Column(Float, nullable=True)
    semantic_risk_score = Column(Float, nullable=True)
    fusion_disagreement = Column(String, nullable=True) # "true" or "false"
    
    decision = Column(String, nullable=False, index=True)  # ALLOW or ESCALATE
    decision_reason = Column(String, nullable=False)
    
    # Capability tracking
    capability_jti = Column(String, unique=True, nullable=True, index=True)
    
    # Execution Tracking
    executed_tx_id = Column(String, nullable=True)

    # Explicit indexes for expected query patterns
    __table_args__ = (
        Index('ix_audit_agent_timestamp', 'agent_id', 'timestamp'),
    )
