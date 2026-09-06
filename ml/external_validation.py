"""
Sentinel — External Validation Framework

Validates that behavioral features generalize beyond synthetic environment.

Strategy:
- Synthetic data → Controlled ground truth with precise labels
- Real-world datasets → External validation of generalization
- Domain shift experiments → Test robustness across distributions

This addresses the key concern: "How do you know the model learned real financial-agent
behavior rather than patterns created by your synthetic-data generator?"
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from sklearn.metrics import roc_auc_score, average_precision_score

logger = logging.getLogger(__name__)


class ExternalValidator:
    """
    Framework for validating Sentinel's behavioral model on real-world datasets.

    Purpose: Demonstrate that behavioral features retain discriminative power
    outside the synthetic environment, even though real autonomous-agent transaction
    data is not publicly available.
    """

    def __init__(self):
        self.datasets_available = {
            "ieee-cis": "IEEE-CIS Fraud Detection (Kaggle)",
            "paysim": "PaySim Synthetic Financial Transactions",
            "credit-card": "Credit Card Fraud Detection",
        }

    def load_ieee_cis_sample(self, sample_size: int = 10000) -> Optional[pd.DataFrame]:
        """
        Load IEEE-CIS Fraud Detection dataset for external validation.

        Note: This is a PLACEHOLDER for buildathon purposes. In production:
        1. Download from Kaggle API: kaggle competitions download -c ieee-fraud-detection
        2. Load train_transaction.csv + train_identity.csv
        3. Map features to Sentinel's behavioral feature space

        For buildathon demo, we document the validation STRATEGY without requiring
        the full 4GB dataset.
        """
        logger.warning(
            "IEEE-CIS dataset not loaded (requires Kaggle API credentials). "
            "This is a validation framework stub. For production: "
            "kaggle competitions download -c ieee-fraud-detection"
        )
        return None

    def map_external_features_to_sentinel(self, df: pd.DataFrame, dataset: str) -> pd.DataFrame:
        """
        Map external dataset features to Sentinel's 38 behavioral features.

        IEEE-CIS mapping example:
        - TransactionAmt → amount
        - C1-C14 (count features) → rolling_1h_count, rolling_24h_count
        - D1-D15 (time deltas) → time_since_previous_action
        - card1-card6 → recipient_id (beneficiary analogue)
        - V columns → behavioral z-scores

        This mapping is dataset-specific and designed to test whether Sentinel's
        behavioral representation generalizes to real financial transactions.
        """
        sentinel_features = {}

        if dataset == "ieee-cis":
            # Map IEEE-CIS features to Sentinel behavioral space
            # This is a STUB - full implementation requires the actual dataset schema
            sentinel_features = {
                "amount": df.get("TransactionAmt", 0),
                "hour_of_day": df.get("TransactionDT", 0) % 24,  # Convert to hour
                # ... additional 36 feature mappings
            }

        return pd.DataFrame(sentinel_features)

    def evaluate_domain_shift(
        self, model, synthetic_test: pd.DataFrame, external_test: Optional[pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Domain Shift Experiment:

        Test A: Synthetic Holdout (baseline)
        - Measures: Can model recognize behavior from same simulated environment?

        Test B: Real-World Dataset (generalization)
        - Measures: Does learned behavioral representation generalize beyond synthetic generator?

        Test C: Adversarial Scenarios (robustness)
        - Measures: Can attacker manipulate behavioral features?

        Returns comparative metrics to quantify domain shift impact.
        """
        results = {"synthetic_holdout": None, "external_validation": None, "domain_shift_delta": None}

        # Test A: Synthetic holdout
        if synthetic_test is not None and len(synthetic_test) > 0:
            y_true_synth = synthetic_test.get("loss_label")
            if y_true_synth is not None and model is not None:
                try:
                    y_pred_synth = model.predict(synthetic_test.drop(columns=["loss_label"], errors="ignore"))
                    results["synthetic_holdout"] = {
                        "roc_auc": roc_auc_score(y_true_synth, y_pred_synth),
                        "pr_auc": average_precision_score(y_true_synth, y_pred_synth),
                        "n_samples": len(synthetic_test),
                    }
                except Exception as e:
                    logger.error(f"Synthetic evaluation failed: {e}")

        # Test B: External validation
        if external_test is not None and len(external_test) > 0:
            y_true_ext = external_test.get("is_fraud")  # External dataset label
            if y_true_ext is not None and model is not None:
                try:
                    # Map external features to Sentinel space
                    external_mapped = self.map_external_features_to_sentinel(external_test, "ieee-cis")
                    y_pred_ext = model.predict(external_mapped)
                    results["external_validation"] = {
                        "roc_auc": roc_auc_score(y_true_ext, y_pred_ext),
                        "pr_auc": average_precision_score(y_true_ext, y_pred_ext),
                        "n_samples": len(external_test),
                    }
                except Exception as e:
                    logger.error(f"External validation failed: {e}")

        # Compute domain shift delta
        if results["synthetic_holdout"] and results["external_validation"]:
            results["domain_shift_delta"] = {
                "roc_auc_drop": (results["synthetic_holdout"]["roc_auc"] - results["external_validation"]["roc_auc"]),
                "pr_auc_drop": (results["synthetic_holdout"]["pr_auc"] - results["external_validation"]["pr_auc"]),
            }

        return results


def validate_no_synthetic_leakage(features_list: list) -> Dict[str, bool]:
    """
    Check for synthetic data leakage in feature engineering.

    BAD features (derived from target):
    - risk_score, is_fraud, attack_type, scenario, label
    - ground_truth_risk, attack_probability, scenario_type

    GOOD features (observable behavior):
    - transaction_amount, transaction_velocity, recipient_novelty
    - time_since_last_action, failed_attempts, tool_usage_frequency

    Returns dict of {feature_name: is_safe} for each feature.
    """
    LEAKAGE_KEYWORDS = [
        "risk",
        "fraud",
        "attack",
        "scenario",
        "label",
        "ground_truth",
        "probability",
        "malicious",
        "suspicious_score",
    ]

    leakage_check = {}
    for feature in features_list:
        feature_lower = feature.lower()
        has_leakage = any(keyword in feature_lower for keyword in LEAKAGE_KEYWORDS)
        leakage_check[feature] = not has_leakage

    return leakage_check


if __name__ == "__main__":
    # Example usage
    validator = ExternalValidator()

    # Check feature leakage
    from ml.features import TRANSACTION_FEATURES, BEHAVIORAL_FEATURES

    all_features = TRANSACTION_FEATURES + BEHAVIORAL_FEATURES

    leakage_results = validate_no_synthetic_leakage(all_features)
    leaked_features = [f for f, is_safe in leakage_results.items() if not is_safe]

    if leaked_features:
        logger.warning(f"Potential feature leakage detected: {leaked_features}")
    else:
        logger.info("✓ No synthetic data leakage detected in feature engineering")
