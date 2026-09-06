import pytest
import json
from unittest.mock import AsyncMock

from execution.gateway import ExecutionGateway
from execution.schema import ExecutionReceipt
from security.idempotency import IdempotencyEngine


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.set = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=None)
    redis.delete = AsyncMock()
    return redis


@pytest.mark.asyncio
async def test_19l_reconciliation_endpoint():
    """
    19L: Reconciliation converts UNKNOWN to CONFIRMED_FAILED if upstream
    says the execution did not happen.
    """
    token_manager = AsyncMock()
    provider = AsyncMock()
    provider.get_health = AsyncMock(return_value={"status": "CONNECTED"})

    gateway = ExecutionGateway(token_manager, provider)

    receipt = ExecutionReceipt(
        execution_id="fail_123",
        intent_id="intent_123",
        decision_id="ALLOW",
        capability_jti="jti_123",
        agent_id="a",
        requested_action="refund",
        mcp_tool="update_refund",
        requested_amount=100,
        executed_amount=0,
        currency="INR",
        provider="razorpay-mcp",
        environment="test",
        status="UNKNOWN",
        latency_ms=0,
        verification_status="VERIFIED",
        timestamp="now",
        provider_reference="Timeout",
    )

    reconciled_receipt = await gateway.reconcile(receipt)
    assert reconciled_receipt.status == "CONFIRMED_FAILED"


@pytest.mark.asyncio
async def test_19m_orphaned_lock_reclamation(mock_redis):
    """
    19M: FAILED state allows idempotency check to succeed on retry
    instead of throwing ConflictException.
    """
    from security.capability_token import IntentContext

    valid_intent = IntentContext(
        intent_id="intent_abc", agent_id="agent_123", action_type="refund", amount=100, currency="INR", recipient="r"
    )

    engine = IdempotencyEngine(mock_redis)
    mock_redis.set.return_value = False
    mock_redis.get.return_value = json.dumps(
        {"intent_hash": engine._hash_intent(valid_intent), "state": "FAILED", "tx_id": None}
    )

    # If the state is FAILED, it should allow the retry (returning None)
    # instead of throwing IdempotencyConflictException
    tx_id = await engine.check_and_record("idem_key_1", valid_intent, "agent_123")

    assert tx_id is None
