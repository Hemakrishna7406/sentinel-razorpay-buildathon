# Sentinel — Dataset Documentation

**Version:** 1.0

---

## 1. Data Is Synthetic

All data used in Sentinel is **explicitly synthetic**. It is generated programmatically by `ml/data_generator.py` using deterministic random seeds.

### Why synthetic data is necessary

- No real-world dataset of autonomous financial agent behavioral abuse exists publicly.
- Real Razorpay transaction data is confidential and unavailable for this submission.
- Synthetic data allows controlled scenario generation with known ground-truth labels.
- Synthetic data enables reproducible evaluation — any reviewer can regenerate the exact dataset from the seed.

### What synthetic data does NOT demonstrate

- Production fraud detection performance.
- Real-world agent behavioral distributions.
- Actual financial loss rates.
- Razorpay-specific transaction patterns.

Benchmark numbers from synthetic data should be interpreted as: **"the system correctly distinguishes synthetic behavioral patterns under controlled conditions"** — not as production fraud detection rates.

---

## 2. Scenario Definitions

Seven scenarios are implemented as independent generator functions. Each scenario models a specific behavioral pattern associated with a threat actor or legitimate condition.

| Scenario | Generator | Threat Actor | Expected Response |
|----------|-----------|-------------|-------------------|
| A: Normal | `gen_normal` | None | ALLOW |
| B: Abuse Burst | `gen_abuse_burst` | Compromised | CONTAIN |
| C: Misconfigured | `gen_misconfigured` | Misconfigured | ESCALATE |
| D: Slow Abuse | `gen_slow_abuse` | Compromised | ESCALATE |
| E: Seasonal Spike | `gen_seasonal_spike` | None (legitimate) | ALLOW |
| F: New Agent | `gen_new_agent` | None (insufficient info) | Conservative ESCALATE |
| G: Benign Drift | `gen_benign_drift` | Drift (benign) | SUSPICIOUS → SAFE |

See `threat-model.md` §4 for detailed scenario characteristics.

---

## 3. Feature Definitions

### Per-intent fields (generated)

| Field | Type | Description |
|-------|------|-------------|
| intent_id | UUID | Unique intent identifier |
| agent_id | str | Agent identifier (A–H) |
| timestamp | datetime | Intent timestamp |
| day | int | Day number (1–30) |
| action_type | str | refund / retry / checkout / payout |
| transaction_id | UUID | Unique transaction identifier |
| amount | int | Amount in **integer paise** (never float) |
| currency | str | Always "INR" |
| recipient_id | str | Recipient identifier |
| recipient_novelty | int | 0=seen before, 1=new recipient for this agent |
| merchant_id | str | Merchant identifier |
| agent_age_days | int | Days since agent registration |
| hour_of_day | int | 0–23 |
| time_since_previous_action | float | Seconds since agent's last action |
| rolling_1m_count | int | Agent's actions in last 1 minute |
| rolling_1h_count | int | Agent's actions in last 1 hour |
| rolling_24h_count | int | Agent's actions in last 24 hours |

### Per-intent context fields (generated)

| Field | Type | Description |
|-------|------|-------------|
| baseline_avg_amount | int | Agent's historical average amount (paise) |
| baseline_std_amount | int | Agent's historical amount std dev (paise) |
| baseline_hourly_rate | float | Agent's historical avg actions/hour |
| typical_hour_start | int | Agent's typical start hour |
| typical_hour_end | int | Agent's typical end hour |
| historical_escalation_rate | float | Agent's historical escalation rate |
| historical_denial_rate | float | Agent's historical denial rate |

### Label fields (generated)

| Field | Type | Description |
|-------|------|-------------|
| scenario_label | str | Which generator produced this row |
| loss_label | int | Ground truth: 0=no loss event, 1=loss event |
| loss_type | str or null | null / "unauthorized_action" / "policy_violation" |
| has_sufficient_history | int | 0=insufficient history, 1=sufficient |

### Fields NOT in the generated dataset

| Field | Computed At | Description |
|-------|-----------|-------------|
| model_risk | ML inference | Risk probability from XGBoost |
| risk_level | ML inference | SAFE / SUSPICIOUS / HIGH-RISK |
| decision | Policy evaluation | ALLOW / ESCALATE / CONTAIN |

