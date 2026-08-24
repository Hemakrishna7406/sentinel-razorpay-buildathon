# Sentinel — Razorpay AI Buildathon 2026 Master Plan

**Version:** 1.0  
**Track:** AI Risk Manager  
**Project:** Sentinel  
**Positioning:** AI-powered behavioral risk detection and bounded containment for autonomous financial agents  
**Primary objective:** Build, measure, demonstrate, and defend a working defense-only system that detects anomalous financial behavior from autonomous agents and contains risky actions before money moves.

---

## 0. Executive Directive

Sentinel must be built as a **Risk Manager submission first**, an authorization system second, and a polished product third.

The project must prove one central hypothesis:

> **Does incorporating agent-level behavioral context improve detection of autonomous financial abuse over transaction-level signals alone while maintaining an acceptable false-escalation rate?**

The implementation must therefore optimize for:

**LOSS DEFINITION → DATA → DETECTOR → HELD-OUT EVALUATION → CONTAINMENT → FAILURE SAFETY → DEMO → INTERVIEW DEFENSIBILITY**

Do not optimize for technology count.

Do not optimize for UI before the detector works.

Do not claim production fraud performance from synthetic data.

Do not claim Razorpay has a missing internal control.

Do not build offense-capable functionality.

---

# 1. Strategic North Star

## 1.1 One-sentence pitch

> **Sentinel detects when an authorized AI agent starts behaving unlike itself, and contains the resulting financial risk before money moves — measured on held-out data, not vibes.**

## 1.2 Closing line

> **“Authorization tells us what an agent is allowed to do. Sentinel tells us when that agent stops behaving like the agent we trusted.”**

## 1.3 Product definition

Sentinel is a defense system for autonomous financial agents such as:

- refund agents
- retry/recovery agents
- checkout agents
- collections agents
- other software agents with delegated financial authority

It maintains an **Agent Behavioral Profile**, compares current behavior against historical baseline, combines behavioral and transaction-level signals, produces a risk decision, and uses bounded containment mechanisms to prevent unsafe execution.

---

# 2. Razorpay Alignment

## 2.1 Official track fit

The Risk Manager track requires a working:

- detector
- verifier
- or auto-responder

for one class of financial loss, with measured precision and recall on a held-out test set.

Sentinel maps directly:

| Requirement | Sentinel |
|---|---|
| One loss class | anomalous/unauthorized financial actions from autonomous agents |
| Detector | behavioral + transaction risk engine |
| Verifier | policy, identity, context, capability validation |
| Auto-responder | allow / escalate / contain |
| Precision | measured on held-out test set |
| Recall | measured on held-out test set |
| Defense-only | yes |
| Failure handling | fail-closed + recovery |

## 2.2 Product positioning

Razorpay publicly has agentic products, authorization controls, spending limits and autonomous guardrails.

Therefore Sentinel must **not** claim:

> “Razorpay does not have agent controls.”

Instead:

> “Sentinel complements authorization and guardrail systems by detecting behavioral deviation over time at the agent level.”

Core distinction:

**Authorization:** What is the agent allowed to do?

**Sentinel:** Is the agent still behaving like the agent we trusted?

---

# 3. Scope Lock

## 3.1 Primary loss class

> **Anomalous or unauthorized financial actions originating from autonomous agents operating with delegated financial authority.**

## 3.2 Primary entity

**Agent**

Not merely the transaction.

## 3.3 Primary signal

**Behavioral deviation over time**

## 3.4 Secondary signal

**Transaction and contextual risk**

## 3.5 Response

- ALLOW
- ESCALATE
- CONTAIN

## 3.6 What Sentinel is not

Sentinel is not:

- a replacement for Razorpay fraud systems
- a generic fraud detector
- an IAM product
- a generic LLM agent platform
- a chatbot
- a generic policy engine
- an offensive security tool
- a replacement for Razorpay Agent Studio
- a claim about Razorpay’s internal architecture

---

# 4. Core Research Hypothesis

#Sentinel provides a zero-trust behavioral risk and governance layer around autonomous financial agents, combining risk signals with deterministic policy and exact-action capability authorization before an agent can reach financial execution infrastructure.

