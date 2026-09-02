# Sentinel — Project Status

## Product Status
The product is transitioning from a static legacy HTML/JS dashboard to a canonical React/Vite/Tailwind frontend. The core security backend, ML engine, capability-token generation, and execution streaming are working.

## Engineering Status
- **Backend**: FastAPI with SQLite (needs PostgreSQL validation), Redis idempotency, Kafka/Redpanda architecture, fail-closed security.
- **Frontend**: React UI actively being built (`frontend/`), superseding legacy `dashboard/`.
- **ML**: XGBoost risk engine with deterministic evaluation.
- **Security**: Capability tokens and execution adapters functional.

## Verified Capabilities
- XGBoost risk engine detection
- Behavioral profiling baselines
- Capability-token authorization
- Redis idempotency 
- Fail-closed execution boundary
- Razorpay MCP Streamable HTTP 
- Real Razorpay Test-mode execution

## Known Limitations
- Semantic provider currently simulated
- Vulcan inference not claimed
- Production Razorpay execution not claimed
- Production-scale throughput not yet demonstrated
- Chaos suite not yet complete
- Dashboard vs Frontend phase discrepancy

## Current Milestone
**Milestone C: Production Frontend (Phase 5 - 16)**
Migrating all UI logic to the new React frontend and establishing it as the canonical UI.

## Next Milestone
**Milestone D: Reliability & Chaos (Phase 17 - 19)**
API contract hardening, Security regression suite, and Chaos & Failure Engineering.

## Production-readiness Scorecard
- Core Security Engine: COMPLETE
- Evaluation & Evidence: COMPLETE
- Production Frontend: IN PROGRESS
- Reliability & Chaos: NOT STARTED
- Operational Readiness: NOT STARTED
- Production Hardening: BLOCKED (Depends on Frontend and Reliability)
- Release Candidate: NOT STARTED
