"""
Sentinel — Evaluation Module

Evaluates XGBoost models, computes calibration, and selects thresholds.
"""

import json
import platform
import psutil
from datetime import datetime
from typing import Dict, Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    precision_recall_curve,
    roc_auc_score,
    confusion_matrix,
)


def compute_metrics(y_true: np.ndarray, y_pred_prob: np.ndarray, threshold: float = 0.5) -> Dict[str, float]:
    """Compute core ML metrics."""
    y_pred = (y_pred_prob >= threshold).astype(int)

    aucpr = average_precision_score(y_true, y_pred_prob) if len(np.unique(y_true)) > 1 else np.nan
    roc_auc = roc_auc_score(y_true, y_pred_prob) if len(np.unique(y_true)) > 1 else np.nan
    brier = brier_score_loss(y_true, y_pred_prob)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    # Custom business metrics
    # False escalation rate = escalations on legitimate / total legitimate
    fer = fp / (tn + fp) if (tn + fp) > 0 else 0.0
    # Unsafe auto-approval = allows on unauthorized / total unauthorized
    unsafe_approval = fn / (tp + fn) if (tp + fn) > 0 else 0.0

    return {
        "aucpr": aucpr,
        "roc_auc": roc_auc,
        "brier_score": brier,
        "precision": precision,
        "recall": recall,
        "false_escalation_rate": fer,
        "unsafe_auto_approval_rate": unsafe_approval,
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
    }


def find_optimal_threshold(y_true: np.ndarray, y_pred_prob: np.ndarray, target_recall: float = 0.90) -> float:
    """Find the threshold that achieves target recall while maximizing precision."""
    if len(np.unique(y_true)) < 2:
        return 0.5

    precisions, recalls, thresholds = precision_recall_curve(y_true, y_pred_prob)

    # Find thresholds where recall >= target_recall
    valid_idx = np.where(recalls[:-1] >= target_recall)[0]
    if len(valid_idx) == 0:
        # Fallback to threshold that maximizes F1 if target recall unattainable
        f1_scores = 2 * (precisions[:-1] * recalls[:-1]) / (precisions[:-1] + recalls[:-1] + 1e-10)
        best_idx = np.argmax(f1_scores)
        return float(thresholds[best_idx])

    # Among valid idx, pick the one with max precision
    best_idx = valid_idx[np.argmax(precisions[valid_idx])]
    return float(thresholds[best_idx])


def generate_calibration_curve(y_true: np.ndarray, y_pred_prob: np.ndarray, n_bins: int = 10) -> Dict[str, list]:
    """Generate data for calibration curve."""
    bins = np.linspace(0.0, 1.0 + 1e-8, n_bins + 1)
    binids = np.digitize(y_pred_prob, bins) - 1

    bin_sums = np.bincount(binids, weights=y_pred_prob, minlength=len(bins))
    bin_true = np.bincount(binids, weights=y_true, minlength=len(bins))
    bin_total = np.bincount(binids, minlength=len(bins))

    nonzero = bin_total != 0
    prob_true = bin_true[nonzero] / bin_total[nonzero]
    prob_pred = bin_sums[nonzero] / bin_total[nonzero]

    return {"prob_true": prob_true.tolist(), "prob_pred": prob_pred.tolist(), "counts": bin_total[nonzero].tolist()}


def get_environment_info() -> Dict[str, str]:
    """Capture environment context for reproducibility."""
    ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
    return {
        "cpu": platform.processor(),
        "ram_gb": str(ram_gb),
        "python_version": platform.python_version(),
        "os": platform.system(),
    }


def generate_manifest(
    model_version: str,
    hyperparams: dict,
    threshold: float,
    metrics: dict,
    calibration: dict,
    dataset_version: str = "1.0",
    seed: int = 42,
) -> Dict[str, Any]:
    """Generate model_manifest.json as required by Phase 3, Recommendation #9."""

    manifest = {
        "dataset_version": dataset_version,
        "generator_seed": seed,
        "feature_version": "1.0",
        "model_version": model_version,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "hyperparameters": hyperparams,
        "thresholds": {
            "suspicious": threshold,
            "high_risk": min(1.0, threshold + 0.2),  # Simple heuristic for HIGH-RISK boundary
        },
        "train_range": {"days": [1, 20], "agents": ["A", "B", "C", "D", "E", "F"]},
        "validation_range": {"days": [21, 25], "agents": ["A", "B", "C", "D", "E", "F"]},
        "test_range": {"days": [26, 30], "agents": ["A", "B", "C", "D", "E", "F", "G", "H"]},
        "metrics": metrics,
        "calibration": calibration,
        "environment": get_environment_info(),
    }

    return manifest
