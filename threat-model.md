# Sentinel — Threat Model

**Version:** 1.0
**Scope:** Defense-only behavioral risk detection for autonomous financial agents.

---

## 1. Assets Under Protection

| Asset | Description | Impact if Compromised |
|-------|------------|----------------------|
| Financial execution capability | Ability to move money (refunds, payouts, retries, checkouts) | Direct financial loss |
| Agent identity | Scoped API key + agent_id binding | Unauthorized execution under trusted identity |
| Behavioral profiles | Historical baseline per agent | Profile poisoning → bypass detection |
| Policy configuration | Decision thresholds + rules | Lowered thresholds → unsafe auto-approval |
| Capability tokens | Exact-action signed authorization | Token forgery/replay → unauthorized execution |
| Audit trail | Hash-chained event log | Evidence tampering, accountability loss |

---

## 2. Trust Boundaries

```
┌─────────────────────────────────────────────────────┐
│                    UNTRUSTED ZONE                    │
│                                                     │
│   AI Agent (refund / retry / checkout / collections) │
│   - May be compromised                              │
│   - May be misconfigured                            │
│   - May drift behaviorally                          │
│                                                     │
└────────────────────┬────────────────────────────────┘
                     │ Intent (scoped API key)
                     ▼
┌─────────────────────────────────────────────────────┐
│               SENTINEL TRUST BOUNDARY                │
│                                                     │
│   Intent Gateway ─→ Behavioral Profile              │
│        │                    │                        │
│        ▼                    ▼                        │
│   Feature Engine ──→ Risk Model ──→ Decision Policy  │
│                                          │           │
│                          ┌───────────────┼────────┐  │
│                          ▼               ▼        ▼  │
│                       ALLOW          ESCALATE  CONTAIN│
│                          │                           │
│                          ▼                           │
│                  Capability Token                    │
│                          │                           │
│                          ▼                           │
│                  Execution Adapter                   │
│                          │                           │
│                          ▼                           │
│                  Verification + Audit                │
│                                                     │
└─────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              EXTERNAL PAYMENT SYSTEM                 │
│   Mock (always) / Razorpay Test Mode (optional)     │
└─────────────────────────────────────────────────────┘
```

---

## 3. Threat Actors / Failure Sources

### A. Compromised Agent

An otherwise legitimate agent begins generating anomalous financial actions. The agent's credentials are valid but its behavior has changed — it may have been tampered with, its prompt/instructions modified, or its underlying model behavior shifted.

**Key characteristic:** Valid authorization, anomalous behavior.

### B. Misconfigured Agent

The agent functions as programmed but operates under incorrect policy or configuration parameters. It is not malicious — it is doing what it was told, but what it was told is wrong.

**Key characteristic:** Consistent but policy-violating behavior. Not malicious intent.

### C. Behavioral Drift

The agent's behavior changes because its operating environment, task distribution, or underlying model behavior changes. This may or may not indicate a problem — environmental changes can be legitimate (e.g., changed business hours, seasonal patterns) or problematic (e.g., gradual capability creep).

**Key characteristic:** Gradual or sudden behavioral deviation from established baseline.

**Important:** These are defensive detection scenarios. No real exploitation is required or permitted (masterplan §21).

---

## 4. Synthetic Scenario Library

Seven scenarios map to the three threat actors above. Each scenario is independently testable via `ml/scenarios.py`.

### Scenario A — Normal

**Threat actor:** None (baseline)
**Characteristics:** Stable volume, stable amounts, known recipients, normal hours, normal action mix.
**Expected loss:** None (`loss_label=0`)
**Expected response:** ALLOW
**Mitigation:** None needed — establishes the behavioral baseline other scenarios deviate from.

---

### Scenario B — Abuse Burst

**Threat actor:** A (Compromised)
**Characteristics:** Extreme velocity, unusual amounts, novel recipients, abnormal time, rapid succession, sudden deviation from baseline.
**Expected loss:** Unauthorized actions (`loss_label=1, loss_type="unauthorized_action"`)
**Expected response:** CONTAIN
**Mitigation:** Behavioral drift detection (velocity_z, amount_z, recipient_novelty spike), risk model escalation, capability denial.

