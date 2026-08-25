# Sentinel Benchmarking Suite

This directory contains the reproducible benchmark harness for Sentinel, establishing performance baselines across Tier A (Micro), Tier B (Service Integration), and Tier C (End-to-End Stress).

## Tiers
- **Tier A (Microbenchmarks)**: Isolated tests using SQLite and mocked I/O. Measures absolute CPU-bound overhead for Redis idempotency, XGBoost (including SHAP), Policy Engine, and Capability token issuance.
- **Tier B (Integration)**: Requires Docker stack (Postgres + Redis + Redpanda). Measures infrastructure overhead and queuing delays.
- **Tier C (End-to-End Stress)**: Realistic traffic mixes (ALLOW/ESCALATE/CONTAIN) scaling from 10 to 1000 concurrent requests to measure security under load and degradation behavior.

## Usage
Run benchmarks from the project root:
```bash
uv run python benchmarks/redis_benchmark.py
uv run python benchmarks/authorization_latency.py
```
