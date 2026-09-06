"""Script to generate Grafana dashboard JSON files for Phase 21."""

import json
import os

os.makedirs("grafana/provisioning/dashboards", exist_ok=True)

# ── Dashboard 4: Security Invariants ──────────────────────────────────────────
security = {
    "title": "Sentinel - Security Invariants",
    "uid": "sentinel-security",
    "tags": ["sentinel", "security"],
    "refresh": "10s",
    "time": {"from": "now-1h", "to": "now"},
    "panels": [
        {
            "id": 1,
            "type": "stat",
            "title": "Unauthorized Executions",
            "description": "MUST BE 0. Non-zero = CRITICAL security breach.",
            "gridPos": {"h": 6, "w": 6, "x": 0, "y": 0},
            "targets": [{"expr": "sentinel_security_unauthorized_execution_total", "legendFormat": "Unauthorized"}],
            "options": {"colorMode": "background"},
            "fieldConfig": {
                "defaults": {
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [{"color": "green", "value": 0}, {"color": "red", "value": 1}],
                    }
                }
            },
        },
        {
            "id": 2,
            "type": "stat",
            "title": "Duplicate Executions",
            "description": "MUST BE 0.",
            "gridPos": {"h": 6, "w": 6, "x": 6, "y": 0},
            "targets": [{"expr": "sentinel_security_duplicate_execution_total", "legendFormat": "Duplicates"}],
            "options": {"colorMode": "background"},
            "fieldConfig": {
                "defaults": {
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [{"color": "green", "value": 0}, {"color": "red", "value": 1}],
                    }
                }
            },
        },
        {
            "id": 3,
            "type": "stat",
            "title": "Unsafe ALLOWs",
            "description": "MUST BE 0. ALLOW issued with unavailable dependency.",
            "gridPos": {"h": 6, "w": 6, "x": 12, "y": 0},
            "targets": [{"expr": "sentinel_security_unsafe_allow_total", "legendFormat": "Unsafe ALLOWs"}],
            "options": {"colorMode": "background"},
            "fieldConfig": {
                "defaults": {
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [{"color": "green", "value": 0}, {"color": "red", "value": 1}],
                    }
                }
            },
        },
        {
            "id": 4,
            "type": "stat",
            "title": "Reconciliation Pending",
            "description": "UNKNOWN idempotency states.",
            "gridPos": {"h": 6, "w": 6, "x": 18, "y": 0},
            "targets": [{"expr": "sentinel_security_reconciliation_pending", "legendFormat": "Pending"}],
            "options": {"colorMode": "background"},
            "fieldConfig": {
                "defaults": {
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [{"color": "green", "value": 0}, {"color": "yellow", "value": 1}],
                    }
                }
            },
        },
        {
            "id": 5,
            "type": "timeseries",
            "title": "Token Rejections Over Time",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 6},
            "targets": [{"expr": "rate(sentinel_security_token_rejection_total[5m])", "legendFormat": "Rejections/s"}],
        },
        {
            "id": 6,
            "type": "timeseries",
            "title": "Escalation Breakdown by Reason",
            "description": "Why Sentinel is escalating.",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 6},
            "targets": [
                {"expr": 'rate(sentinel_decisions_total{decision="ESCALATE"}[5m])', "legendFormat": "{{reason}}"}
            ],
        },
    ],
}

