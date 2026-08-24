# Sentinel — database.md

PostgreSQL for durable state; Redis for hot/short-lived state. Matches masterplan §25.

---

## 1. PostgreSQL schema

```sql
CREATE TABLE agents (
    agent_id        TEXT PRIMARY KEY,
    display_name    TEXT NOT NULL,
    action_types    TEXT[] NOT NULL,           -- e.g. {refund, retry}
    api_key_hash    TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE agent_profiles (
    agent_id                TEXT PRIMARY KEY REFERENCES agents(agent_id),
    avg_actions_per_day     NUMERIC,
    avg_amount              NUMERIC,
    p95_amount               NUMERIC,
    typical_hour_start        INT,             -- 0-23
    typical_hour_end          INT,
    avg_unique_recipients_day NUMERIC,
    historical_escalation_rate NUMERIC,
    historical_denial_rate     NUMERIC,
    policy_violation_count      INT DEFAULT 0,
    computed_from_days           INT,           -- how much history this baseline reflects
    last_computed_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Recomputed on a schedule (e.g. daily) from intents table, NEVER from data
-- newer than the profile's own last_computed_at + never from test-split data.

CREATE TABLE intents (
    intent_id       UUID PRIMARY KEY,
    agent_id        TEXT NOT NULL REFERENCES agents(agent_id),
    action          TEXT NOT NULL,
    amount          BIGINT NOT NULL,            -- paise
    currency        TEXT NOT NULL DEFAULT 'INR',
    recipient_id    TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_intents_agent_time ON intents(agent_id, created_at);

CREATE TABLE risk_scores (
    intent_id           UUID PRIMARY KEY REFERENCES intents(intent_id),
    behavioral_drift_score NUMERIC NOT NULL,
    transaction_risk_score NUMERIC NOT NULL,
    combined_score          NUMERIC NOT NULL,
    top_features             JSONB,             -- SHAP top-3, P1
    model_version              TEXT NOT NULL,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE policies (
    policy_id       UUID PRIMARY KEY,
    org_scope       TEXT NOT NULL DEFAULT 'default',
    name            TEXT NOT NULL,
    active_version  TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE policy_versions (
    policy_id       UUID REFERENCES policies(policy_id),
    version         TEXT NOT NULL,
    rule_json       JSONB NOT NULL,             -- compiled deterministic rules
    source_nl_text  TEXT,                        -- original natural-language policy, P1
    confirmed_by    TEXT,                          -- human who confirmed activation
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (policy_id, version)
);

CREATE TABLE decisions (
    decision_id     UUID PRIMARY KEY,
    intent_id       UUID NOT NULL REFERENCES intents(intent_id),
    risk_level      TEXT NOT NULL,              -- SAFE / SUSPICIOUS / HIGH-RISK
    action          TEXT NOT NULL,              -- ALLOW / ESCALATE / CONTAIN
    policy_version  TEXT NOT NULL,
    reason_code     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE capabilities (
    intent_id       UUID PRIMARY KEY REFERENCES intents(intent_id),
    decision_id     UUID NOT NULL REFERENCES decisions(decision_id),
    transaction_id  TEXT NOT NULL,
    token_hash      TEXT NOT NULL,               -- store hash, not raw signed token
    expires_at      TIMESTAMPTZ NOT NULL,
    used_at         TIMESTAMPTZ,                  -- null until execution consumes it
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE executions (
    intent_id       UUID PRIMARY KEY REFERENCES intents(intent_id),
    adapter         TEXT NOT NULL,               -- mock | razorpay_test
    status          TEXT NOT NULL,               -- success | failed | timeout
    provider_ref    TEXT,
    verified_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_events (
    seq             BIGSERIAL PRIMARY KEY,
    intent_id       UUID,
    event_type      TEXT NOT NULL,               -- intent_received | decision_made | token_issued | executed | denied | outage_queued ...
    payload         JSONB NOT NULL,
    prev_hash       TEXT NOT NULL,
    row_hash        TEXT NOT NULL,               -- sha256(prev_hash || event_type || payload || seq)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_intent ON audit_events(intent_id);
```

## 2. Redis usage

| Key pattern | Purpose | TTL |
|---|---|---|
| `idem:{key}` | idempotency lock during processing | 90s |
| `profile:{agent_id}` | cached agent_profiles row | 5min (invalidate on recompute) |
| `velocity:{agent_id}:1m` / `:1h` / `:24h` | rolling counters (INCR + EXPIRE) | rolling |
| `token:{intent_id}` | active capability token, for fast verify | = token TTL (90s) |
| `outage:queue` | intents received while authorization dependency unavailable | until recovery |

## 3. Deliberately not using yet (per masterplan §31 P2)

- **TimescaleDB** — Postgres with the `created_at` indexes above is enough at demo scale; add only if a real volume/retention need shows up.
- **A vector DB** — nothing in this system does semantic retrieval; the NL policy compiler (P1) is a single-shot LLM call, not RAG.

## 4. Migration/seed strategy

- `alembic` for schema migrations from day one — a panel will ask how you'd evolve this in production, and "we have migrations" is a one-sentence answer.
- `data/sample/seed.sql` generated from `ml/data_generator.py`'s output — the same generator that produces training data also seeds the demo database, so the demo dashboard and the reported benchmark numbers are provably the same data-generation process, not two disconnected stories.
