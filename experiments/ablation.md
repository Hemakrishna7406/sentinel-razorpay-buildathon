# Sentinel Ablation Study

> **Research Question (H1):** Does incorporating agent-level behavioral context improve detection of autonomous financial abuse over transaction-level signals alone?

## Results

| Configuration | PR-AUC | Precision | Recall | False Escalation | Unsafe Auto-Approval |
|---------------|--------|-----------|--------|------------------|----------------------|
| Rules Only (Baseline) | 0.598 | 0.856 | 0.650 | 1.469%| 34.959% |
| Transaction Only | 1.000 | 1.000 | 0.996 | 0.000%| 0.407% |
| Behavioral Only | 0.998 | 1.000 | 0.951 | 0.000%| 4.878% |
| Full Sentinel | 1.000 | 1.000 | 1.000 | 0.000%| 0.000% |

## Conclusion

⚠️ **H1 Weakly Accepted:** Behavioral context provides marginal improvement over transaction-only signals.

## Model Selection

The `full_sentinel` model was selected as the final artifact.
- Selected Hyperparameters: max_depth=4, lr=0.05
- Optimal Decision Threshold (Suspicious): 0.827
