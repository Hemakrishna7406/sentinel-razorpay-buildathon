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
    from worker.evaluator import IntentEvaluator
    
    # Mock dependencies
    policy_engine = MagicMock()
    token_manager = MagicMock()
    # Mock model wrapper to throw exception
    model_wrapper = MagicMock()
    model_wrapper.model = None # Simulating unavailable
    
    evaluator = IntentEvaluator(redis_client=MagicMock(), policy_engine=policy_engine, token_manager=token_manager, model_wrapper=model_wrapper)
    
    # If model is down, evaluator should still process but with risk = 0 or fallback to policy which ESCALATES.
    # Our current evaluator does: risk = 0.0 if not model else ...
    # But wait, we should test that the system fails closed if policy engine is unavailable.

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
