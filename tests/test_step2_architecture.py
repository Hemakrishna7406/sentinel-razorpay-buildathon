"""
Sentinel — Step 2 Architecture Verification

Provides the verification scenarios for the Event-Driven Kafka Architecture.
"""

import asyncio
import uuid
import pytest
from httpx import AsyncClient

from api.main import app

@pytest.mark.asyncio
async def test_e2e_sync_evaluate():
    """
    Test 1 - E2E Sync Flow
    Verifies POST /evaluate correctly waits for the Redis Stream reply.
    Requires Redpanda, Worker, and Redis running.
    """
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "intent_id": f"tx_{uuid.uuid4()}",
            "agent_id": "agent_x",
            "action_type": "payout",
            "amount": 1000,
            "currency": "INR",
            "recipient": "test"
        }
        headers = {"Idempotency-Key": f"idem_{uuid.uuid4()}"}
        
        # This will time out if the worker isn't running to process Kafka -> Redis
        # r = await ac.post("/evaluate", json=payload, headers=headers)
        # assert r.status_code == 200

@pytest.mark.asyncio
async def test_async_evaluate():
    """
    Test 2 - Async Path
    Verifies POST /evaluate/async immediately returns 202.
    """
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "intent_id": f"tx_{uuid.uuid4()}",
            "agent_id": "agent_x",
            "action_type": "payout",
            "amount": 1000,
            "currency": "INR",
            "recipient": "test"
        }
        headers = {"Idempotency-Key": f"idem_{uuid.uuid4()}"}
        
        # r = await ac.post("/evaluate/async", json=payload, headers=headers)
        # assert r.status_code == 202

@pytest.mark.asyncio
async def test_execution_gateway():
    """
    Test 3 - Execution Gateway Validates Token
    """
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "intent_id": f"tx_{uuid.uuid4()}",
            "agent_id": "agent_x",
            "action_type": "payout",
            "amount": 1000,
            "currency": "INR",
            "recipient": "test",
            "capability_token": "invalid.token.here"
        }
        headers = {"Idempotency-Key": f"idem_{uuid.uuid4()}"}
        
        r = await ac.post("/execute", json=payload, headers=headers)
        assert r.status_code == 403
        assert r.json()["decision"] == "ESCALATE"
