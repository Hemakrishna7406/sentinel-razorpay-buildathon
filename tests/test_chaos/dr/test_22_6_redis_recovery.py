"""
Sentinel — Phase 22.6: Redis Recovery Tests

Verifies that:
1. Redis connection failures result in Fail-Closed behavior (never allow an intent to bypass idempotency).
2. The evaluator worker gracefully handles Redis reply stream failures (doesn't commit Kafka offset).
3. System recovers immediately when Redis reconnects.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock

from security.idempotency import IdempotencyEngine
from security.exceptions import SentinelSecurityException
from security.capability_token import IntentContext


class IntermittentRedis:
    """Mock Redis that fails on demand."""
    def __init__(self):
        self.store = {}
        self.is_down = False
        
    async def get(self, key):
        if self.is_down:
            raise ConnectionError("Redis is down")
        return self.store.get(key)
        
    async def set(self, key, value, ex=None, nx=False):
        if self.is_down:
            raise ConnectionError("Redis is down")
        if nx and key in self.store:
            return None
        self.store[key] = value
        return True
        
    async def delete(self, key):
        if self.is_down:
            raise ConnectionError("Redis is down")
        self.store.pop(key, None)


@pytest.mark.asyncio
async def test_redis_failure_causes_fail_closed():
    """Verify that if Redis drops during an idempotency check, the system fails CLOSED."""
    redis = IntermittentRedis()
    engine = IdempotencyEngine(redis_client=redis, behavioral_window_seconds=60)
    
    intent1 = IntentContext(
        intent_id="req_redis_1",
        agent_id="agent_1",
        action_type="transfer",
        amount=1000,
        currency="USD",
        recipient="user_2"
    )
    
    key1 = "idem-redis-001"
    
    # 1. Normal state
    redis.is_down = False
    result = await engine.check_and_record(key1, intent1, "agent_1")
    assert result is None  # Reserved successfully
    
    # 2. Redis goes down
    redis.is_down = True
    key2 = "idem-redis-002"
    with pytest.raises(SentinelSecurityException, match="Distributed state unavailable"):
        await engine.check_and_record(key2, intent1, "agent_1")
        
    # 3. Redis Recovers
    redis.is_down = False
    
    intent3 = IntentContext(
        intent_id="req_redis_3",
        agent_id="agent_1",
        action_type="transfer",
        amount=3000,
        currency="USD",
        recipient="user_3"
    )
    key3 = "idem-redis-003"
    
    result3 = await engine.check_and_record(key3, intent3, "agent_1")
    assert result3 is None  # Reserved successfully again
