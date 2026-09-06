import pytest
import time
from unittest.mock import AsyncMock, patch

from execution.gateway import ExecutionGateway
from execution.schema import ExecutionReceipt
from security.capability_token import TokenManager, IntentContext
from security.idempotency import IdempotencyEngine
from security.exceptions import SentinelSecurityException


@pytest.fixture
def valid_intent():
    return IntentContext(
        intent_id="intent_unit_chaos",
        agent_id="agent_123",
        action_type="refund",
        amount=1000,
        currency="INR",
        recipient="user_abc",
    )


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.set = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=None)
    return redis


@pytest.fixture
def token_manager():
    return TokenManager(secret=b"unit_chaos_secret")


# --- 19A: Redis Failure ---
@pytest.mark.asyncio
async def test_19a_redis_failure(valid_intent, mock_redis):
    """
    19A: Redis failure mid-request must result in fast fail-closed (ESCALATE)
    and zero unauthorized MCP calls.
    """
    mock_redis.set.side_effect = ConnectionError("Redis outage")
    engine = IdempotencyEngine(mock_redis)

    with pytest.raises(SentinelSecurityException, match="Distributed state unavailable"):
        await engine.check_and_record("idem_key_1", valid_intent, "agent_123")


# --- 19E: MCP Failure (Definitive vs Ambiguous) ---
@pytest.mark.asyncio
async def test_19e_mcp_definitive_failure(token_manager, valid_intent):
    """
    19E.1: Definitive MCP failure (503) should result in FAILED state.
    JTI is consumed, no financial mutation.
    """
    provider = AsyncMock()
    # Simulate a generic exception from httpx translating to FAILED
    provider.execute.side_effect = Exception("503 Service Unavailable")
    gateway = ExecutionGateway(token_manager, provider)

    token = token_manager.issue_token(valid_intent, decision="ALLOW")

    # Since execute() handles exceptions now, it returns a receipt with FAILED
    receipt = await gateway.execute(token, valid_intent)
    assert receipt.status == "FAILED"
    assert "503" in receipt.provider_reference


@pytest.mark.asyncio
async def test_19e_mcp_ambiguous_failure(token_manager, valid_intent):
    """
    19E.2: Ambiguous MCP failure (timeout) should result in UNKNOWN state.
    """
    provider = AsyncMock()
    # "timeout" in the error string triggers UNKNOWN state in the adapter
    from execution.adapters.mcp_adapter import RazorpayMCPAdapter

    adapter = RazorpayMCPAdapter(environment="test")
    # Mock the _session.call_tool to raise TimeoutError
    adapter._session = AsyncMock()
    adapter._session.call_tool.side_effect = TimeoutError("ReadTimeout")
    adapter.status = "CONNECTED"

    adapter.tool_cache = ["update_refund"]
    gateway = ExecutionGateway(token_manager, adapter)
    token = token_manager.issue_token(valid_intent, decision="ALLOW")

    receipt = await gateway.execute(token, valid_intent)
    assert receipt.status == "UNKNOWN"


# --- 19F: ML Failure ---
def test_19f_ml_failure_fusion():
    """
    19F: Missing ML risk (NULL) triggers ESCALATE, never assumed safe.
    """
    from ml.fusion.risk_fusion import RiskFusionEngine
    from ml.schema import BehavioralRiskResult, Decision

    fusion = RiskFusionEngine()
    behavioral = BehavioralRiskResult(
        risk_score=None,
        risk_status="MODEL_UNAVAILABLE",
        confidence=0.0,
        reason_codes=["MODEL_UNAVAILABLE"],
        model_version="xgb-v3",
    )

    result = fusion.fuse(behavioral, semantic=None)
    assert result.decision == Decision.ESCALATE
    assert result.final_risk is None
    assert "Behavioral model unavailable" in result.reason


# --- 19G: Policy Engine Crash ---
def test_19g_policy_engine_crash(valid_intent):
    """
    19G: Policy engine crash must not bypass security.
    """
    from security.policy import PolicyEngine

    engine = PolicyEngine()

    # Mock nl_compiler to raise an exception
    engine.nl_compiler.evaluate = lambda ctx: (_ for _ in ()).throw(RuntimeError("Policy engine crash"))

    from ml.schema import RiskAssessment, BehavioralRiskResult, FusionResult, Decision

    assessment = RiskAssessment(
        behavioral=BehavioralRiskResult(risk_score=0.1, confidence=1.0, reason_codes=["OK"], model_version="v1"),
        fusion=FusionResult(final_risk=0.1, disagreement=False, decision=Decision.ALLOW, reason="OK"),
    )

    with pytest.raises(RuntimeError, match="Policy engine crash"):
        engine.evaluate(valid_intent, {}, assessment)


# --- 19H: Signer Failure ---
def test_19h_signer_failure(valid_intent):
    """
    19H: Signer failure returns ESCALATE even if policy allowed.
    """
    from security.policy import PolicyEngine

    engine = PolicyEngine()

    # Sabotage the token manager
    engine.token_manager.issue_token = lambda intent, decision: (_ for _ in ()).throw(Exception("KMS Down"))

    from ml.schema import RiskAssessment, BehavioralRiskResult, FusionResult, Decision

    assessment = RiskAssessment(
        behavioral=BehavioralRiskResult(risk_score=0.1, confidence=1.0, reason_codes=["OK"], model_version="v1"),
        fusion=FusionResult(final_risk=0.1, disagreement=False, decision=Decision.ALLOW, reason="OK"),
    )

    decision, reason, token = engine.evaluate(valid_intent, {"has_sufficient_history": 1}, assessment)
    assert decision == Decision.ESCALATE
    assert token is None
    assert "Failed to issue capability token: KMS Down" in reason


# --- 19K: Execution State Machine Manipulations ---
@pytest.mark.asyncio
async def test_19k_state_machine_invalid_transitions(mock_redis, valid_intent):
    """
    19K: Idempotency state machine must block invalid transitions.
    """
    import json

    engine = IdempotencyEngine(mock_redis)

    # If state is COMPLETED, it returns the tx_id instead of raising (idempotent replay)
    mock_redis.set.return_value = False
    mock_redis.get.return_value = json.dumps(
        {"intent_hash": engine._hash_intent(valid_intent), "state": "COMPLETED", "tx_id": "tx_123"}
    )

    tx_id = await engine.check_and_record("idem_key_2", valid_intent, "agent_123")
    assert tx_id == "tx_123"

    # If state is PUBLISHED, it raises IdempotencyConflictException
    mock_redis.get.return_value = json.dumps({"intent_hash": engine._hash_intent(valid_intent), "state": "PUBLISHED"})
    from security.exceptions import IdempotencyConflictException

    with pytest.raises(IdempotencyConflictException, match="already published"):
        await engine.check_and_record("idem_key_3", valid_intent, "agent_123")
