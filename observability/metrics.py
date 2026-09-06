"""
Sentinel — Central Prometheus Metrics Registry

All sentinel_* metrics are defined here exactly once. Any module that needs to
record a metric imports from this file — no re-registration across processes.

Design contract (per observability.md §6):
- Every metric.inc() / .observe() / .set() call is wrapped in try/except by
  callers. This module never raises on record operations.
- Observability failures must NEVER affect authorization decisions.
- Security invariant counters (unauthorized/duplicate/unsafe_allow) must be
  monotonically increasing and backed by the audit_ledger (Postgres) as the
  authoritative source.

Scrape endpoints:
- sentinel-api:8000/metrics
- sentinel-worker:8001/metrics   (METRICS_PORT env)
- sentinel-audit:8002/metrics    (METRICS_PORT env)
"""

import os
from prometheus_client import Counter, Gauge, Histogram, REGISTRY, CollectorRegistry

# Use the default registry so FastAPI's /metrics and the worker's HTTP server
# both expose the same metrics within their respective processes.
_registry = REGISTRY

# ─────────────────────────────────────────────────────────────────────────────
# 2.1 Authorization Metrics
# ─────────────────────────────────────────────────────────────────────────────

INTENTS_TOTAL = Counter(
    "sentinel_intents_total",
    "Total intent evaluation requests received.",
    registry=_registry,
)

DECISIONS_TOTAL = Counter(
    "sentinel_decisions_total",
    "Authorization decisions by outcome and reason code.",
    labelnames=["decision", "reason"],
    registry=_registry,
)

AUTHORIZATION_LATENCY = Histogram(
    "sentinel_authorization_latency_seconds",
    "End-to-end /evaluate latency measured at the API layer.",
    buckets=[0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 2.5, 5.0, 10.0],
    registry=_registry,
)

RISK_SCORE = Histogram(
    "sentinel_risk_score",
    "Distribution of final fused risk scores (0.0–1.0).",
    buckets=[0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    registry=_registry,
)

# ─────────────────────────────────────────────────────────────────────────────
# 2.2 Worker & Queue Metrics
# ─────────────────────────────────────────────────────────────────────────────

WORKER_ACTIVE_TASKS = Gauge(
    "sentinel_worker_active_tasks",
    "Currently in-flight evaluations (held semaphore slots).",
    registry=_registry,
)

WORKER_CAPACITY = Gauge(
    "sentinel_worker_capacity",
    "Maximum concurrent tasks (MAX_CONCURRENT_TASKS).",
    registry=_registry,
)

WORKER_QUEUE_WAIT = Histogram(
    "sentinel_worker_queue_wait_seconds",
    "Time from Kafka message receive to task start (queue wait).",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=_registry,
)

WORKER_PROCESSING = Histogram(
    "sentinel_worker_processing_seconds",
    "Time spent inside sync_eval (CPU-bound: features + XGBoost + policy).",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0],
    registry=_registry,
)

KAFKA_LAG = Gauge(
    "sentinel_kafka_lag",
    "Consumer group lag per topic partition.",
    labelnames=["topic", "partition"],
    registry=_registry,
)

# ─────────────────────────────────────────────────────────────────────────────
# 2.3 Dependency Metrics
# ─────────────────────────────────────────────────────────────────────────────

REDIS_LATENCY = Histogram(
    "sentinel_redis_latency_seconds",
    "Redis operation latency.",
    labelnames=["operation"],
    buckets=[0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25],
    registry=_registry,
)

