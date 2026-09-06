"""
Sentinel — Concurrency and Resiliency Tests

Verifies exactly-once execution invariants under highly concurrent load
and ensures fail-closed behavior when dependencies (Redis/PostgreSQL) are unavailable.
"""

import asyncio
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
import api.main
import api.dependencies
from security.idempotency import IdempotencyEngine


class MockRedisConcurrency:
    def __init__(self):
        self.store = {}
        self.lock = asyncio.Lock()

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None, nx=False):
        async with self.lock:
            if nx and key in self.store:
                return None
            self.store[key] = value
            return True


class AsyncMockMagic:
    async def send_and_wait(self, *args, **kwargs):
        pass

    async def xread(self, *args, **kwargs):
        import json

        return [
            [
                b"stream",
                [
                    [
                        b"msg_id",
                        {
                            b"data": json.dumps(
                                {
                                    "intent_id": "test",
                                    "decision": "ALLOW",
                                    "capability_token": "mock_token",
                                    "latency_ms": 10,
                                }
                            ).encode("utf-8")
                        },
                    ]
                ],
            ]
        ]


@pytest.fixture(autouse=True)
def mock_dependencies():
    original_get_idem = api.main.get_idempotency_engine
    original_kafka = api.dependencies.kafka_producer
    original_redis = api.dependencies.redis_client

    mock_redis = MockRedisConcurrency()
    api.main.get_idempotency_engine = lambda: IdempotencyEngine(redis_client=mock_redis, behavioral_window_seconds=5)
    api.dependencies.kafka_producer = AsyncMockMagic()
    api.dependencies.redis_client = AsyncMockMagic()

    yield

    api.main.get_idempotency_engine = original_get_idem
    api.dependencies.kafka_producer = original_kafka
    api.dependencies.redis_client = original_redis


@pytest.mark.asyncio
async def test_concurrency_execution_count():
    """
    Test: 100 concurrent identical requests
    -> exactly 1 publish/evaluation request
    -> 99 deduplicated/rejected
    """
    intent_id = f"tx_{uuid.uuid4()}"
    idem_key = f"idem_{uuid.uuid4()}"

    payload = {
        "intent_id": intent_id,
        "agent_id": "test_agent_concurrent",
        "action_type": "payout",
        "amount": 1000,
        "currency": "INR",
        "recipient": "test_recipient",
        "context": {},
    }

    headers = {"Idempotency-Key": idem_key, "X-Sentinel-Mode": "govern"}

    async with AsyncClient(transport=ASGITransport(app=api.main.app), base_url="http://test") as ac:
        # Fire 100 requests concurrently
        tasks = [ac.post("/evaluate", json=payload, headers=headers) for _ in range(100)]
        responses = await asyncio.gather(*tasks)

        accepted = [r for r in responses if r.status_code == 200]
        rejected = [r for r in responses if r.status_code == 403]

        # /evaluate only authorizes; provider execution is a separate token-gated step.
        assert len(accepted) == 1
        assert len(rejected) == 99


@pytest.mark.asyncio
async def test_fail_closed_redis_outage():
    """
    Simulate Redis outage.
    The system MUST fail closed (HTTP 403/500 with decision ESCALATE).
    """

    class OutageMockRedis:
        async def get(self, *args, **kwargs):
            raise Exception("Simulated Redis Outage")

        async def set(self, *args, **kwargs):
            raise Exception("Simulated Redis Outage")

    original_idem = api.main.get_idempotency_engine
    try:
        api.main.get_idempotency_engine = lambda: IdempotencyEngine(
            redis_client=OutageMockRedis(), behavioral_window_seconds=5
        )

        payload = {
            "intent_id": f"tx_{uuid.uuid4()}",
            "agent_id": "test_agent_redis",
            "action_type": "payout",
            "amount": 1000,
            "currency": "INR",
            "recipient": "test_recipient",
            "context": {},
        }

        headers = {"Idempotency-Key": f"idem_{uuid.uuid4()}", "X-Sentinel-Mode": "govern"}

        async with AsyncClient(transport=ASGITransport(app=api.main.app), base_url="http://test") as ac:
            r = await ac.post("/evaluate", json=payload, headers=headers)

            # The system must NOT return ALLOW. It should fail closed.
            assert r.status_code in [403, 500]
            data = r.json()
            assert data["decision"] == "ESCALATE"
    finally:
        api.main.get_idempotency_engine = original_idem
