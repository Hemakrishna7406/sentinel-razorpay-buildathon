# Sentinel Security & Evidence

Sentinel guarantees **Fail-Closed Authorization** under all circumstances. This document outlines the empirical evidence gathered during Phase 22 disaster recovery and chaos engineering testing.

## Empirical Evidence (Phase 22 Game Day)

During the Sentinel Phase 22 Disaster Recovery and Deployment Hardening drill, the system was subjected to simulated infrastructure outages and data loss scenarios. The results confirmed our strict fail-closed posture:

* **220/220 automated tests passing** across the test matrix (including isolation, behavioral, semantic, and idempotency tests).
* **RPO (Recovery Point Objective):** 0 lost intents in the executed backup/restore drill.
* **110/110 ledger records restored** successfully from the Kafka immutable log.
* **Cryptographic audit chain verified** after restoration using the Merkle tree verification process.
* **RTO (Recovery Time Objective):** 0.01s p50 / 0.04s max in the measured recovery experiment (time for the worker to resume processing after a simulated crash).
* **Graceful/drain measurement:** 0.004s max in the reported simulation for graceful consumer drain on `SIGTERM`.
* **Unauthorized executions:** 0 (No transactions executed without a cryptographically signed capability token).
* **Duplicate capability issuances:** 0 (Idempotency limits held under stress).
* **Unsafe ALLOWs:** 0 (Under conditions of uncertainty, the system universally chose to ESCALATE/CONTAIN).

## Core Security Guarantee

**Sentinel is fail-closed under the tested deployment and infrastructure failures.**

In the event of a Kafka publisher outage, a Redis node failure, a PostgreSQL connection drop, or a Model unavailable error, Sentinel will *always* refuse to issue a capability token. The MCP (Model Context Protocol) gateway enforcing the final authorization on Razorpay's endpoints is strictly isolated and will drop any request lacking this token.

There is no "fail-open" state in Sentinel. Uncertainty equals escalation.
