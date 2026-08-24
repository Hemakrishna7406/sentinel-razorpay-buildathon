"""
Tests for the Audit Writer and database models.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base, AuditRecord
from security.audit_writer import AuditWriter
from security.capability_token import IntentContext, CapabilityPayload


@pytest.fixture
def db_session():
    # In-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def audit_writer(db_session):
    return AuditWriter(db_session)


@pytest.fixture
def sample_intent():
    return IntentContext(
        intent_id="int_audit_1",
        agent_id="agent_1",
        action_type="payout",
        amount=1000,
        currency="INR",
        recipient="bank_xyz"
    )


def test_log_evaluation_escalate(audit_writer, db_session, sample_intent):
    """Test logging an escalated decision."""
    
    record = audit_writer.log_evaluation(
        agent_id="agent_1",
        intent=sample_intent,
        model_risk=0.95,
        decision="ESCALATE",
        reason="High ML Risk",
        token_payload=None
    )
    
    assert record.id is not None
    assert record.decision == "ESCALATE"
    assert record.model_risk_score == 0.95
    assert record.capability_jti is None
    
    # Verify in DB
    db_record = db_session.query(AuditRecord).filter_by(intent_id="int_audit_1").first()
    assert db_record is not None
    assert db_record.agent_id == "agent_1"


def test_log_evaluation_allow_with_token(audit_writer, db_session, sample_intent):
    """Test logging an allowed decision with a capability token."""
    
    payload = CapabilityPayload(
        intent_id=sample_intent.intent_id,
        agent_id="agent_1",
        action_type=sample_intent.action_type,
        amount=sample_intent.amount,
        currency=sample_intent.currency,
        recipient=sample_intent.recipient,
        decision="ALLOW",
        jti="nonce_abc123",
        issued_at=1234567890,
        expires_at=1234567895
    )
    
    record = audit_writer.log_evaluation(
        agent_id="agent_1",
        intent=sample_intent,
        model_risk=0.10,
        decision="ALLOW",
        reason="Cleared",
        token_payload=payload
    )
    
    assert record.capability_jti == "nonce_abc123"
    
    # Simulate execution success
    audit_writer.log_execution("int_audit_1", "tx_xyz789")
    
    # Verify DB update
    db_record = db_session.query(AuditRecord).filter_by(intent_id="int_audit_1").first()
    assert db_record.executed_tx_id == "tx_xyz789"
