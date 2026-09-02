import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime

# Adjust path to find modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.config import settings
# Override MLflow tracking URI to avoid connection timeouts to missing local server
settings.MLFLOW_TRACKING_URI = f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mlflow.db'))}"

from ml.data_generator import generate_dataset
from ml.train import run_training_pipeline
from sklearn.metrics import average_precision_score, confusion_matrix, precision_score, recall_score, f1_score


# Configuration for Cost Model
# Synthetic Economic Assumptions
FP_COST = 50.0    # INR - Cost of manual review / user friction / blocked legitimate transaction
FN_COST = 2000.0  # INR - Cost of a fraud loss / unauthorized payout

def run_evaluation():
    print("============================================================")
    print("PHASE 1 - GENERATING DATASET")
    print("============================================================")
    # Use 50 train/val agents and 10 test agents to guarantee we sample anomalous scenarios
    df = generate_dataset(seed=42, days=30, num_agents_train_val=50, num_agents_test_only=10)
    print(f"Generated {len(df)} transactions.")
    
    # Analyze Dataset
    pos_count = (df["loss_label"] == 1).sum()
    neg_count = (df["loss_label"] == 0).sum()
    print(f"Dataset: {pos_count} Positive (Loss), {neg_count} Negative (Legitimate).")

    print("\n============================================================")
    print("PHASE 2 - TRAINING & BASELINE METRICS")
    print("============================================================")
    # Train the model (uses days 1-20 for train, 21-25 for val, 26-30 for test)
    # tune=False speeds up the evaluation for the demo, since we just need the curve
    model, best_params, test_df = run_training_pipeline(df, tune=False)
    
    y_true = test_df["loss_label"].values
    y_prob = test_df["model_risk"].values
    
    test_pos = (y_true == 1).sum()
    test_neg = (y_true == 0).sum()
    print(f"Held-out Test Set: {len(test_df)} transactions ({test_pos} Pos, {test_neg} Neg).")
    
    pr_auc = average_precision_score(y_true, y_prob)
    print(f"Baseline PR-AUC on Test Set: {pr_auc:.4f}")

    print("\n============================================================")
    print("PHASE 4 - THRESHOLD SWEEP & ECONOMIC COST")
    print("============================================================")
    
    thresholds = np.arange(0.10, 0.95, 0.05)
    
    results = []
    
    for t in thresholds:
        y_pred = (y_prob >= t).astype(int)
        
        # Avoid division by zero
        if np.sum(y_pred) == 0:
            precision = 1.0
            recall = 0.0
            f1 = 0.0
        else:
            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)
            
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        cost_fp = fp * FP_COST
        cost_fn = fn * FN_COST
        total_cost = cost_fp + cost_fn
        
        results.append({
            "Threshold": round(t, 2),
            "Precision": round(precision, 4),
            "Recall": round(recall, 4),
            "F1": round(f1, 4),
            "FPR": round(fpr, 4),
            "FNR": round(fnr, 4),
            "TP": tp,
            "TN": tn,
            "FP": fp,
            "FN": fn,
            "Est FP Cost": round(cost_fp, 2),
            "Est FN Cost": round(cost_fn, 2),
            "Total Cost": round(total_cost, 2)
        })
        
    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))
    
    print("\n============================================================")
    print("PHASE 5 - OPTIMAL THRESHOLD")
    print("============================================================")
    
    best_row = results_df.loc[results_df["Total Cost"].idxmin()]
    opt_threshold = best_row["Threshold"]
    
    print(f"Optimal Threshold (Minimizing Cost): {opt_threshold}")
    print(f"Expected Minimum Cost: {best_row['Total Cost']} INR")
    print(f"At this threshold -> TP: {best_row['TP']}, TN: {best_row['TN']}, FP: {best_row['FP']}, FN: {best_row['FN']}")
    
    print("\n============================================================")
    print("PHASE 11 - GENERATING ARTIFACT")
    print("============================================================")
    
    report_content = f"""# Sentinel ML Evaluation & Economic Cost Analysis

## 1. Dataset & Pipeline Characteristics
- **Dataset Generation**: Synthetic behavioral scenarios spanning 30 days (Agents A-H).
- **Positive Class**: Anomalous behavior leading to potential loss (`loss_label = 1`).
- **Negative Class**: Normal baseline activity (`loss_label = 0`).
- **Features Used**: Extracted temporal rolling counts, time since last action, amount aggregations.
- **Data Splitting**: Strict Temporal. Train (Days 1-20), Validation (Days 21-25), Test (Days 26-30).
- **Leakage / Imbalance**: No temporal leakage. Positive class imbalance is handled via XGBoost `scale_pos_weight`.

## 2. Baseline Metrics (Held-out Test Set)
- **Test Set Size**: {len(test_df)} records ({test_pos} Positive, {test_neg} Negative).
- **PR-AUC**: {pr_auc:.4f}

## 3. Economic Cost Model (Synthetic Assumptions)
> **IMPORTANT:** The following costs are synthetic economic assumptions used for threshold optimization, not actual observed Razorpay financial loss data.

- **False Positive (FP)**: Legitimate behavior incorrectly classified as risky.
  - *Cost Assumption*: ₹{FP_COST:,.2f} per FP (accounts for user friction, manual review time, blocked legitimate activity).
- **False Negative (FN)**: Risky behavior incorrectly classified as legitimate.
  - *Cost Assumption*: ₹{FN_COST:,.2f} per FN (accounts for potential unauthorized payout / financial loss).

## 4. Threshold Sweep & Optimal Threshold
The table below sweeps the classification threshold to find the point that minimizes **Total Expected Cost**.

| Threshold | Precision | Recall | F1 | FPR | FNR | TP | TN | FP | FN | Est FP Cost | Est FN Cost | Total Cost |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for _, row in results_df.iterrows():
        report_content += f"| {row['Threshold']:.2f} | {row['Precision']:.4f} | {row['Recall']:.4f} | {row['F1']:.4f} | {row['FPR']:.4f} | {row['FNR']:.4f} | {row['TP']} | {row['TN']} | {row['FP']} | {row['FN']} | ₹{row['Est FP Cost']:,.2f} | ₹{row['Est FN Cost']:,.2f} | ₹{row['Total Cost']:,.2f} |\n"
        
    report_content += f"""
