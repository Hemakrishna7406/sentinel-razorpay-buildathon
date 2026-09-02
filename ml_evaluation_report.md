# Sentinel ML Evaluation & Economic Cost Analysis

## 1. Dataset & Pipeline Characteristics
- **Dataset Generation**: Synthetic behavioral scenarios spanning 30 days (Agents A-H).
- **Positive Class**: Anomalous behavior leading to potential loss (`loss_label = 1`).
- **Negative Class**: Normal baseline activity (`loss_label = 0`).
- **Features Used**: Extracted temporal rolling counts, time since last action, amount aggregations.
- **Data Splitting**: Strict Temporal. Train (Days 1-20), Validation (Days 21-25), Test (Days 26-30).
- **Leakage / Imbalance**: No temporal leakage. Positive class imbalance is handled via XGBoost `scale_pos_weight`.

## 2. Baseline Metrics (Held-out Test Set)
- **Test Set Size**: 40320 records (34132 Positive, 6188 Negative).
- **PR-AUC**: 0.9815

## 3. Economic Cost Model (Synthetic Assumptions)
> **IMPORTANT:** The following costs are synthetic economic assumptions used for threshold optimization, not actual observed Razorpay financial loss data.

- **False Positive (FP)**: Legitimate behavior incorrectly classified as risky.
  - *Cost Assumption*: ₹50.00 per FP (accounts for user friction, manual review time, blocked legitimate activity).
- **False Negative (FN)**: Risky behavior incorrectly classified as legitimate.
  - *Cost Assumption*: ₹2,000.00 per FN (accounts for potential unauthorized payout / financial loss).

## 4. Threshold Sweep & Optimal Threshold
The table below sweeps the classification threshold to find the point that minimizes **Total Expected Cost**.

| Threshold | Precision | Recall | F1 | FPR | FNR | TP | TN | FP | FN | Est FP Cost | Est FN Cost | Total Cost |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0.10 | 0.9876 | 0.6418 | 0.7780 | 0.0446 | 0.3582 | 21905.0 | 5912.0 | 276.0 | 12227.0 | ₹13,800.00 | ₹24,454,000.00 | ₹24,467,800.00 |
| 0.15 | 0.9966 | 0.6413 | 0.7804 | 0.0121 | 0.3587 | 21889.0 | 6113.0 | 75.0 | 12243.0 | ₹3,750.00 | ₹24,486,000.00 | ₹24,489,750.00 |
| 0.20 | 0.9976 | 0.6019 | 0.7508 | 0.0079 | 0.3981 | 20543.0 | 6139.0 | 49.0 | 13589.0 | ₹2,450.00 | ₹27,178,000.00 | ₹27,180,450.00 |
| 0.25 | 0.9979 | 0.5762 | 0.7305 | 0.0066 | 0.4238 | 19666.0 | 6147.0 | 41.0 | 14466.0 | ₹2,050.00 | ₹28,932,000.00 | ₹28,934,050.00 |
| 0.30 | 0.9981 | 0.5751 | 0.7297 | 0.0060 | 0.4249 | 19629.0 | 6151.0 | 37.0 | 14503.0 | ₹1,850.00 | ₹29,006,000.00 | ₹29,007,850.00 |
| 0.35 | 0.9985 | 0.5749 | 0.7297 | 0.0047 | 0.4251 | 19623.0 | 6159.0 | 29.0 | 14509.0 | ₹1,450.00 | ₹29,018,000.00 | ₹29,019,450.00 |
| 0.40 | 0.9987 | 0.5749 | 0.7297 | 0.0040 | 0.4251 | 19621.0 | 6163.0 | 25.0 | 14511.0 | ₹1,250.00 | ₹29,022,000.00 | ₹29,023,250.00 |
| 0.45 | 0.9992 | 0.5748 | 0.7298 | 0.0026 | 0.4252 | 19618.0 | 6172.0 | 16.0 | 14514.0 | ₹800.00 | ₹29,028,000.00 | ₹29,028,800.00 |
| 0.50 | 0.9994 | 0.5746 | 0.7297 | 0.0018 | 0.4254 | 19611.0 | 6177.0 | 11.0 | 14521.0 | ₹550.00 | ₹29,042,000.00 | ₹29,042,550.00 |
| 0.55 | 0.9995 | 0.5745 | 0.7296 | 0.0015 | 0.4255 | 19608.0 | 6179.0 | 9.0 | 14524.0 | ₹450.00 | ₹29,048,000.00 | ₹29,048,450.00 |
| 0.60 | 0.9996 | 0.5744 | 0.7296 | 0.0011 | 0.4256 | 19605.0 | 6181.0 | 7.0 | 14527.0 | ₹350.00 | ₹29,054,000.00 | ₹29,054,350.00 |
| 0.65 | 0.9996 | 0.5743 | 0.7295 | 0.0011 | 0.4257 | 19603.0 | 6181.0 | 7.0 | 14529.0 | ₹350.00 | ₹29,058,000.00 | ₹29,058,350.00 |
| 0.70 | 0.9997 | 0.5742 | 0.7295 | 0.0008 | 0.4258 | 19599.0 | 6183.0 | 5.0 | 14533.0 | ₹250.00 | ₹29,066,000.00 | ₹29,066,250.00 |
| 0.75 | 0.9999 | 0.5740 | 0.7293 | 0.0003 | 0.4260 | 19592.0 | 6186.0 | 2.0 | 14540.0 | ₹100.00 | ₹29,080,000.00 | ₹29,080,100.00 |
| 0.80 | 0.9999 | 0.5737 | 0.7291 | 0.0002 | 0.4263 | 19583.0 | 6187.0 | 1.0 | 14549.0 | ₹50.00 | ₹29,098,000.00 | ₹29,098,050.00 |
| 0.85 | 1.0000 | 0.5735 | 0.7289 | 0.0000 | 0.4265 | 19574.0 | 6188.0 | 0.0 | 14558.0 | ₹0.00 | ₹29,116,000.00 | ₹29,116,000.00 |
| 0.90 | 1.0000 | 0.5725 | 0.7282 | 0.0000 | 0.4275 | 19541.0 | 6188.0 | 0.0 | 14591.0 | ₹0.00 | ₹29,182,000.00 | ₹29,182,000.00 |

### Optimal Threshold Decision
Based on the economic cost model, the threshold that minimizes Total Expected Cost is **0.10**.
At this threshold, the model balances the severe cost of false negatives against the frequent but lower cost of false positives.

## 5. Policy Calibration & Risk Bands
The ML model outputs a raw probability. In Sentinel, this probability is mapped directly to policy outcomes in the Risk Fusion Engine.

Current Risk Bands:
- **LOW RISK (0.0 to < 0.1):** -> `ALLOW`
  - *Behavior*: Typical, low anomaly scores. Cleared for capability token issuance.
- **MEDIUM RISK (>= 0.1 to < 0.85):** -> `ESCALATE`
  - *Behavior*: Deviations detected. Escalated for manual review or 2FA. No token issued.
- **HIGH RISK (>= 0.85):** -> `CONTAIN`
  - *Behavior*: Extreme anomaly. Account contained to prevent immediate loss. No token issued.

## 6. Model Failure Safety
In the event of model failure, Sentinel uses deterministic fallbacks:
- **Model Unavailable / Timeout**: `Decision.ESCALATE`
- **NaN / Out-of-bounds Probability**: Pydantic bounds prevent injection, fallback to `ESCALATE`
- **Semantic Disagreement**: High variance between models yields `ESCALATE`
