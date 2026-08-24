# Sentinel — Failure Engineering & Resiliency

**Version:** 1.0

---

## 1. Fail-Closed Philosophy

Sentinel operates in a high-risk financial environment where an accidental `ALLOW` (False Negative) is significantly more damaging than an accidental `ESCALATE` (False Positive).

Therefore, Sentinel is designed as a **strictly fail-closed system**.

### The Rule of Unhandled Exceptions
If any component in the Sentinel pipeline—from the ML feature extractor to the database audit logger—throws an unexpected exception, the system MUST catch it at the boundary and default the decision to `ESCALATE`.

**No combination of network timeouts, database disconnects, or malformed JSON should ever result in an unauthorized transaction being executed.**

---

## 2. Typed Exception Hierarchy

To ensure boundaries can reason about failures, we use a strict exception hierarchy:

- `SentinelSecurityException`: Base class.
  - `FailClosedException`: Triggered when an internal assumption is violated. Forces an ESCALATE.
  - `IdempotencyConflictException`: Triggered when a client reuses an idempotency key with a mutated payload.
  - `BehavioralDuplicateException`: Triggered when a client script goes rogue and submits identical transfers rapidly.
  - `CapabilityTokenException`: Raised by the Execution Adapter when cryptography fails.

---

## 3. Idempotency & Duplicate Detection

We implement two layers of request deduplication to prevent double-spending and mitigate client-side bugs.

### 3.1 Client Idempotency (Deterministic)
Every API request must include an `Idempotency-Key` header.
- **Same Key + Same Payload:** Returns the cached result of the previous execution (or `ALLOW`/`ESCALATE` status).
- **Same Key + Different Payload:** Raises `IdempotencyConflictException`. This prevents attackers from "reserving" a key with a benign request and re-using it for a malicious one.

### 3.2 Behavioral Duplicate Detection (Heuristic)
Autonomous AI agents can have retry bugs where they fail to record a successful transaction and loop, sending a new request with a new idempotency key but identical semantics.

- **Trigger:** If Sentinel sees a request with a *different* idempotency key, but the exact same `agent_id`, `recipient`, `amount`, `currency`, and `action_type` within a rolling **5-second window**, it raises a `BehavioralDuplicateException`.
- **Result:** The duplicate request is rejected fail-closed, breaking the autonomous agent's infinite loop and forcing human escalation.

---

## 4. Execution Boundary Failures

The `ExecutionAdapter` is the final gate. If it encounters:
1. Missing Capability Token
2. Expired Capability Token
3. Tampered Capability Token Payload
4. Cryptographic Signature Mismatch
5. JTI (Nonce) Replay

It raises an `ExecutionException` and denies the mutation. The API layer catches this and returns an HTTP 500 or 403, completely blocking the transaction.