### Optimal Threshold Decision
Based on the economic cost model, the threshold that minimizes Total Expected Cost is **{opt_threshold:.2f}**.
At this threshold, the model balances the severe cost of false negatives against the frequent but lower cost of false positives.

## 5. Policy Calibration & Risk Bands
The ML model outputs a raw probability. In Sentinel, this probability is mapped directly to policy outcomes in the Risk Fusion Engine.

Current Risk Bands:
- **LOW RISK (0.0 to < {opt_threshold}):** -> `ALLOW`
  - *Behavior*: Typical, low anomaly scores. Cleared for capability token issuance.
- **MEDIUM RISK (>= {opt_threshold} to < 0.85):** -> `ESCALATE`
  - *Behavior*: Deviations detected. Escalated for manual review or 2FA. No token issued.
- **HIGH RISK (>= 0.85):** -> `CONTAIN`
  - *Behavior*: Extreme anomaly. Account contained to prevent immediate loss. No token issued.

## 6. Model Failure Safety
In the event of model failure, Sentinel uses deterministic fallbacks:
- **Model Unavailable / Timeout**: `Decision.ESCALATE`
- **NaN / Out-of-bounds Probability**: Pydantic bounds prevent injection, fallback to `ESCALATE`
- **Semantic Disagreement**: High variance between models yields `ESCALATE`
"""

    report_path = os.path.join(os.path.dirname(__file__), "..", "ml_evaluation_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"Artifact successfully saved to {report_path}")

if __name__ == "__main__":
    run_evaluation()
