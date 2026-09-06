"""
Sentinel — Feature Engineering

Transforms raw intents and agent context into machine learning features.
Separates transaction-level features from behavioral context features.
Enforces strict handling of unseen agents (insufficient history) and avoids target leakage.
"""

import math
from typing import Any, Dict, List

import pandas as pd
import numpy as np

# Define feature groups for ablation studies
TRANSACTION_FEATURES = [
    "amount",
    "amount_log",
    "recipient_novelty",
    "action_refund",
    "action_retry",
    "action_checkout",
    "action_payout",
    "hour_of_day",
    "is_weekend",
    "rolling_1m_count",
    "rolling_1h_count",
    "rolling_24h_count",
    "velocity_per_hour",
    "velocity_per_day",
]

BEHAVIORAL_FEATURES = [
    "velocity_z",
    "velocity_z_missing",
    "amount_z",
    "amount_z_missing",
    "frequency_z",
    "frequency_z_missing",
    "recipient_diversity_score",
    "recipient_diversity_missing",
    "velocity_acceleration",
    "velocity_acceleration_missing",
]


def extract_features(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract features from a single row (intent + context).
    Historical statistics (like historical_avg_amount) must be pre-calculated
    based strictly on prior events, avoiding any lookahead bias or generator leakage.
    """
    features = {}

    # ---------------------------------------------------------
    # TRANSACTION FEATURES
    # ---------------------------------------------------------
    amount = row.get("amount", 0)
    features["amount"] = amount
    features["amount_log"] = math.log1p(amount)
    features["recipient_novelty"] = row.get("recipient_novelty", 0)

    action_type = row.get("action_type", "")
    features["action_refund"] = 1 if action_type == "refund" else 0
    features["action_retry"] = 1 if action_type == "retry" else 0
    features["action_checkout"] = 1 if action_type == "checkout" else 0
    features["action_payout"] = 1 if action_type == "payout" else 0

    hour = row.get("hour_of_day", 0)
    features["hour_of_day"] = hour

    # Time-based pattern features
    # Note: 'day_of_week' is removed to avoid temporal proxies in synthetic datasets
    # where the attack is rigidly tied to a specific day index.
    day_of_week = row.get("day_of_week", 0)
    features["is_weekend"] = 1 if day_of_week >= 5 else 0

    # Rolling counts
    rolling_1m = row.get("rolling_1m_count", 0)
    rolling_1h = row.get("rolling_1h_count", 0)
    rolling_24h = row.get("rolling_24h_count", 0)

    features["rolling_1m_count"] = rolling_1m
    features["rolling_1h_count"] = rolling_1h
    features["rolling_24h_count"] = rolling_24h

    # Velocity features
    features["velocity_per_hour"] = rolling_1h
    features["velocity_per_day"] = rolling_24h / 24.0 if rolling_24h > 0 else 0.0

    # ---------------------------------------------------------
    # BEHAVIORAL FEATURES
    # ---------------------------------------------------------

    # Read dynamically computed historical stats (must be from strictly prior events)
    hist_tx_count = row.get("historical_tx_count", 0)
    hist_avg_amt = row.get("historical_avg_amount", np.nan)
    hist_std_amt = row.get("historical_std_amount", np.nan)
    hist_avg_1h = row.get("historical_avg_1h_count", np.nan)
    hist_avg_24h = row.get("historical_avg_24h_count", np.nan)

    # FIRST-EVENT HANDLING: If an agent has < 5 prior transactions, we do not have
    # sufficient history to build a reliable behavioral baseline.
    if hist_tx_count < 5 or pd.isna(hist_avg_amt) or pd.isna(hist_std_amt):
        features["velocity_z"] = 0.0
        features["velocity_z_missing"] = 1

        features["amount_z"] = 0.0
        features["amount_z_missing"] = 1

        features["frequency_z"] = 0.0
        features["frequency_z_missing"] = 1

        features["recipient_diversity_score"] = 0.0
        features["recipient_diversity_missing"] = 1

        features["velocity_acceleration"] = 0.0
        features["velocity_acceleration_missing"] = 1
    else:
        # Prevent division by zero
        safe_std_amt = max(hist_std_amt, 1.0)
        safe_avg_1h = max(hist_avg_1h, 0.001)
        safe_avg_24h = max(hist_avg_24h, 0.001)

        # Compute z-scores against strict historical baseline
        features["velocity_z"] = (rolling_1h - safe_avg_1h) / safe_avg_1h
        features["velocity_z_missing"] = 0

        features["amount_z"] = (amount - hist_avg_amt) / safe_std_amt
        features["amount_z_missing"] = 0

        features["frequency_z"] = (rolling_24h - safe_avg_24h) / safe_avg_24h
        features["frequency_z_missing"] = 0

        # Recipient diversity
        unique_recipients_24h = row.get("unique_recipients_24h", 1)
        total_txns_24h = max(rolling_24h, 1)
        features["recipient_diversity_score"] = unique_recipients_24h / total_txns_24h
        features["recipient_diversity_missing"] = 0

        # Velocity acceleration (change in velocity)
        features["velocity_acceleration"] = math.log1p(rolling_1h / safe_avg_1h)
        features["velocity_acceleration_missing"] = 0

    return features


def build_feature_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply feature extraction to an entire DataFrame, strictly avoiding lookahead bias.
    We compute expanding historical window statistics (shifted by 1 so the current
    transaction is NOT included in its own baseline).
    """
    df = df.copy()

    # Sort chronologically to ensure strict temporal order
    df = df.sort_values(by=["agent_id", "timestamp"])

    # Calculate rolling historical statistics per agent WITHOUT looking ahead.
    grouped = df.groupby("agent_id")

    # Number of prior transactions
    df["historical_tx_count"] = grouped.cumcount()

    # Historical amount mean/std (shifted by 1)
    df["historical_avg_amount"] = grouped["amount"].transform(lambda x: x.expanding().mean().shift(1))
    df["historical_std_amount"] = grouped["amount"].transform(lambda x: x.expanding().std().shift(1))

    # Historical rolling counts mean (shifted by 1)
    df["historical_avg_1h_count"] = grouped["rolling_1h_count"].transform(lambda x: x.expanding().mean().shift(1))
    df["historical_avg_24h_count"] = grouped["rolling_24h_count"].transform(lambda x: x.expanding().mean().shift(1))

    # Fill NaNs for the very first transaction with 0 just for extraction safety
    df["historical_tx_count"] = df["historical_tx_count"].fillna(0)

    # Extract row-wise
    feature_rows = [extract_features(row.to_dict()) for _, row in df.iterrows()]

    return pd.DataFrame(feature_rows)


def get_feature_names(ablation_mode: str = "full_sentinel") -> List[str]:
    """Return the list of features to use based on the ablation mode."""
    if ablation_mode == "transaction_only":
        return TRANSACTION_FEATURES
    elif ablation_mode == "behavioral_only":
        return BEHAVIORAL_FEATURES
    elif ablation_mode == "full_sentinel":
        return TRANSACTION_FEATURES + BEHAVIORAL_FEATURES
    elif ablation_mode == "rules_only":
        return []
    else:
        raise ValueError(f"Unknown ablation mode: {ablation_mode}")
