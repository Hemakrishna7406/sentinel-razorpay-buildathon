# Sentinel — ai-ml.md

Implements masterplan §7–14. This file is the one most directly graded against "measured precision and recall on a held-out test set" — treat it as the technical core of the submission.

---

## 1. Feature engineering (`ml/features.py`)

**Transaction/context features** (per intent):
```
amount, amount_log
recipient_novelty          # 0 if recipient seen before by this agent, 1 if new
action_type_onehot
hour_of_day, is_typical_hour   # vs. this agent's baseline hours
merchant_context_flags
rolling_1m_count, rolling_1h_count, rolling_24h_count
```

**Agent behavioral features** (per intent, computed against `agent_profiles`):
```
agent_age_days
velocity_ratio        = rolling_1h_count / max(baseline_hourly_rate, epsilon)
amount_deviation       = (amount - baseline_avg_amount) / max(baseline_std_amount, epsilon)
recipient_novelty_ratio = new_recipients_in_window / total_actions_in_window
hour_deviation           = 0 if within [typical_hour_start, typical_hour_end] else distance from range
escalation_rate_delta     = current_window_escalation_rate - historical_escalation_rate
behavioral_drift_score     = weighted combination of the above (see §2)
```

**Robust handling (masterplan §10) — implement explicitly, don't skip:**
```python
def velocity_ratio(current, baseline, agent_age_days):
    if agent_age_days < MIN_BASELINE_DAYS:
        return None  # signals "insufficient history" downstream, not zero
    return current / max(baseline, EPSILON)
```
A `None`/insufficient-history signal must propagate to the decision policy as "conservative escalation" (masterplan Scenario F), not silently default to 0 or 1.

## 2. Behavioral drift score (MVP: transparent, not a black box)

```python
def behavioral_drift_score(features: dict) -> float:
    weights = {"velocity_ratio": 0.3, "amount_deviation": 0.25,
               "recipient_novelty_ratio": 0.25, "hour_deviation": 0.1,
               "escalation_rate_delta": 0.1}
    return sum(weights[k] * normalize(features[k]) for k in weights)
```
Start here. Only reach for Isolation Forest / change-point detection if `experiments/ablation.md` shows this simple baseline is the bottleneck — masterplan §10 is explicit about this, and a defensible simple model beats an undefended complex one in an interview.

## 3. Risk model (`ml/train.py`)

```python
import xgboost as xgb

model = xgb.XGBClassifier(
    max_depth=4, n_estimators=200, learning_rate=0.05,
    scale_pos_weight=compute_class_weight(y_train),  # handle imbalance
    eval_metric="aucpr",
)
model.fit(X_train, y_train, eval_set=[(X_val, y_val)], early_stopping_rounds=20)
```

- **Class imbalance**: abuse/escalation events will be a small fraction of total intents by design (masterplan §6's scenario mix should reflect this realistically — don't balance 50/50, that's not what production traffic looks like). Use `scale_pos_weight` and PR-AUC, not accuracy.
- **Explainability**: SHAP values computed at inference for the top-3 contributing features per decision (P1) — this is what turns "risk_score: 0.92" into a legible reason string on the dashboard.

## 4. Train/validation/test split (`ml/data_generator.py` + `ml/evaluate.py`)

Implements masterplan §8 exactly:
```python
def temporal_agent_split(df, train_days=(1,20), val_days=(21,25), test_days=(26,30), holdout_agents=("G","H")):
    train = df[df.day.between(*train_days) & ~df.agent_id.isin(holdout_agents)]
    val   = df[df.day.between(*val_days) & ~df.agent_id.isin(holdout_agents)]
    test  = df[(df.day.between(*test_days)) | (df.agent_id.isin(holdout_agents) & df.day.between(*test_days))]
    return train, val, test
```
`agent_profiles` used at inference time for the test split must be computed **only from that agent's train-window history** — never recomputed including test-window data. This is the single most important line to get right; a reviewer who understands leakage will check exactly this.

## 5. Ablation study (`experiments/ablation.py` → `experiments/ablation.md`)

```python
configs = {
    "rules_only":         {"features": [], "use_rules": True},
    "transaction_only":   {"features": TRANSACTION_FEATURES, "use_rules": False},
    "behavioral_only":    {"features": BEHAVIORAL_FEATURES, "use_rules": False},
    "full_sentinel":      {"features": TRANSACTION_FEATURES + BEHAVIORAL_FEATURES, "use_rules": False},
}
for name, cfg in configs.items():
    model = train(cfg)
    results[name] = evaluate(model, test_set)  # precision, recall, PR-AUC, false_escalation
write_ablation_report(results)  # → experiments/ablation.md, auto-generated table, not hand-typed
```
Auto-generate the markdown table from the actual run, not hand-typed — this is what lets you honestly say "these numbers are reproducible from the repo," which is a stronger claim than a static table.

## 6. Decision policy — threshold selection (masterplan §12)

```python
# Select thresholds on VALIDATION data via PR-curve inspection, document the choice:
# e.g. "threshold=0.35 chosen to hold false-escalation < 15% while maximizing recall"
thresholds = tune_thresholds(model, X_val, y_val, target_false_escalation=0.15)
```
Write the selection rationale into `evaluation.md` — "we chose X because Y, measured on validation" is the sentence a panel is listening for; "0.3/0.7 because it looked right" is the sentence masterplan §12 explicitly forbids.

## 7. Metrics to compute and report (masterplan §14)

```python
metrics = {
    "precision": precision_score(y_test, y_pred),
    "recall": recall_score(y_test, y_pred),
    "pr_auc": average_precision_score(y_test, y_scores),
    "false_escalation_rate": fp / (fp + tn),
    "unsafe_auto_approval_rate": count_high_risk_allowed / total_allowed,  # target: 0
    "decision_p95_latency_ms": ...,
    "detection_latency_seconds": ...,       # time from burst-start to first HIGH-RISK flag
    "time_to_containment_seconds": ...,     # time from burst-start to first CONTAIN
    "duplicate_detection_rate": ...,
}
```

## 8. Synthetic data generator (`ml/data_generator.py`)

```python
def generate(seed: int, n_agents: int, days: int, scenario_mix: dict, out_path: str):
    """
    scenario_mix e.g. {"normal": 0.85, "abuse_burst": 0.03, "misconfigured": 0.03,
                        "slow_abuse": 0.03, "seasonal_spike": 0.03, "new_agent": 0.03}
    Deterministic given seed. Writes data + a manifest.json recording
    {generator_version, seed, params, created_at} per masterplan §7.2.
    """
```
Implement each scenario from masterplan §6 as its own generator function (`gen_normal`, `gen_abuse_burst`, `gen_misconfigured`, `gen_slow_abuse`, `gen_seasonal_spike`, `gen_new_agent`) — keep them separately testable and separately tunable, since the seasonal-spike scenario in particular needs to be tuned until it genuinely doesn't trigger containment (that's a demo-readiness checklist item, not a one-shot generation).

## 9. What NOT to build for MVP

Isolation Forest, change-point detection, deep learning of any kind, a second model for drift beyond the weighted score in §2, online/streaming retraining. All P2 per masterplan §31 — none are required to answer the actual grading bar, and each adds a failure surface with no corresponding line in the objection matrix that needs it.
