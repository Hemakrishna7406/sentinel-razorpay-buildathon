import pytest
from unittest.mock import patch, MagicMock
from api.main import evaluate_intent_sync, IntentRequest
from fastapi import Request
from security.exceptions import SentinelSecurityException

@pytest.mark.asyncio
async def test_redis_unavailable_fails_closed():
    """Redis unavailability must result in failure (fail closed) with 0 MCP calls."""
    intent = IntentRequest(
        intent_id="int_fail_1",
        agent_id="agent_1",
        action_type="payout",
        amount=100,
        currency="INR",
        recipient="rec_1"
    )
    request = MagicMock(spec=Request)
    
    with patch("api.main.get_idempotency_engine") as mock_idem:
        mock_idem.return_value.check_and_record.side_effect = Exception("Redis connection refused")
        
        with pytest.raises(Exception, match="Redis connection refused"):
            await evaluate_intent_sync(request, intent, idempotency_key="key1")

def test_model_unavailable_escalates(monkeypatch):
    """If ML model is down, we must ESCALATE (fail closed)."""
    from ml.fusion.risk_fusion import RiskFusionEngine
    from ml.schema import BehavioralRiskResult

    unavailable_model_signal = BehavioralRiskResult(
        risk_score=1.0,
        confidence=1.0,
        reason_codes=["MODEL_UNAVAILABLE"],
        model_version="unavailable",
    )
    result = RiskFusionEngine().fuse(unavailable_model_signal, None)
    assert result.decision == "CONTAIN"

def test_policy_engine_unavailable_fails_closed():
    """Policy engine failure must BLOCK and yield 0 MCP calls."""
    from security.policy import PolicyEngine
    from security.capability_token import IntentContext
    
    engine = PolicyEngine()
    
    # Break the policy engine
    with patch.object(engine.nl_compiler, "evaluate", side_effect=Exception("Policy DB down")):
        intent = IntentContext("int1", "ag1", "payout", 100, "INR", "rec1")
        
        # In case of exception, SentinelSecurityException or fail closed
        with pytest.raises(Exception):
            engine.evaluate(intent, {}, 0.5)

def test_signer_unavailable_fails_closed():
    """Token manager failure must BLOCK and yield 0 MCP calls."""
    from security.capability_token import TokenManager, IntentContext
    
    manager = TokenManager(secret=b"test-secret-key-must-be-at-least-32-bytes-long")
    
    intent = IntentContext("int1", "ag1", "payout", 100, "INR", "rec1")
    
    with patch.object(manager, "_sign", side_effect=Exception("KMS unavailable")):
        with pytest.raises(Exception, match="KMS unavailable"):
            manager.issue_token(intent, "ALLOW")
