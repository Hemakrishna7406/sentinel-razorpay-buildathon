# Phase 17 Ablation Study

## Overall Performance
| System | Precision | Recall | F1 | PR-AUC | False Escalation |
|--------|-----------|--------|----|--------|------------------|
| Rules Only | 0.964 | 0.839 | 0.898 | 0.866 | 1.672% |
| Velocity Baseline | 0.691 | 0.908 | 0.785 | 0.660 | 21.979% |
| Transaction Only | 0.999 | 0.998 | 0.998 | 1.000 | 0.055% |
| Behavioral Only | 0.980 | 0.912 | 0.945 | 0.994 | 1.007% |
| Transaction + Behavioral | 1.000 | 1.000 | 1.000 | 1.000 | 0.000% |
| **Full Sentinel** | 0.755 | 1.000 | 0.861 | 1.000 | 17.489% |

## Seen vs Unseen Agents (PR-AUC)
| System | Seen Agents | Unseen Agents |
|--------|-------------|---------------|
| Rules Only | 0.877 | 0.000 |
| Velocity Baseline | 0.751 | 0.000 |
| Transaction Only | 1.000 | 0.000 |
| Behavioral Only | 0.994 | 0.000 |
| Transaction + Behavioral | 1.000 | 0.000 |
| Full Sentinel | 1.000 | 0.000 |
