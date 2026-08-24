"""
Sentinel — End-to-End Integration Tests

Tests the FastAPI endpoints in both Govern and Observe modes.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os
os.environ["CAPABILITY_SIGNING_KEY"] = "test-secret-key-must-be-at-least-32-bytes-long"

from api.main import app
from api.dependencies import get_db
from db.models import Base

# Use a local file DB for tests to avoid multi-connection memory DB issues
TEST_DB_URL = "sqlite:///./test_sentinel.db"
if os.path.exists("./test_sentinel.db"):
    os.remove("./test_sentinel.db")

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

from unittest.mock import AsyncMock
app.dependency_overrides[get_db] = override_get_db

class MockIdempotencyEngine:
    async def check_and_record(self, key, intent, agent_id):
        return None
    async def mark_completed(self, key, request_hash, executed_tx_id):
        pass
    async def mark_failed(self, key):
        pass

import api.main
import api.dependencies
api.main.get_idempotency_engine = lambda: MockIdempotencyEngine()

class AsyncMockMagic:
    async def send_and_wait(self, *args, **kwargs):
        pass
    async def xread(self, *args, **kwargs):
        import json
        return [[b"stream", [[b"msg_id", {b"data": json.dumps({
            "intent_id": "test",
            "decision": "ALLOW",
            "capability_token": "mock_token",
            "latency_ms": 10
        }).encode("utf-8")}]]]]

api.dependencies.kafka_producer = AsyncMockMagic()
api.dependencies.redis_client = AsyncMockMagic()

client = TestClient(app)


def test_health_check():
    response = client.get("/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_evaluate_observe_mode():
    """Observe mode must always return ALLOW and never execute."""
    payload = {
        "intent_id": "int_obs_1",
        "action_type": "payout",
        "amount": 99999999,  # Absolute bounds rule normally blocks > 10,000,000
        "currency": "INR",
        "recipient": "bank_obs",
        "agent_id": "agent_obs",
        "context": {}
    }
    
    headers = {
        "Idempotency-Key": "idem_obs_1",
        "X-Sentinel-Mode": "observe"
    }
    
    response = client.post("/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["decision"] == "ALLOW"
    assert "OBSERVE MODE" in data["reason"]
    assert data["capability_token"] is None
    assert data["executed_tx_id"] is None


def test_evaluate_govern_mode_escalation():
    """Govern mode strictly enforces rules (e.g. absolute bounds)."""
    payload = {
        "intent_id": "int_gov_1",
        "action_type": "payout",
        "amount": 99999999,  # Absolute bounds rule blocks > 10,000,000
        "currency": "INR",
        "recipient": "bank_gov",
        "agent_id": "agent_gov",
        "context": {}
    }
    
    headers = {
        "Idempotency-Key": "idem_gov_1",
        "X-Sentinel-Mode": "govern"
    }
    
    response = client.post("/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["decision"] == "ESCALATE"
    assert data["capability_token"] is None
    assert data["executed_tx_id"] is None


def test_evaluate_govern_mode_allow():
    """Govern mode issues token and executes if allowed."""
    payload = {
        "intent_id": "int_gov_2",
        "action_type": "payout",
        "amount": 1000,
        "currency": "INR",
        "recipient": "bank_allow",
        "agent_id": "agent_allow",
        "context": {
            "has_sufficient_history": 1  # Bypasses the new-agent escalation rule
        }
    }
    
    headers = {
        "Idempotency-Key": "idem_gov_2",
        "X-Sentinel-Mode": "govern"
    }
    
    response = client.post("/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["decision"] == "ALLOW"
    assert data["capability_token"] is not None
    assert data["executed_tx_id"] is not None
    assert data["executed_tx_id"].startswith("tx_")


def test_fastapi_fail_closed_on_idempotency_conflict():
    """FastAPI layer must catch typed security exceptions and return 403 ESCALATE."""
    payload1 = {
        "intent_id": "int_gov_3",
        "action_type": "payout",
        "amount": 1000,
        "currency": "INR",
        "recipient": "bank_conflict",
        "agent_id": "agent_conflict",
        "context": {"has_sufficient_history": 1}
    }
    
    headers = {
        "Idempotency-Key": "idem_conflict_1",
        "X-Sentinel-Mode": "govern"
    }
    
    # First request
    client.post("/evaluate", json=payload1, headers=headers)
    
    # Mutated second request with same key
    payload2 = payload1.copy()
    payload2["amount"] = 5000
    
    response = client.post("/evaluate", json=payload2, headers=headers)
    assert response.status_code == 403
    
    data = response.json()
    assert data["decision"] == "ESCALATE"
    assert "Security violation" in data["reason"]
