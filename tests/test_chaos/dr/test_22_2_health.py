"""
Sentinel — Phase 22.2 Health / Readiness / Liveness Tests

Verifies the component-specific readiness dependency matrix:
  Redis  — REQUIRED
  Kafka  — REQUIRED
  DB     — MONITORED (soft-fail, not blocking)

Invariant: Health checks never alter fail-closed authorization behavior.

NOTE: FastAPI TestClient wraps async route handlers synchronously,
so all tests here are plain synchronous functions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────


def _make_live_redis():
    """Mock a healthy async Redis client."""
    m = AsyncMock()
    m.ping = AsyncMock(return_value=True)
    return m


def _make_dead_redis():
    m = AsyncMock()
    m.ping = AsyncMock(side_effect=ConnectionError("Redis connection refused"))
    return m


def _make_live_kafka():
    m = MagicMock()
    m._closed = False
    return m


def _make_dead_kafka():
    m = MagicMock()
    m._closed = True
    return m


def _make_live_engine():
    """Mock a healthy SQLAlchemy engine."""
    conn = MagicMock()
    conn.execute = MagicMock(return_value=None)
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=conn)
    ctx.__exit__ = MagicMock(return_value=False)
    engine = MagicMock()
    engine.connect = MagicMock(return_value=ctx)
    return engine


def _make_dead_engine():
    engine = MagicMock()
    engine.connect = MagicMock(side_effect=Exception("pg connection refused"))
    return engine


# ─────────────────────────────────────────────────────────────
# 22.2.1 — Liveness
# ─────────────────────────────────────────────────────────────


class TestLiveness:
    def test_liveness_always_200(self, test_client):
        response = test_client.get("/health/live")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["process"] == "alive"

    def test_liveness_does_not_call_redis(self, test_client):
        """Liveness must never touch Redis/Kafka/DB — event-loop-only check."""
        with patch("api.dependencies.redis_client") as mock_redis:
            response = test_client.get("/health/live")
            assert response.status_code == 200
            mock_redis.ping.assert_not_called()


# ─────────────────────────────────────────────────────────────
# 22.2.2 — Readiness: all dependencies healthy
# ─────────────────────────────────────────────────────────────


class TestReadinessAllHealthy:
    def test_ready_200_when_redis_kafka_up(self, test_client):
        redis = _make_live_redis()
        kafka = _make_live_kafka()
        engine = _make_live_engine()
        with (
            patch("api.dependencies.redis_client", redis),
            patch("api.dependencies.kafka_producer", kafka),
            patch("api.dependencies.engine", engine),
        ):
            response = test_client.get("/health/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    def test_ready_200_even_when_db_down(self, test_client):
        """DB outage must NOT block API readiness — monitored dependency only."""
        redis = _make_live_redis()
        kafka = _make_live_kafka()
        engine = _make_dead_engine()
        with (
            patch("api.dependencies.redis_client", redis),
            patch("api.dependencies.kafka_producer", kafka),
            patch("api.dependencies.engine", engine),
        ):
            response = test_client.get("/health/ready")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        # DB degradation must surface as a warning, not a failure
        assert "warnings" in body
        assert "postgres" in body["warnings"]


# ─────────────────────────────────────────────────────────────
# 22.2.3 — Readiness: required dependency failures → 503
# ─────────────────────────────────────────────────────────────


class TestReadinessRequiredFailures:
    def test_503_when_redis_down(self, test_client):
        """Redis outage → 503. API cannot guarantee idempotency without Redis."""
        redis = _make_dead_redis()
        kafka = _make_live_kafka()
        engine = _make_live_engine()
        with (
            patch("api.dependencies.redis_client", redis),
            patch("api.dependencies.kafka_producer", kafka),
            patch("api.dependencies.engine", engine),
        ):
            response = test_client.get("/health/ready")
        assert response.status_code == 503
        body = response.json()["detail"]
        assert body["status"] == "not_ready"
        assert "redis" in body["required_dependencies_failed"]

    def test_503_when_kafka_closed(self, test_client):
        """Kafka producer closed → 503. Cannot publish intents to worker."""
        redis = _make_live_redis()
        kafka = _make_dead_kafka()
        engine = _make_live_engine()
        with (
            patch("api.dependencies.redis_client", redis),
            patch("api.dependencies.kafka_producer", kafka),
            patch("api.dependencies.engine", engine),
        ):
            response = test_client.get("/health/ready")
        assert response.status_code == 503
        body = response.json()["detail"]
        assert "kafka" in body["required_dependencies_failed"]

    def test_503_when_not_initialized(self, test_client):
        """None clients during startup → 503 with startup_incomplete=True."""
        with (
            patch("api.dependencies.redis_client", None),
            patch("api.dependencies.kafka_producer", None),
        ):
            response = test_client.get("/health/ready")
        assert response.status_code == 503
        body = response.json()["detail"]
        assert body["startup_incomplete"] is True

    def test_503_when_both_redis_and_kafka_down(self, test_client):
        """Both required deps failing → both errors reported in response body."""
        redis = _make_dead_redis()
        kafka = _make_dead_kafka()
        engine = _make_live_engine()
        with (
            patch("api.dependencies.redis_client", redis),
            patch("api.dependencies.kafka_producer", kafka),
            patch("api.dependencies.engine", engine),
        ):
            response = test_client.get("/health/ready")
        assert response.status_code == 503
        body = response.json()["detail"]
        assert "redis" in body["required_dependencies_failed"]
        assert "kafka" in body["required_dependencies_failed"]


# ─────────────────────────────────────────────────────────────
# 22.2.4 — Dependencies diagnostic panel
# ─────────────────────────────────────────────────────────────


class TestDependenciesPanel:
    def test_dependencies_always_200(self, test_client):
        """Diagnostic panel must always return 200, even with dead dependencies."""
        redis = _make_dead_redis()
        kafka = _make_dead_kafka()
        engine = _make_dead_engine()
        with (
            patch("api.dependencies.redis_client", redis),
            patch("api.dependencies.kafka_producer", kafka),
            patch("api.dependencies.engine", engine),
            patch("api.dependencies.global_model", None),
        ):
            response = test_client.get("/health/dependencies")
        assert response.status_code == 200
        body = response.json()
        assert body["redis"]["status"] == "unhealthy"
        assert body["redis"]["role"] == "required"
        assert body["kafka"]["status"] == "closed"
        assert body["kafka"]["role"] == "required"
        assert body["postgres"]["status"] == "unhealthy"
        assert body["postgres"]["role"] == "monitored"

    def test_dependencies_shows_role_annotation(self, test_client):
        """Role annotations (required/monitored) must be present for all deps."""
        redis = _make_live_redis()
        kafka = _make_live_kafka()
        engine = _make_live_engine()
        with (
            patch("api.dependencies.redis_client", redis),
            patch("api.dependencies.kafka_producer", kafka),
            patch("api.dependencies.engine", engine),
            patch("api.dependencies.global_model", None),
        ):
            response = test_client.get("/health/dependencies")
        assert response.status_code == 200
        body = response.json()
        for dep in ["redis", "kafka", "postgres"]:
            assert "role" in body[dep], f"Missing role annotation on {dep}"

    def test_dependencies_ml_model_not_loaded_note(self, test_client):
        """Absent ML model: diagnostic panel must explain ESCALATE behavior."""
        redis = _make_live_redis()
        kafka = _make_live_kafka()
        engine = _make_live_engine()
        with (
            patch("api.dependencies.redis_client", redis),
            patch("api.dependencies.kafka_producer", kafka),
            patch("api.dependencies.engine", engine),
            patch("api.dependencies.global_model", None),
        ):
            response = test_client.get("/health/dependencies")
        body = response.json()
        assert body["ml_model"]["status"] == "not_loaded"
        assert "ESCALATE" in body["ml_model"].get("note", "")


# ─────────────────────────────────────────────────────────────
# 22.2.5 — Authorization safety invariant
# ─────────────────────────────────────────────────────────────


class TestHealthAuthorizationInvariant:
    def test_health_endpoints_never_produce_allow_or_escalate(self, test_client):
        """
        Health check responses must never contain authorization decision fields.
        They are diagnostic only and must be invisible to the authorization plane.
        """
        for path in ["/health/live", "/health/ready"]:
            try:
                resp = test_client.get(path)
            except Exception:
                continue
            body = resp.json() if resp.status_code == 200 else {}
            for forbidden_field in ["decision", "capability_token", "allow", "escalate", "contain"]:
                assert (
                    forbidden_field not in body
                ), f"Health endpoint {path} leaked authorization field: {forbidden_field}"
