import pytest
from unittest.mock import MagicMock, AsyncMock
from execution.gateway import ExecutionGateway
from security.capability_token import TokenManager, IntentContext
from security.exceptions import SentinelSecurityException


@pytest.fixture
def token_manager():
    return TokenManager(secret=b"test-secret-key-must-be-at-least-32-bytes-long")


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.execute = AsyncMock(return_value="tx_mock_123")
    return provider


@pytest.fixture
def mock_redis_replay_store():
    # A simple dict-based mock for redis SET NX
    class FakeRedis:
        def __init__(self):
            self.store = {}

        async def set(self, key, value, ex=None, nx=False):
            if nx and key in self.store:
                return None
            self.store[key] = value
            return True

    return FakeRedis()


@pytest.fixture
def gateway(token_manager, mock_provider, mock_redis_replay_store):
    return ExecutionGateway(token_manager, mock_provider, mock_redis_replay_store)


@pytest.fixture
def valid_context():
    return IntentContext(
        intent_id="int_123", agent_id="agent_1", action_type="payout", amount=5000, currency="INR", recipient="bank_1"
    )


@pytest.mark.asyncio
async def test_execution_no_token(gateway, valid_context, mock_provider):
    with pytest.raises(ValueError, match="Missing capability token"):
        await gateway.execute(None, valid_context)
    mock_provider.execute.assert_not_called()


@pytest.mark.asyncio
async def test_execution_expired_token(gateway, valid_context, mock_provider, token_manager):
    token = token_manager.issue_token(valid_context, "ALLOW", ttl_seconds=-1)
    with pytest.raises(ValueError, match="Token expired"):
        await gateway.execute(token, valid_context)
    mock_provider.execute.assert_not_called()


@pytest.mark.asyncio
async def test_execution_mutated_token(gateway, valid_context, mock_provider, token_manager):
    token = token_manager.issue_token(valid_context, "ALLOW")
    payload_str, signature = token.rsplit(".", 1)
    mutated = f"{payload_str.replace('5000', '9999')}.{signature}"
    with pytest.raises(ValueError, match="Invalid signature"):
        await gateway.execute(mutated, valid_context)
    mock_provider.execute.assert_not_called()


@pytest.mark.asyncio
async def test_execution_privilege_violation(gateway, valid_context, mock_provider, token_manager):
    # Token issued for 5000
    token = token_manager.issue_token(valid_context, "ALLOW")
    # Attacker tries to execute 99999
    malicious_context = IntentContext(
        intent_id="int_123", agent_id="agent_1", action_type="payout", amount=99999, currency="INR", recipient="bank_1"
    )
    with pytest.raises(ValueError, match="Amount mismatch"):
        await gateway.execute(token, malicious_context)
    mock_provider.execute.assert_not_called()


@pytest.mark.asyncio
async def test_execution_replayed_token(gateway, valid_context, mock_provider, token_manager):
    token = token_manager.issue_token(valid_context, "ALLOW")

    # First execution succeeds
    tx_id = await gateway.execute(token, valid_context)
    assert tx_id == "tx_mock_123"
    assert mock_provider.execute.call_count == 1

    # Second execution with same token is blocked by Redis SET NX check
    with pytest.raises(ValueError, match="Capability token has already been consumed|Token has already been consumed"):
        await gateway.execute(token, valid_context)

    # Provider must NOT be called a second time
    assert mock_provider.execute.call_count == 1