### H0

Agent behavioral features provide no meaningful improvement over transaction-level signals.

The experiment must be designed so either result can be honestly reported.

This makes the project an engineering experiment rather than a predetermined marketing claim.

---

# 5. Threat Model

## 5.1 Threat actors / failure sources

Sentinel should model three broad causes:

### A. Compromised agent

An otherwise legitimate agent begins generating anomalous financial actions.

### B. Misconfigured agent

The agent is functioning as programmed but has an incorrect policy/configuration.

### C. Behavioral drift

The agent's behavior changes unexpectedly because its operating environment, task distribution, or underlying model behavior changes.

These are defensive detection scenarios.

No real exploitation is required or permitted.

---

# 6. Synthetic Behavioral Scenario Library

The dataset must contain multiple realistic scenarios.

## Scenario A — Normal

Characteristics:

- stable volume
- stable amount distribution
- known recipients
- normal operating hours
- normal action mix

Expected:

**ALLOW**

---

## Scenario B — Synthetic Abuse Burst

Characteristics:

- extreme velocity
- unusual amounts
- new recipients
- abnormal time
- rapid succession
- sudden deviation from agent baseline

Expected:

**CONTAIN**

---

## Scenario C — Misconfigured Agent

Characteristics:

- high frequency
- legitimate recipients
- consistent behavior
- policy threshold incorrectly configured

Expected:

**ESCALATE or policy-driven response**

This prevents Sentinel from equating anomaly with malicious intent.

---

## Scenario D — Slow / Threshold-Aware Abuse

Characteristics:

- low volume
- high-value actions
- actions deliberately close to thresholds
- low velocity
- recipient variation

Expected:

**SUSPICIOUS / ESCALATE**

---

## Scenario E — Legitimate Seasonal Spike

Characteristics:

- 8–10× volume
- legitimate recipients
- expected business period
- stable amount distribution
- historical context supports the spike

Expected:

**ALLOW**

This is the critical anti-shortcut scenario.

---

## Scenario F — New Agent

Characteristics:

- little/no history
- insufficient behavioral baseline

Expected:

**CONSERVATIVE ESCALATION**

Never:

**automatic denial solely due to lack of history**

---

# 7. Dataset Design

## 7.1 Dataset requirements

Generate synthetic event data with:

- agent_id
- timestamp
- action_type
- transaction_id
- amount
- currency
- recipient_id
- recipient_novelty
- merchant_id
- agent_age
- policy_limit
- time_since_previous_action
- rolling_1m_count
- rolling_1h_count
- rolling_24h_count
- historical_denial_rate
- historical_escalation_rate
- baseline_amount
- baseline_velocity
- operating-hour deviation
- behavior drift features
- scenario label
- risk label

## 7.2 Data generator

Create a reproducible generator:

`ml/data_generator.py`

Requirements:

- deterministic random seed
- configurable agent count
- configurable time window
- configurable scenario proportions
- configurable abuse intensity
- configurable seasonal spikes

Every generated dataset must record:

- generator version
- seed
- parameters
- creation timestamp

## 7.3 Dataset documentation

`dataset.md` must explicitly state:

- data is synthetic
- why synthetic data is necessary
- scenario definitions
- feature definitions
- labeling methodology
- known limitations
- potential biases
- intended interpretation

Never present synthetic benchmark numbers as production fraud performance.

---

# 8. Train / Validation / Test Strategy

Random transaction splitting is prohibited as the primary evaluation method.

Use a temporal + agent-aware split.

Example:

```text
Days 1–20
Agents A–F
        ↓
TRAIN

Days 21–25
Agents A–F
        ↓
VALIDATION

Days 26–30
Agents A–F + unseen Agents G–H
        ↓
HELD-OUT TEST
```

The exact split can change after experimentation, but the final methodology must prevent obvious leakage.

The evaluation document must explain:

- why the split was chosen
- what information was unavailable to the model at inference time
- how agent history is constructed
- how unseen agents are handled

---

# 9. Agent Behavioral Profile

Each agent receives a baseline profile.

Example:

