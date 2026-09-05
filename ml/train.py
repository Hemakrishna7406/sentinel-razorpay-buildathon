"""
Sentinel — XGBoost Training Module

Trains the risk model using transaction and behavioral features.
Includes validation-based hyperparameter tuning.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import xgboost as xgb
import mlflow
import mlflow.xgboost

# Disable autologging to prevent duplicate metric insert errors in SQLite backend
mlflow.xgboost.autolog(disable=True)

from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from ml.features import build_feature_dataframe, get_feature_names

logger = logging.getLogger(__name__)


def split_data(
    df: pd.DataFrame,
    train_days: Tuple[int, int] = (1, 20),
    val_days: Tuple[int, int] = (21, 25),
    test_days: Tuple[int, int] = (26, 30)
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split data temporally as per dataset.md §5."""
    train_df = df[(df["day"] >= train_days[0]) & (df["day"] <= train_days[1])].copy()
    val_df = df[(df["day"] >= val_days[0]) & (df["day"] <= val_days[1])].copy()
    test_df = df[(df["day"] >= test_days[0]) & (df["day"] <= test_days[1])].copy()

    return train_df, val_df, test_df


def prepare_matrices(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    ablation_mode: str = "full_sentinel"
) -> Tuple[xgb.DMatrix, xgb.DMatrix, xgb.DMatrix, List[str]]:
    """Convert pandas DataFrames to XGBoost DMatrices.

    CRITICAL: Input DataFrames MUST be pre-sorted by (agent_id, timestamp)
    to match build_feature_dataframe's internal sort order. Misaligned sort
    orders between features and labels was the root cause of the inverted model.
    """

    # 1. Extract features (build_feature_dataframe sorts by agent_id, timestamp internally)
    train_features = build_feature_dataframe(train_df)
    val_features = build_feature_dataframe(val_df)
    test_features = build_feature_dataframe(test_df)

    # 2. Select columns based on ablation mode
    feature_cols = get_feature_names(ablation_mode)
    if not feature_cols:
        raise ValueError("No features selected (rules_only mode?). XGBoost needs features.")

    # 3. Create labels — DataFrames are pre-sorted to match feature extraction order
    y_train = train_df["loss_label"].values
    y_val = val_df["loss_label"].values
    y_test = test_df["loss_label"].values

    # 4. Create DMatrices
    dtrain = xgb.DMatrix(train_features[feature_cols], label=y_train)
    dval = xgb.DMatrix(val_features[feature_cols], label=y_val)
    dtest = xgb.DMatrix(test_features[feature_cols], label=y_test)

    return dtrain, dval, dtest, feature_cols


def train_model(
    dtrain: xgb.DMatrix,
    dval: xgb.DMatrix,
    scale_pos_weight: float = 1.0,
    hyperparameters: dict = None,
) -> Tuple[xgb.Booster, dict]:
    """Train XGBoost model with early stopping on validation PR-AUC."""

    if hyperparameters is None:
        hyperparameters = {
            "max_depth": 4,
            "learning_rate": 0.05,
            "objective": "binary:logistic",
            "eval_metric": "aucpr",
            "scale_pos_weight": scale_pos_weight,
            "tree_method": "hist",
            "seed": 42,
            "min_child_weight": 3,
            "gamma": 0.1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
        }

    evals = [(dtrain, "train"), (dval, "val")]

    model = xgb.train(
        params=hyperparameters,
        dtrain=dtrain,
        num_boost_round=300,
        evals=evals,
        early_stopping_rounds=30,
        verbose_eval=False
    )

    return model, hyperparameters


def tune_and_train(
    dtrain: xgb.DMatrix,
    dval: xgb.DMatrix,
    scale_pos_weight: float
) -> Tuple[xgb.Booster, dict]:
    """Validation-based hyperparameter tuning."""
    param_grid = [
        {"max_depth": 4, "learning_rate": 0.05},
        {"max_depth": 3, "learning_rate": 0.1},
        {"max_depth": 5, "learning_rate": 0.01},
        {"max_depth": 6, "learning_rate": 0.03},
        {"max_depth": 4, "learning_rate": 0.1, "min_child_weight": 5},
    ]

    best_model = None
    best_score = -1.0
    best_params = None

    for params in param_grid:
        full_params = {
            "objective": "binary:logistic",
            "eval_metric": "aucpr",
            "scale_pos_weight": scale_pos_weight,
            "tree_method": "hist",
            "seed": 42,
            "min_child_weight": 3,
            "gamma": 0.1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            **params
        }

        evals = [(dval, "val")]
        model = xgb.train(
            params=full_params,
            dtrain=dtrain,
            num_boost_round=300,
            evals=evals,
            early_stopping_rounds=30,
            verbose_eval=False
        )

        val_preds = model.predict(dval)
        val_aucpr = average_precision_score(dval.get_label(), val_preds)

        if val_aucpr > best_score:
            best_score = val_aucpr
            best_model = model
            best_params = full_params

    logger.info(f"Selected hyperparams based on val PR-AUC ({best_score:.4f}): max_depth={best_params['max_depth']}, lr={best_params['learning_rate']}")
    return best_model, best_params


