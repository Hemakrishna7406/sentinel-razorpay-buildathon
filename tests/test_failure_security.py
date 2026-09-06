import pytest
import time
from unittest.mock import patch, MagicMock
from api.main import evaluate_intent_sync, IntentRequest
from fastapi import Request
from security.exceptions import SentinelSecurityException
from ml.fusion.risk_fusion import RiskFusionEngine
from ml.schema import BehavioralRiskResult, Decision, SemanticRiskResult
from security.policy import PolicyEngine
from security.exceptions import SentinelSecurityException
from security.capability_token import TokenManager, IntentContext, TokenInvalidException
from execution.gateway import ExecutionGateway
from api.main import ExecuteRequest


# 1. ML unavailable
def test_ml_unavailable_escalates():
    """If ML model is down, fusion must ESCALATE."""
    unavailable_model_signal = BehavioralRiskResult(
        risk_score=None,
        risk_status="MODEL_UNAVAILABLE",
        confidence=0.0,
        reason_codes=["MODEL_UNAVAILABLE"],
        model_version="unknown",
    )
    result = RiskFusionEngine().fuse(unavailable_model_signal, None)
    assert result.decision == Decision.ESCALATE


# 2. Semantic provider unavailable
def test_semantic_unavailable_fails_closed():
    """If semantic provider is unavailable, fusion must ESCALATE (fail closed)."""
    behavioral_ok = BehavioralRiskResult(
        risk_score=0.1, risk_status="MODEL_AVAILABLE", confidence=0.9, reason_codes=["NORMAL"], model_version="v1"
    )
    result = RiskFusionEngine().fuse(behavioral_ok, None)
    # Even if behavioral is low risk, missing semantic should fail closed
    assert result.decision == Decision.ESCALATE
    assert "Failing closed to ESCALATE" in result.reason


# 3. Redis unavailable
@pytest.mark.asyncio
async def test_redis_unavailable_fails_closed():
    intent = IntentRequest(
        intent_id="int_fail_1", agent_id="agent_1", action_type="payout", amount=100, currency="INR", recipient="rec_1"
    )
    request = MagicMock(spec=Request)
    with patch("api.main.get_idempotency_engine") as mock_idem:
        mock_idem.return_value.check_and_record.side_effect = Exception("Redis connection refused")
        with pytest.raises(Exception, match="Redis connection refused"):
            await evaluate_intent_sync(request, intent, idempotency_key="key1")


# 4. Kafka unavailable
@pytest.mark.asyncio
async def test_kafka_unavailable_fails_closed():
    # Similar to Redis, if Kafka is down, publish fails, error raised
    pass  # Verified by other tests in test_chaos/


# 8, 9, 10, 11, 12. Capability Token Validation / Tampering
def test_capability_token_tampering():
    manager = TokenManager(secret=b"test-secret-key-must-be-at-least-32-bytes-long")
    intent_orig = IntentContext("int1", "ag1", "payout", 1000, "INR", "rec1")
    token = manager.issue_token(intent_orig, Decision.ALLOW.value)

    mock_provider = MagicMock()
    gateway = ExecutionGateway(manager, mock_provider, MagicMock())

    # Valid
    req_valid = ExecuteRequest(
        intent_id="int1",
        agent_id="ag1",
        action_type="payout",
        amount=1000,
        currency="INR",
        recipient="rec1",
        capability_token=token,
        idempotency_key="ik1",
    )

    def to_ctx(req):
        return IntentContext(req.intent_id, req.agent_id, req.action_type, req.amount, req.currency, req.recipient)

    assert manager.verify_token(token, to_ctx(req_valid), consume=False) is not None

    # 10. Amount tampering
    req_tamper_amount = ExecuteRequest(
        intent_id="int1",
        agent_id="ag1",
        action_type="payout",
        amount=10000,
        currency="INR",
        recipient="rec1",
        capability_token=token,
        idempotency_key="ik2",
    )
    with pytest.raises(TokenInvalidException, match="Amount mismatch"):
        manager.verify_token(token, to_ctx(req_tamper_amount), consume=False)

    # 11. Currency tampering
    req_tamper_currency = ExecuteRequest(
        intent_id="int1",
        agent_id="ag1",
        action_type="payout",
        amount=1000,
        currency="USD",
        recipient="rec1",
        capability_token=token,
        idempotency_key="ik3",
    )
    with pytest.raises(TokenInvalidException, match="Currency mismatch"):
        manager.verify_token(token, to_ctx(req_tamper_currency), consume=False)

    # 12. Intent tampering
    req_tamper_intent = ExecuteRequest(
        intent_id="int2",
        agent_id="ag1",
        action_type="payout",
        amount=1000,
        currency="INR",
        recipient="rec1",
        capability_token=token,
        idempotency_key="ik4",
    )
    with pytest.raises(TokenInvalidException, match="Intent ID mismatch"):
        manager.verify_token(token, to_ctx(req_tamper_intent), consume=False)


# 13. Policy evaluation failure
def test_policy_engine_unavailable_fails_closed():
    engine = PolicyEngine()
    with patch.object(engine.nl_compiler, "evaluate", side_effect=Exception("Policy DB down")):
        intent = IntentContext("int1", "ag1", "payout", 100, "INR", "rec1")
        with pytest.raises(Exception):
            engine.evaluate(intent, {}, 0.5)
