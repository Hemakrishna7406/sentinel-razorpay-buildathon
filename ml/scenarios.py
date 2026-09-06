"""
Sentinel — Scenario Definitions

Defines the seven behavioral scenarios used for synthetic data generation,
threat modeling, and evaluation. Each scenario models a specific behavioral
pattern from threat-model.md §4.

These scenarios are the foundation of the research question (masterplan §4):
    Does incorporating agent-level behavioral context improve detection of
    autonomous financial abuse over transaction-level signals alone?

Scenarios:
    A: Normal            — baseline legitimate behavior
    B: Abuse Burst       — compromised agent, sudden anomalous activity
    C: Misconfigured     — incorrect policy config, not malicious
    D: Slow Abuse        — gradual threshold-aware escalation
    E: Seasonal Spike    — legitimate high-volume period (anti-shortcut)
    F: New Agent         — insufficient history
    G: Benign Drift      — legitimate environmental change
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ThreatActor(Enum):
    """Threat actors / failure sources from threat-model.md §3."""

    NONE = "none"  # Legitimate behavior or insufficient info
    COMPROMISED = "compromised"  # §5A: Valid auth, anomalous behavior
    MISCONFIGURED = "misconfigured"  # §5B: Functioning as programmed but wrong config
    BEHAVIORAL_DRIFT = "behavioral_drift"  # §5C: Environmental / model change


class ExpectedResponse(Enum):
    """Expected system response for each scenario."""

    ALLOW = "ALLOW"
    ESCALATE = "ESCALATE"
    CONTAIN = "CONTAIN"
    CONSERVATIVE_ESCALATE = "CONSERVATIVE_ESCALATE"  # New agent special case
    SUSPICIOUS_THEN_SAFE = "SUSPICIOUS_THEN_SAFE"  # Benign drift trajectory


class LossType(Enum):
    """Ground truth loss classification — what actually happened."""

    NONE = None  # No loss event
    UNAUTHORIZED_ACTION = "unauthorized_action"  # Compromised agent
    POLICY_VIOLATION = "policy_violation"  # Misconfigured agent


@dataclass(frozen=True)
class AmountDistribution:
    """Describes the monetary distribution for a scenario (in paise)."""

    mean: int  # Mean amount in paise
    std: int  # Standard deviation in paise
    min_amount: int  # Floor
    max_amount: int  # Ceiling
    p95: int  # 95th percentile


@dataclass(frozen=True)
class VelocityProfile:
    """Describes the action rate for a scenario."""

    actions_per_hour_mean: float
    actions_per_hour_std: float
    burst_factor: float = 1.0  # Multiplier during active period


@dataclass(frozen=True)
class TemporalProfile:
    """Describes when the agent operates."""

    typical_hour_start: int  # 0-23
    typical_hour_end: int  # 0-23
    operates_outside_hours: bool = False


@dataclass(frozen=True)
class RecipientProfile:
    """Describes recipient diversity."""

    known_recipient_ratio: float  # Fraction of actions to known recipients
    unique_recipients_per_day: int


@dataclass(frozen=True)
class ScenarioDefinition:
    """
    Complete definition of a behavioral scenario.

    Each scenario is independently testable and independently tunable.
    The scenario definitions drive data generation (ml/data_generator.py),
    threat modeling (threat-model.md), and evaluation expectations.
    """

    name: str
    code: str  # Single-letter code (A-G)
    description: str
    threat_actor: ThreatActor
    expected_response: ExpectedResponse
    loss_label: int  # 0 = no loss, 1 = loss event
    loss_type: LossType
    has_sufficient_history: bool  # Whether the agent has enough baseline

    # Behavioral parameters
    amount: AmountDistribution
    velocity: VelocityProfile
    temporal: TemporalProfile
    recipients: RecipientProfile

    # Action type distribution (probabilities must sum to 1.0)
    action_mix: dict = field(default_factory=dict)

    # Scenario-specific flags
    is_legitimate: bool = True  # Whether this is legitimate behavior
    drift_onset_day: Optional[int] = None  # Day when drift begins (D, G)
    spike_start_day: Optional[int] = None  # Day when spike begins (E)
    spike_end_day: Optional[int] = None  # Day when spike ends (E)
    spike_volume_multiplier: float = 1.0  # Volume multiplier during spike (E)

    # Human-readable notes for documentation
    key_signal: str = ""
    mitigation: str = ""


# ============================================================================
# SCENARIO DEFINITIONS
# ============================================================================

SCENARIO_NORMAL = ScenarioDefinition(
    name="Normal",
    code="A",
    description=(
        "Baseline legitimate agent behavior. Stable volume, stable amounts, "
        "known recipients, normal operating hours, normal action mix."
    ),
    threat_actor=ThreatActor.NONE,
    expected_response=ExpectedResponse.ALLOW,
    loss_label=0,
    loss_type=LossType.NONE,
    has_sufficient_history=True,
    amount=AmountDistribution(
        mean=324000,  # ₹3,240 in paise
        std=150000,  # ₹1,500
        min_amount=10000,  # ₹100
        max_amount=890000,  # ₹8,900
        p95=890000,
    ),
    velocity=VelocityProfile(
        actions_per_hour_mean=2.25,  # ~18/day over 8 hours
        actions_per_hour_std=0.75,
    ),
    temporal=TemporalProfile(
        typical_hour_start=9,
        typical_hour_end=19,
    ),
    recipients=RecipientProfile(
        known_recipient_ratio=0.85,
        unique_recipients_per_day=15,
    ),
    action_mix={"refund": 0.60, "retry": 0.20, "checkout": 0.15, "payout": 0.05},
    key_signal="Stable baseline behavior across all dimensions",
    mitigation="None needed — establishes the behavioral baseline",
)

SCENARIO_ABUSE_BURST = ScenarioDefinition(
    name="Abuse Burst",
    code="B",
    description=(
        "Compromised agent generating rapid anomalous financial actions. "
        "Extreme velocity, unusual amounts, novel recipients, abnormal time."
    ),
    threat_actor=ThreatActor.COMPROMISED,
    expected_response=ExpectedResponse.CONTAIN,
    loss_label=1,
    loss_type=LossType.UNAUTHORIZED_ACTION,
    has_sufficient_history=True,
    amount=AmountDistribution(
        mean=1500000,  # ₹15,000 — much higher than baseline
        std=800000,  # ₹8,000 — high variance
        min_amount=500000,  # ₹5,000
        max_amount=5000000,  # ₹50,000
        p95=4000000,
    ),
    velocity=VelocityProfile(
        actions_per_hour_mean=15.0,  # 6–7× baseline
        actions_per_hour_std=5.0,
        burst_factor=3.0,
    ),
    temporal=TemporalProfile(
        typical_hour_start=9,
        typical_hour_end=19,
        operates_outside_hours=True,  # Active at abnormal times
    ),
    recipients=RecipientProfile(
        known_recipient_ratio=0.15,  # Mostly novel recipients
        unique_recipients_per_day=50,  # Much higher than normal
    ),
    action_mix={"refund": 0.10, "retry": 0.05, "checkout": 0.05, "payout": 0.80},
    is_legitimate=False,
    drift_onset_day=15,  # Abuse begins mid-dataset
    key_signal="velocity_z spike, amount_z spike, recipient novelty surge, hour_distance",
    mitigation="Behavioral drift detection → risk escalation → capability denial",
)

SCENARIO_MISCONFIGURED = ScenarioDefinition(
    name="Misconfigured Agent",
    code="C",
    description=(
        "Agent functioning as programmed but with incorrect policy/configuration. "
        "High frequency, legitimate recipients, consistent but policy-violating behavior. "
        "NOT malicious."
    ),
    threat_actor=ThreatActor.MISCONFIGURED,
    expected_response=ExpectedResponse.ESCALATE,
    loss_label=1,
    loss_type=LossType.POLICY_VIOLATION,
    has_sufficient_history=True,
    amount=AmountDistribution(
        mean=1200000,  # ₹12,000 — higher than typical policy allows
        std=200000,  # ₹2,000 — very consistent (not random)
        min_amount=800000,
        max_amount=1500000,
        p95=1400000,
    ),
    velocity=VelocityProfile(
        actions_per_hour_mean=5.0,  # ~2× baseline but not extreme
        actions_per_hour_std=1.0,
    ),
    temporal=TemporalProfile(
        typical_hour_start=9,
        typical_hour_end=19,
    ),
    recipients=RecipientProfile(
        known_recipient_ratio=0.90,  # Legitimate recipients
        unique_recipients_per_day=12,
    ),
    action_mix={"refund": 0.90, "retry": 0.05, "checkout": 0.03, "payout": 0.02},
    is_legitimate=False,  # Policy-violating, though not malicious
    key_signal="Consistent high-amount pattern, legitimate recipients, policy threshold exceeded",
    mitigation="Policy evaluation flags violations, human review triggered",
)

SCENARIO_SLOW_ABUSE = ScenarioDefinition(
    name="Slow / Threshold-Aware Abuse",
    code="D",
    description=(
        "Compromised agent with low volume, high-value actions deliberately "
        "close to thresholds. Low velocity, recipient variation."
    ),
    threat_actor=ThreatActor.COMPROMISED,
    expected_response=ExpectedResponse.ESCALATE,
    loss_label=1,
    loss_type=LossType.UNAUTHORIZED_ACTION,
    has_sufficient_history=True,
    amount=AmountDistribution(
        mean=800000,  # ₹8,000 — near p95 of normal
        std=100000,  # ₹1,000 — tightly clustered near threshold
        min_amount=700000,
        max_amount=950000,
        p95=900000,
    ),
    velocity=VelocityProfile(
        actions_per_hour_mean=0.5,  # Low velocity to avoid detection
        actions_per_hour_std=0.2,
    ),
    temporal=TemporalProfile(
        typical_hour_start=9,
        typical_hour_end=19,
    ),
    recipients=RecipientProfile(
        known_recipient_ratio=0.40,  # Moderate recipient novelty
        unique_recipients_per_day=8,
    ),
    action_mix={"refund": 0.30, "retry": 0.10, "checkout": 0.10, "payout": 0.50},
    is_legitimate=False,
    drift_onset_day=10,  # Gradual onset
    key_signal="amount_z near threshold, recipient novelty, cumulative drift over time",
    mitigation="Amount deviation detection, recipient novelty tracking, cumulative drift",
)

SCENARIO_SEASONAL_SPIKE = ScenarioDefinition(
    name="Legitimate Seasonal Spike",
    code="E",
    description=(
        "Legitimate 8–10× volume increase during expected business period. "
        "Legitimate recipients, stable amount distribution, historical context "
        "supports the spike. THE CRITICAL ANTI-SHORTCUT SCENARIO: model must "
        "NOT learn HIGH VOLUME = BAD."
    ),
    threat_actor=ThreatActor.NONE,
    expected_response=ExpectedResponse.ALLOW,
    loss_label=0,
    loss_type=LossType.NONE,
    has_sufficient_history=True,
    amount=AmountDistribution(
        mean=324000,  # Same as normal — amounts don't change
        std=150000,
        min_amount=10000,
        max_amount=890000,
        p95=890000,
    ),
    velocity=VelocityProfile(
        actions_per_hour_mean=2.25,  # Base rate (multiplied by spike_volume_multiplier)
        actions_per_hour_std=0.75,
        burst_factor=1.0,
    ),
    temporal=TemporalProfile(
        typical_hour_start=9,
        typical_hour_end=19,
    ),
    recipients=RecipientProfile(
        known_recipient_ratio=0.75,  # Slightly more new recipients during sale
        unique_recipients_per_day=40,  # Higher unique count but expected
    ),
    action_mix={"refund": 0.50, "retry": 0.15, "checkout": 0.30, "payout": 0.05},
    spike_start_day=22,
    spike_end_day=26,
    spike_volume_multiplier=9.0,  # 8–10× volume
    key_signal="High volume but consistent amount/recipient/hour distribution",
    mitigation="None needed — behavioral context overrides volume signal",
)

SCENARIO_NEW_AGENT = ScenarioDefinition(
    name="New Agent",
    code="F",
    description=(
        "Agent with little or no history. Insufficient behavioral baseline. "
        "Expected response is conservative escalation — NEVER automatic denial "
        "solely due to lack of history."
    ),
    threat_actor=ThreatActor.NONE,
    expected_response=ExpectedResponse.CONSERVATIVE_ESCALATE,
    loss_label=0,  # Lack of history is NOT guilt
    loss_type=LossType.NONE,
    has_sufficient_history=False,
    amount=AmountDistribution(
        mean=250000,  # ₹2,500 — moderate
        std=100000,
        min_amount=5000,
        max_amount=500000,
        p95=450000,
    ),
    velocity=VelocityProfile(
        actions_per_hour_mean=1.5,
        actions_per_hour_std=0.5,
    ),
    temporal=TemporalProfile(
        typical_hour_start=10,
        typical_hour_end=20,
    ),
    recipients=RecipientProfile(
        known_recipient_ratio=0.50,  # Mix — everything is "new" for a new agent
        unique_recipients_per_day=10,
    ),
    action_mix={"refund": 0.40, "retry": 0.30, "checkout": 0.20, "payout": 0.10},
    key_signal="has_sufficient_history=0, all behavioral features are _missing",
    mitigation="Policy-enforced conservative escalation independent of ML prediction",
)

SCENARIO_BENIGN_DRIFT = ScenarioDefinition(
    name="Benign Behavioral Drift",
    code="G",
    description=(
        "Agent changes operating pattern permanently due to legitimate "
        "environmental change (e.g., merchant changes hours from 09–19 to 11–23). "
        "Behavior shifts but remains internally consistent within new pattern. "
        "This proves that behavioral deviation ≠ necessarily abuse."
    ),
    threat_actor=ThreatActor.BEHAVIORAL_DRIFT,
    expected_response=ExpectedResponse.SUSPICIOUS_THEN_SAFE,
    loss_label=0,  # Not malicious — legitimate change
    loss_type=LossType.NONE,
    has_sufficient_history=True,
    amount=AmountDistribution(
        mean=324000,  # Same amounts as before
        std=150000,
        min_amount=10000,
        max_amount=890000,
        p95=890000,
    ),
    velocity=VelocityProfile(
        actions_per_hour_mean=2.5,  # Slightly different rate
        actions_per_hour_std=0.8,
    ),
    temporal=TemporalProfile(
        typical_hour_start=11,  # Changed from 9→11
        typical_hour_end=23,  # Changed from 19→23
    ),
    recipients=RecipientProfile(
        known_recipient_ratio=0.80,
        unique_recipients_per_day=18,
    ),
    action_mix={"refund": 0.55, "retry": 0.20, "checkout": 0.20, "payout": 0.05},
    drift_onset_day=18,  # Drift begins day 18 — initially looks suspicious
    key_signal="hour_distance spike initially, then new pattern stabilizes",
    mitigation="Baseline recomputation over time. Initial SUSPICIOUS transitions to SAFE.",
)

SCENARIO_BEHAVIORAL_EVASION = ScenarioDefinition(
    name="Behavioral Evasion",
    code="H",
    description=(
        "Adversarial scenario testing Sentinel's core thesis. "
        "Transactions are perfectly normal (normal amount, normal action mix, known recipients), "
        "but the agent's behavior is highly anomalous (high velocity, abnormal hours). "
        "This isolates behavioral drift from transaction-level anomalies."
    ),
    threat_actor=ThreatActor.COMPROMISED,
    expected_response=ExpectedResponse.CONTAIN,
    loss_label=1,
    loss_type=LossType.UNAUTHORIZED_ACTION,
    has_sufficient_history=True,
    amount=AmountDistribution(
        mean=324000,  # Exactly same as normal
        std=150000,
        min_amount=10000,
        max_amount=890000,
        p95=890000,
    ),
    velocity=VelocityProfile(
        actions_per_hour_mean=2.25,  # Same as normal baseline
        actions_per_hour_std=0.75,
        burst_factor=9.0,  # Jumps to ~20/hr during drift
    ),
    temporal=TemporalProfile(
        typical_hour_start=9,
        typical_hour_end=19,
        operates_outside_hours=False,  # Will be set to True dynamically during drift in generator
    ),
    recipients=RecipientProfile(
        known_recipient_ratio=0.85,  # Exactly same as normal
        unique_recipients_per_day=15,  # Exactly same as normal
    ),
    action_mix={"refund": 0.60, "retry": 0.20, "checkout": 0.15, "payout": 0.05},  # Exactly same as normal
    is_legitimate=False,
    drift_onset_day=15,
    key_signal="velocity_z spike, hour_distance spike, while transaction amounts are normal",
    mitigation="Behavioral drift detection → risk escalation",
)

# ============================================================================
# SCENARIO REGISTRY
# ============================================================================

ALL_SCENARIOS: dict[str, ScenarioDefinition] = {
    "normal": SCENARIO_NORMAL,
    "abuse_burst": SCENARIO_ABUSE_BURST,
    "misconfigured": SCENARIO_MISCONFIGURED,
    "slow_abuse": SCENARIO_SLOW_ABUSE,
    "seasonal_spike": SCENARIO_SEASONAL_SPIKE,
    "new_agent": SCENARIO_NEW_AGENT,
    "benign_drift": SCENARIO_BENIGN_DRIFT,
    "behavioral_evasion": SCENARIO_BEHAVIORAL_EVASION,
}

# Default scenario mix for data generation (~85% normal, ~2.5% each anomalous)
DEFAULT_SCENARIO_MIX: dict[str, float] = {
    "normal": 0.85,
    "abuse_burst": 0.021,
    "misconfigured": 0.021,
    "slow_abuse": 0.021,
    "seasonal_spike": 0.021,
    "new_agent": 0.021,
    "benign_drift": 0.021,
    "behavioral_evasion": 0.024,
}

# Multi-distribution experiments (recommendation #11)
EXPERIMENT_MIXES: dict[str, dict[str, float]] = {
    "A_baseline": {
        "normal": 0.85,
        "abuse_burst": 0.025,
        "misconfigured": 0.025,
        "slow_abuse": 0.025,
        "seasonal_spike": 0.025,
        "new_agent": 0.025,
        "benign_drift": 0.025,
    },
    "B_high_normal": {
        "normal": 0.91,
        "abuse_burst": 0.015,
        "misconfigured": 0.015,
        "slow_abuse": 0.015,
        "seasonal_spike": 0.015,
        "new_agent": 0.015,
        "benign_drift": 0.015,
    },
    "C_very_high_normal": {
        "normal": 0.95,
        "abuse_burst": 0.01,
        "misconfigured": 0.008,
        "slow_abuse": 0.008,
        "seasonal_spike": 0.008,
        "new_agent": 0.008,
        "benign_drift": 0.008,
    },
    "D_higher_anomaly": {
        "normal": 0.79,
        "abuse_burst": 0.035,
        "misconfigured": 0.035,
        "slow_abuse": 0.035,
        "seasonal_spike": 0.035,
        "new_agent": 0.035,
        "benign_drift": 0.025,
    },
}


def get_scenario(name: str) -> ScenarioDefinition:
    """Retrieve a scenario definition by name."""
    if name not in ALL_SCENARIOS:
        raise ValueError(f"Unknown scenario '{name}'. Available: {list(ALL_SCENARIOS.keys())}")
    return ALL_SCENARIOS[name]


def validate_scenario_mix(mix: dict[str, float], tolerance: float = 0.01) -> None:
    """Validate that a scenario mix is well-formed."""
    for name in mix:
        if name not in ALL_SCENARIOS:
            raise ValueError(f"Unknown scenario '{name}' in mix")
    total = sum(mix.values())
    if abs(total - 1.0) > tolerance:
        raise ValueError(f"Scenario mix proportions sum to {total}, expected ~1.0")
    for name, proportion in mix.items():
        if proportion < 0:
            raise ValueError(f"Negative proportion for scenario '{name}'")