# ── Dashboard 1: Executive Risk ───────────────────────────────────────────────
executive = {
    "title": "Sentinel - Executive Risk",
    "uid": "sentinel-exec",
    "tags": ["sentinel"],
    "refresh": "30s",
    "time": {"from": "now-1h", "to": "now"},
    "panels": [
        {
            "id": 1,
            "type": "stat",
            "title": "Intents/s",
            "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
            "targets": [{"expr": "rate(sentinel_intents_total[5m])", "legendFormat": "Intents/s"}],
        },
        {
            "id": 2,
            "type": "stat",
            "title": "ALLOW Rate",
            "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0},
            "targets": [{"expr": "sentinel:allow_rate:5m", "legendFormat": "ALLOW/s"}],
            "fieldConfig": {"defaults": {"color": {"fixedColor": "green", "mode": "fixed"}}},
        },
        {
            "id": 3,
            "type": "stat",
            "title": "ESCALATE Rate",
            "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0},
            "targets": [{"expr": "sentinel:escalate_rate:5m", "legendFormat": "ESCALATE/s"}],
            "fieldConfig": {"defaults": {"color": {"fixedColor": "orange", "mode": "fixed"}}},
        },
        {
            "id": 4,
            "type": "stat",
            "title": "CONTAIN Rate",
            "gridPos": {"h": 4, "w": 6, "x": 18, "y": 0},
            "targets": [{"expr": "sentinel:contain_rate:5m", "legendFormat": "CONTAIN/s"}],
            "fieldConfig": {"defaults": {"color": {"fixedColor": "red", "mode": "fixed"}}},
        },
        {
            "id": 5,
            "type": "timeseries",
            "title": "Decision Rate Over Time",
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 4},
            "targets": [
                {"expr": "sentinel:allow_rate:5m", "legendFormat": "ALLOW"},
                {"expr": "sentinel:escalate_rate:5m", "legendFormat": "ESCALATE"},
                {"expr": "sentinel:contain_rate:5m", "legendFormat": "CONTAIN"},
            ],
        },
        {
            "id": 6,
            "type": "timeseries",
            "title": "Risk Score Percentiles",
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 12},
            "targets": [
                {"expr": "histogram_quantile(0.50, rate(sentinel_risk_score_bucket[5m]))", "legendFormat": "p50 risk"},
                {"expr": "histogram_quantile(0.95, rate(sentinel_risk_score_bucket[5m]))", "legendFormat": "p95 risk"},
            ],
        },
    ],
}

# ── Dashboard 2: Authorization Performance ────────────────────────────────────
performance = {
    "title": "Sentinel - Authorization Performance",
    "uid": "sentinel-perf",
    "tags": ["sentinel"],
    "refresh": "15s",
    "time": {"from": "now-1h", "to": "now"},
    "panels": [
        {
            "id": 1,
            "type": "stat",
            "title": "p50 Latency (ms)",
            "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
            "targets": [{"expr": "sentinel:authorization_latency_p50:5m * 1000", "legendFormat": "p50"}],
        },
        {
            "id": 2,
            "type": "stat",
            "title": "p95 Latency (ms)",
            "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0},
            "targets": [{"expr": "sentinel:authorization_latency_p95:5m * 1000", "legendFormat": "p95"}],
            "fieldConfig": {
                "defaults": {
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": 0},
                            {"color": "yellow", "value": 400},
                            {"color": "red", "value": 1000},
                        ],
                    }
                }
            },
        },
        {
            "id": 3,
            "type": "stat",
            "title": "p99 Latency (ms)",
            "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0},
            "targets": [{"expr": "sentinel:authorization_latency_p99:5m * 1000", "legendFormat": "p99"}],
            "fieldConfig": {
                "defaults": {
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": 0},
                            {"color": "yellow", "value": 500},
                            {"color": "red", "value": 1000},
                        ],
                    }
                }
            },
        },
        {
            "id": 4,
            "type": "stat",
            "title": "XGBoost p99 (ms)",
            "gridPos": {"h": 4, "w": 6, "x": 18, "y": 0},
            "targets": [{"expr": "sentinel:ml_inference_p99:5m * 1000", "legendFormat": "XGBoost p99"}],
        },
        {
            "id": 5,
            "type": "timeseries",
            "title": "Authorization Latency Percentiles",
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 4},
            "targets": [
                {"expr": "sentinel:authorization_latency_p50:5m * 1000", "legendFormat": "p50"},
                {"expr": "sentinel:authorization_latency_p95:5m * 1000", "legendFormat": "p95"},
                {"expr": "sentinel:authorization_latency_p99:5m * 1000", "legendFormat": "p99"},
            ],
        },
        {
            "id": 6,
            "type": "timeseries",
            "title": "Component Latency Breakdown (worker p99)",
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 12},
            "targets": [
                {
                    "expr": "histogram_quantile(0.99, rate(sentinel_worker_queue_wait_seconds_bucket[5m])) * 1000",
                    "legendFormat": "Queue Wait p99",
                },
                {"expr": "sentinel:ml_inference_p99:5m * 1000", "legendFormat": "XGBoost p99"},
                {
                    "expr": "histogram_quantile(0.99, rate(sentinel_redis_latency_seconds_bucket[5m])) * 1000",
                    "legendFormat": "Redis p99",
                },
                {
                    "expr": "histogram_quantile(0.99, rate(sentinel_postgres_latency_seconds_bucket[5m])) * 1000",
                    "legendFormat": "Postgres p99",
                },
            ],
        },
    ],
}

