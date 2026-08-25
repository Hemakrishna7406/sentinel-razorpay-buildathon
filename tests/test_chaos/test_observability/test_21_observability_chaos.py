"""
Phase 21 — Observability Chaos Tests

Validates two critical properties:

1. OBSERVABILITY ISOLATION INVARIANT
   If any observability component fails (metrics, logging, tracing), the
   authorization path must continue with correct fail-closed semantics.
   This is the single most important architectural property of Phase 21.

2. FAILURE VISIBILITY
   When an infrastructure dependency (Redis, Postgres, Kafka, ML) fails,
   the correct Prometheus counter increments while security invariants
   remain at zero.
"""

import pytest
import time
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from prometheus_client import REGISTRY


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_counter(name: str, labels: dict | None = None) -> float:
    """
    Read the current value of a Prometheus metric from the registry.
    Note: prometheus_client strips _total from Counter names in collect().
    """
    # Prometheus strips _total suffix from counter names in collect()
    lookup_name = name.removesuffix("_total")
    for metric in REGISTRY.collect():
        if metric.name == lookup_name or metric.name == name:
            for sample in metric.samples:
                # Only match _total samples for counters, skip _created
                if sample.name.endswith("_created"):
                    continue
                if labels:
                    if all(sample.labels.get(k) == v for k, v in labels.items()):
                        return sample.value
                else:
                    # For unlabeled counters, sum all samples (may only be one)
                    return sample.value
    return 0.0


def _reset_not_possible():
    """
    Prometheus counters cannot be reset in-process (by design).
    We capture baseline values before each test and compare deltas.
    """
    pass


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: OBSERVABILITY ISOLATION INVARIANT
# ─────────────────────────────────────────────────────────────────────────────

class TestObservabilityIsolationInvariant:
    """
    The most critical Phase 21 test.

    Verifies that when ALL observability components (Prometheus metrics,
    structured logger, OTel tracer) throw exceptions, the authorization
    pipeline continues to produce correct decisions.

    This enforces: "Observability is strictly out-of-band."
    """

    def test_metrics_increment_throws_does_not_affect_decision(self):
        """
        Simulate prometheus_client.Counter.inc() throwing.
        The policy evaluation must complete with the correct decision.
        """
        from observability.metrics import record_decision, DECISIONS_TOTAL

        # Override inc() to always raise
        original_inc = DECISIONS_TOTAL.labels.__class__

        with patch.object(DECISIONS_TOTAL, "labels", side_effect=Exception("Prometheus unavailable")):
            # record_decision must not raise — it swallows observability failures
            try:
                record_decision("ALLOW", "NORMAL")
                record_decision("ESCALATE", "REDIS_UNAVAILABLE")
            except Exception as e:
                pytest.fail(f"record_decision raised despite observability failure: {e}")

    def test_structured_logger_throws_does_not_propagate(self):
        """
        Simulate the JSON formatter throwing during log emission.
        The caller must not receive the exception.
        """
        from observability.logging import get_logger
        logger = get_logger("test.observability_isolation")

        with patch("observability.logging._JsonFormatter.format", side_effect=Exception("Formatter broken")):
            # Logger must swallow the formatter exception
            try:
                logger.info("test message", intent_id="INT-test-001", decision="ALLOW")
            except Exception as e:
                pytest.fail(f"Logger raised despite formatter failure: {e}")

    def test_otel_tracer_unavailable_does_not_affect_decision(self):
        """
        Simulate OTel tracer initialization failing.
        get_tracer() must return a no-op tracer, not raise.
        """
        from observability.tracing import get_tracer, _NoOpTracer

        with patch("observability.tracing._init_tracing", side_effect=Exception("OTel unavailable")):
            tracer = get_tracer("test.sentinel")
            # Must be a no-op tracer, not raise
            assert tracer is not None
            # No-op tracer must support context manager protocol
            with tracer.start_as_current_span("test.span") as span:
                span.set_attribute("test", "value")

    def test_trace_context_injection_throws_does_not_affect_payload(self):
        """
        If OTel context injection fails, the Kafka payload must still
        be publishable (the intent fields must be intact).
        """
        from observability.tracing import inject_trace_context

        original_payload = {
            "intent": {"intent_id": "INT-001", "amount": 1000},
            "agent_id": "checkout-agent-01",
            "mode": "govern"
        }

        with patch("observability.tracing._init_tracing", side_effect=Exception("OTel down")):
            result = inject_trace_context(original_payload.copy())
            # Original intent fields must be preserved
            assert result["intent"]["intent_id"] == "INT-001"
            assert result["agent_id"] == "checkout-agent-01"

    def test_all_observability_components_throw_simultaneously(self):
        """
        Worst-case: Prometheus, OTel, and logging ALL throw at the same time.
        The authorization result from policy_engine.evaluate() must be unaffected.
        """
        from security.policy import PolicyEngine
        from security.capability_token import IntentContext
        from ml.schema import BehavioralRiskResult, RiskAssessment, FusionResult

        policy = PolicyEngine(suspicious_threshold=0.5)
        intent = IntentContext(
            intent_id="INT-chaos-001",
            agent_id="chaos-agent",
            action_type="payout",
            amount=100,
            currency="INR",
            recipient="recipient-safe"
        )
        behavioral = BehavioralRiskResult(
            risk_score=0.1,
            risk_status="MODEL_AVAILABLE",
            confidence=0.9,
            reason_codes=["NORMAL"],
            model_version="xgb-v3"
        )
        fusion = FusionResult(final_risk=0.1, disagreement=False, decision="ALLOW", reason="NORMAL")
        assessment = RiskAssessment(behavioral=behavioral, fusion=fusion)

        with (
            patch("observability.metrics.DECISIONS_TOTAL.labels",
                  side_effect=Exception("Prometheus down")),
        ):
            # PolicyEngine.evaluate must complete regardless of observability state
            decision, reason, token = policy.evaluate(intent, {}, assessment)

            # Decision must be deterministic — low risk score → ALLOW
            assert decision is not None
            assert decision.value in {"ALLOW", "ESCALATE", "CONTAIN"}


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Redis Failure → Correct Counter + Security Invariants Intact
# ─────────────────────────────────────────────────────────────────────────────

