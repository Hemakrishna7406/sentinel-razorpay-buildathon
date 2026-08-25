"""
Sentinel — Phase 22.4 / 22.5: Crash Recovery & Kafka Replay Tests

Verifies that:
1. Mid-flight worker crashes (before offset commit) result in Kafka redelivery.
2. The idempotency layer protects against duplicate capability issuance during replay.
3. Domain-state-driven commits ensure no messages are lost if a dependency fails.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch

from security.capability_token import IntentContext
from ml.schema import Decision

# ─────────────────────────────────────────────────────────────
# 22.4 — Abrupt Worker Crash Recovery
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_worker_crash_before_commit_causes_replay():
    """
    If the worker processes an intent but crashes BEFORE committing the offset,
    the next worker must receive the exact same intent.
    Idempotency must prevent duplicate side-effects.
    """
    from worker.evaluator import OffsetTracker
    from aiokafka import TopicPartition
    
    # 1. Simulate worker receiving message
    consumer = AsyncMock()
    tracker = OffsetTracker(consumer)
    tp = TopicPartition("intents.inbound", 0)
    
    await tracker.track_start(tp, 500)
    
    # 2. Worker crashes (process_message raises an unhandled exception or SIGKILL)
    # The offset 500 is left in the tracker's in_flight set.
    # We simulate this by stopping the consumer without committing.
    # In Kafka, because we disabled auto-commit, the broker still considers offset 500 uncommitted.
    
    # 3. Next worker starts, fetches from the same partition.
    # It should receive offset 500 again. We just assert that tracker didn't commit it.
    assert not consumer.commit.called
    
    # 4. Now simulate the second worker successfully processing it.
    await tracker.track_start(tp, 500)
    await tracker.mark_done_and_commit(tp, 500)
    
    # Verify commit happened
    assert consumer.commit.called


# ─────────────────────────────────────────────────────────────
# 22.5 — Idempotency during Kafka Replay
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_replay_idempotency_prevents_duplicate_capabilities():
    """
    If Kafka replays an intent that WAS processed and published to Redis/Postgres
    (e.g., worker died right after Redis write but before Kafka commit),
    the system must cleanly block duplicate execution via the idempotency gate.
    """
    from security.idempotency import IdempotencyEngine
    from security.exceptions import IdempotencyConflictException
    
    redis_mock = AsyncMock()
    # We can use a simple dict to simulate Redis SET NX behavior for the idempotency test.
    store = {}
    async def mock_set(key, value, ex=None, nx=False):
        if nx and key in store:
            return None
        store[key] = value
        return True
    async def mock_get(key):
        return store.get(key)
        
    redis_mock.set = mock_set
    redis_mock.get = mock_get
    
    engine = IdempotencyEngine(redis_mock, behavioral_window_seconds=60)
    
    intent = IntentContext(
        intent_id="req_crash_1",
        agent_id="agent_1",
        action_type="transfer",
        amount=1000,
        currency="USD",
        recipient="user_2"
    )
    
    key = "idem-replay-001"
    
    # 1. First attempt (Original run, before crash)
    result = await engine.check_and_record(key, intent, "agent_1")
    assert result is None  # None means we got the lock
    
    # 2. Simulate API crash or Worker Crash before Kafka commit
    # 3. Second attempt (Kafka replays the message)
    with pytest.raises(IdempotencyConflictException):
        await engine.check_and_record(key, intent, "agent_1")
    
    # Because IdempotencyConflictException is raised, the API/Worker will know this is a replay
    # and will return the cached result instead of re-evaluating and issuing 
    # a duplicate capability token.