These are model/policy outputs, computed at inference time. They are **never** present in the training dataset.

---

## 4. Label Methodology

### Ground truth: `loss_label`

The `loss_label` field indicates whether a genuine loss event occurred:

- **0**: No financial loss. The action is legitimate, even if unusual (seasonal spike, benign drift, new agent with legitimate intent).
- **1**: A loss event occurred. The action represents unauthorized or policy-violating financial activity.

The `loss_type` field provides categorization:

- `null`: No loss event.
- `"unauthorized_action"`: Compromised agent generating illegitimate financial actions.
- `"policy_violation"`: Misconfigured agent violating policy (not malicious, but incorrect).

### Why this is NOT `risk_label`

The ground truth label captures **whether a loss occurred**, not what the model should predict. The model learns to predict loss probability. The policy layer maps predictions to decisions. These are three separate stages:

```
loss_label (ground truth, in dataset)
    ↓
model_risk (ML output, at inference)
    ↓
decision (policy output, at inference)
```

This separation prevents the dataset from becoming a proxy for the scenario generator.

---

## 5. Train / Validation / Test Split

```
TRAIN:      Days 1–20,  Agents A–F
VALIDATION: Days 21–25, Agents A–F
TEST:       Days 26–30, Agents A–H (G, H are unseen)
```

### Split rationale

- **Temporal split** prevents future-information leakage. The model never sees data from after the training window during training.
- **Agent-level holdout** tests generalization to entirely new agents. Agents G and H have never been seen during training.
- **Combined temporal + agent split** is the strongest holdout methodology for this domain — it prevents both time leakage and agent-identity memorization.

### Unseen agent handling (G, H)

Agents G and H appear only in the test set. They have:

- `has_sufficient_history=0`
- No behavioral profile derived from training data
- No baseline statistics

The model receives explicit `*_missing=1` flags for all behavioral features. The policy layer enforces conservative escalation **independently** of the model's prediction.

Profiles for G/H are **never** constructed from test-window data.

---

## 6. Known Limitations

1. **Synthetic distributions may not reflect real-world complexity.** Real agent behavior has more variance, noise, and edge cases than synthetic generators produce.

2. **Scenario boundaries are sharp.** Real compromised agents may exhibit subtler behavioral changes than synthetic abuse bursts.

3. **The scenario mix is configurable but arbitrary.** We test robustness across multiple distributions (85/3/3/3/3/3/2, 90/2/2/2/2/2/0, etc.) but the true distribution of anomalous agent behavior is unknown.

4. **Temporal patterns are simplified.** Real agents exhibit complex temporal patterns (weekday/weekend, holiday, gradual ramp-up) that synthetic data approximates but does not fully capture.

5. **Agent behavioral diversity is limited.** Eight synthetic agents cannot represent the full diversity of real autonomous financial agents.

6. **Label assignment is deterministic by scenario.** All abuse_burst rows are labeled `loss_label=1`. In reality, some anomalous behavior might not result in actual loss.

---

## 7. Potential Biases

1. **Scenario-label leakage risk:** If the model can infer the scenario generator from non-behavioral features, performance may be inflated. The ablation study tests this by comparing transaction-only vs. behavioral features.

2. **Volume bias:** If normal agents always have low volume and abuse scenarios have high volume, the model may learn volume as a shortcut. Scenario E (seasonal spike) explicitly tests this.

3. **Temporal bias:** If anomalous scenarios cluster in specific time periods, the model may learn time-of-day as a proxy. Generator ensures scenarios can occur across the full time range.

---

## 8. Intended Interpretation

Benchmark results from this synthetic dataset demonstrate:

1. The system can distinguish synthetic behavioral patterns under controlled conditions.
2. Agent-level behavioral features provide measurable improvement (or not — H0 is acceptable) over transaction-level features alone.
3. The holdout methodology prevents obvious information leakage.
4. The system handles edge cases (seasonal spikes, new agents, benign drift) as specified.

Results should **never** be presented as production fraud detection performance.