# ── Dashboard 3: Worker & Queue Health ────────────────────────────────────────
worker = {
    "title": "Sentinel - Worker & Queue Health",
    "uid": "sentinel-worker",
    "tags": ["sentinel"],
    "refresh": "10s",
    "time": {"from": "now-1h", "to": "now"},
    "panels": [
        {
            "id": 1,
            "type": "gauge",
            "title": "Worker Utilization",
            "gridPos": {"h": 6, "w": 6, "x": 0, "y": 0},
            "targets": [{"expr": "sentinel:worker_utilization:5m", "legendFormat": "Utilization"}],
            "fieldConfig": {
                "defaults": {
                    "min": 0,
                    "max": 1,
                    "unit": "percentunit",
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": 0},
                            {"color": "yellow", "value": 0.7},
                            {"color": "red", "value": 0.9},
                        ],
                    },
                }
            },
        },
        {
            "id": 2,
            "type": "stat",
            "title": "Active Tasks",
            "gridPos": {"h": 6, "w": 6, "x": 6, "y": 0},
            "targets": [{"expr": "sentinel_worker_active_tasks", "legendFormat": "Active"}],
        },
        {
            "id": 3,
            "type": "stat",
            "title": "Capacity (MAX_CONCURRENT_TASKS)",
            "gridPos": {"h": 6, "w": 6, "x": 12, "y": 0},
            "targets": [{"expr": "sentinel_worker_capacity", "legendFormat": "Capacity"}],
        },
        {
            "id": 4,
            "type": "timeseries",
            "title": "Kafka Consumer Lag",
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 6},
            "targets": [{"expr": "sentinel_kafka_lag", "legendFormat": "{{topic}}[{{partition}}]"}],
        },
        {
            "id": 5,
            "type": "timeseries",
            "title": "Queue Wait p99 (ms)",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 14},
            "targets": [
                {
                    "expr": "histogram_quantile(0.99, rate(sentinel_worker_queue_wait_seconds_bucket[5m])) * 1000",
                    "legendFormat": "Queue Wait p99",
                }
            ],
        },
        {
            "id": 6,
            "type": "timeseries",
            "title": "Dependency Errors/s",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 14},
            "targets": [
                {"expr": "rate(sentinel_redis_errors_total[5m])", "legendFormat": "Redis"},
                {"expr": "rate(sentinel_postgres_errors_total[5m])", "legendFormat": "Postgres"},
                {"expr": "rate(sentinel_kafka_errors_total[5m])", "legendFormat": "Kafka"},
                {"expr": "rate(sentinel_ml_errors_total[5m])", "legendFormat": "ML"},
            ],
        },
    ],
}

for fname, dash in [
    ("04_security_invariants.json", security),
    ("01_executive_risk.json", executive),
    ("02_authorization_performance.json", performance),
    ("03_worker_queue_health.json", worker),
]:
    path = f"grafana/provisioning/dashboards/{fname}"
    with open(path, "w") as f:
        json.dump(dash, f, indent=2)
    print(f"Created: {path}")

print("Done.")
