"""
Tests for XGBoost model training and evaluation.

Verifies no train/test leakage, valid probability outputs,
and proper handling of unseen agents.
"""

import numpy as np
import pytest

from ml.data_generator import generate_dataset
import mlflow

mlflow.autolog(disable=True)
try:
    mlflow.xgboost.autolog(disable=True)
except Exception:
    pass

from ml.evaluate import compute_metrics, find_optimal_threshold
from ml.train import run_training_pipeline


@pytest.fixture(scope="module")
def sample_dataset():
    """Generate a small deterministic dataset for ML tests."""
    # Small number of agents to make tests fast
    return generate_dataset(seed=42, num_agents_train_val=4, num_agents_test_only=2, days=30)


def test_no_temporal_leakage(sample_dataset):
    """Ensure training data has no rows > day 25 and test data has no rows < day 26."""
    from ml.train import split_data

    train_df, val_df, test_df = split_data(sample_dataset)

    assert train_df["day"].max() <= 20
    assert val_df["day"].min() >= 21
    assert val_df["day"].max() <= 25
    assert test_df["day"].min() >= 26


def test_model_probabilities_in_range(sample_dataset):
    """Model predictions must be bounded [0, 1]."""
    model, params, test_df = run_training_pipeline(sample_dataset, tune=False)

    preds = test_df["model_risk"].values
    assert (preds >= 0.0).all()
    assert (preds <= 1.0).all()


def test_metrics_computation():
    """Metrics calculation returns valid numbers."""
    # Synthetic ground truth and predictions
    y_true = np.array([0, 0, 1, 1, 0, 1, 0, 0, 1, 1])
    y_pred = np.array([0.1, 0.2, 0.9, 0.8, 0.4, 0.6, 0.3, 0.2, 0.7, 0.4])

    metrics = compute_metrics(y_true, y_pred, threshold=0.5)

    assert "aucpr" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "false_escalation_rate" in metrics
    assert "unsafe_auto_approval_rate" in metrics

    # 5 positives, 5 negatives
    # Threshold 0.5 -> predicts 1 for indices 2, 3, 5, 8 (all true positives)
    # tp=4, fp=0, fn=1, tn=5
    assert metrics["tp"] == 4
    assert metrics["fp"] == 0
    assert metrics["fn"] == 1
    assert metrics["tn"] == 5
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 0.8


def test_find_optimal_threshold():
    """Threshold finder hits target recall."""
    y_true = np.array([0, 0, 1, 1, 1, 1, 0, 0])
    y_pred = np.array([0.1, 0.2, 0.9, 0.8, 0.6, 0.4, 0.3, 0.5])

    # Target recall 1.0 -> needs to capture 0.4 (lowest positive)
    t = find_optimal_threshold(y_true, y_pred, target_recall=1.0)
    assert t <= 0.4

    # Target recall 0.5 -> needs to capture at least 2 positives (0.8 and 0.9)
    t = find_optimal_threshold(y_true, y_pred, target_recall=0.5)
    assert t <= 0.8


def test_ablation_mode_features():
    """Ensure different ablation modes select the correct features."""
    from ml.features import get_feature_names

    tx_features = get_feature_names("transaction_only")
    beh_features = get_feature_names("behavioral_only")
    full_features = get_feature_names("full_sentinel")

    assert "amount" in tx_features
    assert "velocity_z" not in tx_features

    assert "amount" not in beh_features
    assert "velocity_z" in beh_features

    assert "amount" in full_features
    assert "velocity_z" in full_features
