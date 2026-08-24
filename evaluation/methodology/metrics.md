# Sentinel Evaluation Metrics

This document provides explicit definitions for all metrics used in the Sentinel benchmark to ensure reproducibility.

## 1. Detection Metrics (ML Layer)

Evaluated against the ground truth `loss_label` (0 = no loss, 1 = unauthorized action / policy violation).

*   **Precision**: `True Positives / (True Positives + False Positives)`
    *   Measures: Of all intents the model flagged as anomalous, what fraction were actually anomalous?
*   **Recall**: `True Positives / (True Positives + False Negatives)`
    *   Measures: Of all actual anomalous intents, what fraction did the model successfully flag?
*   **F1 Score**: `2 * (Precision * Recall) / (Precision + Recall)`
    *   Measures: The harmonic mean of precision and recall.
*   **PR-AUC**: Area under the Precision-Recall curve.
    *   Measures: The overall performance across all possible classification thresholds. (If no positive instances exist in the subset, PR-AUC = N/A).
*   **AUROC**: Area under the Receiver Operating Characteristic curve.
    *   Measures: The model's ability to discriminate between positive and negative classes across all thresholds.

## 2. Governance Metrics (Policy Layer)

Evaluated based on the final policy decision (ALLOW, ESCALATE, CONTAIN).

*   **False Escalation Rate**: `# legitimate test intents escalated / # all legitimate test intents`
    *   Note: "Escalated" includes both `ESCALATE` and `CONTAIN` decisions on ground-truth legitimate intents.
*   **Containment Rate**: `# anomalous test intents contained / # all anomalous test intents`
    *   Measures: The policy's ability to block malicious intent.
*   **Auto-approval Rate**: `# intents ALLOWED / # all intents`
    *   Measures: The proportion of intent passing through without friction.
*   **Unsafe Auto-approval Rate**: `# anomalous test intents ALLOWED / # all anomalous test intents`
    *   Measures: The critical failure rate where policy allows a loss event to proceed.
*   **New-Agent Escalation Rate**: `# legitimate test intents from new agents escalated / # legitimate test intents from new agents`
    *   Measures: The friction applied specifically to agents with insufficient history.

## 3. Execution Metrics (Gateway Layer)

*   **Capability Issuance Rate**: `# valid capability tokens issued / # valid requests`
*   **MCP Invocation Rate**: `# successful MCP tool executions / # capability tokens presented`
