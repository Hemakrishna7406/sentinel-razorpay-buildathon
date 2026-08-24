"""
Sentinel — Audit Writer

Writes intent evaluations and execution results to the immutable ledger.
"""

from typing import Optional
from sqlalchemy.orm import Session

from db.models import AuditRecord
from security.capability_token import IntentContext, CapabilityPayload


class AuditWriter:
    def __init__(self, session: Session):
        self.session = session
        
    def log_evaluation(
        self, 
        agent_id: str,
        intent: IntentContext, 
        model_risk: Optional[float],
        decision: str, 
        reason: str,
        token_payload: Optional[CapabilityPayload] = None
    ) -> AuditRecord:
        """Log the policy engine's decision before execution."""
        import hashlib
        
        last_record = self.session.query(AuditRecord).order_by(AuditRecord.id.desc()).first()
        prev_hash = None
        if last_record:
            prev_hash = hashlib.sha256(f"{last_record.id}:{last_record.intent_id}".encode()).hexdigest()
            
        record = AuditRecord(
            previous_hash=prev_hash,
            intent_id=intent.intent_id,
            agent_id=agent_id,
            action_type=intent.action_type,
            amount=intent.amount,
            currency=intent.currency,
            recipient=intent.recipient,
            model_risk_score=model_risk,
            decision=decision,
            decision_reason=reason,
            capability_jti=token_payload.jti if token_payload else None
        )
        
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record
        
    def log_execution(self, intent_id: str, tx_id: str):
        """Update the ledger with the downstream transaction ID."""
        record = self.session.query(AuditRecord).filter_by(intent_id=intent_id).first()
        if record:
            record.executed_tx_id = tx_id
            self.session.commit()