---

### Scenario C — Misconfigured Agent

**Threat actor:** B (Misconfigured)
**Characteristics:** High frequency, legitimate recipients, consistent behavior pattern, policy threshold incorrectly configured.
**Expected loss:** Policy violations (`loss_label=1, loss_type="policy_violation"`)
**Expected response:** ESCALATE (not CONTAIN — not malicious)
**Mitigation:** Policy evaluation flags violations. Human review triggered. This prevents Sentinel from equating anomaly with malicious intent.

---

### Scenario D — Slow / Threshold-Aware Abuse

**Threat actor:** A (Compromised)
**Characteristics:** Low volume, high-value actions, amounts deliberately near thresholds, low velocity, recipient variation.
**Expected loss:** Unauthorized actions (`loss_label=1, loss_type="unauthorized_action"`)
**Expected response:** SUSPICIOUS → ESCALATE
**Mitigation:** Amount deviation detection, recipient novelty tracking, cumulative drift scoring.

---

### Scenario E — Legitimate Seasonal Spike

**Threat actor:** None (legitimate environmental change)
**Characteristics:** 8–10× volume, legitimate recipients, expected business period (e.g., sale, holiday), stable amount distribution within the spike, historical context supports elevated activity.
**Expected loss:** None (`loss_label=0`)
**Expected response:** ALLOW
**Mitigation needed:** None — this is the **critical anti-shortcut scenario**. The model must NOT learn `HIGH VOLUME = BAD`. This scenario proves Sentinel is a behavior detector, not a volume blocker.

---

### Scenario F — New Agent

**Threat actor:** None (insufficient information)
**Characteristics:** Little or no history, insufficient behavioral baseline, no established profile.
**Expected loss:** Unknown (`loss_label=0` — lack of history is not guilt)
**Expected response:** CONSERVATIVE ESCALATION (never automatic denial solely due to lack of history)
**Mitigation:** `has_sufficient_history=0` flag. Policy layer enforces escalation independent of ML prediction. As history accumulates, agent transitions to normal evaluation.

---

### Scenario G — Benign Behavioral Drift

**Threat actor:** C (Behavioral Drift — benign variant)
**Characteristics:** Agent changes operating pattern permanently due to legitimate environmental change (e.g., merchant changes hours from 09–19 to 11–23). Behavior shifts but remains internally consistent within the new pattern.
**Expected loss:** None (`loss_label=0`)
**Expected response:** SUSPICIOUS initially → SAFE after baseline adaptation
**Mitigation needed:** Baseline recomputation over time. This scenario proves that `behavioral deviation ≠ necessarily abuse`. Without this scenario, the model could learn that any deviation from historical norms indicates malicious activity.

---

## 5. Mitigations Matrix

| Threat | Detection Signal | Response | Invariant |
|--------|-----------------|----------|-----------|
| Compromised agent | velocity_z, amount_z, recipient_novelty, hour_distance | CONTAIN | No token → no execution |
| Misconfigured agent | Policy violation flags, consistent anomaly pattern | ESCALATE | Human review required |
| Slow abuse | Amount deviation, cumulative drift | ESCALATE | Time-windowed monitoring |
| Seasonal spike (legitimate) | High volume, consistent distribution | ALLOW | Behavioral context overrides volume |
| New agent | Insufficient history flag | Conservative ESCALATE | Policy-enforced, independent of ML |
| Benign drift | Temporary deviation, new pattern stabilizes | Initial SUSPICIOUS → SAFE | Baseline adaptation |
| Token forgery/replay | HMAC verification, nonce, expiry | Reject execution | 10 security invariants |
| Authorization outage | Fail-closed detection | ESCALATE, no token | No ALLOW on any failure |
| Audit tampering | Hash chain verification | Integrity alert | Chain breaks on modification |

---

## 6. Infrastructure & Network Threats (Added: 2026-08-29)

### Infrastructure Replay Attacks

