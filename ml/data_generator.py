import json
import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from ml.scenarios import (
    ALL_SCENARIOS,
    DEFAULT_SCENARIO_MIX,
    ScenarioDefinition,
    ThreatActor,
    get_scenario,
    validate_scenario_mix,
)

logger = logging.getLogger(__name__)


def set_seed(seed: int) -> None:
    """Set the deterministic random seed."""
    random.seed(seed)


def generate_id() -> str:
    """Generate a pseudo-random UUID-like string using random for determinism."""
    return f"{random.getrandbits(32):08x}-{random.getrandbits(16):04x}-{random.getrandbits(16):04x}-{random.getrandbits(16):04x}-{random.getrandbits(48):012x}"


def get_random_action(action_mix: Dict[str, float]) -> str:
    """Pick an action type based on the defined mix."""
    actions = list(action_mix.keys())
    weights = list(action_mix.values())
    return random.choices(actions, weights=weights, k=1)[0]


def get_random_amount(amount_def: Any) -> int:
    """Generate a random amount in paise within the scenario distribution."""
    # Approximate a normal distribution bounded by min and max
    while True:
        val = int(random.gauss(amount_def.mean, amount_def.std))
        if amount_def.min_amount <= val <= amount_def.max_amount:
            return val


class AgentState:
    """Tracks state for an agent during generation."""
    def __init__(self, agent_id: str, scenario: ScenarioDefinition, start_day: int):
        self.agent_id = agent_id
        self.scenario = scenario
        self.start_day = start_day
        self.known_recipients: set[str] = set()
        self.last_action_time: Optional[datetime] = None
        self.action_history: List[datetime] = []
        
        # Baseline stats for context
        self.baseline_avg_amount = scenario.amount.mean
        self.baseline_std_amount = scenario.amount.std
        self.baseline_hourly_rate = scenario.velocity.actions_per_hour_mean
        self.typical_hour_start = scenario.temporal.typical_hour_start
        self.typical_hour_end = scenario.temporal.typical_hour_end
        
        # We start with default values for historical stats
        self.historical_escalation_rate = 0.05
        self.historical_denial_rate = 0.01

    def get_recipient(self, is_novel: bool) -> str:
        """Get a recipient ID (either novel or from history)."""
        if is_novel or not self.known_recipients:
            new_recip = f"recp_{generate_id()[:8]}"
            self.known_recipients.add(new_recip)
            return new_recip
        return random.choice(list(self.known_recipients))
        
    def add_action(self, dt: datetime):
        self.last_action_time = dt
        self.action_history.append(dt)
        
        # Keep only last 24h for rolling counts
        cutoff = dt - timedelta(days=1)
        self.action_history = [t for t in self.action_history if t > cutoff]

    def get_rolling_counts(self, dt: datetime) -> Tuple[int, int, int]:
        count_1m = sum(1 for t in self.action_history if dt - t <= timedelta(minutes=1))
        count_1h = sum(1 for t in self.action_history if dt - t <= timedelta(hours=1))
        count_24h = sum(1 for t in self.action_history if dt - t <= timedelta(hours=24))
        return count_1m, count_1h, count_24h


def _generate_intent_row(
    agent: AgentState,
    dt: datetime,
    day_idx: int,
    is_novel_recipient: bool,
    amount_override: Optional[int] = None,
    action_override: Optional[str] = None
) -> Dict[str, Any]:
    """Create a single intent record."""
    
    amount = amount_override if amount_override is not None else get_random_amount(agent.scenario.amount)
    action_type = action_override if action_override is not None else get_random_action(agent.scenario.action_mix)
    recipient_id = agent.get_recipient(is_novel_recipient)
    
    time_since_last = (dt - agent.last_action_time).total_seconds() if agent.last_action_time else -1.0
    
    agent.add_action(dt)
    count_1m, count_1h, count_24h = agent.get_rolling_counts(dt)
    
    # If agent started after day 20, they are unseen (test agents G/H)
    is_unseen = agent.start_day > 20
    
    # Determine if agent is currently drifting
    is_drifting = False
    if agent.scenario.name == "Behavioral Evasion":
        drift_day = 28 if is_unseen else agent.scenario.drift_onset_day
        is_drifting = day_idx >= drift_day
    elif agent.scenario.name in ["Abuse Burst", "Slow / Threshold-Aware Abuse", "Benign Behavioral Drift"]:
        is_drifting = day_idx >= (agent.scenario.drift_onset_day or 999)
        
    # If the scenario is anomalous, it only counts as a loss event during/after drift (if applicable)
    # or always if there is no drift onset (like misconfigured)
    actual_loss_label = agent.scenario.loss_label
    if agent.scenario.drift_onset_day and not is_drifting:
        actual_loss_label = 0
        
    row = {
        "intent_id": generate_id(),
        "agent_id": agent.agent_id,
        "timestamp": dt,
        "day": day_idx,
        "action_type": action_type,
        "transaction_id": generate_id(),
        "amount": amount,
        "currency": "INR",
        "recipient_id": recipient_id,
        "recipient_novelty": 1 if is_novel_recipient else 0,
        "merchant_id": f"merch_{agent.agent_id}",
        "agent_age_days": day_idx - agent.start_day + 1,
        "hour_of_day": dt.hour,
        "time_since_previous_action": time_since_last,
        "rolling_1m_count": count_1m,
        "rolling_1h_count": count_1h,
        "rolling_24h_count": count_24h,
        
        "baseline_avg_amount": agent.baseline_avg_amount,
        "baseline_std_amount": agent.baseline_std_amount,
        "baseline_hourly_rate": agent.baseline_hourly_rate,
        "typical_hour_start": agent.typical_hour_start,
        "typical_hour_end": agent.typical_hour_end,
        "historical_escalation_rate": agent.historical_escalation_rate,
        "historical_denial_rate": agent.historical_denial_rate,
        
        "scenario_label": agent.scenario.name,
        "loss_label": actual_loss_label,
        "loss_type": agent.scenario.loss_type.value if actual_loss_label == 1 and agent.scenario.loss_type else None,
        "has_sufficient_history": 0 if is_unseen else int(agent.scenario.has_sufficient_history)
    }
    return row