def _init_mlflow():
    """Initialize MLflow with local file-based tracking as fallback."""
    from core.config import settings
    uri = settings.MLFLOW_TRACKING_URI
    try:
        mlflow.set_tracking_uri(uri)
        mlflow.set_experiment("Sentinel_Ablation_Study")
    except Exception:
        local_path = Path(__file__).parent.parent / "mlruns"
        local_uri = f"file:///{str(local_path).replace(chr(92), '/')}"
        logger.warning(f"MLflow server at {uri} unavailable, using local tracking: {local_uri}")
        mlflow.set_tracking_uri(local_uri)
        mlflow.set_experiment("Sentinel_Ablation_Study")


def run_training_pipeline(
    df: pd.DataFrame,
    ablation_mode: str = "full_sentinel",
    tune: bool = True
) -> Tuple[xgb.Booster, dict, pd.DataFrame, bool]:
    """End-to-end training pipeline for a given ablation mode."""

    _init_mlflow()

    train_df, val_df, test_df = split_data(df)

    # Sort all splits by (agent_id, timestamp) to match build_feature_dataframe's
    # internal sort order. This ensures labels align with extracted features.
    train_df = train_df.sort_values(by=["agent_id", "timestamp"]).reset_index(drop=True)
    val_df = val_df.sort_values(by=["agent_id", "timestamp"]).reset_index(drop=True)
    test_df = test_df.sort_values(by=["agent_id", "timestamp"]).reset_index(drop=True)

    if len(train_df) == 0:
        raise ValueError("No training data found in days 1-20.")

    num_neg = (train_df["loss_label"] == 0).sum()
    num_pos = (train_df["loss_label"] == 1).sum()
    raw_spw = num_neg / max(1, num_pos)
    spw = min(raw_spw, 15.0)

    logger.info(f"Class balance: neg={num_neg}, pos={num_pos}, spw={spw:.2f} (raw={raw_spw:.2f})")

    dtrain, dval, dtest, feature_cols = prepare_matrices(train_df, val_df, test_df, ablation_mode)

    with mlflow.start_run(run_name=f"mode_{ablation_mode}"):
        mlflow.log_param("ablation_mode", ablation_mode)

        if tune:
            model, best_params = tune_and_train(dtrain, dval, spw)
        else:
            best_params = {
                "max_depth": 4, "learning_rate": 0.05,
                "objective": "binary:logistic", "eval_metric": "aucpr",
                "scale_pos_weight": spw, "tree_method": "hist", "seed": 42,
                "min_child_weight": 3, "gamma": 0.1,
                "subsample": 0.8, "colsample_bytree": 0.8,
                "reg_alpha": 0.1, "reg_lambda": 1.0,
            }
            model, best_params = train_model(dtrain, dval, spw, best_params)

        test_df = test_df.copy()
        test_df["model_risk"] = model.predict(dtest)

        # Check validation ROC-AUC — if inverted, flag it and flip scores
        invert_scores = False
        val_preds = model.predict(dval)
        y_val = dval.get_label()
        if len(set(y_val)) > 1:
            val_roc = roc_auc_score(y_val, val_preds)
            logger.info(f"Validation ROC-AUC: {val_roc:.4f}")
            if val_roc < 0.5:
                invert_scores = True
                test_df["model_risk"] = 1.0 - test_df["model_risk"]
                logger.warning(f"ROC-AUC inverted ({val_roc:.4f} < 0.5) — flipping scores")

        # Register the production model if full_sentinel
        if ablation_mode == "full_sentinel":
            try:
                mlflow.xgboost.log_model(
                    model,
                    artifact_path="model",
                    registered_model_name="sentinel_xgboost"
                )
                logger.info("Registered full_sentinel model to MLflow Model Registry as 'sentinel_xgboost'")
            except Exception as e:
                logger.warning(f"MLflow model registration failed (non-blocking): {e}")
                model.save_model(str(Path(__file__).parent / "sentinel_model.json"))

    return model, best_params, test_df, invert_scores