```text
REFUND_AGENT_01

Average refunds/day: 18
Average amount: ₹3,240
95th percentile amount: ₹8,900
Typical hours: 09:00–19:00
Unique recipients/day: 15
Historical escalation rate: 0.8%
Policy violations: 0
```

The profile must be calculated from historical data only.

Never use future test data to build a training baseline.

---

# 10. Behavioral Drift Engine

For MVP, implement transparent statistical drift features.

Potential features:

- velocity ratio
- amount deviation
- recipient novelty ratio
- operating-hour deviation
- action-frequency deviation
- historical escalation deviation
- rolling-window deviation

Example:

```text
velocity_ratio = current_velocity / historical_velocity
```

Use robust handling for:

- zero baselines
- new agents
- sparse agents
- seasonal periods

The output is:

`behavioral_drift_score`

Do not add Isolation Forest, change-point detection or advanced anomaly models unless experiments show the baseline is insufficient.

---

# 11. Risk Model

## 11.1 Primary model

XGBoost classifier.

Reason:

- strong tabular performance
- explainability
- fast inference
- manageable engineering complexity
- suitable for behavioral + transaction features

## 11.2 Feature families

### Transaction/context

- amount
- recipient novelty
- action type
- time
- merchant context
- velocity

### Agent behavior

- agent age
- baseline amount
- baseline velocity
- historical action distribution
- historical denial rate
- historical escalation rate
- behavioral drift

## 11.3 Output

The model produces:

`agent_action_risk_score`

Map it to:

- SAFE
- SUSPICIOUS
- HIGH-RISK

Thresholds must be selected using validation data, not chosen solely for the demo.

---

# 12. Risk Decision Policy

The detector and response engine must remain separate.

Example:

```text
Risk score
    ↓
Decision policy
    ↓
SAFE / SUSPICIOUS / HIGH-RISK
    ↓
ALLOW / ESCALATE / CONTAIN
```

The exact thresholds should be tuned after evaluation.

Do not hard-code arbitrary values such as 0.3/0.7 merely because they look reasonable.

Document how thresholds were selected.

---

# 13. Ablation Study

This is a required experiment.

Compare:

### Baseline 1

Rules only

### Baseline 2

Transaction features only

### Baseline 3

Behavioral features only

### Model 4

Full Sentinel

Report:

- precision
- recall
- PR-AUC
- false escalation rate
- detection latency
- time-to-containment

Example structure:

| Model | Precision | Recall | PR-AUC | False Escalation |
|---|---:|---:|---:|---:|
| Rules only | measured | measured | N/A | measured |
| Transaction only | measured | measured | measured | measured |
| Behavioral only | measured | measured | measured | measured |
| **Full Sentinel** | **measured** | **measured** | **measured** | **measured** |

Do not fabricate numbers.

A negative result is acceptable and should be documented honestly.

---

# 14. Evaluation Metrics

Minimum:

- Precision
- Recall
- PR-AUC
- False escalation rate
- Unsafe auto-approval rate
- Decision p95 latency
- Detection latency
- Time-to-containment
- Duplicate-intent detection rate

## Primary safety metric

**Unsafe auto-approval rate**

Target:

`0` in defined safety test scenarios.

## Primary operational metric

**Time-to-containment**

Measure:

```text
abnormal behavior begins
        ↓
detection
        ↓
containment
```

---

# 15. Authorization / Containment Layer

This layer exists to enforce detector decisions.

## Flow

```text
Intent
 ↓
Risk
 ↓
Policy/context
 ↓
Decision
 ↓
Capability token
 ↓
Execution
```

## Capability token

The token must be bound to the exact action:

- intent_id
- agent_id
- action
- transaction_id
- amount
- currency
- recipient
- decision_id
- policy_version
- expiry
- nonce

It must not represent a general spending ceiling.

---

# 16. Security Invariants

The following must become automated tests.

### Invariant 1

No valid capability token → no execution.

```python
assert execution_without_valid_token is False
```

### Invariant 2

Expired token → no execution.

### Invariant 3

Wrong transaction_id → no execution.

### Invariant 4

Wrong agent_id → no execution.

