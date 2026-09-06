"""
Gate 18.1E — Redis JTI Distributed Replay Protection

Verifies that the ExecutionGateway's JTI claim logic satisfies:
  1. First execution       → succeeds (SET NX acquires)
  2. Second execution      → BLOCK (replay attack detected)
  3. Concurrent execution  → exactly one succeeds
  4. Redis unavailable     → FAIL CLOSED (0 provider calls)
  5. TTL expiration        → expired token re-uses are blocked by token verify first

Security invariant: NO MCP call occurs if JTI claim fails.
"""

import asyncio
import time
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from security.capability_token import TokenManager, IntentContext, CapabilityPayload
from execution.gateway import ExecutionGateway
from execution.schema import ExecutionReceipt

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_intent(
    intent_id="int-001", agent_id="agent-A", action="create_order", amount=5000, currency="INR", recipient="rec-001"
):
    return IntentContext(
        intent_id=intent_id,
        agent_id=agent_id,
        action_type=action,
        amount=amount,
        currency=currency,
        recipient=recipient,
    )


def _make_receipt(execution_id="exec_abc123"):
    return ExecutionReceipt(
        execution_id=execution_id,
        intent_id="int-001",
        decision_id="dec-001",
        capability_jti="jti-001",
        agent_id="agent-A",
        requested_action="create_order",
        mcp_tool="create_order",
        requested_amount=5000,
        executed_amount=5000,
        currency="INR",
        provider="razorpay",
        environment="test",
        status="SUCCESS",
        latency_ms=120,
        verification_status="VERIFIED",
        timestamp="2026-08-24T00:00:00Z",
        provider_reference="order_xyz",
    )


def _make_gateway(redis_mock):
    """Create an ExecutionGateway with a real TokenManager but mocked Redis + provider."""
    tm = TokenManager()
    provider = AsyncMock()
    provider.execute.return_value = _make_receipt()
    return ExecutionGateway(tm, provider, replay_store=redis_mock), tm, provider


# ---------------------------------------------------------------------------
# Gate 18.1E-1: First execution succeeds
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_jti_first_claim_succeeds():
    """
    First call with a fresh JTI must succeed end-to-end.
    Provider must be called exactly once.
    """
    redis_mock = AsyncMock()
    redis_mock.set.return_value = True  # SET NX acquired

    gateway, tm, provider = _make_gateway(redis_mock)
    intent = _make_intent()
    token = tm.issue_token(intent, decision="ALLOW")

    receipt = await gateway.execute(token, intent)

    assert receipt.status == "SUCCESS"
    redis_mock.set.assert_called_once()
    # Confirm NX was set
    call_kwargs = redis_mock.set.call_args
    assert call_kwargs.kwargs.get("nx") is True
    provider.execute.assert_called_once()


# ---------------------------------------------------------------------------
# Gate 18.1E-2: Second execution with same JTI is BLOCKED
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_jti_replay_is_blocked():
    """
    Second call with the same JTI must raise ValueError.
    Provider must NOT be called on the second attempt.
    """
    redis_mock = AsyncMock()
    # First call acquires, second returns None (key already exists)
    redis_mock.set.side_effect = [True, None]

    gateway, tm, provider = _make_gateway(redis_mock)
    intent = _make_intent()
    token = tm.issue_token(intent, decision="ALLOW")

    # First execution succeeds
    await gateway.execute(token, intent)
    assert provider.execute.call_count == 1

    # Second execution is BLOCKED
    with pytest.raises(ValueError, match="replay attack"):
        await gateway.execute(token, intent)

    # Provider still only called once
    assert provider.execute.call_count == 1


# ---------------------------------------------------------------------------
# Gate 18.1E-3: Concurrent execution — exactly one succeeds
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_jti_concurrent_only_one_succeeds():
    """
    Concurrent calls with the same JTI must result in exactly one success
    and all others raising ValueError.
    """
    # Simulate realistic Redis NX: only first SET returns True
    call_count = 0

    async def mock_set(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return True  # First caller wins the lock
        return None  # Subsequent callers lose

    redis_mock = AsyncMock()
    redis_mock.set.side_effect = mock_set

    gateway, tm, provider = _make_gateway(redis_mock)
    intent = _make_intent()
    # Issue same token to all concurrent tasks (same JTI)
    token = tm.issue_token(intent, decision="ALLOW")

    results = []
    errors = []

    async def attempt():
        try:
            r = await gateway.execute(token, intent)
            results.append(r)
        except ValueError as e:
            errors.append(str(e))

    # Launch 5 concurrent attempts
    await asyncio.gather(*[attempt() for _ in range(5)])

    assert len(results) == 1, f"Expected exactly 1 success, got {len(results)}"
    assert len(errors) == 4, f"Expected 4 blocked attempts, got {len(errors)}"
    assert provider.execute.call_count == 1


# ---------------------------------------------------------------------------
# Gate 18.1E-4: Redis unavailable → FAIL CLOSED
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_jti_redis_unavailable_fails_closed():
    """
    If Redis raises an exception during JTI claim, the gateway must
    fail closed: raise ValueError and NOT call the provider.
    """
    redis_mock = AsyncMock()
    redis_mock.set.side_effect = ConnectionError("Redis connection refused")

    gateway, tm, provider = _make_gateway(redis_mock)
    intent = _make_intent()
    token = tm.issue_token(intent, decision="ALLOW")

    with pytest.raises(ValueError, match="Replay-protection state unavailable"):
        await gateway.execute(token, intent)

    # Critical invariant: provider was NEVER called
    provider.execute.assert_not_called()


# ---------------------------------------------------------------------------
# Gate 18.1E-5: No replay_store falls back to in-memory set (isolated mode)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_jti_inmemory_fallback_blocks_replay():
    """
    When replay_store=None (isolated tests), the in-memory _consumed_jtis set
    must still block replays.
    """
    tm = TokenManager()
    provider = AsyncMock()
    provider.execute.return_value = _make_receipt("exec_inmem")
    gateway = ExecutionGateway(tm, provider, replay_store=None)
    intent = _make_intent()
    token = tm.issue_token(intent, decision="ALLOW")

    # First call succeeds
    await gateway.execute(token, intent)
    assert provider.execute.call_count == 1

    # Second call is blocked even with in-memory store
    with pytest.raises(ValueError, match="replay attack"):
        await gateway.execute(token, intent)

    assert provider.execute.call_count == 1


# ---------------------------------------------------------------------------
# Gate 18.1E-6: TTL is derived from token expiry (not hardcoded)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_jti_ttl_derived_from_token_expiry():
    """
    The Redis SET command must use ex= derived from the token's expires_at,
    not a hardcoded constant.
    """
    redis_mock = AsyncMock()
    redis_mock.set.return_value = True

    gateway, tm, provider = _make_gateway(redis_mock)
    intent = _make_intent()
    token = tm.issue_token(intent, decision="ALLOW")

    # Decode expected TTL
    payload = tm.verify_token(token, intent, consume=False)
    expected_ttl_approx = max(1, payload.expires_at - int(time.time()))

    await gateway.execute(token, intent)

    call_kwargs = redis_mock.set.call_args
    actual_ex = call_kwargs.kwargs.get("ex")

    # TTL should be within 5 seconds of expected (test timing tolerance)
    assert actual_ex is not None, "ex= must be set in the Redis SET call"
    assert (
        abs(actual_ex - expected_ttl_approx) <= 5
    ), f"TTL {actual_ex} deviates too far from expected {expected_ttl_approx}"
