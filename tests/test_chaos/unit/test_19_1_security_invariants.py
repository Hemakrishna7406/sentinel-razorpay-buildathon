import pytest
import time
from unittest.mock import AsyncMock

from security.capability_token import TokenManager, IntentContext, CapabilityTokenException
from execution.gateway import ExecutionGateway
from security.exceptions import SentinelSecurityException
from execution.schema import ExecutionReceipt


@pytest.fixture
def token_manager():
    return TokenManager(secret=b"chaos_test_secret_key")


@pytest.fixture
def mock_provider():
    provider = AsyncMock()
    # By default, mock successful receipt
    provider.execute = AsyncMock(
        return_value=ExecutionReceipt(
            execution_id="mock_tx_123",
            intent_id="intent_123",
            decision_id="ALLOW",
            capability_jti="jti_123",
            agent_id="agent_123",
            requested_action="refund",
            mcp_tool="update_refund",
            requested_amount=1000,
            executed_amount=1000,
            currency="INR",
            provider="razorpay-mcp",
            environment="test",
            status="SUCCESS",
            latency_ms=10,
            verification_status="VERIFIED",
            timestamp=str(time.time()),
            provider_reference=None,
        )
    )
    provider.get_health = AsyncMock(return_value={"status": "CONNECTED"})
    return provider


@pytest.fixture
def gateway(token_manager, mock_provider):
    return ExecutionGateway(token_manager, mock_provider, replay_store=None)


@pytest.fixture
def valid_intent():
    return IntentContext(
        intent_id="intent_123",
        agent_id="agent_123",
        action_type="refund",
        amount=1000,
        currency="INR",
        recipient="user_abc",
    )


@pytest.mark.asyncio
async def test_no_token_no_execution(gateway, valid_intent, mock_provider):
    """Execution must fail if no token is provided."""
    with pytest.raises(ValueError, match="Missing capability token"):
        await gateway.execute("", valid_intent)
    mock_provider.execute.assert_not_called()


@pytest.mark.asyncio
async def test_expired_token_rejection(gateway, token_manager, valid_intent, mock_provider):
    token = token_manager.issue_token(valid_intent, decision="ALLOW")
    import base64
    import json
    import hmac
    import hashlib

    payload, signature = token.split(".")
    payload_dict = json.loads(payload)
    payload_dict["expires_at"] = int(time.time()) - 10
    new_payload = json.dumps(payload_dict, sort_keys=True)
    new_sig = hmac.new(token_manager._secret, new_payload.encode(), hashlib.sha256).hexdigest()
    expired_token = f"{new_payload}.{new_sig}"

    with pytest.raises(ValueError, match="Execution rejected: Token expired"):
        await gateway.execute(expired_token, valid_intent)
    mock_provider.execute.assert_not_called()


@pytest.mark.asyncio
async def test_token_binding_mismatch(gateway, token_manager, valid_intent, mock_provider):
    token = token_manager.issue_token(valid_intent, decision="ALLOW")

    mismatched_intent = IntentContext(
        intent_id=valid_intent.intent_id,
        agent_id=valid_intent.agent_id,
        action_type="refund",
        amount=2000,  # Mismatch
        currency=valid_intent.currency,
        recipient=valid_intent.recipient,
    )

    with pytest.raises(ValueError, match="Execution rejected: .*mismatch"):
        await gateway.execute(token, mismatched_intent)
    mock_provider.execute.assert_not_called()


@pytest.mark.asyncio
async def test_tampered_token(gateway, token_manager, valid_intent, mock_provider):
    token = token_manager.issue_token(valid_intent, decision="ALLOW")
    tampered = token[:-5] + "12345"
    with pytest.raises(ValueError, match="Execution rejected: Invalid signature"):
        await gateway.execute(tampered, valid_intent)
    mock_provider.execute.assert_not_called()


@pytest.mark.asyncio
async def test_consumed_jti_replay_protection(gateway, token_manager, valid_intent, mock_provider):
    token = token_manager.issue_token(valid_intent, decision="ALLOW")

    receipt = await gateway.execute(token, valid_intent)
    assert receipt.status == "SUCCESS"
    assert mock_provider.execute.call_count == 1

    with pytest.raises(ValueError, match="Execution rejected: Token has already been consumed"):
        await gateway.execute(token, valid_intent)

    assert mock_provider.execute.call_count == 1