### Invariant 5

Amount mismatch → no execution.

### Invariant 6

Tampered token → no execution.

### Invariant 7

Authorization dependency unavailable → no new capability token.

---

# 17. Execution Adapter

Create an interface:

```text
PaymentExecutionAdapter
```

Implement:

```text
MockPaymentAdapter
RazorpayTestModeAdapter
```

The mock adapter must support the complete demonstration.

Razorpay test-mode integration is optional and must never become a dependency.

---

# 18. Three Operating Modes

## OBSERVE

Purpose:

- learn baseline
- monitor agent
- block nothing

Output:

- behavioral profile
- drift signals
- risk scores

---

## SIMULATE

Purpose:

- test policies
- compare thresholds
- estimate operational impact

Example:

```text
Policy A: ₹25K threshold
Actions affected: X%
Exposure governed: ₹X
Manual reviews: X

Policy B: ₹50K threshold
Actions affected: X%
Exposure governed: ₹X
Manual reviews: X
```

---

## GOVERN

Purpose:

- enforce live containment

Outputs:

- ALLOW
- ESCALATE
- CONTAIN

---

# 19. Natural-Language Policy Compiler

P1 only.

Flow:

```text
Natural language
       ↓
LLM
       ↓
Structured policy
       ↓
Schema validation
       ↓
Safety validation
       ↓
Simulation
       ↓
Human confirmation
       ↓
Active policy
```

The LLM must never directly authorize financial execution.

The compiler has no execution privileges.

---

# 20. Failure Engineering

Minimum scenarios:

## Failure 1 — LLM policy compilation error

Response:

- schema validation
- human review
- no silent activation

## Failure 2 — execution timeout

Response:

- idempotency
- verification
- reconciliation

## Failure 3 — duplicate intent

Response:

- idempotency key
- duplicate rejection
- audit event

## Failure 4 — synthetic abuse burst

Response:

- behavioral drift
- risk escalation
- containment

## Failure 5 — authorization dependency unavailable

Response:

- fail closed
- no capability token
- no execution
- re-evaluate queued intents after recovery

---

# 21. Demonstration Architecture

The demo must use a controlled synthetic environment.

No offensive functionality.

No real exploitation.

No credential attacks.

No bypassing payment controls.

The abuse generator should simply create synthetic financial intents with predefined behavioral patterns.

---

# 22. Five-Minute Demo

## 0:00–0:20

Problem:

> “An AI agent can be fully authorized and still become dangerous if its behavior changes.”

Show agent baseline.

Then current anomalous behavior.

---

## 0:20–1:10

Synthetic Abuse Burst.

Show:

- velocity
- amount deviation
- recipient novelty
- time anomaly
- drift score
- risk score

Decision:

**CONTAIN**

---

## 1:10–1:50

Show held-out metrics:

- precision
- recall
- PR-AUC
- false escalation
- time-to-containment

These must be real measured values.

---

## 1:50–2:30

Seasonal legitimate spike.

Show:

**8–10× volume**

but behavior remains consistent.

Decision:

**ALLOW**

Message:

> “Sentinel is not a volume blocker. It is a behavior detector.”

---

## 2:30–3:10

Fail-closed scenario.

Disable authorization dependency.

New intent:

```text
NO CAPABILITY TOKEN
NO EXECUTION
```

Restore.

Re-evaluate queued intent.

---

## 3:10–3:40

One architecture diagram.

---

## 3:40–4:20

Optional policy simulation.

Only include if P0 demo is stable.

---

## 4:20–5:00

Closing:

> “Authorization tells us what an agent is allowed to do. Sentinel tells us when that agent stops behaving like the agent we trusted.”

---

# 23. Frontend Requirements

The dashboard is an observability layer, not the product's core innovation.

Minimum screens:

## Agent Overview

Show:

- agent name
- risk state
- baseline
- current behavior
- recent decisions

## Live Intent Stream

Show:

- timestamp
- agent
- action
- amount
- risk
- decision

## Behavioral Drift View

Show:

- baseline
- current window
- deviation
- risk contribution

## Decision Detail

Show:

