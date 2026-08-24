# Sentinel — architecture.md

Derived from `masterplan.md`. This is the implementation-level architecture; masterplan.md remains the source of truth for scope, priorities, and gates.

---

## 1. System diagram

```
                              AI Agent
                    (refund / retry / checkout / collections)
                                  │
                                  ▼
                          Intent Gateway
                    (scoped API key per agent_id)
                                  │
                  ┌───────────────┴────────────────┐
                  ▼                                 ▼
       Agent Behavioral Profile              Transaction Context
       (Postgres + Redis cache)              (amount, recipient,
                  │                            time, novelty)
                  └───────────────┬─────────────────┘
                                  ▼
                    Behavioral Drift + Risk Model
                         (features.py → XGBoost)
                                  │
                                  ▼
                  agent_action_risk_score → SAFE / SUSPICIOUS / HIGH-RISK
                                  │
                                  ▼
                        Decision Policy (policies table)
                                  │
                  ┌───────────────┼────────────────┐
                  ▼                ▼                ▼
               ALLOW           ESCALATE          CONTAIN
                  │
                  ▼
          Capability Token issuer
        (exact-action scoped, signed)
                  │
                  ▼
        PaymentExecutionAdapter
         ├── MockPaymentAdapter        (always on)
         └── RazorpayTestModeAdapter   (if credentials available)
                  │
                  ▼
             Verification job
                  │
                  ▼
        Audit Log (hash-chained, append-only)
```

## 2. Service boundaries

One backend service (`services/api`) for the MVP — masterplan §25/§31 explicitly defers Kafka/microservices to P2. Internally organized as modules, not separate deployables:

```
services/api/
├── identity/         # agent registration, scoped API keys
├── profile/          # Agent Behavioral Profile: build + retrieve baseline
├── intents/           # intent ingestion, normalization, idempotency check
├── risk/               # feature calculation, model inference, drift score
├── policy/             # policy storage, evaluation, versioning
├── authorization/       # decision engine, capability token issuance/verification
├── execution/            # PaymentExecutionAdapter + implementations
├── audit/                 # hash-chained audit writer
└── simulate/               # what-if evaluation against historical intents (P1)
```

Module boundaries matter more than process boundaries here — this is what lets you later split into real microservices (P2) without a rewrite, while keeping deployment trivial before Sept 5.

## 3. Request lifecycle (the one flow to get right)

```
POST /intents
  → normalize + idempotency check (reject duplicate via hash(agent, amount, recipient, time-bucket))
  → fetch agent_profile (Redis cache, fallback Postgres)
  → compute transaction features + behavioral drift features
  → risk.infer() → agent_action_risk_score + SHAP top-3 (P1)
  → policy.evaluate(score, context) → SAFE/SUSPICIOUS/HIGH-RISK → ALLOW/ESCALATE/CONTAIN
  → if ALLOW: authorization.issue_capability(intent) → capability_token
  → execution_adapter.execute(capability_token) [only with a valid, unexpired, exact-match token]
  → verification.reconcile(execution_result)
  → audit.record(intent, decision, token, execution_result)
  → response to agent: decision + (capability_token | escalation_id | denial_reason)
```

Every arrow above is a place a failure scenario from masterplan §20 attaches — build each arrow assuming the next step can fail.

## 4. Data flow for Observe / Simulate / Govern (masterplan §18)

- **Observe**: intents flow through feature calculation + risk inference, decision is computed and logged, but `authorization.issue_capability` is never called — nothing blocks, everything is recorded for profile-building.
- **Simulate**: `POST /simulate` takes a candidate policy + a historical intent window (no live intents), runs the same policy.evaluate() path in a dry run, returns aggregate impact — never touches the capability/execution path at all.
- **Govern**: full lifecycle above, live.

Same policy-evaluation code path across all three modes — don't fork the logic per mode, only fork what happens *after* the decision (log-only vs. simulate-aggregate vs. issue-token).

## 5. Cross-cutting concerns

- **Idempotency**: enforced at intent ingestion, keyed on `hash(agent_id, action, amount, recipient_id, time_bucket)`. Store the key with a short TTL in Redis, check-then-set atomically.
- **Fail-closed**: any exception or timeout between risk inference and capability issuance must resolve to ESCALATE or CONTAIN, never ALLOW. Implement this as a single decorator/middleware around the authorization module so it can't be forgotten in a new code path — `@fail_closed` wrapping any step that can throw.
- **Audit**: append-only table, each row includes `hash(prev_row_hash + row_content)`. Verify chain integrity with a standalone script (`tests/test_audit_chain.py`), not just on write.
- **Config-as-data, not code**: policy thresholds, decision boundaries, and drift-feature parameters live in the `policies`/`policy_versions` tables, not hardcoded constants — this is what makes Simulate mode meaningful (you're testing real config changes, not code changes).

## 6. Deployment (MVP)

Single-host `docker-compose` is sufficient and correct for the Sept 5 deadline:

```yaml
services:
  api:        # FastAPI, services/api
  dashboard:  # React, served via nginx or Vite preview
  postgres:
  redis:
```

No ECS, no Kafka, no multi-service orchestration — masterplan §31 puts all of that in P2, gated on the P0/P1 list being fully done with time to spare.
