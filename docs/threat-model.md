# Sentinel — Threat Model

*Content ported and integrated from existing threat model documentation.*

## Core Threats

1. **Prompt Injection / Malicious Fine-tuning**
   - **Asset**: Execution Boundary
   - **Defense**: Sentinel XGBoost model, NL Policy engine.
   - **Containment**: Fail-closed mechanism.

2. **Replay Attacks**
   - **Asset**: API Endpoints
   - **Defense**: Redis Idempotency Engine.
   - **Containment**: Immediate rejection of duplicate intents.

3. **Token Theft / Tampering**
   - **Asset**: Capability Token
   - **Defense**: Short-lived (5s) JWTs bound to specific intent and amount. Cryptographic verification.

4. **Observability Outage**
   - **Asset**: Logging / Metrics
   - **Defense**: Segregated non-authoritative path. System must not fail-open if metrics fail to publish.

5. **Dependency / Database Outage**
   - **Asset**: Redis/PostgreSQL
   - **Defense**: Fail-closed validation. If DB is down, capability token cannot be issued.