def generate_agent_history(
    agent_id: str,
    scenario_name: str,
    start_date: datetime,
    num_days: int = 30,
    start_day_idx: int = 1
) -> List[Dict[str, Any]]:
    """Generate the full history for a single agent based on its scenario."""
    scenario = get_scenario(scenario_name)
    agent = AgentState(agent_id, scenario, start_day_idx)
    rows = []
    
    for day_offset in range(num_days):
        current_day = start_day_idx + day_offset
        current_date = start_date + timedelta(days=day_offset)
        
        # Determine active hours and rates based on scenario logic
        start_hour = scenario.temporal.typical_hour_start
        end_hour = scenario.temporal.typical_hour_end
        hourly_rate = scenario.velocity.actions_per_hour_mean
        novel_ratio = 1.0 - scenario.recipients.known_recipient_ratio
        
        # Apply scenario-specific overrides
        if scenario.name == "Abuse Burst":
            if scenario.drift_onset_day and current_day >= scenario.drift_onset_day:
                hourly_rate *= scenario.velocity.burst_factor
                start_hour = 0
                end_hour = 23
        elif scenario.name == "Behavioral Evasion":
            # For unseen agents starting late, drift on Day 28. Otherwise, scenario default.
            drift_day = 28 if agent.start_day >= 26 else scenario.drift_onset_day
            if drift_day and current_day >= drift_day:
                hourly_rate *= scenario.velocity.burst_factor
                start_hour = 0
                end_hour = 23
                novel_ratio = 1.0 # Force high recipient novelty to trigger anomaly
        elif scenario.name == "Seasonal Spike":
            if scenario.spike_start_day and scenario.spike_end_day:
                if scenario.spike_start_day <= current_day <= scenario.spike_end_day:
                    hourly_rate *= scenario.spike_volume_multiplier
        elif scenario.name == "Slow / Threshold-Aware Abuse":
            if scenario.drift_onset_day and current_day >= scenario.drift_onset_day:
                 pass # Rate stays low, but amounts cluster near max (handled in get_random_amount logic ideally, but we'll use default distribution for now as it's defined to be clustered)
        elif scenario.name == "Benign Behavioral Drift":
             if scenario.drift_onset_day and current_day >= scenario.drift_onset_day:
                 # Shift hours
                 start_hour = 11
                 end_hour = 23
        
        # Generate actions for this day
        num_actions = int(random.gauss(hourly_rate * (end_hour - start_hour + 1), scenario.velocity.actions_per_hour_std * (end_hour - start_hour + 1)))
        num_actions = max(0, num_actions)
        
        for _ in range(num_actions):
            hour = random.randint(start_hour, end_hour)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            dt = current_date.replace(hour=hour, minute=minute, second=second)
            
            is_novel = random.random() < novel_ratio
            rows.append(_generate_intent_row(agent, dt, current_day, is_novel))
            
    # Sort by timestamp
    rows.sort(key=lambda x: x["timestamp"])
    return rows


def generate_dataset(
    seed: int = 42,
    num_agents_train_val: int = 6, # A-F
    num_agents_test_only: int = 2, # G-H
    days: int = 30,
    scenario_mix: Optional[Dict[str, float]] = None,
    out_path: Optional[str] = None
) -> pd.DataFrame:
    """Generate the full dataset."""
    set_seed(seed)
    
    if scenario_mix is None:
        scenario_mix = DEFAULT_SCENARIO_MIX
    validate_scenario_mix(scenario_mix)
    
    start_date = datetime(2026, 1, 1)
    all_rows = []
    
    # Train/Val agents (A-F) operate for the full 30 days
    train_val_agents = [chr(ord('A') + i) for i in range(num_agents_train_val)]
    for agent_id in train_val_agents:
        # Pick a scenario for this agent based on mix
        scenario_name = random.choices(list(scenario_mix.keys()), weights=list(scenario_mix.values()))[0]
        rows = generate_agent_history(agent_id, scenario_name, start_date, num_days=days)
        all_rows.extend(rows)
        
    # Test-only agents (G-H) operate only in days 26-30
    test_only_agents = [chr(ord('A') + num_agents_train_val + i) for i in range(num_agents_test_only)]
    test_start_date = start_date + timedelta(days=25)
    for agent_id in test_only_agents:
        # Test agents build normal history for 2 days, then evade on day 28
        scenario_name = "behavioral_evasion" 
        rows = generate_agent_history(agent_id, scenario_name, test_start_date, num_days=5, start_day_idx=26)
        all_rows.extend(rows)
        
    df = pd.DataFrame(all_rows)
    df.sort_values(by="timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    if out_path:
        df.to_csv(out_path, index=False)
        
    return df

if __name__ == "__main__":
    df = generate_dataset()
    print(f"Generated {len(df)} rows.")
    print(df.head())
