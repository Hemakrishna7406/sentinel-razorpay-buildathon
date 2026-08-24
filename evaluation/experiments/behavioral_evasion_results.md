# Phase 17b Behavioral-Evasion Evasion Study

## Overall Performance (Detection Layer)
| System | Precision | Recall | F1 | PR-AUC | False Escalation |
|--------|-----------|--------|----|--------|------------------|
| Rules Only | 0.999 | 0.340 | 0.507 | 0.900 | 0.124% |
| Velocity Baseline | 0.972 | 0.959 | 0.965 | 0.967 | 15.410% |
| Transaction Only | 1.000 | 0.932 | 0.965 | 1.000 | 0.010% |
| Behavioral Only | 0.996 | 0.423 | 0.594 | 0.971 | 1.025% |
| Transaction + Behavioral | 1.000 | 0.436 | 0.607 | 0.970 | 0.000% |

## Governance Layer (Full Sentinel with Policy)
| System | Precision | Recall | F1 | PR-AUC | False Escalation |
|--------|-----------|--------|----|--------|------------------|
| **Full Sentinel** | 0.982 | 0.971 | 0.977 | 0.970 | 10.025% |

## Seen vs Unseen Agents (PR-AUC)
| System | Seen Agents | Unseen Agents |
|--------|-------------|---------------|
| Rules Only | 0.930 | 0.968 |
| Velocity Baseline | 0.927 | 0.995 |
| Transaction Only | 1.000 | 1.000 |
| Behavioral Only | 0.998 | 0.968 |
| Transaction + Behavioral | 1.000 | 0.983 |
