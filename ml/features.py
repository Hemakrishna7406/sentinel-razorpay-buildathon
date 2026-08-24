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
    "hour_of_day", "is_typical_hour",
    "rolling_1m_count", "rolling_1h_count", "rolling_24h_count",
]

BEHAVIORAL_FEATURES = [
    "agent_age_days",
    "velocity_z", "velocity_z_missing",
    "amount_z", "amount_z_missing",
    "hour_distance", "hour_distance_missing",
    "frequency_z", "frequency_z_missing",
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
    
    typ_start = row.get("typical_hour_start", 0)
    typ_end = row.get("typical_hour_end", 23)
    
    # Handle wrap-around hours if needed (assuming simple contiguous range for now)
    if typ_start <= typ_end:
        is_typical = 1 if typ_start <= hour <= typ_end else 0
    else:
        is_typical = 1 if hour >= typ_start or hour <= typ_end else 0
    features["is_typical_hour"] = is_typical
    
    features["rolling_1m_count"] = row.get("rolling_1m_count", 0)
    features["rolling_1h_count"] = row.get("rolling_1h_count", 0)
    features["rolling_24h_count"] = row.get("rolling_24h_count", 0)


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
        
        # Diagnostic drift score (not used by model unless ablation allows)
        features["behavioral_drift_score"] = (
            abs(features["velocity_z"]) + 
            abs(features["amount_z"]) + 
            features["hour_distance"] / 12.0
        ) / 3.0

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
