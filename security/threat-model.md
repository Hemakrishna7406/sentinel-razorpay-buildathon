# Sentinel Threat Model

This document outlines the end-to-end threat model for Sentinel, covering agent compromise, token theft, replay attacks, and MCP exploitation.

## 1. System Boundary
Sentinel acts as a zero-trust verification layer between Autonomous Financial Agents and the Razorpay MCP (Model Context Protocol) execution layer. The fundamental assumption is that the **Agent is inherently untrusted and potentially compromised**.

## 2. Threat Actors
- **Compromised Autonomous Agent**: An agent whose LLM or policy has been hijacked via prompt injection, adversarial drift, or account takeover.
- **Internal Threat**: A malicious operator attempting to manually invoke MCP tools.
- **Network Adversary**: An attacker attempting to intercept and replay capability tokens.

## 3. Attack Vectors & Mitigations

### 3.1. Unauthorized MCP Execution
**Threat**: Agent attempts to call Razorpay APIs or MCP tools directly, bypassing Sentinel.
**Mitigation**: The MCP server is firewalled and exclusively accepts connections from Sentinel's Execution Gateway. Sentinel's Application Code has exactly one governed path to execution.

### 3.2. Token Theft and Substitution
**Threat**: Attacker steals a valid Capability Token issued to Agent A and attempts to use it for Agent B.
**Mitigation**: Cryptographic invariant 4 strictly binds the Capability Token to `agent_id`. Token substitution will cause an immediate `Agent ID mismatch` rejection, with 0 downstream MCP calls.

### 3.3. Replay Attacks
**Threat**: Attacker intercepts a valid, executed token and attempts to submit it again to double the transaction amount.
**Mitigation**: Cryptographic invariant 6 (JTI/Nonce tracking) ensures a Capability Token can be consumed exactly once. Second attempts result in immediate rejection.

### 3.4. Privilege Escalation (Amount / Action)
**Threat**: Agent is authorized for a ₹500 payout, but modifies the request to ₹50,000 before sending it to the Gateway.
**Mitigation**: Cryptographic invariant 8 (Immutability). Modifying the payload invalidates the HMAC-SHA256 signature. Modifying the request intent without modifying the payload triggers Invariant 1 (Amount mismatch).

### 3.5. Component Unavailability (Fail-Closed)
**Threat**: Attackers DDoS the Redis cache, ML model, or Policy Engine in hopes that the system fails open.
**Mitigation**: Sentinel defaults to `BLOCK` or `ESCALATE` upon any internal exception. No uncertainty may silently become ALLOW.

## 4. Conclusion
Sentinel's execution boundary is resilient to network interception, credential theft, and prompt-injection-driven privilege escalation.