POSTGRES_LATENCY = Histogram(
    "sentinel_postgres_latency_seconds",
    "Postgres operation latency.",
    labelnames=["operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
    registry=_registry,
)

KAFKA_PUBLISH_LATENCY = Histogram(
    "sentinel_kafka_publish_latency_seconds",
    "Kafka producer send_and_wait latency.",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
    registry=_registry,
)

ML_INFERENCE_LATENCY = Histogram(
    "sentinel_ml_inference_latency_seconds",
    "XGBoost inference latency.",
    labelnames=["backend"],
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
    registry=_registry,
)

REDIS_ERRORS_TOTAL = Counter(
    "sentinel_redis_errors_total",
    "Redis errors by operation.",
    labelnames=["operation"],
    registry=_registry,
)

POSTGRES_ERRORS_TOTAL = Counter(
    "sentinel_postgres_errors_total",
    "Postgres errors by operation.",
    labelnames=["operation"],
    registry=_registry,
)

KAFKA_ERRORS_TOTAL = Counter(
    "sentinel_kafka_errors_total",
    "Kafka errors by operation.",
    labelnames=["operation"],
    registry=_registry,
)

ML_ERRORS_TOTAL = Counter(
    "sentinel_ml_errors_total",
    "ML inference errors.",
    registry=_registry,
)

# ─────────────────────────────────────────────────────────────────────────────
# 2.4 Security Invariant Metrics
# These must always be zero. Non-zero = operational emergency.
# ─────────────────────────────────────────────────────────────────────────────

SECURITY_UNAUTHORIZED_EXECUTION = Counter(
    "sentinel_security_unauthorized_execution_total",
    "Financial executions that occurred without a valid capability token. MUST BE 0.",
    registry=_registry,
)

SECURITY_DUPLICATE_EXECUTION = Counter(
    "sentinel_security_duplicate_execution_total",
    "Duplicate financial executions detected. MUST BE 0.",
    registry=_registry,
)

SECURITY_UNSAFE_ALLOW = Counter(
    "sentinel_security_unsafe_allow_total",
    "ALLOW decisions issued when a critical dependency was unavailable. MUST BE 0.",
    registry=_registry,
)

SECURITY_TOKEN_REJECTION = Counter(
    "sentinel_security_token_rejection_total",
    "Capability token validation failures at the execution gateway.",
    registry=_registry,
)

SECURITY_RECONCILIATION_PENDING = Gauge(
    "sentinel_security_reconciliation_pending",
    "Idempotency keys in PUBLISH_UNKNOWN or UNKNOWN state requiring reconciliation.",
    registry=_registry,
)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def record_decision(decision: str, reason: str) -> None:
    """
    Increment DECISIONS_TOTAL safely. Never raises.
    Maps raw reason strings to the canonical label vocabulary from observability.md.
    """
    try:
        # Canonicalize reason to label-safe string
        canonical = _canonicalize_reason(reason)
        DECISIONS_TOTAL.labels(decision=decision, reason=canonical).inc()
    except Exception:
        pass  # Observability must never affect authorization


def _canonicalize_reason(reason: str) -> str:
    """Map free-form decision reason strings to canonical label values."""
    if not reason:
        return "UNKNOWN"
    r = reason.upper()
    if "MODEL_UNAVAILABLE" in r or "MODEL NOT" in r or "NOT LOADED" in r or ("MODEL" in r and "UNAVAIL" in r):
        return "MODEL_UNAVAILABLE"
    if "REDIS" in r or "IDEMPOTENCY" in r and "UNAVAILABLE" in r:
        return "REDIS_UNAVAILABLE"
    if "KAFKA" in r or "PUBLISH" in r and "UNAVAILABLE" in r:
        return "KAFKA_UNAVAILABLE"
    if "POLICY" in r and "UNAVAILABLE" in r:
        return "POLICY_ENGINE_UNAVAILABLE"
    if "SIGNING" in r or "TOKEN" in r and "FAIL" in r:
        return "CAPABILITY_SIGNING_FAILED"
    if "MCP" in r and "UNAVAILABLE" in r:
        return "MCP_UNAVAILABLE"
    if "UNKNOWN" in r and "EXECUTION" in r:
        return "EXECUTION_UNKNOWN"
    if "IDEMPOTENCY" in r or "DUPLICATE" in r:
        return "IDEMPOTENCY_CONFLICT"
    if "DEPENDENCY" in r:
        return "DEPENDENCY_FAILURE"
    if "OBSERVE MODE" in r:
        return "OBSERVE_MODE"
    if "ALLOW" in r and ("RISK" in r or "NORMAL" in r):
        return "NORMAL"
    if "RISK" in r or "SCORE" in r or "THRESHOLD" in r or "DRIFT" in r:
        return "RISK_TOO_HIGH"
    return "OTHER"


# Initialize capacity gauge from env at module load time
def _init_capacity() -> None:
    try:
        from core.config import settings

        cap = settings.MAX_CONCURRENT_TASKS
        WORKER_CAPACITY.set(cap)
    except Exception:
        pass


_init_capacity()
