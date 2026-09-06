"""
Gate 18.1F — Execution Idempotency State Machine

Verifies that IdempotencyEngine provides exactly-once execution semantics
under crashes, retries, concurrent requests, and API restarts.

State machine:
  NEW (implicit) → RESERVED/PROCESSING → PUBLISHED → COMPLETED
                                        ↘ FAILED (retryable)

Critical properties:
  1. Duplicate HTTP → only ONE Kafka message
  2. Kafka failure → FAILED state, reservation RETAINED (not deleted)
  3. API restart → does NOT blindly republish
  4. Concurrent requests → exactly ONE proceeds
  5. Payload mutation on same key → BLOCKED as security violation
  6. COMPLETED replay → returns cached tx_id, no new execution
  7. FAILED state → allows safe retry
  8. Redis unavailable → FAIL CLOSED
"""

import asyncio
import json
import time
import pytest
from security.capability_token import IntentContext
from security.idempotency import IdempotencyEngine
from security.exceptions import (
    IdempotencyConflictException,
    BehavioralDuplicateException,
    SentinelSecurityException,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_intent(intent_id="int-001", amount=5000, recipient="rec-001"):
    return IntentContext(
        intent_id=intent_id,
        agent_id="agent-A",
        action_type="payout",
        amount=amount,
        currency="INR",
        recipient=recipient,
    )


class AtomicMockRedis:
    """Thread/coroutine-safe mock Redis with NX semantics."""

    def __init__(self):
        self.store: dict = {}
        self._lock = asyncio.Lock()

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None, nx=False):
        async with self._lock:
            if nx and key in self.store:
                return None
            self.store[key] = value
            return True

    async def delete(self, key):
        async with self._lock:
            self.store.pop(key, None)

    def _inject_state(self, key, state, intent_hash="abc123", tx_id=None):
        """Directly inject a state to simulate crash recovery scenarios."""
        self.store[key] = json.dumps(
            {
                "intent_hash": intent_hash,
                "state": state,
                "tx_id": tx_id,
                "timestamp": time.time(),
            }
        )


class FailingRedis:
    """Redis that always fails — for fail-closed tests."""

    async def get(self, key):
        raise ConnectionError("Redis unreachable")

    async def set(self, key, value, **kwargs):
        raise ConnectionError("Redis unreachable")

    async def delete(self, key):
        raise ConnectionError("Redis unreachable")


# ---------------------------------------------------------------------------
# 18.1F-1: Duplicate HTTP requests — only one proceeds
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_duplicate_http_only_one_reservation():
    """
    Two concurrent requests with the same idempotency key:
    only one should acquire the reservation (return None = proceed),
    the other must raise IdempotencyConflictException.
    """
    redis = AtomicMockRedis()
    engine = IdempotencyEngine(redis_client=redis, behavioral_window_seconds=60)
    intent = _make_intent()
    key = "idem-concurrent-001"

    results = []
    errors = []

    async def attempt():
        try:
            result = await engine.check_and_record(key, intent, "agent-A")
            results.append(result)
        except IdempotencyConflictException as e:
            errors.append(str(e))

    await asyncio.gather(attempt(), attempt())

    # Exactly one gets through, one is blocked
    assert len(results) == 1
    assert len(errors) == 1
    assert results[0] is None  # First caller gets reservation


@pytest.mark.asyncio
async def test_duplicate_http_100_concurrent():
    """
    100 concurrent requests with the same key — exactly 1 must proceed.
    """
    redis = AtomicMockRedis()
    engine = IdempotencyEngine(redis_client=redis, behavioral_window_seconds=60)
    intent = _make_intent()
    key = "idem-concurrent-100"

    proceeds = 0
    blocks = 0

    async def attempt():
        nonlocal proceeds, blocks
        try:
            result = await engine.check_and_record(key, intent, "agent-A")
            if result is None:
                proceeds += 1
        except (IdempotencyConflictException, BehavioralDuplicateException):
            blocks += 1

    await asyncio.gather(*[attempt() for _ in range(100)])

    assert proceeds == 1, f"Expected 1 proceed, got {proceeds}"
    assert blocks == 99, f"Expected 99 blocks, got {blocks}"


# ---------------------------------------------------------------------------
# 18.1F-2: Kafka publish failure — reservation must NOT be deleted
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_kafka_failure_reservation_retained():
    """
    If Kafka publish fails after reservation, the state should be FAILED
    and the Redis key must STILL EXIST (not deleted).

    This prevents silent loss of the security record.
    """
    redis = AtomicMockRedis()
    engine = IdempotencyEngine(redis_client=redis, behavioral_window_seconds=60)
    intent = _make_intent()
    key = "idem-kafka-fail-001"

    # Reserve
    await engine.check_and_record(key, intent, "agent-A")

    # Simulate Kafka failure — mark FAILED (should keep key)
    await engine.mark_failed(key)

    idem_key = f"idem:{key}"
    stored_raw = await redis.get(idem_key)
    assert stored_raw is not None, "Reservation must be retained after FAILED state"

    stored = json.loads(stored_raw)
    assert stored["state"] == "FAILED"


