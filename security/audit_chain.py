"""Canonical hashing and verification for the Sentinel audit ledger."""

import hashlib
import json
from typing import Any, Iterable


CHAIN_FIELDS = (
    # All fields including 'timestamp' are included in the hash computation
    # to prevent tampering. The timestamp value is included in hash verification
    # to ensure audit records cannot be backdated or modified.
    "intent_id", "timestamp", "agent_id", "action_type", "amount", "currency",
    "recipient", "model_risk_score", "behavioral_risk_score", "semantic_risk_score",
    "fusion_disagreement", "decision", "decision_reason", "capability_jti",
    "executed_tx_id", "previous_hash",
)


def audit_record_hash(values: dict[str, Any]) -> str:
    """Hash the stable audit payload and its predecessor link."""
    payload = {field: values.get(field) for field in CHAIN_FIELDS}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def verify_audit_chain(records: Iterable[Any]) -> tuple[bool, int, list[int]]:
    """Return chain validity, record count, and invalid record IDs."""
    previous_hash = None
    checked = 0
    invalid: list[int] = []
    for record in records:
        checked += 1
        values = {field: getattr(record, field, None) for field in CHAIN_FIELDS}
        # Include actual timestamp in hash verification to prevent tampering
        if record.previous_hash != previous_hash or record.record_hash != audit_record_hash(values):
            invalid.append(record.id)
        previous_hash = record.record_hash
    return not invalid, checked, invalid
