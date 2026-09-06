"""
Simplified training script that bypasses MLflow for quick retraining.
"""

import logging
import joblib
from pathlib import Path
from ml.data_generator import generate_dataset
from ml.train import split_data, prepare_matrices, tune_and_train
from ml.evaluate import compute_metrics, find_optimal_threshold, generate_calibration_curve, generate_manifest
from sklearn.linear_model import LogisticRegression
import numpy as np


def calibrate_model_platt(y_true, y_scores):
    """Apply Platt scaling to raw model scores."""
    scores_2d = np.array(y_scores).reshape(-1, 1)
    calibrator = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000)
    calibrator.fit(scores_2d, y_true)
    return calibrator


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def train_simple(ablation_mode="full_sentinel", seed=42):
    """Train model without MLflow."""
    logger.info(f"Generating dataset (seed={seed})...")
    df = generate_dataset(seed=seed)

    logger.info(f"Training {ablation_mode}...")
    train_df, val_df, test_df = split_data(df)

    # Sort all splits
    train_df = train_df.sort_values(by=["agent_id", "timestamp"]).reset_index(drop=True)
    val_df = val_df.sort_values(by=["agent_id", "timestamp"]).reset_index(drop=True)
    test_df = test_df.sort_values(by=["agent_id", "timestamp"]).reset_index(drop=True)

    num_neg = (train_df["loss_label"] == 0).sum()
    num_pos = (train_df["loss_label"] == 1).sum()
    raw_spw = num_neg / max(1, num_pos)
    spw = min(raw_spw, 15.0)

    logger.info(f"Class balance: neg={num_neg}, pos={num_pos}, spw={spw:.2f}")

    dtrain, dval, dtest, feature_cols = prepare_matrices(train_df, val_df, test_df, ablation_mode)

    logger.info("Tuning hyperparameters...")
    model, best_params = tune_and_train(dtrain, dval, spw)

    logger.info("Evaluating on test set...")
    test_df = test_df.copy()
    test_df["model_risk"] = model.predict(dtest)

    # Check for inversion
    from sklearn.metrics import roc_auc_score

    val_preds = model.predict(dval)
    y_val = dval.get_label()
    invert_scores = False
    if len(set(y_val)) > 1:
        val_roc = roc_auc_score(y_val, val_preds)
        logger.info(f"Validation ROC-AUC: {val_roc:.4f}")
        if val_roc < 0.5:
            invert_scores = True
            test_df["model_risk"] = 1.0 - test_df["model_risk"]
            logger.warning(f"ROC-AUC inverted ({val_roc:.4f}) — flipping scores")

    y_true = test_df["loss_label"].values
    y_pred_prob = test_df["model_risk"].values

    # Auto-check test set
    if len(set(y_true)) > 1:
        test_roc = roc_auc_score(y_true, y_pred_prob)
        if test_roc < 0.5 and not invert_scores:
            invert_scores = True
            y_pred_prob = 1.0 - y_pred_prob
            test_df["model_risk"] = y_pred_prob
            logger.warning(f"Test ROC-AUC inverted ({test_roc:.4f}) — flipping scores")

    threshold = find_optimal_threshold(y_true, y_pred_prob)
    metrics = compute_metrics(y_true, y_pred_prob, threshold)

    logger.info("=" * 70)
    logger.info(f"RESULTS FOR {ablation_mode}")
    logger.info(f"  ROC-AUC: {metrics['roc_auc']:.4f}")
    logger.info(f"  PR-AUC: {metrics['aucpr']:.4f}")
    logger.info(f"  Precision: {metrics['precision']:.3f}")
    logger.info(f"  Recall: {metrics['recall']:.3f}")
    logger.info(f"  False Escalation Rate: {metrics['false_escalation_rate']:.3f}")
    logger.info(f"  Unsafe Auto-Approval: {metrics['unsafe_auto_approval_rate']:.3f}")
    logger.info(f"  Threshold: {threshold:.4f}")
    logger.info(f"  Inverted: {invert_scores}")
    logger.info("=" * 70)

    # Save full_sentinel model
    if ablation_mode == "full_sentinel":
        logger.info("Saving full_sentinel model artifacts...")
        model.save_model("ml/sentinel_model.json")

        # Save calibrator
        calibrator = calibrate_model_platt(y_true, y_pred_prob)
        joblib.dump(calibrator, "ml/calibrator.pkl")

        # Save manifest
        calib = generate_calibration_curve(y_true, y_pred_prob)
        manifest = generate_manifest(
            model_version="v1.0.0-xgb",
            hyperparams=best_params,
            threshold=threshold,
            metrics=metrics,
            calibration=calib,
            seed=seed,
        )
        manifest["invert_scores"] = invert_scores

        import json

        with open("ml/model_manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)

        logger.info("Saved: ml/sentinel_model.json, ml/calibrator.pkl, ml/model_manifest.json")

    return model, best_params, metrics, invert_scores


if __name__ == "__main__":
    train_simple("full_sentinel", seed=42)
