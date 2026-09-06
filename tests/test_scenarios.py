"""
Tests for ml/scenarios.py

Verifies that all seven scenario definitions are correct, independently
instantiable, and produce the expected behavioral fingerprints.

Per masterplan §6 and threat-model.md §4.
"""

import pytest
from ml.scenarios import (
    ALL_SCENARIOS,
    DEFAULT_SCENARIO_MIX,
    EXPERIMENT_MIXES,
    SCENARIO_ABUSE_BURST,
    SCENARIO_BENIGN_DRIFT,
    SCENARIO_MISCONFIGURED,
    SCENARIO_NEW_AGENT,
    SCENARIO_NORMAL,
    SCENARIO_SEASONAL_SPIKE,
    SCENARIO_SLOW_ABUSE,
    ExpectedResponse,
    LossType,
    ThreatActor,
    get_scenario,
    validate_scenario_mix,
)


class TestScenarioRegistry:
    """Test that all scenarios are properly registered."""

    def test_seven_scenarios_registered(self):
        """All seven scenarios exist in the registry."""
        assert len(ALL_SCENARIOS) == 8
        expected_names = {
            "normal",
            "abuse_burst",
            "misconfigured",
            "slow_abuse",
            "seasonal_spike",
            "new_agent",
            "benign_drift",
            "behavioral_evasion",
        }
        assert set(ALL_SCENARIOS.keys()) == expected_names

    def test_unique_codes(self):
        """Each scenario has a unique single-letter code."""
        codes = [s.code for s in ALL_SCENARIOS.values()]
        assert len(codes) == len(set(codes)), "Duplicate scenario codes found"
        for code in codes:
            assert len(code) == 1, f"Code '{code}' is not a single letter"

    def test_get_scenario_valid(self):
        """get_scenario returns the correct definition."""
        for name, expected in ALL_SCENARIOS.items():
            assert get_scenario(name) is expected

    def test_get_scenario_invalid(self):
        """get_scenario raises ValueError for unknown names."""
        with pytest.raises(ValueError, match="Unknown scenario"):
            get_scenario("nonexistent_scenario")

    def test_all_scenarios_independently_instantiable(self):
        """Each scenario can be accessed independently without errors."""
        for name, scenario in ALL_SCENARIOS.items():
            assert scenario.name, f"Scenario '{name}' has no name"
            assert scenario.description, f"Scenario '{name}' has no description"
            assert scenario.amount.mean > 0, f"Scenario '{name}' has invalid amount mean"
            assert scenario.velocity.actions_per_hour_mean > 0


class TestScenarioLabels:
    """Test the label methodology: loss_label, loss_type, and expected response."""

    def test_loss_label_is_binary(self):
        """loss_label is always 0 or 1."""
        for name, scenario in ALL_SCENARIOS.items():
            assert scenario.loss_label in (0, 1), f"Scenario '{name}' has invalid loss_label: {scenario.loss_label}"

    def test_no_model_risk_or_decision_in_scenario(self):
        """Scenarios define loss_label, NOT model_risk or decision."""
        for name, scenario in ALL_SCENARIOS.items():
            assert not hasattr(scenario, "model_risk"), f"Scenario '{name}' should not have model_risk"
            assert not hasattr(scenario, "decision"), f"Scenario '{name}' should not have a 'decision' field"

    def test_loss_type_matches_loss_label(self):
        """loss_type is None when loss_label=0, non-None when loss_label=1."""
        for name, scenario in ALL_SCENARIOS.items():
            if scenario.loss_label == 0:
                assert (
                    scenario.loss_type == LossType.NONE
                ), f"Scenario '{name}': loss_label=0 but loss_type={scenario.loss_type}"
            else:
                assert scenario.loss_type != LossType.NONE, f"Scenario '{name}': loss_label=1 but loss_type is NONE"


class TestNormalScenario:
    """Scenario A — Normal."""

    def test_allow_response(self):
        assert SCENARIO_NORMAL.expected_response == ExpectedResponse.ALLOW

    def test_no_loss(self):
        assert SCENARIO_NORMAL.loss_label == 0
        assert SCENARIO_NORMAL.loss_type == LossType.NONE

    def test_legitimate(self):
        assert SCENARIO_NORMAL.is_legitimate is True

    def test_sufficient_history(self):
        assert SCENARIO_NORMAL.has_sufficient_history is True

    def test_no_threat_actor(self):
        assert SCENARIO_NORMAL.threat_actor == ThreatActor.NONE

    def test_amounts_in_paise(self):
        """All amounts are integers (paise, not rupees)."""
        assert isinstance(SCENARIO_NORMAL.amount.mean, int)
        assert SCENARIO_NORMAL.amount.mean > 1000  # >₹10 in paise

    def test_action_mix_sums_to_one(self):
        total = sum(SCENARIO_NORMAL.action_mix.values())
        assert abs(total - 1.0) < 0.01