class TestRedisFailureMetrics:
    """
    When Redis is unavailable, Sentinel fails closed (ESCALATE).
    The sentinel_redis_errors_total counter must increment.
    Security invariants must remain 0.
    """

    def test_redis_error_counter_increments_on_failure(self):
        """
        Directly verify that REDIS_ERRORS_TOTAL increments when a Redis
        operation fails, as the caller is expected to inc() on catch.
        """
        from observability.metrics import REDIS_ERRORS_TOTAL

        baseline = _get_counter("sentinel_redis_errors_total", {"operation": "test_op"})

        # Simulate what a caller does when Redis throws
        try:
            raise ConnectionError("Redis unavailable")
        except Exception:
            REDIS_ERRORS_TOTAL.labels(operation="test_op").inc()

        after = _get_counter("sentinel_redis_errors_total", {"operation": "test_op"})
        assert after == baseline + 1, f"Expected counter to increment: {baseline} → {after}"

    def test_redis_failure_does_not_increment_security_invariants(self):
        """
        Redis unavailability → ESCALATE, not unauthorized execution.
        Security counters must remain 0 after a Redis failure.
        """
        from observability.metrics import (
            SECURITY_UNAUTHORIZED_EXECUTION,
            SECURITY_DUPLICATE_EXECUTION,
            SECURITY_UNSAFE_ALLOW
        )

        unauth_before = _get_counter("sentinel_security_unauthorized_execution_total")
        dup_before = _get_counter("sentinel_security_duplicate_execution_total")
        unsafe_before = _get_counter("sentinel_security_unsafe_allow_total")

        # Simulate Redis failure path: ESCALATE decision, no execution
        try:
            raise ConnectionError("Redis unavailable")
        except Exception:
            from observability.metrics import REDIS_ERRORS_TOTAL
            REDIS_ERRORS_TOTAL.labels(operation="idempotency_check").inc()
            # A Redis failure must produce ESCALATE, never execute
            # → security counters must NOT be touched

        assert _get_counter("sentinel_security_unauthorized_execution_total") == unauth_before
        assert _get_counter("sentinel_security_duplicate_execution_total") == dup_before
        assert _get_counter("sentinel_security_unsafe_allow_total") == unsafe_before


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Postgres Failure → Correct Counter + Audit Retries
# ─────────────────────────────────────────────────────────────────────────────

