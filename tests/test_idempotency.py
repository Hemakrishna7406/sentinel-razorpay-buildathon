"""
Tests for Idempotency and Duplicate Detection.
"""

import time
import json
import pytest

from security.capability_token import IntentContext
from security.idempotency import IdempotencyEngine
from security.exceptions import IdempotencyConflictException, BehavioralDuplicateException


class MockRedis:
    def __init__(self):
        self.store = {}
    async def get(self, key):
        return self.store.get(key)
    async def set(self, key, value, ex=None, nx=False):
        self.store[key] = value


@pytest.fixture
def engine():
    return IdempotencyEngine(redis_client=MockRedis(), behavioral_window_seconds=1)


@pytest.fixture
def base_intent():
    return IntentContext(
        intent_id="idem_test_1",
        agent_id="agent_1",
        action_type="payout",
        amount=1000,
        currency="INR",
        recipient="bank_1"
    )


@pytest.mark.asyncio
async def test_idempotency_exact_match(engine, base_intent):
    """Same intent_id and identical payload returns the execution ID."""
    key = "idem_key_1"
    
    # First execution
    tx_id_1 = await engine.check_and_record(key, base_intent, "agent_1")
    assert tx_id_1 is None
    
    # Simulate execution success
    hash_val = engine._hash_intent(base_intent)
    await engine.mark_completed(key, hash_val, "tx_123")
    
    # Second execution
    tx_id_2 = await engine.check_and_record(key, base_intent, "agent_1")
    assert tx_id_2 == "tx_123"


@pytest.mark.asyncio
async def test_idempotency_conflict(engine, base_intent):
    """Same intent_id but DIFFERENT payload raises a security exception."""
    key = "idem_key_2"
    await engine.check_and_record(key, base_intent, "agent_1")
    
    mutated_intent = IntentContext(
        intent_id="idem_test_1",
        agent_id="agent_1",
        action_type="payout",
        amount=5000,  # Changed
        currency="INR",
        recipient="bank_123"
    )
    
    with pytest.raises(IdempotencyConflictException, match="different payload parameters"):
        await engine.check_and_record(key, mutated_intent, "agent_1")


@pytest.mark.asyncio
async def test_behavioral_duplicate(engine, base_intent):
    """Different intent_id but identical payload within window raises behavioral exception."""
    key1 = "idem_key_3"
    key2 = "idem_key_4"
    
    await engine.check_and_record(key1, base_intent, "agent_1")
    
    with pytest.raises(BehavioralDuplicateException, match="Behavioral duplicate detected"):
        await engine.check_and_record(key2, base_intent, "agent_1")


@pytest.mark.asyncio
async def test_behavioral_duplicate_expires(engine, base_intent):
    """Behavioral duplicate check expires after the time window."""
    key1 = "idem_key_5"
    key2 = "idem_key_6"
    
    await engine.check_and_record(key1, base_intent, "agent_1")
    
    # Simulate window expiration
    engine.redis_client.store.clear()
    
    tx_id = await engine.check_and_record(key2, base_intent, "agent_1")
    assert tx_id is None

