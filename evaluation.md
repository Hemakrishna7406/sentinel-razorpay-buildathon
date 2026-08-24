# Sentinel — Evaluation Methodology

**Version:** 1.0

---

## 1. Split Rationale

The dataset is partitioned using a **strict temporal and agent-level split**. This is the most rigorous methodology for evaluating behavioral detection systems, as it prevents both time leakage and agent-identity memorization.

```text
TRAIN:      Days 1–20,  Agents A–F
VALIDATION: Days 21–25, Agents A–F
TEST:       Days 26–30, Agents A–H
```

### Information unavailable at inference
During training, the model does NOT have access to:
- Any data from days 21–30.
- Any behavioral profiles or baseline statistics for Agents G and H.
- The scenario labels, ground truth loss labels, or loss types (except as the `loss_label` training target).

---

## 2. Unseen Agent Handling

Agents G and H are explicitly introduced in the Test set (Days 26–30). They represent entirely new autonomous agents interacting with the financial system for the first time.

**Methodology for unseen agents:**
1. **No Profile Generation:** We do NOT construct a baseline profile for G and H using test data. This would violate the temporal constraint, as a real-time system cannot peek at the next 5 days of data to establish a baseline for today.
2. **Missing Indicators:** The feature extraction engine (`ml/features.py`) explicitly sets `has_sufficient_history=0` for these agents. All behavioral z-scores are set to `NaN`, and explicit missing indicator variables (`velocity_z_missing=1`, etc.) are activated.
3. **Conservative Escalation:** The policy layer (Phase 4) will enforce `ESCALATE` for agents with insufficient history, completely independent of the XGBoost model's prediction. The model learns to rely on transaction-level features when behavioral context is missing.

---

## 3. Threshold Selection Rationale

The XGBoost model outputs a risk probability $P(loss) \in [0, 1]$. This probability must be converted into discrete policy decisions.

We use the **Validation Set (Days 21–25)** to select the operational threshold.

1. **Target Recall:** In financial risk detection, catching unauthorized actions (Recall) is typically prioritized over minimizing false positives (Precision), up to a certain operational limit of manual review capacity.
2. **Selection Logic:** We find the threshold that achieves a target recall (e.g., 0.90) on the validation set. If multiple thresholds achieve this, we select the one that maximizes precision.
3. **Application:** This validation-derived threshold is then frozen and applied to the Test set. We never tune the threshold on test data.

The policy layer defines two boundaries:
- `SUSPICIOUS` = validation-derived threshold
- `HIGH-RISK` = validation-derived threshold + safety margin (e.g., +0.2)

---

## 4. Calibration Analysis

Because policy decisions (SAFE / SUSPICIOUS / HIGH-RISK) depend heavily on the raw probability scores, the probabilities themselves must be well-calibrated. A score of 0.85 should roughly correspond to an 85% chance of the action being a loss event.

**Calibration Metrics Recorded:**
- **Brier Score:** Measures the mean squared difference between predicted probabilities and actual outcomes. A lower score indicates better calibration.
- **Calibration Curve Data:** Stored in `model_manifest.json` for visualization. It compares the predicted probability (binned) against the true fraction of positives in each bin.

---

## 5. Ablation Study

To answer the core research hypothesis ($H_1$: *Does incorporating agent-level behavioral context improve detection over transaction-level signals alone?*), we evaluate four distinct model configurations on the exact same test set:

1. **Rules Only:** A static baseline using simple heuristics (e.g., amount > 90th percentile).
2. **Transaction Only:** XGBoost trained only on the current intent's details (amount, recipient novelty, hour).
3. **Behavioral Only:** XGBoost trained only on the agent's behavioral z-scores and context.
4. **Full Sentinel:** XGBoost trained on both transaction and behavioral features.

The results are automatically generated in `experiments/ablation.md` by `ml/ablation.py`.