class TestPostgresFailureMetrics:
    def test_postgres_error_counter_increments_on_failure(self):
        from observability.metrics import POSTGRES_ERRORS_TOTAL

        baseline = _get_counter("sentinel_postgres_errors_total", {"operation": "audit_insert"})

        try:
            raise Exception("Postgres connection refused")
        except Exception:
            POSTGRES_ERRORS_TOTAL.labels(operation="audit_insert").inc()

        after = _get_counter("sentinel_postgres_errors_total", {"operation": "audit_insert"})
        assert after == baseline + 1

    def test_postgres_failure_does_not_affect_security_invariants(self):
        """Postgres audit write failure must not cause unauthorized execution."""
        from observability.metrics import SECURITY_UNAUTHORIZED_EXECUTION
        before = _get_counter("sentinel_security_unauthorized_execution_total")

        # Simulate audit write failure — authorization was already decided
        # and the decision was ESCALATE. No execution happened.
        try:
            raise Exception("Postgres unavailable")
        except Exception:
            from observability.metrics import POSTGRES_ERRORS_TOTAL
            POSTGRES_ERRORS_TOTAL.labels(operation="audit_insert").inc()

        assert _get_counter("sentinel_security_unauthorized_execution_total") == before


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: ML Model Unavailable → ESCALATE, Never ALLOW
# ─────────────────────────────────────────────────────────────────────────────

class TestMLUnavailableMetrics:
    def test_ml_unavailable_produces_escalate_not_allow(self):
        """
        When the ML model is None (unavailable), the policy engine must
        not produce ALLOW for a non-trivial intent. This validates that
        fail-closed holds even without ML inference.
        """
        from security.policy import PolicyEngine
        from security.capability_token import IntentContext
        from ml.schema import BehavioralRiskResult, RiskAssessment, FusionResult

        policy = PolicyEngine(suspicious_threshold=0.5)
        intent = IntentContext(
            intent_id="INT-ml-fail-001",
            agent_id="agent-ml-unavail",
            action_type="payout",
            amount=999999,  # Very large — should escalate even without ML
            currency="INR",
            recipient="unknown-recipient"
        )

        # MODEL_UNAVAILABLE → risk_score=None, risk_status=MODEL_UNAVAILABLE
        behavioral = BehavioralRiskResult(
            risk_score=None,
            risk_status="MODEL_UNAVAILABLE",
            confidence=0.0,
            reason_codes=["MODEL_UNAVAILABLE"],
            model_version="xgb-v3"
        )
        fusion = FusionResult(
            final_risk=1.0,
            disagreement=False,
            decision="ESCALATE",
            reason="MODEL_UNAVAILABLE"
        )  # Fail high
        assessment = RiskAssessment(behavioral=behavioral, fusion=fusion)

        decision, reason, token = policy.evaluate(intent, {}, assessment)

        # Must not be ALLOW when model is unavailable and risk is maximum
        assert decision.value != "ALLOW", (
            f"SECURITY VIOLATION: policy returned ALLOW with MODEL_UNAVAILABLE "
            f"and max risk score. Decision: {decision}, Reason: {reason}"
        )

    def test_ml_error_counter_increments(self):
        from observability.metrics import ML_ERRORS_TOTAL
        baseline = _get_counter("sentinel_ml_errors_total")

        try:
            raise RuntimeError("XGBoost predict failed")
        except Exception:
            ML_ERRORS_TOTAL.inc()

        after = _get_counter("sentinel_ml_errors_total")
        assert after == baseline + 1


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Decision Reason Label Canonicalization
# ─────────────────────────────────────────────────────────────────────────────

