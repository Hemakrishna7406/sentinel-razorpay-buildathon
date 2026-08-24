"""
Tests for ml/features.py

Verifies that feature extraction correctly handles transaction features,
behavioral features (z-scores), and unseen agents (missing indicators).
"""

import numpy as np
import pytest

from ml.features import extract_features


def test_transaction_features_extracted_correctly():
    row = {
        "amount": 1000,
        "recipient_novelty": 1,
        "action_type": "refund",
        "hour_of_day": 14,
        "typical_hour_start": 9,
        "typical_hour_end": 17,
        "rolling_1m_count": 2,
        "rolling_1h_count": 5,
        "rolling_24h_count": 20,
        "has_sufficient_history": 1,
        "baseline_hourly_rate": 2.0,
        "baseline_avg_amount": 500,
        "baseline_std_amount": 250,
    }
    
    features = extract_features(row)
    
    assert features["amount"] == 1000
    assert features["amount_log"] > 0
    assert features["recipient_novelty"] == 1
    assert features["action_refund"] == 1
    assert features["action_payout"] == 0
    assert features["hour_of_day"] == 14
    assert features["is_typical_hour"] == 1
    assert features["rolling_1h_count"] == 5


def test_behavioral_z_scores():
    row = {
        "amount": 1000,
        "hour_of_day": 14,
        "typical_hour_start": 9,
        "typical_hour_end": 17,
        "rolling_1h_count": 5,
        "rolling_24h_count": 20,
        "has_sufficient_history": 1,
        "baseline_hourly_rate": 2.0,
        "baseline_avg_amount": 500,
        "baseline_std_amount": 250,
    }
    
    features = extract_features(row)
    
    # amount_z = (1000 - 500) / 250 = 2.0
    assert features["amount_z"] == 2.0
    assert features["amount_z_missing"] == 0
    
    # velocity_z = (5 - 2.0) / 2.0 = 1.5
    assert features["velocity_z"] == 1.5
    assert features["velocity_z_missing"] == 0
    
    # Hour is typical, so distance is 0
    assert features["hour_distance"] == 0


def test_insufficient_history():
    """Agents with insufficient history should get NaN and missing=1 for behavioral features."""
    row = {
        "amount": 1000,
        "has_sufficient_history": 0,  # Critical flag
        # These should be ignored because history is insufficient
        "baseline_hourly_rate": 2.0, 
        "baseline_avg_amount": 500,
        "baseline_std_amount": 250,
    }
    
    features = extract_features(row)
    
    # Transaction features still present
    assert features["amount"] == 1000
    
    # Behavioral features must be missing
    assert np.isnan(features["amount_z"])
    assert features["amount_z_missing"] == 1
    
    assert np.isnan(features["velocity_z"])
    assert features["velocity_z_missing"] == 1
    
    assert np.isnan(features["hour_distance"])
    assert features["hour_distance_missing"] == 1
