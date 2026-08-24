import os
import json
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score, brier_score_loss, confusion_matrix
import xgboost as xgb

from ml.train import prepare_matrices, split_data, train_model

def run_phase17_ablation():
    print("Loading frozen dataset...", flush=True)
    df = pd.read_parquet("evaluation/dataset/sentinel_v1.parquet")
    
    train_df, val_df, test_df = split_data(df)
    print(f"Train rows: {len(train_df)}, Val rows: {len(val_df)}, Test rows: {len(test_df)}", flush=True)
    
    modes = {
        "rules_only": "Rules Only",
        "velocity_baseline": "Velocity Baseline",
        "transaction_only": "Transaction Only",
        "behavioral_only": "Behavioral Only",
        "fusion": "Transaction + Behavioral",
        "full_sentinel": "Full Sentinel"
    }
    
    results = {}
    
    for mode, mode_name in modes.items():
        print(f"\nEvaluating {mode_name}...", flush=True)
        
        if mode in ["rules_only", "velocity_baseline"]:
            # Naive models, no training
            test_preds = np.zeros(len(test_df))
            if mode == "rules_only":
                # Rules: Amount > 90th percentile OR (action=payout AND amount > 50th)
                amt_90 = train_df["amount"].quantile(0.90)
                amt_50 = train_df["amount"].quantile(0.50)
                test_preds = (
                    (test_df["amount"] > amt_90) | 
                    ((test_df["action_type"] == "payout") & (test_df["amount"] > amt_50))
                ).astype(int).values
            elif mode == "velocity_baseline":
                # Velocity > X or Amount > Y
                vel_90 = train_df["rolling_1h_count"].quantile(0.90)
                amt_90 = train_df["amount"].quantile(0.90)
                test_preds = (
                    (test_df["rolling_1h_count"] > vel_90) | 
                    (test_df["amount"] > amt_90) |
                    (test_df["recipient_novelty"] == 1)
                ).astype(int).values
                
            y_test = test_df["loss_label"].values
            results[mode] = calculate_metrics(y_test, test_preds, test_preds, test_df)
        else:
            # XGBoost models
            # mapping mode to feature set:
            # transaction_only -> transaction_only
            # behavioral_only -> behavioral_only
            # fusion -> full_sentinel (no policy)
            # full_sentinel -> full_sentinel (with policy)
            feature_mode = "full_sentinel" if mode in ["fusion", "full_sentinel"] else mode
            
            dtrain, dval, dtest, _ = prepare_matrices(train_df, val_df, test_df, feature_mode)
            
            num_neg = (train_df["loss_label"] == 0).sum()
            num_pos = (train_df["loss_label"] == 1).sum()
            spw = num_neg / max(1, num_pos)
            
            # Use fixed params for stable comparison, or we could tune
            hyperparams = {
                "max_depth": 4, "learning_rate": 0.05, 
                "objective": "binary:logistic", "eval_metric": "aucpr", 
                "scale_pos_weight": spw, "tree_method": "hist", "seed": 42
            }
            
            model, _ = train_model(dtrain, dval, spw, hyperparams)
            
            y_val = dval.get_label()
            val_preds = model.predict(dval)
            threshold = select_threshold(y_val, val_preds)
            
            y_test = dtest.get_label()
            test_preds_prob = model.predict(dtest)
            test_preds = (test_preds_prob > threshold).astype(int)
            
            # For Full Sentinel, we apply policy (escalate unseen agents)
            if mode == "full_sentinel":
                # Policy: If has_sufficient_history == 0, ESCALATE (1)
                mask = test_df["has_sufficient_history"] == 0
                test_preds[mask] = 1
                
            results[mode] = calculate_metrics(y_test, test_preds, test_preds_prob, test_df, threshold)

    write_ablation_report(results, modes)

def select_threshold(y_val, val_preds):
    precision, recall, thresholds = precision_recall_curve(y_val, val_preds)
    # Find threshold where recall >= 0.90
    idx = np.where(recall >= 0.90)[0]
    if len(idx) > 0:
        # Of those, pick the one with max precision
        best_idx = idx[np.argmax(precision[idx])]
        # If best_idx is the last element in precision/recall, thresholds has one less element
        thresh_idx = min(best_idx, len(thresholds) - 1)
        return thresholds[thresh_idx]
    return 0.5

def calculate_metrics(y_true, y_pred, y_prob, test_df, threshold=0.5):
    precision_val, recall_val, thresholds = precision_recall_curve(y_true, y_prob)
    aucpr = average_precision_score(y_true, y_prob)
    auroc = roc_auc_score(y_true, y_prob) if len(np.unique(y_true)) > 1 else 0
    brier = brier_score_loss(y_true, y_prob)
    
    # Seen vs unseen
    is_seen = test_df["has_sufficient_history"] == 1
    
    metrics = {
        "overall": calc_subset_metrics(y_true, y_pred, y_prob, np.ones(len(y_true), dtype=bool)),
        "seen": calc_subset_metrics(y_true, y_pred, y_prob, is_seen),
        "unseen": calc_subset_metrics(y_true, y_pred, y_prob, ~is_seen),
        "aucpr": aucpr,
        "auroc": auroc,
        "brier": brier,
        "threshold": threshold
    }
    return metrics

def calc_subset_metrics(y_true, y_pred, y_prob, mask):
    if not np.any(mask):
        return {"precision": 0, "recall": 0, "f1": 0, "far": 0, "aucpr": 0}
        
    y_t = y_true[mask]
    y_p = y_pred[mask]
    y_prob_sub = y_prob[mask]
    
    tp = np.sum((y_t == 1) & (y_p == 1))
    fp = np.sum((y_t == 0) & (y_p == 1))
    fn = np.sum((y_t == 1) & (y_p == 0))
    tn = np.sum((y_t == 0) & (y_p == 0))
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    far = fp / (fp + tn) if (fp + tn) > 0 else 0
    aucpr = average_precision_score(y_t, y_prob_sub) if len(np.unique(y_t)) > 1 else 0
    
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "far": far,
        "aucpr": aucpr
    }

def write_ablation_report(results, modes):
    with open("evaluation/experiments/ablation.md", "w") as f:
        f.write("# Phase 17 Ablation Study\n\n")
        f.write("## Overall Performance\n")
        f.write("| System | Precision | Recall | F1 | PR-AUC | False Escalation |\n")
        f.write("|--------|-----------|--------|----|--------|------------------|\n")
        
        for mode, name in modes.items():
            m = results[mode]["overall"]
            pr_auc = results[mode]["aucpr"]
            name_bold = f"**{name}**" if mode == "full_sentinel" else name
            f.write(f"| {name_bold} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | {pr_auc:.3f} | {m['far']:.3%} |\n")
            
        f.write("\n## Seen vs Unseen Agents (PR-AUC)\n")
        f.write("| System | Seen Agents | Unseen Agents |\n")
        f.write("|--------|-------------|---------------|\n")
        
        for mode, name in modes.items():
            seen = results[mode]["seen"]["aucpr"]
            unseen = results[mode]["unseen"]["aucpr"]
            f.write(f"| {name} | {seen:.3f} | {unseen:.3f} |\n")

if __name__ == "__main__":
    run_phase17_ablation()
