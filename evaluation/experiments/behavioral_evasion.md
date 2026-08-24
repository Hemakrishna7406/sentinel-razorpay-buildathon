# Sentinel-v2: Behavioral-Evasion Challenge

This document pre-registers the methodology, hypothesis, and expected metrics for the `sentinel-v2` benchmark experiment.

## The Challenge Scenario
The v1 benchmark demonstrated that transaction-level features achieved perfect separation (PR-AUC 1.000), meaning the synthetic anomalies were obvious at the transaction level. 

To test the core thesis of Sentinel, we introduce a new dataset (`sentinel_v2`) containing the `SCENARIO_BEHAVIORAL_EVASION` scenario, designed such that:
- **Transaction Features**: Perfectly mirror the legitimate distribution (Amount = Normal, Action Mix = Normal, Known Recipient).
- **Behavioral Features**: Highly anomalous (Velocity = 15x baseline, Abnormal operating hours).

### Unseen Agent Abuse (Generalization)
Agents G and H (which first appear in the test set on Day 26) will execute 5-10 legitimate actions to build a minimal profile, then abruptly transition into `SCENARIO_BEHAVIORAL_EVASION`.

## Hypotheses

### H1 (Alternative Hypothesis)

Sentinel provides a zero-trust behavioral risk and governance layer around autonomous financial agents, combining risk signals with deterministic policy and exact-action capability authorization before an agent can reach financial execution infrastructure. We hypothesize that while pure behavioral evasion challenges ML detectors, embedding contextual metadata (operating hours, novelty) directly into the transaction evaluation maintains high detection capabilities.

### H0 (Null Hypothesis)
Behavioral features provide no measurable advantage over transaction-level features under the behavioral-evasion scenario (Transaction Only remains perfectly separable, or Behavioral Only fails).

## Experimental Design

### Primary Comparison
We will evaluate the following models on the isolated test set (Days 26-30):
1. **Transaction Only**
2. **Behavioral Only**
3. **Transaction + Behavioral** (Full Sentinel ML)

### Primary Metrics
- **PR-AUC**: Measures the ability to separate evasion from legitimate behavior across thresholds.
- **Recall**: Measures the ability to detect evasion abuse at the chosen operating point.
- **Precision**: Measures the false positive rate on legitimate intents.
- **F1 Score**: Harmonic mean of Precision and Recall.
- **False Escalation Rate**: The governance friction on legitimate intents.

### Generalization Analysis
We will separately compute PR-AUC for:
- **Seen Agents**: Agents present in the training set (A-F).
- **Unseen Agents**: Agents exclusively in the test set (G-H).

*This methodology is locked prior to viewing the experimental results.*
