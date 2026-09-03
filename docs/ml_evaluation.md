# ML Evaluation & Drift Remediation

## The Leakage Problem
In the original iteration of Sentinel, the feature generator inadvertently introduced **target leakage** and **temporal leakage**. Specifically, synthetic ground-truth parameters (such as `baseline_avg_amount`) used to label the data were passed directly into the XGBoost feature array. Additionally, agent age was provided as a static feature, creating a proxy for temporal progression. As a result, the model achieved a synthetically inflated Precision-Recall AUC (PR-AUC) of `>0.94` because it was mathematically memorizing the ground truth rather than learning to detect behavioral drift.

## Remediation Methodology
To resolve this and provide an honest assessment of Sentinel's capability to detect behavioral drift, we implemented the following changes:
1. **Strict Temporal Isolation**: Removed all generative parameters (`baseline_avg_amount`, `baseline_std_amount`, `anomaly_label`) from the feature set.
2. **Rolling Expanding Windows**: State-dependent behavioral features are now constructed strictly from historical observations. We implemented an `.expanding()` window explicitly shifted by `1` (`shift(1)`) to guarantee that the baseline for transaction $T$ is computed exclusively from transactions $0$ to $T-1$.
3. **Cold Start Penalties**: The model now enforces a cold start phase. Agents with fewer than 5 transactions are penalized with neutral Z-scores, forcing the model to rely on deterministic policy bounds until sufficient behavioral history is established.

## Final Metrics
Upon retraining the XGBoost model on the corrected, temporally-strict dataset, the evaluation metrics restabilized at their true performance levels:
- **PR-AUC**: ~0.17
- **ROC-AUC**: ~0.76

### Why 0.17 is the Correct Metric
While a PR-AUC of 0.17 is optically lower than 0.94, it is the mathematically honest metric for a severely imbalanced dataset (fraud events constitute < 1% of total volume). An inflated 0.94 PR-AUC on an imbalanced dataset implies target leakage. The 0.17 metric confirms that Sentinel is effectively learning genuine behavioral drift without relying on the hidden answer key.

## Limitations & Future Work
1. **Synthetic Limitations**: The current dataset is fully synthetic. Real-world financial telemetry contains significantly more noise and seasonal periodicity (e.g., end-of-month payroll).
2. **Feature Breadth**: The model currently relies heavily on velocity and standard-deviation tracking. Incorporating graph-based features (e.g., recipient hop counts) would significantly increase the true PR-AUC in production.
