# Sentinel Ablation Study

> **Research Question (H1):** Does incorporating agent-level behavioral context improve detection of autonomous financial abuse over transaction-level signals alone?

## Results

| Configuration | PR-AUC | Precision | Recall | False Escalation | Unsafe Auto-Approval |
|---------------|--------|-----------|--------|------------------|----------------------|
| Rules Only (Baseline) | 0.788 | 0.928 | 0.065 | 1.755%| 93.523% |
| Transaction Only | 0.783 | 0.778 | 1.000 | 100.000%| 0.000% |
| Behavioral Only | 0.775 | 0.779 | 0.997 | 99.532%| 0.300% |
| Full Sentinel | 0.753 | 0.778 | 1.000 | 100.000%| 0.000% |

## Conclusion

❌ **H0 Accepted:** Behavioral context does not improve detection performance in this synthetic environment.

## Model Selection

The `full_sentinel` model was selected as the final artifact.
- Selected Hyperparameters: max_depth=4, lr=0.05
- Optimal Decision Threshold (Suspicious): 0.208