class TestAbuseBurstScenario:
    """Scenario B — Abuse Burst."""

    def test_contain_response(self):
        assert SCENARIO_ABUSE_BURST.expected_response == ExpectedResponse.CONTAIN

    def test_loss_event(self):
        assert SCENARIO_ABUSE_BURST.loss_label == 1
        assert SCENARIO_ABUSE_BURST.loss_type == LossType.UNAUTHORIZED_ACTION

    def test_not_legitimate(self):
        assert SCENARIO_ABUSE_BURST.is_legitimate is False

    def test_compromised_threat_actor(self):
        assert SCENARIO_ABUSE_BURST.threat_actor == ThreatActor.COMPROMISED

    def test_higher_velocity_than_normal(self):
        assert SCENARIO_ABUSE_BURST.velocity.actions_per_hour_mean > SCENARIO_NORMAL.velocity.actions_per_hour_mean * 3

    def test_higher_amounts_than_normal(self):
        assert SCENARIO_ABUSE_BURST.amount.mean > SCENARIO_NORMAL.amount.mean * 2

    def test_more_novel_recipients(self):
        assert SCENARIO_ABUSE_BURST.recipients.known_recipient_ratio < SCENARIO_NORMAL.recipients.known_recipient_ratio

    def test_operates_outside_hours(self):
        assert SCENARIO_ABUSE_BURST.temporal.operates_outside_hours is True


class TestMisconfiguredScenario:
    """Scenario C — Misconfigured Agent."""

    def test_escalate_response(self):
        """Misconfigured → ESCALATE, not CONTAIN (not malicious)."""
        assert SCENARIO_MISCONFIGURED.expected_response == ExpectedResponse.ESCALATE

    def test_policy_violation_loss(self):
        assert SCENARIO_MISCONFIGURED.loss_label == 1
        assert SCENARIO_MISCONFIGURED.loss_type == LossType.POLICY_VIOLATION

    def test_not_malicious_but_not_legitimate(self):
        """Not legitimate (policy violation) but not marked as compromised."""
        assert SCENARIO_MISCONFIGURED.threat_actor == ThreatActor.MISCONFIGURED
        assert SCENARIO_MISCONFIGURED.threat_actor != ThreatActor.COMPROMISED

    def test_legitimate_recipients(self):
        """High known-recipient ratio — recipients are fine, policy is wrong."""
        assert SCENARIO_MISCONFIGURED.recipients.known_recipient_ratio >= 0.85


class TestSlowAbuseScenario:
    """Scenario D — Slow / Threshold-Aware Abuse."""

    def test_escalate_response(self):
        assert SCENARIO_SLOW_ABUSE.expected_response == ExpectedResponse.ESCALATE

    def test_unauthorized_loss(self):
        assert SCENARIO_SLOW_ABUSE.loss_label == 1
        assert SCENARIO_SLOW_ABUSE.loss_type == LossType.UNAUTHORIZED_ACTION

    def test_low_velocity(self):
        """Slow abuse deliberately keeps velocity low."""
        assert SCENARIO_SLOW_ABUSE.velocity.actions_per_hour_mean < SCENARIO_NORMAL.velocity.actions_per_hour_mean

    def test_amounts_near_threshold(self):
        """Amounts cluster near the normal p95 (threshold-aware)."""
        normal_p95 = SCENARIO_NORMAL.amount.p95
        assert SCENARIO_SLOW_ABUSE.amount.mean <= normal_p95 * 1.2


class TestSeasonalSpikeScenario:
    """Scenario E — Legitimate Seasonal Spike. THE CRITICAL ANTI-SHORTCUT."""

    def test_allow_response(self):
        """Seasonal spike MUST be ALLOW — Sentinel is not a volume blocker."""
        assert SCENARIO_SEASONAL_SPIKE.expected_response == ExpectedResponse.ALLOW

    def test_no_loss(self):
        """Seasonal spike is legitimate — no loss event."""
        assert SCENARIO_SEASONAL_SPIKE.loss_label == 0
        assert SCENARIO_SEASONAL_SPIKE.loss_type == LossType.NONE

    def test_legitimate(self):
        assert SCENARIO_SEASONAL_SPIKE.is_legitimate is True

    def test_high_volume_multiplier(self):
        """8–10× volume increase."""
        assert SCENARIO_SEASONAL_SPIKE.spike_volume_multiplier >= 8.0

    def test_same_amount_distribution_as_normal(self):
        """Amount distribution should match normal — only volume changes."""
        assert SCENARIO_SEASONAL_SPIKE.amount.mean == SCENARIO_NORMAL.amount.mean

    def test_spike_window_defined(self):
        """Spike has defined start and end days."""
        assert SCENARIO_SEASONAL_SPIKE.spike_start_day is not None
        assert SCENARIO_SEASONAL_SPIKE.spike_end_day is not None
        assert SCENARIO_SEASONAL_SPIKE.spike_start_day < SCENARIO_SEASONAL_SPIKE.spike_end_day