@pytest.mark.asyncio
async def test_failed_state_allows_retry():
    """
    A request that reached FAILED state can be safely retried.
    The reservation transitions back to PROCESSING.
    """
    redis = AtomicMockRedis()
    engine = IdempotencyEngine(redis_client=redis, behavioral_window_seconds=60)
    intent = _make_intent()
    key = "idem-retry-001"

    # First attempt — reserve
    await engine.check_and_record(key, intent, "agent-A")

    # Kafka failure
    await engine.mark_failed(key)

    # Retry — must succeed (return None = proceed again)
    result = await engine.check_and_record(key, intent, "agent-A")
    assert result is None, "FAILED state must allow retry"

    # State must now be PROCESSING again
    stored = json.loads(await redis.get(f"idem:{key}"))
    assert stored["state"] == "PROCESSING"


# ---------------------------------------------------------------------------
# 18.1F-3: API restart — does not blindly republish PUBLISHED state
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_api_restart_does_not_republish_published():
    """
    If the API crashes after PUBLISHED, a second API instance (simulated
    by a fresh check_and_record call on the same key) must NOT return None
    (i.e., it must NOT be treated as a new request to process).

    It should raise IdempotencyConflictException so the caller knows
    this is in-flight, not a new request.
    """
    redis = AtomicMockRedis()
    engine = IdempotencyEngine(redis_client=redis, behavioral_window_seconds=60)
    intent = _make_intent()
    key = "idem-restart-001"
    intent_hash = engine._hash_intent(intent)

    # Simulate: instance A reserved and published, then crashed
    redis._inject_state(f"idem:{key}", "PUBLISHED", intent_hash)

    # Instance B comes up and receives the same request
    with pytest.raises(IdempotencyConflictException, match="already published"):
        await engine.check_and_record(key, intent, "agent-A")


@pytest.mark.asyncio
async def test_api_restart_finds_completed_returns_tx_id():
    """
    If the API crashes after COMPLETED, a new request with the same key
    should receive the original tx_id (idempotent replay).
    """
    redis = AtomicMockRedis()
    engine = IdempotencyEngine(redis_client=redis, behavioral_window_seconds=60)
    intent = _make_intent()
    key = "idem-restart-complete-001"
    intent_hash = engine._hash_intent(intent)

    # Simulate completed state from prior execution
    redis._inject_state(f"idem:{key}", "COMPLETED", intent_hash, tx_id="tx_original_123")

    # New request on same key → must get cached tx_id back
    tx_id = await engine.check_and_record(key, intent, "agent-A")
    assert tx_id == "tx_original_123"


# ---------------------------------------------------------------------------
# 18.1F-4: Payload mutation on same key is blocked as security violation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_payload_mutation_blocked():
    """
    Using the same idempotency key with a different payload (amount mutation)
    must be blocked as a security violation.
    """
    redis = AtomicMockRedis()
    engine = IdempotencyEngine(redis_client=redis, behavioral_window_seconds=60)
    intent_a = _make_intent(amount=5000)
    intent_b = _make_intent(amount=99999)  # mutated amount
    key = "idem-mutation-001"

    await engine.check_and_record(key, intent_a, "agent-A")

    with pytest.raises(IdempotencyConflictException, match="different payload parameters"):
        await engine.check_and_record(key, intent_b, "agent-A")


# ---------------------------------------------------------------------------
# 18.1F-5: COMPLETED replay returns cached tx_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_completed_replay_returns_cached_tx_id():
    """
    After a successful execution (COMPLETED), re-submitting the same
    idempotency key must return the original tx_id without any new execution.
    """
    redis = AtomicMockRedis()
    engine = IdempotencyEngine(redis_client=redis, behavioral_window_seconds=60)
    intent = _make_intent()
    key = "idem-complete-001"

    # First request
    await engine.check_and_record(key, intent, "agent-A")
    intent_hash = engine._hash_intent(intent)

    # Simulate successful execution
    await engine.mark_completed(key, intent_hash, "tx_abc_xyz")

    # Replay → must get tx_id back
    tx_id = await engine.check_and_record(key, intent, "agent-A")
    assert tx_id == "tx_abc_xyz"


# ---------------------------------------------------------------------------
# 18.1F-6: Redis unavailable → FAIL CLOSED
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_redis_unavailable_fails_closed():
    """
    If Redis is down, the idempotency engine must raise SentinelSecurityException
    (fail closed) — never allow unguarded execution.
    """
    engine = IdempotencyEngine(redis_client=FailingRedis(), behavioral_window_seconds=60)
    intent = _make_intent()

    with pytest.raises(SentinelSecurityException, match="Distributed state unavailable"):
        await engine.check_and_record("idem-redis-down-001", intent, "agent-A")


# ---------------------------------------------------------------------------
# 18.1F-7: State transition ordering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_state_transitions_in_order():
    """
    Verify the correct lifecycle: PROCESSING → PUBLISHED → COMPLETED.
    Each mark_* call must update state correctly.
    """
    redis = AtomicMockRedis()
    engine = IdempotencyEngine(redis_client=redis, behavioral_window_seconds=60)
    intent = _make_intent()
    key = "idem-lifecycle-001"
    idem_key = f"idem:{key}"

    # 1. Reserve
    await engine.check_and_record(key, intent, "agent-A")
    state = json.loads(await redis.get(idem_key))["state"]
    assert state == "PROCESSING"

    # 2. Publish
    await engine.mark_published(key)
    state = json.loads(await redis.get(idem_key))["state"]
    assert state == "PUBLISHED"

    # 3. Complete
    intent_hash = engine._hash_intent(intent)
    await engine.mark_completed(key, intent_hash, "tx_lifecycle_001")
    stored = json.loads(await redis.get(idem_key))
    assert stored["state"] == "COMPLETED"
    assert stored["tx_id"] == "tx_lifecycle_001"
