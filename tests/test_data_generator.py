"""
Tests for ml/data_generator.py

Verifies determinism, schema, leakage rules, and scenario-specific flags.
"""

import pandas as pd
import pytest

from ml.data_generator import generate_dataset


@pytest.fixture(scope="module")
def default_df():
    """Generate a standard dataset for testing."""
    return generate_dataset(seed=42)


class TestDataGenerator:

    def test_determinism(self):
        """Same seed must produce identical output."""
        df1 = generate_dataset(seed=123)
        df2 = generate_dataset(seed=123)
        pd.testing.assert_frame_equal(df1, df2)

    def test_schema_present(self, default_df):
        """All expected fields must be present in the generated DataFrame."""
        expected_columns = {
            "intent_id", "agent_id", "timestamp", "day", "action_type",
            "transaction_id", "amount", "currency", "recipient_id",
            "recipient_novelty", "merchant_id", "agent_age_days",
            "hour_of_day", "time_since_previous_action",
            "rolling_1m_count", "rolling_1h_count", "rolling_24h_count",
            "scenario_label", "loss_label", "loss_type", "has_sufficient_history"
        }
        assert set(default_df.columns) == expected_columns

    def test_no_float_money(self, default_df):
        """Amounts must be integers (paise)."""
        assert pd.api.types.is_integer_dtype(default_df["amount"])

    def test_no_leakage_columns(self, default_df):
        """model_risk and decision must NEVER be in the generated dataset."""
        assert "model_risk" not in default_df.columns
        assert "decision" not in default_df.columns

    def test_agent_g_h_only_in_test(self):
        """Agents G and H should only appear in days 26-30."""
        # Make sure they are generated
        # A-F = 6 agents, G-H = 2 agents
        df = generate_dataset(seed=42, num_agents_train_val=6, num_agents_test_only=2, days=30)
        
        test_agents = df[df["agent_id"].isin(["G", "H"])]
        assert not test_agents.empty, "Agents G and H were not generated"
        
        # Check they only appear in day 26 or later
        assert test_agents["day"].min() >= 26

    def test_seasonal_spike_loss_label(self):
        """Seasonal spike must have loss_label = 0."""
        df = generate_dataset(seed=999, scenario_mix={"seasonal_spike": 1.0}, num_agents_test_only=0)
        assert (df["loss_label"] == 0).all()

    def test_benign_drift_loss_label(self):
        """Benign drift must have loss_label = 0."""
        df = generate_dataset(seed=999, scenario_mix={"benign_drift": 1.0}, num_agents_test_only=0)
        assert (df["loss_label"] == 0).all()

    def test_new_agent_history_flag(self):
        """New agents must have has_sufficient_history = 0."""
        df = generate_dataset(seed=999, scenario_mix={"new_agent": 1.0}, num_agents_test_only=0)
        assert (df["has_sufficient_history"] == 0).all()

    def test_abuse_burst_loss_label(self):
        """Abuse burst has both normal baseline and loss events."""
        df = generate_dataset(seed=999, scenario_mix={"abuse_burst": 1.0}, num_agents_test_only=0)
        assert (df["loss_label"] == 1).sum() > 0
        assert (df["loss_label"] == 0).sum() > 0