- risk score
- top features
- decision
- policy rule
- capability status

## Audit

Show:

- intent
- decision
- policy version
- token
- execution result
- verification result

---

# 24. Backend Requirements

FastAPI service responsibilities:

- agent registration
- scoped authentication
- intent ingestion
- feature calculation
- behavioral profile retrieval
- risk inference
- policy evaluation
- decision generation
- capability issuance
- execution adapter invocation
- verification
- audit recording

Suggested API surface:

```text
POST /agents
GET  /agents/{agent_id}

POST /intents
GET  /intents/{intent_id}

POST /authorize
GET  /decisions/{decision_id}

POST /capabilities/verify

POST /simulate

GET  /agents/{agent_id}/profile

GET  /audit
```

Do not build unnecessary endpoints.

---

# 25. Database Model

PostgreSQL tables:

```text
agents
agent_profiles
intents
risk_scores
decisions
policies
policy_versions
capabilities
executions
audit_events
```

Redis:

- rolling velocity
- short-lived features
- capability/token state where appropriate
- cached behavioral profile features

Avoid adding TimescaleDB unless volume actually requires it.

---

# 26. Repository

```text
sentinel/
├── README.md
├── ARCHITECTURE.md
├── threat-model.md
├── evaluation.md
├── dataset.md
├── security/
│   ├── capability-token.md
│   └── failure-handling.md
├── experiments/
│   ├── baseline.md
│   └── ablation.md
├── services/
│   ├── api/
│   └── dashboard/
├── ml/
│   ├── data_generator.py
│   ├── features.py
│   ├── train.py
│   ├── evaluate.py
│   └── notebooks/
├── data/
│   └── sample/
├── tests/
│   ├── test_risk.py
│   ├── test_capabilities.py
│   ├── test_idempotency.py
│   └── chaos/
├── docs/
│   └── demo.md
└── LICENSE
```

---

# 27. README Structure

The first screen must communicate the project immediately.

Recommended order:

1. Sentinel name
2. one-line thesis
3. loss class
4. architecture image
5. benchmark table
6. demo GIF/video
7. methodology
8. agent behavioral profile
9. risk model
10. ablation study
11. containment
12. failure handling
13. setup
14. limitations
15. future work

Do not open with:

> “Sentinel is an innovative AI-powered platform…”

Avoid marketing language.

---

# 28. Documentation Requirements

## `threat-model.md`

Document:

- assets
- actors
- failure sources
- trust boundaries
- attack-independent synthetic scenarios
- mitigations

## `dataset.md`

Document:

- generator
- features
- labels
- scenarios
- splits
- limitations

## `evaluation.md`

Document:

- train/validation/test
- temporal split
- unseen agents
- metrics
- threshold selection
- statistical limitations

## `experiments/ablation.md`

Document:

- rules-only
- transaction-only
- behavioral-only
- full model
- results
- interpretation

## `security/capability-token.md`

Document:

- token structure
- exact-action scope
- expiration
- validation
- replay protection
- invariants

---

# 29. Testing Strategy

## Unit tests

Test:

- feature calculations
- risk scoring
- policy evaluation
- token validation
- idempotency
- baseline calculation

## Integration tests

Test:

```text
Intent
→ Risk
→ Decision
→ Token
→ Execution
→ Verification
→ Audit
```

## Security tests

Test:

- expired token
- wrong agent
- wrong transaction
- amount mismatch
- tampering
- replay
- missing token

## Failure tests

Test:

- LLM unavailable
- risk model unavailable
- database unavailable
- authorization unavailable
- execution timeout
- duplicate intent

---

# 30. Performance Targets

Targets are engineering goals, not fabricated results.

Aim for:

- authorization p95 <300 ms
- risk inference <100 ms
- feature retrieval <50 ms
- capability validation <20 ms

Report actual values.

Do not report target values as benchmark results.

---

# 31. P0 / P1 / P2

## P0 — Non-negotiable