**Threat ID:** T-NET-01  
**Scenario:** Attacker captures network traffic between API and Redis/Kafka and replays capability tokens or idempotency keys.  
**Attack Vector:** Man-in-the-middle on unencrypted Redis/Kafka connections  
**Likelihood:** MEDIUM (requires network access)  
**Impact:** HIGH (could bypass authorization)  

**Current Mitigations:**
- JTI replay protection via Redis atomic SET NX
- Short token TTL (5 seconds default)
- Idempotency keys prevent duplicate processing

**Gaps Identified:**
- Redis connections may not enforce TLS
- Kafka connections may not use SASL_SSL
- Network security relies on infrastructure configuration

**Recommendations:**
1. Enforce TLS for all Redis connections (rediss://)
2. Enforce Kafka SASL_SSL authentication
3. Document network security requirements in deployment guide
4. Add startup validation that fails if insecure connections detected in production

---

### Time Synchronization Attacks

**Threat ID:** T-TIME-01  
**Scenario:** Clock skew between API server and worker causes token expiry validation to fail incorrectly.  
**Attack Vector:** NTP manipulation or misconfigured system clocks  
**Likelihood:** LOW (requires infrastructure access)  
**Impact:** MEDIUM (could accept expired tokens)  

**Current Mitigations:**
- Token TTL is short (5 seconds), limiting window
- Expiry checked at both issuance and verification

**Gaps Identified:**
- No NTP synchronization monitoring
- No clock drift alerting
- No documented time sync requirements

**Recommendations:**
1. Add NTP sync monitoring to health checks
2. Alert on clock drift > 1 second between services
3. Document time synchronization requirements (NTP servers, stratum)
4. Consider adding timestamp to token payload for drift detection

---

### Rate Limiting Bypass (Application-Layer DDoS)

**Threat ID:** T-DOS-01  
**Scenario:** Attacker floods API with evaluation requests to exhaust resources or poison behavioral profiles.  
**Attack Vector:** Direct API access without rate limiting  
**Likelihood:** HIGH (no rate limiting implemented)  
**Impact:** HIGH (service degradation, false positives)  

**Current Mitigations:**
- NONE - Rate limiting not implemented

**Gaps Identified:**
- No request rate limiting at API layer
- No agent-level throttling
- Could exhaust Redis/Kafka/PostgreSQL connections
- Could trigger false behavioral anomalies

**Recommendations:**
1. Implement rate limiting (100 requests/minute per IP)
2. Add per-agent rate limiting (1000 requests/hour per agent_id)
3. Implement circuit breakers for dependency overload
4. Add rate limit metrics to monitoring

**Status:** CRITICAL - Must be addressed before production

---

### Clickjacking & UI Redressing

**Threat ID:** T-UI-01  
**Scenario:** Attacker embeds Sentinel dashboard in malicious iframe, overlays fake UI to trick operators into approving malicious requests.  
**Attack Vector:** Missing X-Frame-Options header  
**Likelihood:** MEDIUM (requires operator interaction)  
**Impact:** MEDIUM (social engineering attack)  

**Current Mitigations:**
- NONE - Security headers not implemented

**Recommendations:**
1. Add X-Frame-Options: DENY header
2. Add Content-Security-Policy with frame-ancestors 'none'
3. Implement CSRF tokens if session-based auth added

**Status:** HIGH - Must be addressed before production

---

## 7. What This Threat Model Is NOT

- NOT a model of attacks against Razorpay's infrastructure
- NOT a penetration testing framework
- NOT an offensive security assessment
- NOT a claim about Razorpay's internal controls
- NOT a generic fraud detection threat model

This is a **defensive behavioral detection** threat model for the specific loss class: anomalous financial actions from autonomous agents.

---

## 8. Threat Model Updates

**Version 1.0** (Initial): Core threat actors and behavioral scenarios  
**Version 1.1** (2026-08-29): Added infrastructure, network, and application-layer threats based on penetration test findings  

**Next Review:** Post-remediation of critical findings (T-DOS-01)
