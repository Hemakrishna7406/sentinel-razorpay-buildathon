# Sentinel Architecture

**Sentinel** is a fail-closed authorization and containment layer for autonomous financial agents. It treats uncertainty, replay, and infrastructure failure as first-class security states. Sentinel sits between autonomous agent intent generation and the MCP (Model Context Protocol) gateway, ensuring that all actions taken on financial backends (e.g., Razorpay) are strictly evaluated against behavioral and semantic risk limits before capability tokens are issued.

## The Sentinel Proposition

> Recovery is not allowed to create authorization. Recovery may only restore previously established state or force the system into a safer uncertain state.

Sentinel is engineered under the assumption that AI agents will inevitably drift, hallucinate, or be compromised. In all unpredictable scenarios—from agent drift to Kafka timeouts to complete Redis failure—Sentinel defaults to **ESCALATE** and strictly refuses to issue a capability token.

## The Four Planes

Sentinel operates across four distinct planes to ensure absolute separation of concerns between authorization, observability, persistence, and disaster recovery.

### 1. Decision Plane (Authorization & ML)
**Components:** FastAPI Gateway, XGBoost Behavioral Model, Semantic NL Policy Engine (Pydantic/LiteLLM), Redis (Idempotency cache).
- Evaluates the incoming `IntentContext` via a combined risk fusion model.
- If and only if both the Behavioral Model and Semantic Engine agree the risk is below the dynamic threshold, a **Capability Token** (JTI-bound) is issued.
- **Fail-Closed Guarantee:** Any exception, model unreachability, timeout, or disagreement between models automatically forces an `ESCALATE` decision without a token.

### 2. Audit Plane (Cryptographic Ledger)
**Components:** PostgreSQL, Merkle Hash Chain.
- Every intent, context feature, decision, reason, and execution trace is logged immutably.
- Records are chained cryptographically (previous hash is included in the new hash).
- **Asynchronous Persistence:** The Audit Plane is populated via an independent Kafka consumer (`sentinel-audit`). This guarantees that a slow database cannot stall the Fast-Path authorization (bounded degradation).

### 3. Observability Plane (Metrics & Tracing)
**Components:** Prometheus, Grafana, Jaeger (OpenTelemetry).
- Provides real-time visibility into the agent's behavior.
- Monitors throughput (QPS), Risk Fusion scores, Policy rejections, Kafka latency, and Redis cache hit rates.
- **Non-Authoritative:** Telemetry failures (e.g., Jaeger downtime) explicitly trap exceptions and never disrupt the Decision Plane.

### 4. Recovery Plane (Disaster Recovery & State)
**Components:** Redpanda (Kafka), `OffsetTracker`.
- The single source of truth for pending intents. If the worker or API crashes, intents are guaranteed to be re-processed or cleanly escalate on idempotency limits.
- **Strict RPO:** Ensures 0 lost intents during failure via explicit offset commits only after the Audit and Redis caches are successfully synchronized.
- During complete node failure, state is restored identically from Kafka and PostgreSQL ledgers.

## The Token Invariant

The core security constraint of Sentinel is the **Capability Token Invariant**:
- **ALLOW:** Token ISSUED → MCP Execution ALLOWED
- **ESCALATE:** Token NOT ISSUED → MCP Execution BLOCKED
- **CONTAIN:** Token NOT ISSUED → MCP Execution BLOCKED
- **REPLAY:** Same Token/Idempotency Key → NOT RE-EXECUTED (Failed Replay)
- **INFRA FAILURE (e.g. Redis Down):** Token NOT ISSUED → MCP Execution BLOCKED

No transaction can proceed on the underlying Razorpay API without a valid, one-time-use capability token signed and issued by the Sentinel Decision Plane.

## Deployment Hardening (Phase 22+)
- **Graceful Drains:** Processes handle SIGTERM by pausing Kafka consumption and draining the active execution queue (bounded < 1s).
- **Startup Integrity:** API containers refuse readiness (`/health/ready` returns 503) if Kafka or Redis are unavailable, ensuring the load balancer drops them before they fail an intent.
- **Audit Verification:** The cryptographic chain can be manually verified using `verify_audit_chain()` to prove the historical integrity of all financial intents.
