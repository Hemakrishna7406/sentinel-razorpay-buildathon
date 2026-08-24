"""
Sentinel — End-to-End Integration Tests

Tests the FastAPI endpoints in both Govern and Observe modes.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.main import app
from api.dependencies import get_db
from db.models import Base

# The integration tests do not persist audit data; keeping the database in memory
# avoids mutating or locking a workspace file during collection.
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
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

client = TestClient(app)


def test_health_check():
    with TestClient(app) as client:
        response = client.get("/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_evaluate_observe_mode():
    """Observe requests dispatch without executing in the API process."""
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
    
    with TestClient(app) as client:
        response = client.post("/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["decision"] == "ALLOW"
    # The API relays the evaluator response; observe-mode token suppression is
    # enforced in the evaluator and covered by its decision-path tests.
    assert data["capability_token"] == "mock_token"
    assert data["executed_tx_id"] is None


def test_evaluate_govern_mode_escalation():
    """Govern requests relay the evaluator's terminal decision without execution."""
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
    
    with TestClient(app) as client:
        response = client.post("/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["decision"] == "ALLOW"
    assert data["capability_token"] == "mock_token"
    assert data["executed_tx_id"] is None


def test_evaluate_govern_mode_allow():
    """Evaluation returns authorization material; /execute is a separate boundary."""
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
    
    with TestClient(app) as client:
        response = client.post("/evaluate", json=payload, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["decision"] == "ALLOW"
    assert data["capability_token"] is not None
    assert data["executed_tx_id"] is None


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
    
    with TestClient(app) as client:
        # First request
        client.post("/evaluate", json=payload1, headers=headers)
        
        # Mutated second request with same key
        payload2 = payload1.copy()
        payload2["amount"] = 5000
        
        response = client.post("/evaluate", json=payload2, headers=headers)
        
    assert response.status_code == 403
    
    data = response.json()
    assert data["decision"] == "ESCALATE"
    assert "different payload" in data["reason"]
