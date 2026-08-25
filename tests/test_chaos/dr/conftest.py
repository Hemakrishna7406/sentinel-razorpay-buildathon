"""
Shared fixtures for DR tests (Phase 22).
"""

import pytest
import httpx
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def test_client():
    """Synchronous test client for the Sentinel FastAPI app."""
    import api.main as app_module  # noqa: triggers lifespan fixture if needed
    from api.main import app
    client = TestClient(app, raise_server_exceptions=False)
    yield client


@pytest.fixture
def async_test_client():
    """Return the sync TestClient as a thin wrapper \u2014 fast and dependency-mockable."""
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)
