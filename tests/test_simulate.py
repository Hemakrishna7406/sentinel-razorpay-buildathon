import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from api.main import app


@patch("execution.adapters.mcp_adapter.RazorpayMCPAdapter.execute", new_callable=AsyncMock)
def test_simulate_does_not_execute(mock_execute):
    """
    Test that the /simulate endpoint runs the full RiskAssessment -> Policy -> Decision path,
    but NEVER attempts actual provider execution, regardless of outcome.
    """
    payload = {"num_samples": 5, "seed": 42}

    with TestClient(app) as client:
        response = client.post("/simulate", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert "allowed" in data
    assert "escalated" in data
    assert "contained" in data
    assert "decisions" in data

    # Assert provider execution was NOT called
    mock_execute.assert_not_called()

    # We should have decisions and they should only be ALLOW, ESCALATE, or CONTAIN
    for d in data["decisions"]:
        assert d["decision"] in ["ALLOW", "ESCALATE", "CONTAIN"]


from api.dependencies import get_policy_engine


@patch("execution.adapters.mcp_adapter.RazorpayMCPAdapter.execute", new_callable=AsyncMock)
def test_simulate_with_exception_never_executes(mock_execute):
    """
    Test that even if a policy engine fails, we don't accidentally leak execution.
    """

    def override_get_policy_engine():
        from unittest.mock import MagicMock

        m = MagicMock()
        m.evaluate.side_effect = Exception("Policy engine failure")
        return m

    app.dependency_overrides[get_policy_engine] = override_get_policy_engine

    payload = {"num_samples": 1, "seed": 100}

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/simulate", json=payload)

    app.dependency_overrides.pop(get_policy_engine, None)

    # fails closed with an ESCALATE decision.
    assert response.status_code == 500
    # TestClient with raise_server_exceptions=False returns a standard 500 text response

    mock_execute.assert_not_called()
    mock_execute.assert_not_called()
