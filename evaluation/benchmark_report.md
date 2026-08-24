# Sentinel Benchmark Report

**Evaluation Suite**: v1 (Baseline) & v2 (Behavioral-Evasion Challenge)
**Hardware**: Standard Buildathon compute node (4 vCPU, 16GB RAM)

This benchmark evaluates the end-to-end performance of Sentinel across three distinct layers: Detection (ML), Governance (Policy), and Execution (Zero-Trust Gateway & MCP).

## Layer 1 — Detection Performance

**Can Sentinel identify abnormal agent behavior?**

We evaluated Sentinel using two frozen datasets with strict temporal holdouts (Days 26-30 as the isolated test set).

### Sentinel-v1 (Baseline)
The baseline synthetic dataset generated realistic autonomous abuse profiles. The results indicated that the generated abuse scenarios were highly separable at the transaction level.

| System | Precision | Recall | F1 | PR-AUC | False Escalation |
|--------|-----------|--------|----|--------|------------------|
| Transaction Only | 0.999 | 0.998 | 0.998 | 1.000 | 0.055% |
| Behavioral Only | 0.980 | 0.912 | 0.945 | 0.994 | 1.007% |
| Transaction + Behavioral | 1.000 | 1.000 | 1.000 | 1.000 | 0.000% |

### Sentinel-v2 (Behavioral-Evasion Challenge)
To test the core Sentinel hypothesis, we generated `sentinel-v2`, containing the `Behavioral Evasion` scenario. In this scenario, transaction distributions (amount, action mix) remain completely normal, but the agent's velocity and operating hours become highly anomalous. We explicitly tested this on unseen agents (G and H) which began with a legitimate prefix before transitioning to abuse.

| System | Precision | Recall | F1 | PR-AUC (Seen) | PR-AUC (Unseen) |
|--------|-----------|--------|----|---------------|-----------------|
| Transaction Only | 1.000 | 0.932 | 0.965 | 1.000 | 1.000 |
| Behavioral Only | 0.996 | 0.423 | 0.594 | 0.998 | 0.968 |
| Transaction + Behavioral | 1.000 | 0.436 | 0.607 | 1.000 | 0.983 |

**Investigation & Conclusion on ML Thesis**: 
The behavioral-evasion experiment did not produce a transaction-only failure. Transaction-only maintained 1.000 PR-AUC because the current transaction feature family includes contextual metadata such as operating hour and recipient novelty. This demonstrates that the present feature taxonomy itself provides strong detection capability, while leaving the incremental contribution of agent-level behavioral profiling unresolved.

Under the Sentinel-v2 synthetic behavioral-evasion scenario, transaction-level contextual features remained sufficient for perfect ranking performance.

## Layer 2 — Governance Performance

**What does Sentinel do with the detection?**

The governance layer sits above the ML detector. Its goal is to apply business logic to the raw risk scores, notably enforcing conservative safety policies on unknown agents.

| Metric | Measurement (Full Sentinel on v2) |
|--------|-------------|
| **False Escalation Rate** | 10.025% |
| **Containment Rate (Recall)** | 97.1% |
| **New-Agent Escalation Rate** | 100.0% (By Policy Design) |

**Conclusion on Governance**:
The 10.025% false escalation rate is not a detector failure; it is the intentional operating characteristic of Sentinel's conservative governance policy. Legitimate but entirely unseen agents (with `has_sufficient_history == 0`) are proactively escalated until a baseline profile is formed, ensuring fail-safe operation during cold starts.

## Layer 3 — Execution Performance

**Can a legitimate action safely reach Razorpay with minimal latency?**

Sentinel enforces a zero-trust boundary via cryptographic capability tokens before invoking the Razorpay Test MCP. 

### Security Invariants Proven
| Test Case | Condition | Result (MCP Calls) |
|-----------|-----------|--------------------|
| **Valid Execution** | Normal intent + valid risk score | ALLOW (MCP Invoked) |
| **Missing/Expired Token** | Direct call to gateway without valid token | BLOCK (0 calls) |
| **Privilege Violation** | Token allows `refund`, action is `payout` | BLOCK (0 calls) |
| **Agent Compromise** | Abnormal behavioral pattern detected | CONTAIN (0 calls) |

**The core security thesis is validated: No valid capability → no MCP invocation.**

### Latency Overhead
Sentinel demonstrates that agentic financial actions can be evaluated, governed, and executed through a zero-trust boundary while preserving a low-latency decision path. Measurements were collected via empirical execution on hardware, not extrapolated.

| Component | p50 Latency | p95 Latency | p99 Latency |
|-----------|-------------|-------------|-------------|
| Feature Extraction (Redis) | 8.1 ms | 12.4 ms | 18.2 ms |
| ML Inference (XGBoost) | 0.14 ms | 0.24 ms | 0.28 ms |
| Policy Engine | 1.2 ms | 2.1 ms | 3.5 ms |
| Execution Gateway | 2.5 ms | 3.8 ms | 5.2 ms |
| **Total Sentinel Overhead** | **~12 ms** | **~19 ms** | **~27 ms** |

*(External Razorpay MCP network latency typically ranges from ~150ms to ~400ms. Sentinel's sub-30ms overhead is highly performant and suitable for scale testing).*

## Final Integration Note
Sentinel integrates with Razorpay's Remote MCP server using the official Python MCP SDK (v2.0.0) and Streamable HTTP transport. The semantic engine (Vulcan) is currently described via a simulated integration boundary to prepare for future authorized access.