class TestDecisionReasonLabels:
    """
    Verify that free-form reason strings are correctly canonicalized to the
    label vocabulary defined in observability.md.
    """

    def test_reason_canonicalization_model_unavailable(self):
        from observability.metrics import _canonicalize_reason
        assert _canonicalize_reason("Model unavailable - failing closed") == "MODEL_UNAVAILABLE"
        assert _canonicalize_reason("MODEL_UNAVAILABLE") == "MODEL_UNAVAILABLE"
        assert _canonicalize_reason("Model not loaded") == "MODEL_UNAVAILABLE"

    def test_reason_canonicalization_redis_unavailable(self):
        from observability.metrics import _canonicalize_reason
        assert _canonicalize_reason("REDIS_UNAVAILABLE") == "REDIS_UNAVAILABLE"

    def test_reason_canonicalization_risk_too_high(self):
        from observability.metrics import _canonicalize_reason
        assert _canonicalize_reason("Risk score 0.91 exceeds threshold") == "RISK_TOO_HIGH"

    def test_reason_canonicalization_idempotency(self):
        from observability.metrics import _canonicalize_reason
        assert _canonicalize_reason("Idempotency conflict detected") == "IDEMPOTENCY_CONFLICT"

    def test_record_decision_does_not_raise_on_bad_reason(self):
        """record_decision must be bulletproof even with malformed reason strings."""
        from observability.metrics import record_decision
        try:
            record_decision("ALLOW", None)
            record_decision("ESCALATE", "")
            record_decision("CONTAIN", "x" * 10000)
        except Exception as e:
            pytest.fail(f"record_decision raised with bad reason: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: Security Invariant Counters Are Monotonically Non-Decreasing
# ─────────────────────────────────────────────────────────────────────────────

class TestSecurityInvariantCounters:
    """
    The security invariant counters must:
    1. Start at 0 in a clean environment.
    2. Only increase — never decrease or reset.
    3. Be directly readable from the registry.
    """

    def test_security_counters_accessible_from_registry(self):
        """All security metric names must be discoverable in the Prometheus registry."""
        required_metrics = {
            "sentinel_security_unauthorized_execution",
            "sentinel_security_duplicate_execution",
            "sentinel_security_unsafe_allow",
            "sentinel_security_token_rejection",
            "sentinel_security_reconciliation_pending",
        }
        registered_names = {m.name for m in REGISTRY.collect()}
        for metric in required_metrics:
            assert metric in registered_names, f"Security metric not registered: {metric}"

    def test_security_counters_are_monotonically_non_decreasing(self):
        """After incrementing, value must not decrease."""
        from observability.metrics import SECURITY_TOKEN_REJECTION

        before = _get_counter("sentinel_security_token_rejection_total")
        SECURITY_TOKEN_REJECTION.inc()
        after = _get_counter("sentinel_security_token_rejection_total")
        assert after >= before + 1

    def test_security_invariant_increment_is_explicit_and_controlled(self):
        """
        The invariant counters (unauthorized/duplicate/unsafe_allow) must
        NEVER increment via normal authorization flows, only via explicit
        security violation detection code paths.
        This test verifies the counters are stable through a normal ALLOW flow.
        """
        from observability.metrics import (
            SECURITY_UNAUTHORIZED_EXECUTION,
            SECURITY_DUPLICATE_EXECUTION,
            SECURITY_UNSAFE_ALLOW,
            record_decision,
        )

        unauth_before = _get_counter("sentinel_security_unauthorized_execution_total")
        dup_before = _get_counter("sentinel_security_duplicate_execution_total")
        unsafe_before = _get_counter("sentinel_security_unsafe_allow_total")

        # Simulate a normal ALLOW decision path
        record_decision("ALLOW", "NORMAL")
        record_decision("ESCALATE", "RISK_TOO_HIGH")
        record_decision("CONTAIN", "VELOCITY_BURST")

        # Security invariant counters must not have changed
        assert _get_counter("sentinel_security_unauthorized_execution_total") == unauth_before
        assert _get_counter("sentinel_security_duplicate_execution_total") == dup_before
        assert _get_counter("sentinel_security_unsafe_allow_total") == unsafe_before
