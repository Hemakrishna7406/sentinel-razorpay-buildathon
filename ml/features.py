"""
Sentinel — Feature Engineering

Transforms raw intents and agent context into machine learning features.
Separates transaction-level features from behavioral context features.
Enforces strict handling of unseen agents (insufficient history).
"""

import math
from typing import Any, Dict, List, Tuple

import pandas as pd
import numpy as np


# Define feature groups for ablation studies
TRANSACTION_FEATURES = [
    "amount", "amount_log", "recipient_novelty",
    "action_refund", "action_retry", "action_checkout", "action_payout",
    "hour_of_day", "is_typical_hour", "day_of_week", "is_weekend",
    "rolling_1m_count", "rolling_1h_count", "rolling_24h_count",
    "velocity_per_hour", "velocity_per_day",
]

BEHAVIORAL_FEATURES = [
    "agent_age_days",
    "velocity_z", "velocity_z_missing",
    "amount_z", "amount_z_missing",
    "hour_distance", "hour_distance_missing",
    "frequency_z", "frequency_z_missing",
    "recipient_diversity_score", "recipient_diversity_missing",
    "amount_percentile", "amount_percentile_missing",
    "velocity_acceleration", "velocity_acceleration_missing",
]


def extract_features(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract features from a single row (intent + context).
    
    This function simulates what happens at inference time when a new intent arrives.
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
    day_of_week = row.get("day_of_week", 0)  # 0=Monday, 6=Sunday
    features["day_of_week"] = day_of_week
    features["is_weekend"] = 1 if day_of_week >= 5 else 0

    typ_start = row.get("typical_hour_start", 0)
    typ_end = row.get("typical_hour_end", 23)

    # Handle wrap-around hours if needed (assuming simple contiguous range for now)
    if typ_start <= typ_end:
        is_typical = 1 if typ_start <= hour <= typ_end else 0
    else:
        is_typical = 1 if hour >= typ_start or hour <= typ_end else 0
    features["is_typical_hour"] = is_typical

    # Rolling counts
    rolling_1m = row.get("rolling_1m_count", 0)
    rolling_1h = row.get("rolling_1h_count", 0)
    rolling_24h = row.get("rolling_24h_count", 0)

    features["rolling_1m_count"] = rolling_1m
    features["rolling_1h_count"] = rolling_1h
    features["rolling_24h_count"] = rolling_24h

    # Velocity features (transactions per time unit)
    features["velocity_per_hour"] = rolling_1h  # Already per hour
    features["velocity_per_day"] = rolling_24h / 24.0 if rolling_24h > 0 else 0.0


    # ---------------------------------------------------------
    # BEHAVIORAL FEATURES
    # ---------------------------------------------------------
    features["agent_age_days"] = row.get("agent_age_days", 0)

    has_history = row.get("has_sufficient_history", 1)

    if not has_history:
        # Explicitly mark missing behavioral context for new agents
        features["velocity_z"] = np.nan
        features["velocity_z_missing"] = 1

        features["amount_z"] = np.nan
        features["amount_z_missing"] = 1

        features["hour_distance"] = np.nan
        features["hour_distance_missing"] = 1

        features["frequency_z"] = np.nan
        features["frequency_z_missing"] = 1

        features["recipient_diversity_score"] = np.nan
        features["recipient_diversity_missing"] = 1

        features["amount_percentile"] = np.nan
        features["amount_percentile_missing"] = 1

        features["velocity_acceleration"] = np.nan
        features["velocity_acceleration_missing"] = 1

        features["behavioral_drift_score"] = np.nan
    else:
        # Compute z-scores against baseline
        baseline_hourly = row.get("baseline_hourly_rate", 1.0)
        baseline_hourly = max(baseline_hourly, 0.001)  # Prevent div by zero
        
        # velocity_z = (current_1h - baseline_hourly) / baseline_hourly
        features["velocity_z"] = (features["rolling_1h_count"] - baseline_hourly) / baseline_hourly
        features["velocity_z_missing"] = 0
        
        baseline_avg_amt = row.get("baseline_avg_amount", 0)
        baseline_std_amt = row.get("baseline_std_amount", 1)
        baseline_std_amt = max(baseline_std_amt, 1)
        
        features["amount_z"] = (amount - baseline_avg_amt) / baseline_std_amt
        features["amount_z_missing"] = 0
        
        # Hour distance
        if is_typical:
            dist = 0
        else:
            # Shortest distance to typical window
            dist1 = min(abs(hour - typ_start), 24 - abs(hour - typ_start))
            dist2 = min(abs(hour - typ_end), 24 - abs(hour - typ_end))
            dist = min(dist1, dist2)
        features["hour_distance"] = dist
        features["hour_distance_missing"] = 0
        
        # Frequency Z (using 24h count vs expected daily volume)
        expected_daily = baseline_hourly * (typ_end - typ_start + 1 if typ_start <= typ_end else 24 - typ_start + typ_end + 1)
        expected_daily = max(expected_daily, 0.001)
        features["frequency_z"] = (features["rolling_24h_count"] - expected_daily) / expected_daily
        features["frequency_z_missing"] = 0

        # Recipient diversity metrics
        unique_recipients_24h = row.get("unique_recipients_24h", 1)
        total_txns_24h = max(rolling_24h, 1)
        # Diversity score: ratio of unique recipients to total transactions
        # High diversity (close to 1) = each txn to different recipient (suspicious)
        # Low diversity (close to 0) = repeated recipients (normal)
        features["recipient_diversity_score"] = unique_recipients_24h / total_txns_24h
        features["recipient_diversity_missing"] = 0

        # Amount distribution features
        # Percentile of current amount in agent's historical distribution
        baseline_q25 = row.get("baseline_amount_q25", baseline_avg_amt)
        baseline_q75 = row.get("baseline_amount_q75", baseline_avg_amt)

        if amount <= baseline_q25:
            amount_percentile = 0.25 * (amount / max(baseline_q25, 1))
        elif amount <= baseline_avg_amt:
            amount_percentile = 0.25 + 0.25 * ((amount - baseline_q25) / max(baseline_avg_amt - baseline_q25, 1))
        elif amount <= baseline_q75:
            amount_percentile = 0.50 + 0.25 * ((amount - baseline_avg_amt) / max(baseline_q75 - baseline_avg_amt, 1))
        else:
            # Above 75th percentile, scale to 1.0
            amount_percentile = 0.75 + 0.25 * min(1.0, (amount - baseline_q75) / max(baseline_q75, 1))

        features["amount_percentile"] = amount_percentile
        features["amount_percentile_missing"] = 0

        # Velocity acceleration (change in velocity)
        # Compare recent 1h velocity to baseline
        recent_velocity = rolling_1h
        velocity_ratio = recent_velocity / max(baseline_hourly, 0.001)
        # Log-scale acceleration to capture sudden bursts
        features["velocity_acceleration"] = math.log1p(velocity_ratio)
        features["velocity_acceleration_missing"] = 0

        # Diagnostic drift score (not used by model unless ablation allows)
        features["behavioral_drift_score"] = (
            abs(features["velocity_z"]) +
            abs(features["amount_z"]) +
            features["hour_distance"] / 12.0 +
            features["recipient_diversity_score"] +
            abs(features["velocity_acceleration"])
        ) / 5.0

    return features


def build_feature_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply feature extraction to an entire DataFrame."""
    feature_rows = [extract_features(row) for _, row in df.iterrows()]
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