- synthetic scenario generator
- Agent Behavioral Profile
- behavioral drift
- transaction features
- XGBoost risk model
- held-out temporal + agent evaluation
- precision
- recall
- PR-AUC
- false escalation
- time-to-containment
- SAFE / SUSPICIOUS / HIGH-RISK
- ALLOW / ESCALATE / CONTAIN
- capability token
- no-token-no-execution invariant
- fail-closed behavior
- mock execution adapter
- public GitHub
- evaluation documentation
- five-minute demo

## P1 — Differentiators

- NL policy compiler
- policy simulation
- Observe / Simulate / Govern UI
- SHAP explanations
- Razorpay test-mode adapter
- audit UI
- policy trade-off comparison
- agent profile visualization
- replay/recovery queue

## P2 — Only if fully stable

- Kafka
- streaming architecture
- Grafana
- ECS/cloud deployment
- multi-agent orchestration
- agent reputation system
- advanced anomaly detection
- sophisticated policy DSL

---

# 32. Build Order

## Phase 1 — Research and Threat Model

Deliverables:

- threat model
- loss definition
- scenario library
- feature specification
- evaluation methodology

Gate:

**No coding of product UI until this is approved.**

---

## Phase 2 — Dataset

Deliverables:

- reproducible generator
- scenario distributions
- labels
- train/validation/test split
- data documentation

Gate:

**No risk model until leakage is checked.**

---

## Phase 3 — Detector

Deliverables:

- behavioral baseline
- drift score
- transaction features
- XGBoost
- evaluation
- ablation

Gate:

**No serious product work until the detector has measurable results.**

---

## Phase 4 — Containment

Deliverables:

- decision engine
- capability token
- mock execution
- verification
- audit

Gate:

**No execution without a valid capability.**

---

## Phase 5 — Failure Engineering

Deliverables:

- fail-closed
- idempotency
- timeout recovery
- abuse-burst containment
- automated tests

Gate:

**Every P0 failure scenario must have reproducible evidence.**

---

## Phase 6 — Product Layer

Deliverables:

- Observe
- Simulate
- Govern
- agent dashboard
- decision visualization

---

## Phase 7 — P1 AI Layer

Deliverables:

- NL policy compiler
- validation
- simulation
- human confirmation

---

## Phase 8 — Competition Packaging

Deliverables:

- README
- architecture diagram
- benchmark report
- demo video
- pitch
- interview preparation

---

# 33. Demo Readiness Checklist

Before recording the final demo:

- [ ] Model is trained from documented data
- [ ] Test set is held out
- [ ] Metrics are real
- [ ] Abuse scenario is generated, not scripted
- [ ] Seasonal spike does not trigger unnecessary containment
- [ ] New agent escalates conservatively
- [ ] Capability token is exact-action scoped
- [ ] Invalid token cannot execute
- [ ] Authorization outage fails closed
- [ ] Recovery works
- [ ] Dashboard updates in real time
- [ ] Demo works without Razorpay credentials
- [ ] Razorpay adapter works if credentials are available
- [ ] No offense-capable functionality exists
- [ ] No fabricated performance claims
- [ ] Demo can be restarted from a clean state

---

# 34. Judge Objection Matrix

## “Isn't this just fraud detection?”

Answer:

> Sentinel's primary entity is the agent and its primary signal is behavioral deviation over time. Transaction-level signals are included, but the research question is whether agent context adds predictive value.

## “Razorpay already has guardrails.”

Answer:

> Correct. Sentinel is complementary. Guardrails define what an agent is allowed to do; Sentinel detects whether the agent's behavior has deviated from the behavior we trusted.

## “Why AI?”

Answer:

> The risk model learns compound behavioral patterns across time, context and agent history that static thresholds do not capture. The LLM is separately used for natural-language policy compilation and never controls financial execution.

## “Why XGBoost?”

Answer:

> The problem is primarily structured/tabular behavioral data. XGBoost gives strong performance, fast inference and explainability without unnecessary model complexity.

## “What if the model is wrong?”

Answer:

> The model cannot directly move money. Decisions are bounded by policy, capability scope and fail-closed execution controls. Uncertainty becomes escalation rather than unrestricted autonomy.

## “What happens with a new agent?”

Answer:

> We don't treat lack of history as guilt. The system enters a conservative state and escalates until sufficient behavioral evidence exists.