class TestNewAgentScenario:
    """Scenario F — New Agent."""

    def test_conservative_escalation(self):
        """New agents get conservative escalation, NOT denial."""
        assert SCENARIO_NEW_AGENT.expected_response == ExpectedResponse.CONSERVATIVE_ESCALATE

    def test_no_loss(self):
        """Lack of history is NOT guilt."""
        assert SCENARIO_NEW_AGENT.loss_label == 0

    def test_insufficient_history(self):
        """Must have has_sufficient_history=False."""
        assert SCENARIO_NEW_AGENT.has_sufficient_history is False

    def test_no_threat_actor(self):
        """No threat actor — just insufficient information."""
        assert SCENARIO_NEW_AGENT.threat_actor == ThreatActor.NONE


class TestBenignDriftScenario:
    """Scenario G — Benign Behavioral Drift."""

    def test_suspicious_then_safe(self):
        """Benign drift: initially suspicious, then safe after adaptation."""
        assert SCENARIO_BENIGN_DRIFT.expected_response == ExpectedResponse.SUSPICIOUS_THEN_SAFE

    def test_no_loss(self):
        """Benign drift is NOT malicious — no loss event."""
        assert SCENARIO_BENIGN_DRIFT.loss_label == 0
        assert SCENARIO_BENIGN_DRIFT.loss_type == LossType.NONE

    def test_drift_actor(self):
        assert SCENARIO_BENIGN_DRIFT.threat_actor == ThreatActor.BEHAVIORAL_DRIFT

    def test_sufficient_history(self):
        """Agent has history — the drift is from a known baseline."""
        assert SCENARIO_BENIGN_DRIFT.has_sufficient_history is True

    def test_different_hours_from_normal(self):
        """Operating hours have changed from normal baseline."""
        assert (
            SCENARIO_BENIGN_DRIFT.temporal.typical_hour_start != SCENARIO_NORMAL.temporal.typical_hour_start
            or SCENARIO_BENIGN_DRIFT.temporal.typical_hour_end != SCENARIO_NORMAL.temporal.typical_hour_end
        )

    def test_has_drift_onset(self):
        """Drift has a defined onset day."""
        assert SCENARIO_BENIGN_DRIFT.drift_onset_day is not None

    def test_same_amounts_as_normal(self):
        """Amounts don't change — only operating pattern changes."""
        assert SCENARIO_BENIGN_DRIFT.amount.mean == SCENARIO_NORMAL.amount.mean


class TestScenarioMixes:
    """Test scenario mix configurations."""

    def test_default_mix_valid(self):
        validate_scenario_mix(DEFAULT_SCENARIO_MIX)

    def test_default_mix_has_all_scenarios(self):
        assert set(DEFAULT_SCENARIO_MIX.keys()) == set(ALL_SCENARIOS.keys())

    def test_default_mix_mostly_normal(self):
        assert DEFAULT_SCENARIO_MIX["normal"] >= 0.80

    def test_all_experiment_mixes_valid(self):
        for name, mix in EXPERIMENT_MIXES.items():
            validate_scenario_mix(mix), f"Experiment mix '{name}' is invalid"

    def test_invalid_mix_rejected(self):
        with pytest.raises(ValueError, match="Unknown scenario"):
            validate_scenario_mix({"fake_scenario": 1.0})

    def test_invalid_proportions_rejected(self):
        with pytest.raises(ValueError, match="sum to"):
            validate_scenario_mix({"normal": 0.5})  # Doesn't sum to 1.0


class TestAmountsInPaise:
    """All monetary values across all scenarios must be integers (paise)."""

    def test_all_amounts_are_integers(self):
        for name, scenario in ALL_SCENARIOS.items():
            assert isinstance(scenario.amount.mean, int), f"Scenario '{name}': amount.mean is not int"
            assert isinstance(scenario.amount.std, int), f"Scenario '{name}': amount.std is not int"
            assert isinstance(scenario.amount.min_amount, int), f"Scenario '{name}': amount.min_amount is not int"
            assert isinstance(scenario.amount.max_amount, int), f"Scenario '{name}': amount.max_amount is not int"
            assert isinstance(scenario.amount.p95, int), f"Scenario '{name}': amount.p95 is not int"

    def test_no_float_amounts(self):
        """Explicitly verify no floating-point money (masterplan §19)."""
        for name, scenario in ALL_SCENARIOS.items():
            assert not isinstance(
                scenario.amount.mean, float
            ), f"Scenario '{name}': FLOAT money detected in amount.mean"


class TestActionMixes:
    """All action mixes must be valid probability distributions."""

    def test_all_mixes_sum_to_one(self):
        for name, scenario in ALL_SCENARIOS.items():
            if scenario.action_mix:
                total = sum(scenario.action_mix.values())
                assert abs(total - 1.0) < 0.01, f"Scenario '{name}': action_mix sums to {total}"

    def test_all_actions_valid(self):
        valid_actions = {"refund", "retry", "checkout", "payout"}
        for name, scenario in ALL_SCENARIOS.items():
            for action in scenario.action_mix:
                assert action in valid_actions, f"Scenario '{name}': unknown action '{action}'"