## “What happens during a legitimate traffic spike?”

Answer:

> The benchmark includes seasonal legitimate spikes specifically to test this. Volume alone is not sufficient for containment; behavioral context matters.

## “Isn't the dataset artificial?”

Answer:

> Yes. It is explicitly documented as synthetic. We use it to test the hypothesis and system behavior, not to claim production fraud performance. The important evaluation design is the temporal and unseen-agent holdout plus ablation study.

---

# 35. Interview Knowledge Areas

Prepare deeply for:

### ML

- XGBoost
- feature engineering
- class imbalance
- calibration
- precision/recall
- PR-AUC
- threshold selection
- leakage
- drift
- concept drift
- model monitoring

### Agents

- tool permissions
- delegated authority
- agent identity
- prompt injection
- bounded autonomy
- capability security
- human escalation

### Payments

- idempotency
- duplicate transactions
- authorization
- settlement vs execution
- refunds
- retries
- payment failure
- reconciliation

### Backend

- FastAPI
- PostgreSQL
- Redis
- API authentication
- concurrency
- queues
- retries
- circuit breakers

### Distributed systems

- at-least-once delivery
- idempotency
- replay
- consistency
- failure modes
- graceful degradation

### Security

- scoped credentials
- token replay
- privilege escalation
- policy tampering
- audit integrity
- least privilege

---

# 36. Personal Hiring Narrative

Your personal story should be:

```text
Computer Science
      ↓
AI/ML + Financial Analytics
      ↓
Quantitative / financial systems work
      ↓
SentinelOS / autonomous-agent governance exploration
      ↓
Razorpay problem:
"What changes when autonomous agents interact with money?"
      ↓
Sentinel
      ↓
Agent behavioral risk detection
      ↓
Measured + defense-only + production-minded system
```

Do not present Sentinel as a random hackathon idea.

Present it as the next technical evolution of your interest in **AI + financial systems + autonomous decision-making**.

---

# 37. What Success Looks Like

Sentinel is successful if a judge can understand all of this within five minutes:

1. Autonomous financial agents can behave abnormally even when authorized.
2. Sentinel builds a behavioral baseline for each agent.
3. Sentinel detects deviations using measurable ML signals.
4. Sentinel distinguishes legitimate spikes from suspicious behavior.
5. Sentinel produces a measurable risk decision.
6. Sentinel contains risky actions before execution.
7. Sentinel fails closed when authorization infrastructure is unavailable.
8. The detector has real held-out precision/recall results.
9. Agent-level features provide measurable experimental value.
10. The system is defensible as a future financial-risk component.

---

# 38. Definition of Done

The project is **not done** when:

- the UI looks good
- the API works
- the LLM responds
- the dashboard has charts

The project is done when:

```text
Synthetic scenario
        ↓
Agent behavior
        ↓
Behavioral profile
        ↓
Risk features
        ↓
Risk model
        ↓
Held-out evaluation
        ↓
Decision
        ↓
Containment
        ↓
Capability verification
        ↓
Execution
        ↓
Verification
        ↓
Audit
```

works end-to-end and has reproducible evidence.

---

# 39. Final Strategic Principle

Do not try to win by saying:

> “Our AI is smarter.”

Try to win by demonstrating:

> **“Our system knows when not to trust an autonomous agent.”**

The strongest version of Sentinel is not the one with the most models, agents, APIs or infrastructure.

It is the one where:

**the problem is precise, the detector is measurable, the response is bounded, the failure behavior is safe, and every major claim is backed by an experiment.**

---

# 40. Master Build Equation

```text
Sentinel
=
Agent Behavioral Profile
+
Behavioral Drift
+
Transaction Context
+
Explainable Risk Model
+
Held-Out Evaluation
+
Bounded Containment
+
Exact-Action Capability
+
Fail-Closed Execution
+
Failure Recovery
+
Evidence
```

# FINAL NORTH STAR

**BUILD → MEASURE → CONTAIN → DEMONSTRATE → DEFEND → GET NOTICED → GET HIRED**

The implementation should never sacrifice the first five for the last two.
